import logging
import logging.handlers
from pathlib import Path
import json
import os
import functools
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable

class DJLogger:
    """Sistema de logging estructurado para DjAlfin"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.setup_logging()
            self._initialized = True
    
    def setup_logging(self, log_level: str = "INFO", log_dir: str = "logs"):
        """Configurar sistema de logging comprehensivo"""
        # Crear directorio de logs
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Configurar múltiples handlers
        handlers = [
            self._get_file_handler(log_path / "app.log"),
            self._get_error_handler(log_path / "errors.log"),
            self._get_performance_handler(log_path / "performance.log"),
            self._get_console_handler()
        ]
        
        # Configurar logger principal
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Limpiar handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Añadir nuevos handlers
        for handler in handlers:
            root_logger.addHandler(handler)
        
        # Configurar loggers específicos
        self._setup_specialized_loggers()
        
        logging.info("DJLogger initialized successfully")
    
    def _get_file_handler(self, filename: Path) -> logging.Handler:
        """Handler para archivo general"""
        handler = logging.handlers.RotatingFileHandler(
            filename, maxBytes=10*1024*1024, backupCount=5
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        return handler
    
    def _get_error_handler(self, filename: Path) -> logging.Handler:
        """Handler para errores críticos"""
        handler = logging.handlers.RotatingFileHandler(
            filename, maxBytes=5*1024*1024, backupCount=3
        )
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        handler.setFormatter(formatter)
        return handler
    
    def _get_performance_handler(self, filename: Path) -> logging.Handler:
        """Handler para métricas de rendimiento"""
        handler = logging.handlers.RotatingFileHandler(
            filename, maxBytes=10*1024*1024, backupCount=5
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')  # JSON puro
        handler.setFormatter(formatter)
        return handler
    
    def _get_console_handler(self) -> logging.Handler:
        """Handler para consola con colores"""
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        return handler
    
    def _setup_specialized_loggers(self):
        """Configurar loggers especializados"""
        # Logger para acciones de usuario
        user_logger = logging.getLogger("user_actions")
        user_logger.setLevel(logging.INFO)
        
        # Logger para rendimiento
        perf_logger = logging.getLogger("performance")
        perf_logger.setLevel(logging.INFO)
        
        # Logger para audio
        audio_logger = logging.getLogger("audio")
        audio_logger.setLevel(logging.DEBUG)
        
        # Logger para base de datos
        db_logger = logging.getLogger("database")
        db_logger.setLevel(logging.INFO)
    
    @staticmethod
    def log_performance(operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Registrar métricas de rendimiento"""
        perf_logger = logging.getLogger("performance")
        data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "metadata": metadata or {}
        }
        perf_logger.info(json.dumps(data))
    
    @staticmethod
    def log_user_action(action: str, details: Dict[str, Any] = None):
        """Registrar acciones del usuario"""
        user_logger = logging.getLogger("user_actions")
        data = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details or {}
        }
        user_logger.info(json.dumps(data))
    
    @staticmethod
    def log_audio_event(event: str, track_info: Dict[str, Any] = None):
        """Registrar eventos de audio"""
        audio_logger = logging.getLogger("audio")
        data = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "track_info": track_info or {}
        }
        audio_logger.info(json.dumps(data))
    
    @staticmethod
    def log_database_operation(operation: str, table: str, duration: float, affected_rows: int = None):
        """Registrar operaciones de base de datos"""
        db_logger = logging.getLogger("database")
        data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "table": table,
            "duration_ms": round(duration * 1000, 2),
            "affected_rows": affected_rows
        }
        db_logger.info(json.dumps(data))

class ColoredFormatter(logging.Formatter):
    """Formatter con colores para consola"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Verde
        'WARNING': '\033[33m',  # Amarillo
        'ERROR': '\033[31m',    # Rojo
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

# Decoradores para logging automático
def log_performance(operation_name: str = None):
    """Decorador para logging automático de rendimiento"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                DJLogger.log_performance(operation, duration, {"success": True})
                return result
            except Exception as e:
                duration = time.time() - start_time
                DJLogger.log_performance(operation, duration, {
                    "success": False, 
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                raise
        return wrapper
    return decorator

def log_user_action(action_name: str = None):
    """Decorador para logging de acciones de usuario"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            action = action_name or f"{func.__name__}"
            try:
                result = func(*args, **kwargs)
                DJLogger.log_user_action(action, {"success": True})
                return result
            except Exception as e:
                DJLogger.log_user_action(action, {
                    "success": False,
                    "error": str(e)
                })
                raise
        return wrapper
    return decorator

def log_audio_operation(operation_name: str = None):
    """Decorador para logging de operaciones de audio"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation = operation_name or f"{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                DJLogger.log_audio_event(operation, {
                    "duration_ms": round(duration * 1000, 2),
                    "success": True
                })
                return result
            except Exception as e:
                duration = time.time() - start_time
                DJLogger.log_audio_event(operation, {
                    "duration_ms": round(duration * 1000, 2),
                    "success": False,
                    "error": str(e)
                })
                raise
        return wrapper
    return decorator

# Inicializar logger global
dj_logger = DJLogger()

# Funciones de conveniencia
def get_logger(name: str) -> logging.Logger:
    """Obtener logger con nombre específico"""
    return logging.getLogger(name)

def log_info(message: str, **kwargs):
    """Log nivel INFO con metadata"""
    logger = logging.getLogger("app")
    if kwargs:
        message = f"{message} - {json.dumps(kwargs)}"
    logger.info(message)

def log_error(message: str, exception: Exception = None, **kwargs):
    """Log nivel ERROR con metadata"""
    logger = logging.getLogger("app")
    extra_data = {"metadata": kwargs}
    if exception:
        extra_data["exception_type"] = type(exception).__name__
        extra_data["exception_message"] = str(exception)
    
    message = f"{message} - {json.dumps(extra_data)}"
    logger.error(message, exc_info=exception is not None)

def log_warning(message: str, **kwargs):
    """Log nivel WARNING con metadata"""
    logger = logging.getLogger("app")
    if kwargs:
        message = f"{message} - {json.dumps(kwargs)}"
    logger.warning(message)

def log_debug(message: str, **kwargs):
    """Log nivel DEBUG con metadata"""
    logger = logging.getLogger("app")
    if kwargs:
        message = f"{message} - {json.dumps(kwargs)}"
    logger.debug(message)
