import sys
import os
import sentry_sdk
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from config.secure_config import secure_config
from ui.stylesheet import get_stylesheet
from core.logging_config import DJLogger, log_info, log_error

def setup_sentry():
    dsn = secure_config.get_sentry_dsn()
    if dsn and secure_config.is_sentry_enabled():
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            enable_tracing=True
        )

def main():
    """Función principal para iniciar la aplicación."""
    # Inicializar sistema de logging
    logger = DJLogger()
    log_info("🚀 Iniciando aplicación DjAlfin...")
    
    try:
        setup_sentry()
        log_info("✅ Sentry configurado correctamente")
    except Exception as e:
        log_error("❌ Error configurando Sentry", exception=e)
    
    try:
        app = QApplication(sys.argv)
        
        # Aplicar el stylesheet global
        app.setStyleSheet(get_stylesheet())
        log_info("✅ Stylesheet aplicado correctamente")
        
        # Añadir la ruta del proyecto al sys.path
        project_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        
        # Inicializar base de datos
        from core.database import init_db
        init_db()
        log_info("✅ Base de datos inicializada")
        
        # Crear y mostrar ventana principal
        window = MainWindow()
        window.show()
        log_info("✅ MainWindow mostrada")
        
        log_info("🔄 Iniciando bucle de eventos...")
        return app.exec()
    
    except Exception as e:
        log_error("❌ Error crítico en main()", exception=e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
