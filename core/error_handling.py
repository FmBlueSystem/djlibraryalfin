import functools
import traceback
import time
import logging
from enum import Enum
from typing import Optional, Callable, Any, Type, Union, Dict
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

class ErrorSeverity(Enum):
    """Niveles de severidad de errores"""
    LOW = "low"          # No afecta funcionalidad
    MEDIUM = "medium"    # Degrada funcionalidad
    HIGH = "high"        # Funcionalidad crítica afectada
    CRITICAL = "critical" # App puede fallar

class ErrorCategory(Enum):
    """Categorías de errores"""
    AUDIO = "audio"
    DATABASE = "database"
    NETWORK = "network"
    FILE_IO = "file_io"
    UI = "ui"
    SYSTEM = "system"
    VALIDATION = "validation"

class RecoveryAction(Enum):
    """Acciones de recuperación"""
    RETRY = "retry"
    FALLBACK = "fallback"
    IGNORE = "ignore"
    RESTART_COMPONENT = "restart_component"
    SHOW_ERROR = "show_error"
    LOG_ONLY = "log_only"

class DJError(Exception):
    """Excepción base para errores de DjAlfin"""
    
    def __init__(self, message: str, category: ErrorCategory, 
                 severity: ErrorSeverity, recoverable: bool = True,
                 metadata: Dict[str, Any] = None):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.metadata = metadata or {}
        self.timestamp = time.time()

class AudioError(DJError):
    """Errores relacionados con audio"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, **kwargs):
        super().__init__(message, ErrorCategory.AUDIO, severity, **kwargs)

class DatabaseError(DJError):
    """Errores de base de datos"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH, **kwargs):
        super().__init__(message, ErrorCategory.DATABASE, severity, **kwargs)

class NetworkError(DJError):
    """Errores de red"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, **kwargs):
        super().__init__(message, ErrorCategory.NETWORK, severity, **kwargs)

class FileIOError(DJError):
    """Errores de archivos"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, **kwargs):
        super().__init__(message, ErrorCategory.FILE_IO, severity, **kwargs)

class UIError(DJError):
    """Errores de interfaz de usuario"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.LOW, **kwargs):
        super().__init__(message, ErrorCategory.UI, severity, **kwargs)

class ValidationError(DJError):
    """Errores de validación"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, **kwargs):
        super().__init__(message, ErrorCategory.VALIDATION, severity, **kwargs)

