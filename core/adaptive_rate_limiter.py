# core/adaptive_rate_limiter.py

import time
import threading
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from collections import deque
import statistics
from enum import Enum

class ApiHealthStatus(Enum):
    """Estados de salud de una API."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    THROTTLED = "throttled"
    DOWN = "down"

@dataclass
class ApiMetrics:
    """Métricas de performance de una API."""
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    success_count: int = 0
    error_count: int = 0
    throttle_count: int = 0
    timeout_count: int = 0
    last_success: float = 0
    last_error: float = 0
    last_request: float = 0
    
    # Rate limiting dinámico
    current_delay: float = 0.2
    min_delay: float = 0.1
    max_delay: float = 10.0
    
    # Health tracking
    consecutive_errors: int = 0
    consecutive_successes: int = 0
    health_status: ApiHealthStatus = ApiHealthStatus.HEALTHY
    
    def __post_init__(self):
        if isinstance(self.response_times, list):
            self.response_times = deque(self.response_times, maxlen=100)

@dataclass
class RequestResult:
    """Resultado de una petición a la API."""
    success: bool
    response_time: float
    error_type: str = None
    status_code: int = None
    was_throttled: bool = False
    was_timeout: bool = False
    retry_after: float = None

class AdaptiveRateLimiter:
    """
    Sistema de rate limiting adaptativo que se ajusta automáticamente
    basándose en la respuesta y comportamiento de cada API.
    
    Features:
    - Rate limiting adaptativo por API
    - Health monitoring continuo
    - Auto-recovery de APIs caídas
    - Timeouts optimizados dinámicamente
    - Backoff exponencial inteligente
    """
    
    def __init__(self):
        self.metrics: Dict[str, ApiMetrics] = {}
        self.locks: Dict[str, threading.RLock] = {}
        self.global_lock = threading.RLock()
        
        # Configuración base por fuente
        self.base_config = {
            'musicbrainz': {
                'min_delay': 1.0,      # MusicBrainz es estricto con rate limiting
                'max_delay': 30.0,
                'base_timeout': 15.0,
                'error_threshold': 3,
                'throttle_detection': [429, 503]
            },
            'spotify': {
                'min_delay': 0.1,      # Spotify permite más requests
                'max_delay': 10.0,
                'base_timeout': 12.0,
                'error_threshold': 5,
                'throttle_detection': [429, 503]
            },
            'discogs': {
                'min_delay': 0.8,      # Discogs tiene límites moderados
                'max_delay': 20.0,
                'base_timeout': 18.0,
                'error_threshold': 3,
                'throttle_detection': [429]
            },
            'lastfm': {
                'min_delay': 0.2,      # Last.fm es generalmente permisivo
                'max_delay': 15.0,
                'base_timeout': 10.0,
                'error_threshold': 4,
                'throttle_detection': [429, 503]
            }
        }
        
        # Inicializar métricas
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Inicializa métricas para todas las fuentes configuradas."""
        for source, config in self.base_config.items():
            self.metrics[source] = ApiMetrics(
                min_delay=config['min_delay'],
                max_delay=config['max_delay'],
                current_delay=config['min_delay']
            )
            self.locks[source] = threading.RLock()
    
    def wait_for_rate_limit(self, source: str) -> float:
        """
        Espera el tiempo necesario según el rate limiting de la fuente.
        
        Args:
            source: Nombre de la fuente API
            
        Returns:
            Tiempo esperado en segundos
        """
        if source not in self.metrics:
            self._initialize_source(source)
        
        with self.locks[source]:
            metrics = self.metrics[source]
            current_time = time.time()
            
            # Calcular tiempo desde última petición
            time_since_last = current_time - metrics.last_request
            
            # Determinar delay necesario basándose en el estado de la API
            required_delay = self._calculate_required_delay(source, metrics)
            
            # Esperar si es necesario
            if time_since_last < required_delay:
                wait_time = required_delay - time_since_last
                print(f"⏳ Rate limit wait {source}: {wait_time:.2f}s (estado: {metrics.health_status.value})")
                time.sleep(wait_time)
                return wait_time
            
            # Actualizar timestamp de última petición
            metrics.last_request = current_time
            return 0.0
    
    def _calculate_required_delay(self, source: str, metrics: ApiMetrics) -> float:
        """Calcula el delay requerido basándose en el estado de la API."""
        base_delay = metrics.current_delay
        
        # Ajustes basados en el estado de salud
        if metrics.health_status == ApiHealthStatus.DOWN:
            return metrics.max_delay  # Máximo delay para APIs caídas
        elif metrics.health_status == ApiHealthStatus.THROTTLED:
            return min(base_delay * 2, metrics.max_delay)
        elif metrics.health_status == ApiHealthStatus.DEGRADED:
            return min(base_delay * 1.5, metrics.max_delay)
        else:  # HEALTHY
            return base_delay
    
    def record_request_result(self, source: str, result: RequestResult):
        """
        Registra el resultado de una petición y ajusta métricas.
        
        Args:
            source: Nombre de la fuente API
            result: Resultado de la petición
        """
        if source not in self.metrics:
            self._initialize_source(source)
        
        with self.locks[source]:
            metrics = self.metrics[source]
            current_time = time.time()
            
            # Registrar tiempo de respuesta
            metrics.response_times.append(result.response_time)
            
            if result.success:
                self._handle_successful_request(metrics, current_time, result)
            else:
                self._handle_failed_request(metrics, current_time, result)
            
            # Actualizar estado de salud
            self._update_health_status(source, metrics)
            
            # Ajustar delays dinámicamente
            self._adjust_rate_limits(metrics, result)
    
    def _handle_successful_request(self, metrics: ApiMetrics, current_time: float, 
                                 result: RequestResult):
        """Maneja una petición exitosa."""
        metrics.success_count += 1
        metrics.last_success = current_time
        metrics.consecutive_successes += 1
        metrics.consecutive_errors = 0
        
        # Recuperación gradual de delays
        if metrics.consecutive_successes >= 3 and metrics.current_delay > metrics.min_delay:
            # Reducir delay gradualmente
            reduction_factor = 0.8
            metrics.current_delay = max(
                metrics.min_delay,
                metrics.current_delay * reduction_factor
            )
    
    def _handle_failed_request(self, metrics: ApiMetrics, current_time: float,
                             result: RequestResult):
        """Maneja una petición fallida."""
        metrics.error_count += 1
        metrics.last_error = current_time
        metrics.consecutive_errors += 1
        metrics.consecutive_successes = 0
        
        # Contabilizar tipos específicos de errores
        if result.was_throttled:
            metrics.throttle_count += 1
        if result.was_timeout:
            metrics.timeout_count += 1
        
        # Incrementar delay en caso de errores
        if result.was_throttled or result.status_code in [429, 503]:
            # Rate limit hit - incremento agresivo
            metrics.current_delay = min(
                metrics.max_delay,
                metrics.current_delay * 2.0
            )
        elif result.was_timeout:
            # Timeout - incremento moderado
            metrics.current_delay = min(
                metrics.max_delay,
                metrics.current_delay * 1.5
            )
        elif metrics.consecutive_errors >= 3:
            # Errores consecutivos - incremento gradual
            metrics.current_delay = min(
                metrics.max_delay,
                metrics.current_delay * 1.3
            )
    
    def _update_health_status(self, source: str, metrics: ApiMetrics):
        """Actualiza el estado de salud de la API."""
        config = self.base_config.get(source, {})
        error_threshold = config.get('error_threshold', 3)
        
        # Calcular tasa de éxito reciente
        total_recent = metrics.success_count + metrics.error_count
        if total_recent > 0:
            recent_success_rate = metrics.success_count / total_recent
        else:
            recent_success_rate = 1.0
        
        # Determinar estado basándose en errores consecutivos y tasa de éxito
        if metrics.consecutive_errors >= error_threshold * 2:
            metrics.health_status = ApiHealthStatus.DOWN
        elif metrics.throttle_count > metrics.success_count and metrics.throttle_count > 3:
            metrics.health_status = ApiHealthStatus.THROTTLED
        elif recent_success_rate < 0.5 or metrics.consecutive_errors >= error_threshold:
            metrics.health_status = ApiHealthStatus.DEGRADED
        elif metrics.consecutive_successes >= 3 and recent_success_rate > 0.8:
            metrics.health_status = ApiHealthStatus.HEALTHY
    
    def _adjust_rate_limits(self, metrics: ApiMetrics, result: RequestResult):
        """Ajusta límites de rate basándose en el resultado."""
        # Si la API nos dio un Retry-After header, respetarlo
        if result.retry_after and result.retry_after > 0:
            metrics.current_delay = min(result.retry_after, metrics.max_delay)
        
        # Ajuste basado en tiempo de respuesta
        if result.response_time > 5.0:  # Respuesta muy lenta
            metrics.current_delay = min(
                metrics.max_delay,
                metrics.current_delay * 1.2
            )
        elif result.response_time < 1.0 and result.success:  # Respuesta rápida
            metrics.current_delay = max(
                metrics.min_delay,
                metrics.current_delay * 0.95
            )
    
    def get_optimal_timeout(self, source: str) -> float:
        """
        Calcula el timeout óptimo para una fuente basándose en métricas históricas.
        
        Args:
            source: Nombre de la fuente API
            
        Returns:
            Timeout optimizado en segundos
        """
        if source not in self.metrics:
            self._initialize_source(source)
        
        metrics = self.metrics[source]
        config = self.base_config.get(source, {})
        base_timeout = config.get('base_timeout', 10.0)
        
        # Si no tenemos suficientes datos, usar timeout base
        if len(metrics.response_times) < 5:
            return base_timeout
        
        # Calcular estadísticas de tiempo de respuesta
        response_times = list(metrics.response_times)
        
        try:
            avg_response = statistics.mean(response_times)
            p95_response = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            
            # Timeout optimizado: P95 + buffer, pero con límites razonables
            optimal_timeout = p95_response * 2.0  # 2x el P95 como buffer
            
            # Aplicar límites
            min_timeout = max(base_timeout * 0.5, 3.0)
            max_timeout = base_timeout * 3.0
            
            return max(min_timeout, min(optimal_timeout, max_timeout))
            
        except (statistics.StatisticsError, IndexError):
            return base_timeout
    
    def _initialize_source(self, source: str):
        """Inicializa una nueva fuente que no estaba configurada."""
        if source not in self.metrics:
            # Usar configuración default si no existe configuración específica
            default_config = {
                'min_delay': 0.2,
                'max_delay': 15.0,
                'base_timeout': 10.0,
                'error_threshold': 3,
                'throttle_detection': [429, 503]
            }
            
            self.base_config[source] = default_config
            self.metrics[source] = ApiMetrics(
                min_delay=default_config['min_delay'],
                max_delay=default_config['max_delay'],
                current_delay=default_config['min_delay']
            )
            self.locks[source] = threading.RLock()
    
    def get_source_status(self, source: str) -> Dict:
        """Obtiene estado completo de una fuente."""
        if source not in self.metrics:
            return {'status': 'not_initialized'}
        
        metrics = self.metrics[source]
        response_times = list(metrics.response_times)
        
        stats = {
            'health_status': metrics.health_status.value,
            'current_delay': metrics.current_delay,
            'success_rate': 0.0,
            'avg_response_time': 0.0,
            'p95_response_time': 0.0,
            'consecutive_errors': metrics.consecutive_errors,
            'consecutive_successes': metrics.consecutive_successes,
            'total_requests': metrics.success_count + metrics.error_count,
            'throttle_count': metrics.throttle_count,
            'timeout_count': metrics.timeout_count
        }
        
        # Calcular estadísticas si tenemos datos
        total_requests = stats['total_requests']
        if total_requests > 0:
            stats['success_rate'] = metrics.success_count / total_requests
        
        if response_times:
            stats['avg_response_time'] = statistics.mean(response_times)
            if len(response_times) >= 5:
                try:
                    stats['p95_response_time'] = statistics.quantiles(response_times, n=20)[18]
                except (statistics.StatisticsError, IndexError):
                    stats['p95_response_time'] = max(response_times)
        
        return stats
    
    def get_all_status(self) -> Dict:
        """Obtiene estado de todas las fuentes."""
        return {
            source: self.get_source_status(source)
            for source in self.metrics.keys()
        }
    
    def reset_source(self, source: str):
        """Resetea métricas de una fuente específica."""
        if source in self.metrics:
            config = self.base_config.get(source, {})
            with self.locks[source]:
                self.metrics[source] = ApiMetrics(
                    min_delay=config.get('min_delay', 0.2),
                    max_delay=config.get('max_delay', 15.0),
                    current_delay=config.get('min_delay', 0.2)
                )
            print(f"🔄 Rate limiter resetted para {source}")
    
    def force_recovery(self, source: str):
        """Fuerza la recuperación de una API marcada como DOWN."""
        if source in self.metrics:
            with self.locks[source]:
                metrics = self.metrics[source]
                metrics.health_status = ApiHealthStatus.HEALTHY
                metrics.consecutive_errors = 0
                metrics.consecutive_successes = 1
                metrics.current_delay = metrics.min_delay
            print(f"💚 Forced recovery para {source}")

