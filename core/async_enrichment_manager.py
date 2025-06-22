# core/async_enrichment_manager.py

import asyncio
import aiohttp
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
from enum import Enum

from .intelligent_cache import get_cache
from .adaptive_rate_limiter import get_rate_limiter, RequestResult

class TaskStatus(Enum):
    """Estados de una tarea de enriquecimiento."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class EnrichmentTask:
    """Tarea de enriquecimiento asíncrono."""
    task_id: str
    track_info: Dict
    sources: List[str]
    callback: Optional[Callable] = None
    priority: int = 1  # 1=alta, 2=media, 3=baja
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = None
    started_at: float = None
    completed_at: float = None
    results: Dict = None
    errors: List[str] = None
    progress: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.results is None:
            self.results = {}
        if self.errors is None:
            self.errors = []

@dataclass
class BatchEnrichmentTask:
    """Tarea de enriquecimiento por lotes."""
    batch_id: str
    tasks: List[EnrichmentTask]
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    completed_tasks: int = 0
    total_tasks: int = 0
    callback: Optional[Callable] = None
    
    def __post_init__(self):
        self.total_tasks = len(self.tasks)

class AsyncEnrichmentManager:
    """
    Gestor de enriquecimiento asíncrono que coordina múltiples fuentes API
    de forma concurrente con gestión inteligente de recursos.
    
    Features:
    - Procesamiento verdaderamente asíncrono
    - Pool de workers configurables 
    - Cola de prioridades para tareas
    - Batch processing para múltiples tracks
    - Progress tracking en tiempo real
    - Circuit breaker para APIs fallidas
    - Resource pooling y connection reuse
    """
    
    def __init__(self, max_concurrent_tasks: int = 10, max_workers_per_source: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_workers_per_source = max_workers_per_source
        
        # Task management
        self.task_queue = queue.PriorityQueue()
        self.active_tasks: Dict[str, EnrichmentTask] = {}
        self.completed_tasks: Dict[str, EnrichmentTask] = {}
        self.batch_tasks: Dict[str, BatchEnrichmentTask] = {}
        
        # Worker management
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.worker_pools = {}  # Por fuente
        self.active_workers = 0
        
        # HTTP session pools para async requests
        self.session_pools: Dict[str, aiohttp.ClientSession] = {}
        
        # Control de flujo
        self.is_running = False
        self.worker_thread = None
        self.lock = threading.RLock()
        
        # Métricas
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_processing_time': 0.0,
            'cache_hits': 0,
            'api_calls': 0
        }
        
        # Integración con otros sistemas
        self.cache = get_cache()
        self.rate_limiter = get_rate_limiter()
        
        # Configuración de fuentes
        self.source_config = {
            'musicbrainz': {
                'concurrent_limit': 2,  # MusicBrainz es estricto
                'timeout': 15.0,
                'circuit_breaker_threshold': 5
            },
            'spotify': {
                'concurrent_limit': 5,  # Spotify permite más concurrencia
                'timeout': 12.0,
                'circuit_breaker_threshold': 8
            },
            'discogs': {
                'concurrent_limit': 3,  # Moderado
                'timeout': 18.0,
                'circuit_breaker_threshold': 4
            },
            'lastfm': {
                'concurrent_limit': 4,  # Generoso
                'timeout': 10.0,
                'circuit_breaker_threshold': 6
            }
        }
        
        self._initialize_worker_pools()
    
    def _initialize_worker_pools(self):
        """Inicializa pools de workers para cada fuente."""
        for source, config in self.source_config.items():
            max_workers = min(config['concurrent_limit'], self.max_workers_per_source)
            self.worker_pools[source] = ThreadPoolExecutor(max_workers=max_workers)
    
    def start(self):
        """Inicia el gestor asíncrono."""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("🚀 AsyncEnrichmentManager iniciado")
    
    def stop(self):
        """Detiene el gestor asíncrono."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        # Cerrar executor y pools
        self.executor.shutdown(wait=False)
        for pool in self.worker_pools.values():
            pool.shutdown(wait=False)
        
        # Cerrar sessiones HTTP
        asyncio.run(self._close_http_sessions())
        
        print("🛑 AsyncEnrichmentManager detenido")
    
    async def _close_http_sessions(self):
        """Cierra todas las sesiones HTTP."""
        for session in self.session_pools.values():
            if session and not session.closed:
                await session.close()
        self.session_pools.clear()
    
    def _worker_loop(self):
        """Loop principal del worker que procesa la cola de tareas."""
        while self.is_running:
            try:
                # Obtener tarea con timeout
                try:
                    priority, task_id = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Verificar si la tarea aún existe
                if task_id not in self.active_tasks:
                    continue
                
                task = self.active_tasks[task_id]
                
                # Procesar tarea
                try:
                    self._process_task(task)
                except Exception as e:
                    print(f"❌ Error procesando tarea {task_id}: {e}")
                    task.status = TaskStatus.FAILED
                    task.errors.append(str(e))
                finally:
                    self.task_queue.task_done()
                
            except Exception as e:
                print(f"❌ Error en worker loop: {e}")
                time.sleep(0.1)
    
    def enrich_track_async(self, track_info: Dict, sources: List[str] = None,
                          priority: int = 1, callback: Callable = None) -> str:
        """
        Inicia enriquecimiento asíncrono de un track.
        
        Args:
            track_info: Información del track
            sources: Lista de fuentes a consultar (None = todas)
            priority: Prioridad de la tarea (1=alta, 3=baja)
            callback: Función callback para notificar resultados
            
        Returns:
            Task ID para seguimiento
        """
        if not self.is_running:
            self.start()
        
        if sources is None:
            sources = list(self.source_config.keys())
        
        # Generar task ID único
        task_id = f"task_{int(time.time() * 1000)}_{hash(str(track_info)) % 10000}"
        
        # Crear tarea
        task = EnrichmentTask(
            task_id=task_id,
            track_info=track_info,
            sources=sources,
            callback=callback,
            priority=priority
        )
        
        # Registrar tarea
        with self.lock:
            self.active_tasks[task_id] = task
            self.stats['total_tasks'] += 1
        
        # Añadir a cola con prioridad
        self.task_queue.put((priority, task_id))
        
        print(f"📝 Tarea async creada: {task_id} (fuentes: {', '.join(sources)})")
        return task_id
    
    def enrich_batch_async(self, tracks_info: List[Dict], sources: List[str] = None,
                          callback: Callable = None) -> str:
        """
        Inicia enriquecimiento por lotes de múltiples tracks.
        
        Args:
            tracks_info: Lista de información de tracks
            sources: Fuentes a consultar
            callback: Callback para progreso del lote
            
        Returns:
            Batch ID para seguimiento
        """
        if not tracks_info:
            return None
        
        batch_id = f"batch_{int(time.time() * 1000)}"
        
        # Crear tareas individuales
        tasks = []
        for i, track_info in enumerate(tracks_info):
            task_id = f"{batch_id}_track_{i}"
            task = EnrichmentTask(
                task_id=task_id,
                track_info=track_info,
                sources=sources or list(self.source_config.keys()),
                priority=2  # Prioridad media para batches
            )
            tasks.append(task)
        
        # Crear batch task
        batch_task = BatchEnrichmentTask(
            batch_id=batch_id,
            tasks=tasks,
            callback=callback
        )
        
        # Registrar batch y tareas individuales
        with self.lock:
            self.batch_tasks[batch_id] = batch_task
            for task in tasks:
                self.active_tasks[task.task_id] = task
                self.stats['total_tasks'] += 1
                self.task_queue.put((task.priority, task.task_id))
        
        print(f"📦 Batch async creado: {batch_id} ({len(tasks)} tracks)")
        return batch_id
    
    def _process_task(self, task: EnrichmentTask):
        """Procesa una tarea individual."""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = time.time()
        
        print(f"⚡ Procesando {task.task_id} con fuentes: {', '.join(task.sources)}")
        
        # Procesar fuentes concurrentemente
        with ThreadPoolExecutor(max_workers=len(task.sources)) as executor:
            # Crear futures para cada fuente
            future_to_source = {}
            for source in task.sources:
                future = executor.submit(self._enrich_from_source, task, source)
                future_to_source[future] = source
            
            # Recopilar resultados conforme completan
            completed_sources = 0
            for future in as_completed(future_to_source.keys()):
                source = future_to_source[future]
                try:
                    result = future.result()
                    if result:
                        task.results[source] = result
                except Exception as e:
                    task.errors.append(f"{source}: {str(e)}")
                
                completed_sources += 1
                task.progress = completed_sources / len(task.sources)
        
        # Finalizar tarea
        task.completed_at = time.time()
        task.status = TaskStatus.COMPLETED if task.results else TaskStatus.FAILED
        task.progress = 1.0
        
        # Actualizar estadísticas
        with self.lock:
            self.stats['completed_tasks'] += 1
            if task.status == TaskStatus.FAILED:
                self.stats['failed_tasks'] += 1
            
            processing_time = task.completed_at - task.started_at
            current_avg = self.stats['avg_processing_time']
            completed = self.stats['completed_tasks']
            self.stats['avg_processing_time'] = (current_avg * (completed - 1) + processing_time) / completed
        
        # Mover a completed
        with self.lock:
            self.completed_tasks[task.task_id] = task
            del self.active_tasks[task.task_id]
        
        # Ejecutar callback si existe
        if task.callback:
            try:
                task.callback(task)
            except Exception as e:
                print(f"❌ Error en callback de {task.task_id}: {e}")
        
        # Actualizar batch si es parte de uno
        self._update_batch_progress(task)
        
        print(f"✅ Completado {task.task_id} en {processing_time:.2f}s")
    
    def _enrich_from_source(self, task: EnrichmentTask, source: str) -> Optional[Dict]:
        """Enriquece desde una fuente específica."""
        track_info = task.track_info
        artist = track_info.get('artist', '')
        title = track_info.get('title', '')
        
        # Verificar cache primero
        cached_result = self.cache.get(artist, title, source)
        if cached_result:
            with self.lock:
                self.stats['cache_hits'] += 1
            return cached_result
        
        # Wait for rate limiting
        wait_time = self.rate_limiter.wait_for_rate_limit(source)
        
        # Obtener timeout optimizado
        timeout = self.rate_limiter.get_optimal_timeout(source)
        
        # Realizar petición
        start_time = time.time()
        result = None
        error_occurred = False
        
        try:
            # Llamar función de enriquecimiento específica
            enrichment_func = self._get_enrichment_function(source)
            if enrichment_func:
                result = enrichment_func(track_info, source)
                
            with self.lock:
                self.stats['api_calls'] += 1
            
        except Exception as e:
            error_occurred = True
            response_time = time.time() - start_time
            
            # Determinar tipo de error
            was_timeout = "timeout" in str(e).lower()
            was_throttled = "429" in str(e) or "rate limit" in str(e).lower()
            
            # Registrar resultado en rate limiter
            api_result = RequestResult(
                success=False,
                response_time=response_time,
                error_type=type(e).__name__,
                was_timeout=was_timeout,
                was_throttled=was_throttled
            )
            self.rate_limiter.record_request_result(source, api_result)
            
            print(f"❌ Error en {source} para {artist} - {title}: {e}")
            return None
        
        # Si fue exitoso
        if result and not error_occurred:
            response_time = time.time() - start_time
            
            # Calcular confidence (básico)
            confidence = 0.8 if result.get('genre') else 0.3
            
            # Registrar éxito en rate limiter
            api_result = RequestResult(
                success=True,
                response_time=response_time
            )
            self.rate_limiter.record_request_result(source, api_result)
            
            # Guardar en cache
            self.cache.put(artist, title, source, result, confidence)
            
            return result
        
        return None
    
    def _get_enrichment_function(self, source: str) -> Optional[Callable]:
        """Obtiene la función de enriquecimiento para una fuente."""
        # Importar dinámicamente para evitar dependencias circulares
        try:
            if source == 'musicbrainz':
                from .metadata_enricher import _search_musicbrainz
                return lambda track_info, src: _search_musicbrainz(track_info)
            elif source == 'spotify':
                from .metadata_enricher import _search_spotify
                return lambda track_info, src: _search_spotify(track_info)
            elif source == 'discogs':
                from .metadata_enricher import _search_discogs
                return lambda track_info, src: _search_discogs(track_info)
            elif source == 'lastfm':
                from .lastfm_client import search_lastfm_genres
                return lambda track_info, src: search_lastfm_genres(
                    track_info.get('artist', ''), 
                    track_info.get('title', '')
                )
        except ImportError as e:
            print(f"⚠️ No se pudo importar función para {source}: {e}")
        
        return None
    
    def _update_batch_progress(self, completed_task: EnrichmentTask):
        """Actualiza progreso de batch si la tarea es parte de uno."""
        # Buscar batch que contenga esta tarea
        for batch_id, batch_task in self.batch_tasks.items():
            task_ids = [t.task_id for t in batch_task.tasks]
            if completed_task.task_id in task_ids:
                batch_task.completed_tasks += 1
                batch_task.progress = batch_task.completed_tasks / batch_task.total_tasks
                
                # Verificar si batch está completo
                if batch_task.completed_tasks >= batch_task.total_tasks:
                    batch_task.status = TaskStatus.COMPLETED
                    
                    # Ejecutar callback de batch
                    if batch_task.callback:
                        try:
                            batch_task.callback(batch_task)
                        except Exception as e:
                            print(f"❌ Error en callback de batch {batch_id}: {e}")
                
                break
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Obtiene el estado de una tarea."""
        # Buscar en activas
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
        elif task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
        else:
            return None
        
        return {
            'task_id': task.task_id,
            'status': task.status.value,
            'progress': task.progress,
            'sources': task.sources,
            'results_count': len(task.results),
            'errors_count': len(task.errors),
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'processing_time': (task.completed_at - task.started_at) if task.completed_at and task.started_at else None
        }
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """Obtiene el estado de un batch."""
        if batch_id not in self.batch_tasks:
            return None
        
        batch = self.batch_tasks[batch_id]
        return {
            'batch_id': batch.batch_id,
            'status': batch.status.value,
            'progress': batch.progress,
            'completed_tasks': batch.completed_tasks,
            'total_tasks': batch.total_tasks,
            'tasks': [self.get_task_status(t.task_id) for t in batch.tasks]
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea pendiente."""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    del self.active_tasks[task_id]
                    return True
        return False
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del gestor."""
        with self.lock:
            stats = self.stats.copy()
        
        stats.update({
            'active_tasks': len(self.active_tasks),
            'completed_tasks_stored': len(self.completed_tasks),
            'active_batches': len([b for b in self.batch_tasks.values() if b.status != TaskStatus.COMPLETED]),
            'queue_size': self.task_queue.qsize(),
            'is_running': self.is_running,
            'worker_pools': {
                source: pool._threads for source, pool in self.worker_pools.items()
                if hasattr(pool, '_threads')
            }
        })
        
        return stats
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Limpia tareas completadas antiguas."""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        with self.lock:
            # Limpiar tareas completadas
            old_task_ids = [
                task_id for task_id, task in self.completed_tasks.items()
                if task.completed_at and task.completed_at < cutoff_time
            ]
            
            for task_id in old_task_ids:
                del self.completed_tasks[task_id]
            
            # Limpiar batches completados
            old_batch_ids = [
                batch_id for batch_id, batch in self.batch_tasks.items()
                if batch.status == TaskStatus.COMPLETED
            ]
            
            for batch_id in old_batch_ids:
                del self.batch_tasks[batch_id]
            
            if old_task_ids or old_batch_ids:
                print(f"🧹 Cleanup: {len(old_task_ids)} tareas, {len(old_batch_ids)} batches")

# Instancia global del gestor
_async_manager_instance = None

def get_async_manager() -> AsyncEnrichmentManager:
    """Obtiene la instancia global del gestor asíncrono."""
    global _async_manager_instance
    if _async_manager_instance is None:
        _async_manager_instance = AsyncEnrichmentManager()
    return _async_manager_instance

# Funciones de conveniencia
def enrich_async(track_info: Dict, sources: List[str] = None, callback: Callable = None) -> str:
    """Función de conveniencia para enriquecimiento asíncrono."""
    return get_async_manager().enrich_track_async(track_info, sources, callback=callback)

def enrich_batch(tracks: List[Dict], sources: List[str] = None, callback: Callable = None) -> str:
    """Función de conveniencia para enriquecimiento por lotes."""
    return get_async_manager().enrich_batch_async(tracks, sources, callback)

def get_task_progress(task_id: str) -> Optional[Dict]:
    """Función de conveniencia para obtener progreso de tarea."""
    return get_async_manager().get_task_status(task_id)

def get_async_stats() -> Dict:
    """Función de conveniencia para obtener estadísticas."""
    return get_async_manager().get_stats()