# core/intelligent_cache.py

import time
import hashlib
import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from datetime import datetime, timedelta

@dataclass
class CacheEntry:
    """Entrada de cache para resultados de APIs."""
    key: str
    source: str
    data: Dict
    confidence: float
    timestamp: float
    hits: int = 0
    last_accessed: float = None
    expires_at: float = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
        if self.expires_at is None:
            # Duraciones variables según confianza y fuente
            base_duration = 86400  # 24 horas base
            confidence_factor = max(0.1, self.confidence) * 2
            duration = base_duration * confidence_factor
            self.expires_at = self.timestamp + duration

@dataclass
class CacheStats:
    """Estadísticas del cache."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls_saved: int = 0
    total_size_mb: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        return self.cache_hits / max(1, self.total_requests)
    
    @property
    def api_savings_rate(self) -> float:
        return self.api_calls_saved / max(1, self.total_requests)

class IntelligentCache:
    """
    Sistema de cache inteligente para resultados de APIs de metadatos.
    
    Features:
    - Cache persistente en SQLite
    - Expiración inteligente basada en confianza
    - Cleanup automático de entradas obsoletas
    - Estadísticas detalladas de performance
    - Thread-safe operations
    """
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size_mb = max_size_mb
        
        # Base de datos para cache persistente
        self.db_path = self.cache_dir / "metadata_cache.db"
        self.lock = threading.RLock()
        
        # Cache en memoria para acceso rápido
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        
        # Configuración por fuente
        self.source_config = {
            'musicbrainz': {'weight': 1.0, 'base_duration': 7*24*3600},  # 7 días
            'spotify': {'weight': 0.9, 'base_duration': 5*24*3600},      # 5 días  
            'discogs': {'weight': 0.8, 'base_duration': 10*24*3600},     # 10 días
            'lastfm': {'weight': 0.7, 'base_duration': 3*24*3600},       # 3 días
        }
        
        self._init_database()
        self._load_cache_from_db()
        
    def _init_database(self):
        """Inicializa la base de datos de cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    source TEXT,
                    data TEXT,
                    confidence REAL,
                    timestamp REAL,
                    hits INTEGER,
                    last_accessed REAL,
                    expires_at REAL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_source ON cache_entries(source)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at)
            """)
    
    def _load_cache_from_db(self):
        """Carga entradas de cache desde la base de datos."""
        current_time = time.time()
        loaded_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Cargar solo entradas no expiradas
            cursor.execute("""
                SELECT * FROM cache_entries 
                WHERE expires_at > ?
                ORDER BY last_accessed DESC
                LIMIT 1000
            """, (current_time,))
            
            for row in cursor.fetchall():
                try:
                    entry = CacheEntry(
                        key=row['key'],
                        source=row['source'],
                        data=json.loads(row['data']),
                        confidence=row['confidence'],
                        timestamp=row['timestamp'],
                        hits=row['hits'],
                        last_accessed=row['last_accessed'],
                        expires_at=row['expires_at']
                    )
                    self.memory_cache[entry.key] = entry
                    loaded_count += 1
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"⚠️ Error cargando entrada de cache: {e}")
        
        print(f"📦 Cache inicializado: {loaded_count} entradas cargadas")
        self._cleanup_expired_entries()
    
    def _generate_cache_key(self, artist: str, title: str, source: str, 
                          extra_params: Dict = None) -> str:
        """Genera una clave única para el cache."""
        # Normalizar strings para mejor cache hit rate
        artist_norm = self._normalize_string(artist)
        title_norm = self._normalize_string(title)
        
        # Base key
        base_data = f"{source}:{artist_norm}:{title_norm}"
        
        # Agregar parámetros adicionales si los hay
        if extra_params:
            sorted_params = sorted(extra_params.items())
            params_str = json.dumps(sorted_params, sort_keys=True)
            base_data += f":{params_str}"
        
        # Generar hash MD5
        return hashlib.md5(base_data.encode('utf-8')).hexdigest()
    
    def _normalize_string(self, text: str) -> str:
        """Normaliza strings para mejorar cache hit rate."""
        if not text:
            return ""
        
        # Convertir a minúsculas
        normalized = text.lower().strip()
        
        # Remover caracteres especiales comunes
        import re
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Normalizar espacios
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def get(self, artist: str, title: str, source: str, 
            extra_params: Dict = None) -> Optional[Dict]:
        """
        Obtiene datos del cache si están disponibles y válidos.
        
        Args:
            artist: Nombre del artista
            title: Título del track
            source: Fuente de datos (spotify, musicbrainz, etc.)
            extra_params: Parámetros adicionales para la clave
            
        Returns:
            Datos en cache o None si no están disponibles/válidos
        """
        with self.lock:
            self.stats.total_requests += 1
            
            cache_key = self._generate_cache_key(artist, title, source, extra_params)
            
            # Verificar cache en memoria
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                
                # Verificar expiración
                current_time = time.time()
                if current_time > entry.expires_at:
                    # Entrada expirada
                    del self.memory_cache[cache_key]
                    self._remove_from_db(cache_key)
                    self.stats.cache_misses += 1
                    return None
                
                # Cache hit!
                entry.hits += 1
                entry.last_accessed = current_time
                self.stats.cache_hits += 1
                self.stats.api_calls_saved += 1
                
                # Actualizar en base de datos de forma asíncrona
                self._update_db_entry_async(entry)
                
                print(f"✅ Cache HIT: {source} para {artist} - {title} (hits: {entry.hits})")
                return entry.data.copy()
            
            self.stats.cache_misses += 1
            return None
    
    def put(self, artist: str, title: str, source: str, data: Dict, 
            confidence: float, extra_params: Dict = None):
        """
        Almacena datos en el cache.
        
        Args:
            artist: Nombre del artista
            title: Título del track  
            source: Fuente de datos
            data: Datos a cachear
            confidence: Nivel de confianza de los datos (0.0-1.0)
            extra_params: Parámetros adicionales para la clave
        """
        if not data or confidence <= 0:
            return
        
        with self.lock:
            cache_key = self._generate_cache_key(artist, title, source, extra_params)
            current_time = time.time()
            
            # Calcular duración de cache basada en confianza y fuente
            base_duration = self.source_config.get(source, {}).get('base_duration', 86400)
            confidence_multiplier = max(0.1, confidence) * 2
            duration = base_duration * confidence_multiplier
            expires_at = current_time + duration
            
            # Crear entrada
            entry = CacheEntry(
                key=cache_key,
                source=source,
                data=data.copy(),
                confidence=confidence,
                timestamp=current_time,
                hits=0,
                last_accessed=current_time,
                expires_at=expires_at
            )
            
            # Almacenar en memoria
            self.memory_cache[cache_key] = entry
            
            # Almacenar en base de datos
            self._save_to_db(entry)
            
            print(f"💾 Cache STORE: {source} para {artist} - {title} (exp: {duration/3600:.1f}h)")
            
            # Cleanup si es necesario
            self._check_size_limits()
    
    def _save_to_db(self, entry: CacheEntry):
        """Guarda una entrada en la base de datos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, source, data, confidence, timestamp, hits, last_accessed, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.key,
                    entry.source, 
                    json.dumps(entry.data),
                    entry.confidence,
                    entry.timestamp,
                    entry.hits,
                    entry.last_accessed,
                    entry.expires_at
                ))
        except sqlite3.Error as e:
            print(f"❌ Error guardando en cache DB: {e}")
    
    def _update_db_entry_async(self, entry: CacheEntry):
        """Actualiza entrada en DB de forma asíncrona."""
        def update_worker():
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE cache_entries 
                        SET hits = ?, last_accessed = ?
                        WHERE key = ?
                    """, (entry.hits, entry.last_accessed, entry.key))
            except sqlite3.Error as e:
                print(f"❌ Error actualizando cache DB: {e}")
        
        # Ejecutar en thread separado para no bloquear
        import threading
        threading.Thread(target=update_worker, daemon=True).start()
    
    def _remove_from_db(self, cache_key: str):
        """Remueve entrada de la base de datos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (cache_key,))
        except sqlite3.Error as e:
            print(f"❌ Error removiendo de cache DB: {e}")
    
    def _cleanup_expired_entries(self):
        """Limpia entradas expiradas del cache."""
        current_time = time.time()
        expired_keys = []
        
        # Identificar entradas expiradas en memoria
        for key, entry in self.memory_cache.items():
            if current_time > entry.expires_at:
                expired_keys.append(key)
        
        # Remover de memoria
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Remover de base de datos
        if expired_keys:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        DELETE FROM cache_entries WHERE expires_at <= ?
                    """, (current_time,))
                    removed_count = conn.total_changes
                    
                print(f"🧹 Cache cleanup: {len(expired_keys)} en memoria, {removed_count} en DB")
            except sqlite3.Error as e:
                print(f"❌ Error en cleanup de cache: {e}")
    
    def _check_size_limits(self):
        """Verifica y mantiene límites de tamaño del cache."""
        if len(self.memory_cache) > 10000:  # Límite de 10k entradas en memoria
            # Remover 20% de las entradas menos usadas
            entries_sorted = sorted(
                self.memory_cache.items(),
                key=lambda x: (x[1].hits, x[1].last_accessed)
            )
            
            remove_count = len(entries_sorted) // 5  # 20%
            for i in range(remove_count):
                key = entries_sorted[i][0]
                del self.memory_cache[key]
            
            print(f"🗑️ Cache size limit: removidas {remove_count} entradas LRU")
    
    def get_stats(self) -> CacheStats:
        """Retorna estadísticas actuales del cache."""
        # Calcular tamaño aproximado
        size_bytes = 0
        for entry in self.memory_cache.values():
            size_bytes += len(json.dumps(entry.data).encode('utf-8'))
        
        self.stats.total_size_mb = size_bytes / (1024 * 1024)
        return self.stats
    
    def get_detailed_report(self) -> Dict:
        """Genera reporte detallado del cache."""
        current_time = time.time()
        
        # Estadísticas por fuente
        source_stats = {}
        for entry in self.memory_cache.values():
            source = entry.source
            if source not in source_stats:
                source_stats[source] = {
                    'entries': 0,
                    'total_hits': 0,
                    'avg_confidence': 0.0,
                    'oldest_entry': current_time,
                    'newest_entry': 0
                }
            
            stats = source_stats[source]
            stats['entries'] += 1
            stats['total_hits'] += entry.hits
            stats['avg_confidence'] += entry.confidence
            stats['oldest_entry'] = min(stats['oldest_entry'], entry.timestamp)
            stats['newest_entry'] = max(stats['newest_entry'], entry.timestamp)
        
        # Calcular promedios
        for source, stats in source_stats.items():
            if stats['entries'] > 0:
                stats['avg_confidence'] /= stats['entries']
                stats['avg_hits'] = stats['total_hits'] / stats['entries']
        
        return {
            'cache_stats': asdict(self.get_stats()),
            'memory_entries': len(self.memory_cache),
            'source_breakdown': source_stats,
            'top_entries': self._get_top_entries(),
            'expiration_distribution': self._get_expiration_distribution()
        }
    
    def _get_top_entries(self, limit: int = 10) -> List[Dict]:
        """Obtiene las entradas más populares."""
        entries_sorted = sorted(
            self.memory_cache.values(),
            key=lambda x: x.hits,
            reverse=True
        )
        
        return [
            {
                'source': entry.source,
                'hits': entry.hits,
                'confidence': entry.confidence,
                'age_hours': (time.time() - entry.timestamp) / 3600
            }
            for entry in entries_sorted[:limit]
        ]
    
    def _get_expiration_distribution(self) -> Dict:
        """Analiza distribución de tiempos de expiración."""
        current_time = time.time()
        distribution = {
            'expired': 0,
            'expires_1h': 0,
            'expires_24h': 0,
            'expires_week': 0,
            'expires_longer': 0
        }
        
        for entry in self.memory_cache.values():
            time_to_expire = entry.expires_at - current_time
            
            if time_to_expire <= 0:
                distribution['expired'] += 1
            elif time_to_expire <= 3600:  # 1 hora
                distribution['expires_1h'] += 1
            elif time_to_expire <= 86400:  # 24 horas
                distribution['expires_24h'] += 1
            elif time_to_expire <= 604800:  # 1 semana
                distribution['expires_week'] += 1
            else:
                distribution['expires_longer'] += 1
        
        return distribution
    
    def invalidate_source(self, source: str):
        """Invalida todas las entradas de una fuente específica."""
        with self.lock:
            keys_to_remove = [
                key for key, entry in self.memory_cache.items() 
                if entry.source == source
            ]
            
            for key in keys_to_remove:
                del self.memory_cache[key]
                self._remove_from_db(key)
            
            print(f"🔄 Cache invalidated para fuente {source}: {len(keys_to_remove)} entradas")
    
    def clear_all(self):
        """Limpia completamente el cache."""
        with self.lock:
            self.memory_cache.clear()
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM cache_entries")
                print("🗑️ Cache completamente limpiado")
            except sqlite3.Error as e:
                print(f"❌ Error limpiando cache DB: {e}")

# Instancia global del cache
_cache_instance = None

def get_cache() -> IntelligentCache:
    """Obtiene la instancia global del cache."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = IntelligentCache()
    return _cache_instance

# Funciones de conveniencia
def cache_get(artist: str, title: str, source: str, **kwargs) -> Optional[Dict]:
    """Función de conveniencia para obtener del cache."""
    return get_cache().get(artist, title, source, kwargs)

def cache_put(artist: str, title: str, source: str, data: Dict, 
              confidence: float, **kwargs):
    """Función de conveniencia para almacenar en cache."""
    get_cache().put(artist, title, source, data, confidence, kwargs)

def cache_stats() -> Dict:
    """Función de conveniencia para obtener estadísticas."""
    return get_cache().get_detailed_report()