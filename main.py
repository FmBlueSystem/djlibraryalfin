import sys
import os
import sentry_sdk
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from config.config import AppConfig
from ui.stylesheet import get_stylesheet

def setup_sentry():
    config = AppConfig()
    dsn = config.get_sentry_dsn()
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            enable_tracing=True
        )

def main():
    """Función principal para iniciar la aplicación."""
    setup_sentry()
    
    app = QApplication(sys.argv)
    
    # Aplicar el stylesheet global
    app.setStyleSheet(get_stylesheet())

    # Añadir la ruta del proyecto al sys.path
    project_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    
    print("🚀 Iniciando aplicación DjAlfin...")
    init_db()
    
    window = MainWindow()
    window.show()
    print("✅ MainWindow mostrada")
    
    print("🔄 Iniciando bucle de eventos...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