class ErrorHandler(QObject):
    """Manejador central de errores con capacidades de recuperación"""
    
    error_occurred = Signal(str, str, str)  # message, category, severity
    recovery_attempted = Signal(str, str)   # action, result
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.logger = logging.getLogger("error_handler")
        self.parent_widget = parent
        self.recovery_strategies = self._setup_recovery_strategies()
        self.error_counts = {}  # Para tracking de errores recurrentes
        
    def _setup_recovery_strategies(self) -> Dict[ErrorCategory, Dict[Type[Exception], RecoveryAction]]:
        """Configurar estrategias de recuperación por tipo de error"""
        return {
            ErrorCategory.AUDIO: {
                FileNotFoundError: RecoveryAction.FALLBACK,
                PermissionError: RecoveryAction.SHOW_ERROR,
                AudioError: RecoveryAction.RETRY,
            },
            ErrorCategory.DATABASE: {
                DatabaseError: RecoveryAction.RETRY,
                FileNotFoundError: RecoveryAction.RESTART_COMPONENT,
                PermissionError: RecoveryAction.SHOW_ERROR,
            },
            ErrorCategory.NETWORK: {
                NetworkError: RecoveryAction.RETRY,
                ConnectionError: RecoveryAction.RETRY,
                TimeoutError: RecoveryAction.RETRY,
            },
            ErrorCategory.FILE_IO: {
                FileNotFoundError: RecoveryAction.FALLBACK,
                PermissionError: RecoveryAction.SHOW_ERROR,
                FileIOError: RecoveryAction.RETRY,
            },
            ErrorCategory.UI: {
                UIError: RecoveryAction.LOG_ONLY,
                Exception: RecoveryAction.LOG_ONLY,
            },
            ErrorCategory.VALIDATION: {
                ValidationError: RecoveryAction.SHOW_ERROR,
                ValueError: RecoveryAction.SHOW_ERROR,
            }
        }
    
    def handle_error(self, error: Exception, context: str = "", 
                    category: Optional[ErrorCategory] = None,
                    severity: Optional[ErrorSeverity] = None) -> bool:
        """Manejar error con recuperación automática"""
        
        # Determinar categoría y severidad si no se proporcionan
        if isinstance(error, DJError):
            category = error.category
            severity = error.severity
        else:
            category = category or self._infer_category(error)
            severity = severity or self._infer_severity(error)
        
        # Logging del error
        error_key = f"{category.value}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        self.logger.error(
            f"Error in {context}: {str(error)}",
            extra={
                "category": category.value,
                "severity": severity.value,
                "error_type": type(error).__name__,
                "context": context,
                "occurrence_count": self.error_counts[error_key],
                "traceback": traceback.format_exc()
            }
        )
        
        # Emitir señal
        self.error_occurred.emit(str(error), category.value, severity.value)
        
        # Intentar recuperación
        return self._attempt_recovery(error, category, context)
    
    def _infer_category(self, error: Exception) -> ErrorCategory:
        """Inferir categoría del error basado en el tipo"""
        error_type = type(error).__name__
        
        if 'Audio' in error_type or 'Sound' in error_type:
            return ErrorCategory.AUDIO
        elif 'Database' in error_type or 'SQL' in error_type:
            return ErrorCategory.DATABASE
        elif 'Network' in error_type or 'Connection' in error_type or 'HTTP' in error_type:
            return ErrorCategory.NETWORK
        elif 'File' in error_type or 'IO' in error_type or 'Path' in error_type:
            return ErrorCategory.FILE_IO
        elif 'UI' in error_type or 'Widget' in error_type or 'Qt' in error_type:
            return ErrorCategory.UI
        elif 'Validation' in error_type or 'Value' in error_type:
            return ErrorCategory.VALIDATION
        else:
            return ErrorCategory.SYSTEM
    
    def _infer_severity(self, error: Exception) -> ErrorSeverity:
        """Inferir severidad del error"""
        critical_types = [SystemError, MemoryError, KeyboardInterrupt]
        high_types = [FileNotFoundError, PermissionError, ConnectionError]
        medium_types = [ValueError, TypeError, AttributeError]
        
        if any(isinstance(error, t) for t in critical_types):
            return ErrorSeverity.CRITICAL
        elif any(isinstance(error, t) for t in high_types):
            return ErrorSeverity.HIGH
        elif any(isinstance(error, t) for t in medium_types):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _attempt_recovery(self, error: Exception, category: ErrorCategory, context: str) -> bool:
        """Intentar recuperación del error"""
        strategy = self.recovery_strategies.get(category, {})
        error_type = type(error)
        
        # Buscar estrategia específica o genérica
        action = strategy.get(error_type) or strategy.get(Exception, RecoveryAction.LOG_ONLY)
        
        try:
            success = self._execute_recovery_action(action, error, context)
            self.recovery_attempted.emit(action.value, "success" if success else "failed")
            return success
        except Exception as recovery_error:
            self.logger.error(f"Recovery action failed: {recovery_error}")
            self.recovery_attempted.emit(action.value, "error")
            return False
    
    def _execute_recovery_action(self, action: RecoveryAction, error: Exception, context: str) -> bool:
        """Ejecutar acción de recuperación"""
        if action == RecoveryAction.RETRY:
            # La lógica de retry se maneja en los decoradores
            return True
        
        elif action == RecoveryAction.FALLBACK:
            # Usar valor por defecto o modo degradado
            self.logger.info(f"Using fallback for error in {context}")
            return True
        
        elif action == RecoveryAction.SHOW_ERROR:
            # Mostrar error al usuario
            self._show_error_dialog(error, context)
            return True
        
        elif action == RecoveryAction.RESTART_COMPONENT:
            # Reiniciar componente afectado
            self.logger.info(f"Restarting component after error in {context}")
            return True
        
        elif action == RecoveryAction.LOG_ONLY:
            # Solo registrar, no hacer nada más
            return True
        
        elif action == RecoveryAction.IGNORE:
            # Ignorar completamente
            return True
        
        return False
    
    def _show_error_dialog(self, error: Exception, context: str):
        """Mostrar diálogo de error al usuario"""
        if self.parent_widget:
            QMessageBox.warning(
                self.parent_widget,
                "Error en DjAlfin",
                f"Se produjo un error en {context}:\n\n{str(error)}\n\nLa aplicación continuará funcionando."
            )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de errores"""
        total_errors = sum(self.error_counts.values())
        most_common = max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        
        return {
            "total_errors": total_errors,
            "unique_errors": len(self.error_counts),
            "most_common_error": most_common[0] if most_common else None,
            "most_common_count": most_common[1] if most_common else 0,
            "error_breakdown": dict(self.error_counts)
        }

class ErrorRecovery:
    """Decoradores para manejo automático de errores con recuperación"""
    
    @staticmethod
    def with_retry(max_attempts: int = 3, 
                  exceptions: tuple = (Exception,),
                  delay: float = 1.0,
                  backoff_factor: float = 2.0):
        """Decorador para reintentos automáticos"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = logging.getLogger(f"retry.{func.__name__}")
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        if attempt == max_attempts - 1:
                            logger.error(f"All {max_attempts} retry attempts failed for {func.__name__}: {e}")
                            raise
                        
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}. Waiting {wait_time:.1f}s")
                        time.sleep(wait_time)
                
                return None
            return wrapper
        return decorator
    
    @staticmethod
    def graceful_degradation(fallback_func: Callable, 
                           exceptions: tuple = (Exception,)):
        """Decorador para degradación graciosa"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = logging.getLogger(f"fallback.{func.__name__}")
                
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"Function {func.__name__} failed, using fallback: {e}")
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback function also failed: {fallback_error}")
                        raise e  # Elevar error original
            return wrapper
        return decorator
    
    @staticmethod
    def safe_execution(default_return: Any = None,
                      log_errors: bool = True,
                      exceptions: tuple = (Exception,)):
        """Decorador para ejecución segura que nunca eleva excepciones"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if log_errors:
                        logger = logging.getLogger(f"safe.{func.__name__}")
                        logger.error(f"Safe execution caught error in {func.__name__}: {e}")
                    return default_return
            return wrapper
        return decorator
    
    @staticmethod
    def with_timeout(timeout_seconds: float):
        """Decorador para timeout de funciones"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                
                # Configurar timeout solo en sistemas Unix
                if hasattr(signal, 'SIGALRM'):
                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(timeout_seconds))
                    
                    try:
                        result = func(*args, **kwargs)
                        signal.alarm(0)  # Cancelar timeout
                        return result
                    finally:
                        signal.signal(signal.SIGALRM, old_handler)
                else:
                    # En Windows, ejecutar sin timeout
                    return func(*args, **kwargs)
            return wrapper
        return decorator

# Instancia global del manejador de errores
global_error_handler = ErrorHandler()

# Funciones de conveniencia
def handle_error(error: Exception, context: str = "", 
                category: Optional[ErrorCategory] = None,
                severity: Optional[ErrorSeverity] = None) -> bool:
    """Manejar error usando el handler global"""
    return global_error_handler.handle_error(error, context, category, severity)

def set_error_handler_parent(parent: QWidget):
    """Configurar widget padre para diálogos de error"""
    global_error_handler.parent_widget = parent

def get_error_statistics() -> Dict[str, Any]:
    """Obtener estadísticas de errores"""
    return global_error_handler.get_error_statistics()
