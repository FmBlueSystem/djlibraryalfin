# core/enrichment_logger.py

import logging
import time
import json
import traceback
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
import threading
from collections import defaultdict, deque

class LogLevel(Enum):
    """Niveles de logging específicos para enriquecimiento."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"
    PERFORMANCE = "performance"

class EventType(Enum):
    """Tipos de eventos de enriquecimiento."""
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    ERROR = "error"
    AGGREGATION = "aggregation"
    SCORING = "scoring"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    BATCH_PROGRESS = "batch_progress"

@dataclass
class LogEvent:
    """Evento de log estructurado."""
    timestamp: float
    level: LogLevel
    event_type: EventType
    source: str
    message: str
    data: Dict = None
    track_info: Dict = None
    performance_metrics: Dict = None
    error_details: Dict = None
    context: Dict = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.error_details is None:
            self.error_details = {}
        if self.context is None:
            self.context = {}

@dataclass
class ErrorPattern:
    """Patrón de error para análisis."""
    error_type: str
    source: str
    count: int
    first_seen: float
    last_seen: float
    sample_messages: List[str]
    suggested_fix: str = None

class EnrichmentLogger:
    """
    Sistema de logging avanzado para enriquecimiento de metadatos.
    
    Features:
    - Logging estructurado con contexto
    - Análisis de patrones de errores
    - Métricas de performance en tiempo real
    - Dashboard de estadísticas
    - Alertas automáticas
    - Export de reportes
    """
    
    def __init__(self, log_dir: str = "logs", max_log_size_mb: int = 50):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_log_size_mb = max_log_size_mb
        
        # Logging tradicional
        self._setup_traditional_logging()
        
        # Event storage
        self.events: deque = deque(maxlen=10000)  # En memoria para análisis rápido
        self.events_lock = threading.RLock()
        
        # Error tracking
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.recent_errors = deque(maxlen=1000)
        
        # Performance tracking
        self.performance_stats = defaultdict(list)
        self.response_times = defaultdict(lambda: deque(maxlen=100))
        
        # Context tracking
        self.current_context = threading.local()
        
        # Configuración de alertas
        self.alert_thresholds = {
            'error_rate': 0.2,          # 20% de errores
            'avg_response_time': 10.0,   # 10 segundos promedio
            'consecutive_failures': 5,   # 5 fallos consecutivos
            'cache_miss_rate': 0.8      # 80% cache misses
        }
        
        # Statistics
        self.stats = {
            'total_events': 0,
            'events_by_level': defaultdict(int),
            'events_by_source': defaultdict(int),
            'events_by_type': defaultdict(int),
            'error_rate_last_hour': 0.0,
            'avg_response_time': 0.0
        }
        
        print(f"📊 EnrichmentLogger inicializado (dir: {self.log_dir})")
    
    def _setup_traditional_logging(self):
        """Configura logging tradicional de Python."""
        self.logger = logging.getLogger('enrichment')
        self.logger.setLevel(logging.DEBUG)
        
        # Formatter con más información
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler con rotación
        log_file = self.log_dir / 'enrichment.log'
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        
        # Console handler para errores
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)
        
        self.logger.addHandler(handler)
        self.logger.addHandler(console_handler)
    
    def set_context(self, **context):
        """Establece contexto para logs subsecuentes."""
        if not hasattr(self.current_context, 'data'):
            self.current_context.data = {}
        self.current_context.data.update(context)
    
    def clear_context(self):
        """Limpia el contexto actual."""
        if hasattr(self.current_context, 'data'):
            self.current_context.data.clear()
    
    def get_context(self) -> Dict:
        """Obtiene el contexto actual."""
        if hasattr(self.current_context, 'data'):
            return self.current_context.data.copy()
        return {}
    
    def log_event(self, level: LogLevel, event_type: EventType, source: str, 
                  message: str, **kwargs):
        """
        Registra un evento de enriquecimiento.
        
        Args:
            level: Nivel de log
            event_type: Tipo de evento
            source: Fuente que genera el evento
            message: Mensaje descriptivo
            **kwargs: Datos adicionales (data, track_info, performance_metrics, etc.)
        """
        timestamp = time.time()
        
        # Crear evento
        event = LogEvent(
            timestamp=timestamp,
            level=level,
            event_type=event_type,
            source=source,
            message=message,
            context=self.get_context(),
            **kwargs
        )
        
        # Almacenar evento
        with self.events_lock:
            self.events.append(event)
            self.stats['total_events'] += 1
            self.stats['events_by_level'][level.value] += 1
            self.stats['events_by_source'][source] += 1
            self.stats['events_by_type'][event_type.value] += 1
        
        # Log tradicional
        log_level = self._map_log_level(level)
        context_str = f" | Context: {json.dumps(event.context)}" if event.context else ""
        full_message = f"[{event_type.value.upper()}] {source}: {message}{context_str}"
        
        self.logger.log(log_level, full_message)
        
        # Análisis especial para ciertos eventos
        if level == LogLevel.ERROR:
            self._analyze_error(event)
        elif event_type == EventType.API_RESPONSE and event.performance_metrics:
            self._track_performance(event)
        
        # Verificar alertas
        self._check_alerts()
    
    def _map_log_level(self, level: LogLevel) -> int:
        """Mapea niveles custom a niveles estándar de logging."""
        mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.SUCCESS: logging.INFO,
            LogLevel.PERFORMANCE: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        return mapping.get(level, logging.INFO)
    
    def _analyze_error(self, event: LogEvent):
        """Analiza un error para detectar patrones."""
        error_key = f"{event.source}:{event.error_details.get('type', 'unknown')}"
        
        if error_key in self.error_patterns:
            pattern = self.error_patterns[error_key]
            pattern.count += 1
            pattern.last_seen = event.timestamp
            pattern.sample_messages.append(event.message)
            # Mantener solo últimos 5 mensajes
            pattern.sample_messages = pattern.sample_messages[-5:]
        else:
            self.error_patterns[error_key] = ErrorPattern(
                error_type=event.error_details.get('type', 'unknown'),
                source=event.source,
                count=1,
                first_seen=event.timestamp,
                last_seen=event.timestamp,
                sample_messages=[event.message],
                suggested_fix=self._suggest_fix(event)
            )
        
        # Añadir a errores recientes
        self.recent_errors.append(event)
    
    def _suggest_fix(self, error_event: LogEvent) -> str:
        """Sugiere una solución para un error."""
        error_type = error_event.error_details.get('type', '').lower()
        source = error_event.source
        message = error_event.message.lower()
        
        # Patrones comunes y sus soluciones
        if 'timeout' in error_type or 'timeout' in message:
            return f"Aumentar timeout para {source} o verificar conectividad"
        elif 'rate limit' in message or '429' in message:
            return f"Reducir frecuencia de requests a {source}"
        elif 'authentication' in message or '401' in message:
            return f"Verificar API key para {source}"
        elif 'not found' in message or '404' in message:
            return "Track no encontrado - probar con términos de búsqueda diferentes"
        elif 'connection' in message:
            return f"Verificar conectividad de red a {source}"
        elif 'json' in error_type:
            return f"Respuesta malformada de {source} - posible problema en su API"
        else:
            return "Revisar logs detallados y documentación de la API"
    
    def _track_performance(self, event: LogEvent):
        """Rastrea métricas de performance."""
        source = event.source
        metrics = event.performance_metrics
        
        if 'response_time' in metrics:
            response_time = metrics['response_time']
            self.response_times[source].append(response_time)
            
            # Actualizar estadísticas globales
            all_times = []
            for times in self.response_times.values():
                all_times.extend(times)
            
            if all_times:
                self.stats['avg_response_time'] = sum(all_times) / len(all_times)
    
    def _check_alerts(self):
        """Verifica si se deben disparar alertas."""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Calcular error rate en la última hora
        recent_events = [e for e in self.events if e.timestamp > hour_ago]
        if recent_events:
            error_events = [e for e in recent_events if e.level == LogLevel.ERROR]
            error_rate = len(error_events) / len(recent_events)
            self.stats['error_rate_last_hour'] = error_rate
            
            # Alerta por alto error rate
            if error_rate > self.alert_thresholds['error_rate']:
                self._trigger_alert(
                    f"Alto error rate detectado: {error_rate:.1%} en la última hora",
                    severity="high"
                )
        
        # Alerta por tiempo de respuesta
        if self.stats['avg_response_time'] > self.alert_thresholds['avg_response_time']:
            self._trigger_alert(
                f"Tiempo de respuesta alto: {self.stats['avg_response_time']:.1f}s promedio",
                severity="medium"
            )
    
    def _trigger_alert(self, message: str, severity: str = "medium"):
        """Dispara una alerta."""
        self.log_event(
            LogLevel.CRITICAL,
            EventType.ERROR,
            "alert_system",
            f"ALERTA [{severity.upper()}]: {message}",
            data={'severity': severity, 'alert_type': 'automated'}
        )
        
        # Aquí se podría integrar con sistemas externos de alertas
        print(f"🚨 ALERTA: {message}")
    
    # Métodos de conveniencia para logging
    def debug(self, source: str, message: str, **kwargs):
        """Log de debug."""
        self.log_event(LogLevel.DEBUG, EventType.API_REQUEST, source, message, **kwargs)
    
    def info(self, source: str, message: str, **kwargs):
        """Log informativo."""
        self.log_event(LogLevel.INFO, EventType.API_REQUEST, source, message, **kwargs)
    
    def success(self, source: str, message: str, **kwargs):
        """Log de éxito."""
        self.log_event(LogLevel.SUCCESS, EventType.API_RESPONSE, source, message, **kwargs)
    
    def warning(self, source: str, message: str, **kwargs):
        """Log de advertencia."""
        self.log_event(LogLevel.WARNING, EventType.ERROR, source, message, **kwargs)
    
    def error(self, source: str, message: str, error: Exception = None, **kwargs):
        """Log de error."""
        error_details = kwargs.get('error_details', {})
        
        if error:
            error_details.update({
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            })
        
        self.log_event(
            LogLevel.ERROR, EventType.ERROR, source, message,
            error_details=error_details, **kwargs
        )
    
    def performance(self, source: str, message: str, metrics: Dict, **kwargs):
        """Log de performance."""
        self.log_event(
            LogLevel.PERFORMANCE, EventType.API_RESPONSE, source, message,
            performance_metrics=metrics, **kwargs
        )
    
    def api_request(self, source: str, track_info: Dict, request_details: Dict = None):
        """Log de request a API."""
        self.log_event(
            LogLevel.DEBUG, EventType.API_REQUEST, source,
            f"Requesting {track_info.get('artist', 'Unknown')} - {track_info.get('title', 'Unknown')}",
            track_info=track_info,
            data=request_details or {}
        )
    
    def api_response(self, source: str, track_info: Dict, success: bool, 
                    response_time: float, data: Dict = None):
        """Log de response de API."""
        level = LogLevel.SUCCESS if success else LogLevel.ERROR
        message = f"Response from {source}: {'SUCCESS' if success else 'FAILED'}"
        
        self.log_event(
            level, EventType.API_RESPONSE, source, message,
            track_info=track_info,
            performance_metrics={'response_time': response_time},
            data=data or {}
        )
    
    def cache_hit(self, source: str, track_info: Dict):
        """Log de cache hit."""
        self.log_event(
            LogLevel.DEBUG, EventType.CACHE_HIT, source,
            f"Cache hit for {track_info.get('artist')} - {track_info.get('title')}",
            track_info=track_info
        )
    
    def cache_miss(self, source: str, track_info: Dict):
        """Log de cache miss."""
        self.log_event(
            LogLevel.DEBUG, EventType.CACHE_MISS, source,
            f"Cache miss for {track_info.get('artist')} - {track_info.get('title')}",
            track_info=track_info
        )
    
    def aggregation_start(self, track_info: Dict, sources: List[str]):
        """Log de inicio de agregación."""
        self.log_event(
            LogLevel.INFO, EventType.AGGREGATION, "aggregator",
            f"Starting aggregation for {track_info.get('artist')} - {track_info.get('title')}",
            track_info=track_info,
            data={'sources': sources}
        )
    
    def aggregation_complete(self, track_info: Dict, results: Dict, processing_time: float):
        """Log de completar agregación."""
        self.log_event(
            LogLevel.SUCCESS, EventType.AGGREGATION, "aggregator",
            f"Aggregation completed: {len(results.get('final_genres', []))} genres found",
            track_info=track_info,
            data=results,
            performance_metrics={'processing_time': processing_time}
        )
    
    def get_stats_report(self) -> Dict:
        """Genera reporte completo de estadísticas."""
        current_time = time.time()
        hour_ago = current_time - 3600
        day_ago = current_time - 86400
        
        # Eventos recientes
        recent_hour = [e for e in self.events if e.timestamp > hour_ago]
        recent_day = [e for e in self.events if e.timestamp > day_ago]
        
        # Análisis de errores
        error_analysis = {}
        for pattern_key, pattern in self.error_patterns.items():
            error_analysis[pattern_key] = {
                'count': pattern.count,
                'first_seen': datetime.fromtimestamp(pattern.first_seen).isoformat(),
                'last_seen': datetime.fromtimestamp(pattern.last_seen).isoformat(),
                'sample_messages': pattern.sample_messages[-3:],
                'suggested_fix': pattern.suggested_fix
            }
        
        # Performance por fuente
        performance_by_source = {}
        for source, times in self.response_times.items():
            if times:
                performance_by_source[source] = {
                    'avg_response_time': sum(times) / len(times),
                    'min_response_time': min(times),
                    'max_response_time': max(times),
                    'total_requests': len(times)
                }
        
        return {
            'summary': self.stats.copy(),
            'time_ranges': {
                'last_hour': {
                    'total_events': len(recent_hour),
                    'errors': len([e for e in recent_hour if e.level == LogLevel.ERROR]),
                    'successes': len([e for e in recent_hour if e.level == LogLevel.SUCCESS])
                },
                'last_day': {
                    'total_events': len(recent_day),
                    'errors': len([e for e in recent_day if e.level == LogLevel.ERROR]),
                    'successes': len([e for e in recent_day if e.level == LogLevel.SUCCESS])
                }
            },
            'error_patterns': error_analysis,
            'performance': performance_by_source,
            'top_sources': dict(sorted(
                self.stats['events_by_source'].items(),
                key=lambda x: x[1], reverse=True
            )[:10]),
            'top_event_types': dict(sorted(
                self.stats['events_by_type'].items(),
                key=lambda x: x[1], reverse=True
            )[:10])
        }
    
    def export_logs(self, start_time: Optional[float] = None, 
                   end_time: Optional[float] = None,
                   sources: Optional[List[str]] = None,
                   levels: Optional[List[LogLevel]] = None) -> List[Dict]:
        """
        Exporta logs filtrados.
        
        Args:
            start_time: Timestamp de inicio
            end_time: Timestamp de fin
            sources: Filtrar por fuentes
            levels: Filtrar por niveles
            
        Returns:
            Lista de eventos filtrados
        """
        filtered_events = []
        
        for event in self.events:
            # Filtro por tiempo
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            
            # Filtro por fuente
            if sources and event.source not in sources:
                continue
            
            # Filtro por nivel
            if levels and event.level not in levels:
                continue
            
            # Convertir a dict serializable
            event_dict = asdict(event)
            event_dict['timestamp_iso'] = datetime.fromtimestamp(event.timestamp).isoformat()
            event_dict['level'] = event.level.value
            event_dict['event_type'] = event.event_type.value
            
            filtered_events.append(event_dict)
        
        return filtered_events
    
    def clear_old_events(self, max_age_hours: int = 48):
        """Limpia eventos antiguos."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        with self.events_lock:
            original_count = len(self.events)
            # Deque no tiene remove, así que recreamos
            recent_events = deque(
                (e for e in self.events if e.timestamp > cutoff_time),
                maxlen=self.events.maxlen
            )
            self.events = recent_events
            
            removed_count = original_count - len(self.events)
            if removed_count > 0:
                print(f"🧹 Logger cleanup: {removed_count} eventos antiguos removidos")