# Instancia global del rate limiter
_rate_limiter_instance = None

def get_rate_limiter() -> AdaptiveRateLimiter:
    """Obtiene la instancia global del rate limiter."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = AdaptiveRateLimiter()
    return _rate_limiter_instance

# Funciones de conveniencia
def wait_for_api(source: str) -> float:
    """Función de conveniencia para esperar rate limit."""
    return get_rate_limiter().wait_for_rate_limit(source)

def record_api_result(source: str, success: bool, response_time: float, 
                     error_type: str = None, status_code: int = None, 
                     was_throttled: bool = False, was_timeout: bool = False,
                     retry_after: float = None):
    """Función de conveniencia para registrar resultado de API."""
    result = RequestResult(
        success=success,
        response_time=response_time,
        error_type=error_type,
        status_code=status_code,
        was_throttled=was_throttled,
        was_timeout=was_timeout,
        retry_after=retry_after
    )
    get_rate_limiter().record_request_result(source, result)

def get_api_timeout(source: str) -> float:
    """Función de conveniencia para obtener timeout optimizado."""
    return get_rate_limiter().get_optimal_timeout(source)

def get_api_status(source: str = None) -> Dict:
    """Función de conveniencia para obtener estado de APIs."""
    if source:
        return get_rate_limiter().get_source_status(source)
    else:
        return get_rate_limiter().get_all_status()