# Instancia global del logger
_enrichment_logger_instance = None

def get_enrichment_logger() -> EnrichmentLogger:
    """Obtiene la instancia global del logger de enriquecimiento."""
    global _enrichment_logger_instance
    if _enrichment_logger_instance is None:
        _enrichment_logger_instance = EnrichmentLogger()
    return _enrichment_logger_instance

# Funciones de conveniencia
def log_api_request(source: str, track_info: Dict, **kwargs):
    """Log de conveniencia para request."""
    get_enrichment_logger().api_request(source, track_info, kwargs)

def log_api_response(source: str, track_info: Dict, success: bool, response_time: float, **kwargs):
    """Log de conveniencia para response."""
    get_enrichment_logger().api_response(source, track_info, success, response_time, kwargs)

def log_error(source: str, message: str, error: Exception = None, **kwargs):
    """Log de conveniencia para errores."""
    get_enrichment_logger().error(source, message, error, **kwargs)

def log_success(source: str, message: str, **kwargs):
    """Log de conveniencia para éxitos."""
    get_enrichment_logger().success(source, message, **kwargs)

def set_log_context(**context):
    """Establece contexto de logging."""
    get_enrichment_logger().set_context(**context)

def get_enrichment_stats() -> Dict:
    """Obtiene estadísticas de enriquecimiento."""
    return get_enrichment_logger().get_stats_report()