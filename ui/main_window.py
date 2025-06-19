import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QDialog, QStatusBar, QMenuBar, QMenu, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtCore import Qt, Signal, QTimer

from config.design_system import Theme

from core.database import init_db, create_connection, get_db_path
from core.audio_service import AudioService
from core.library_scanner import LibraryScanner
from services.playlist_service import PlaylistService

from .track_list import TrackListView
from .playback_panel import PlaybackPanel
from .enrichment_panel import EnrichmentPanel
from .playlist_panel import PlaylistPanel
from .smart_playlist_editor import SmartPlaylistEditor
from .api_config_dialog import APIConfigDialog

class MainWindow(QMainWindow):
    """
    La ventana principal de la aplicación DjAlfin.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DjAlfin - Professional DJ Library")
        self.setGeometry(100, 100, 1800, 1000)

        # --- Core Components ---
        init_db()
        self.db_conn = create_connection()
        self.audio_service = AudioService(self)
        self.playlist_service = PlaylistService(get_db_path())

        # --- UI Components ---
        self.track_list_view = TrackListView(db_connection=self.db_conn)
        self.enrichment_panel = EnrichmentPanel()
        self.playback_panel = PlaybackPanel(self.audio_service)
        self.playlist_panel = PlaylistPanel(service=self.playlist_service)
        
        # Configurar políticas de tamaño para mejor distribución
        self.track_list_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.enrichment_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.playlist_panel.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.playback_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        # --- Layout ---
        self.setup_layout()
        
        # --- Connections ---
        self.connect_signals()
        
        # --- Menu ---
        self._create_menu()

        self.status_bar.showMessage("✅ Aplicación iniciada y lista.", 5000)
        self.track_list_view.load_all_tracks()

    def setup_layout(self):
        """Configura el layout principal con TrackListView como componente principal."""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)

        # Splitter vertical simple: TrackListView arriba, EnrichmentPanel abajo (opcional)
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setHandleWidth(4)  # Separador delgado
        
        # Panel principal: TrackListView ocupa todo el ancho disponible
        content_splitter.addWidget(self.track_list_view)
        
        # Panel inferior: Enrichment (compacto y oculto por defecto)
        self.enrichment_panel.setMinimumHeight(200)
        self.enrichment_panel.setMaximumHeight(350)
        self.enrichment_panel.setVisible(False)  # Oculto por defecto
        content_splitter.addWidget(self.enrichment_panel)
        
        # Configurar proporciones del splitter vertical
        # 85% para TrackListView, 15% para EnrichmentPanel cuando esté visible
        content_splitter.setSizes([850, 150])
        
        # Ocultar PlaylistPanel completamente
        self.playlist_panel.setVisible(False)
        
        # Layout principal: contenido arriba, playback minimalista abajo
        main_layout.addWidget(content_splitter, 1)  # Se expande
        main_layout.addWidget(self.playback_panel, 0)  # Altura fija

        self.setCentralWidget(main_widget)
        
        # Aplicar estilos minimalistas al splitter
        self.apply_splitter_styles(content_splitter)
        
    def apply_splitter_styles(self, splitter):
        """Aplica estilos minimalistas al splitter."""
        splitter_style = f"""
        QSplitter::handle {{
            background: {Theme.BORDER};
        }}
        
        QSplitter::handle:horizontal {{
            width: 4px;
            background: {Theme.BORDER};
        }}
        
        QSplitter::handle:vertical {{
            height: 4px;
            background: {Theme.BORDER};
        }}
        
        QSplitter::handle:hover {{
            background: {Theme.PRIMARY};
        }}
        """
        
        splitter.setStyleSheet(splitter_style)
        
    def toggle_enrichment_panel(self):
        """Alterna la visibilidad del panel de enriquecimiento."""
        is_visible = self.enrichment_panel.isVisible()
        self.enrichment_panel.setVisible(not is_visible)
        
        # Actualizar mensaje de estado
        if not is_visible:
            self.status_bar.showMessage("Panel de metadatos mostrado", 2000)
        else:
            self.status_bar.showMessage("Panel de metadatos oculto", 2000)
    
    def toggle_playlist_panel(self):
        """Alterna la visibilidad del panel de playlists."""
        is_visible = self.playlist_panel.isVisible()
        self.playlist_panel.setVisible(not is_visible)
        
        # Actualizar mensaje de estado
        if not is_visible:
            self.status_bar.showMessage("Panel de playlists mostrado", 2000)
            # Reconectar señales si es necesario
            if hasattr(self.playlist_panel, 'selection_changed'):
                self.playlist_panel.selection_changed.connect(self.handle_playlist_selection)
        else:
            self.status_bar.showMessage("Panel de playlists oculto", 2000)

    def connect_signals(self):
        """Conecta todas las señales y slots de la aplicación."""
        self.track_list_view.track_selected.connect(self.audio_service.load_track)
        self.track_list_view.track_selected.connect(self.enrichment_panel.update_track_info)
        self.enrichment_panel.metadataChanged.connect(self.track_list_view.refresh_current_row)
        self.enrichment_panel.enrichRequested.connect(self.handle_enrichment_request)
        # self.playlist_panel.selection_changed.connect(self.handle_playlist_selection)  # Deshabilitado - panel oculto
        self.audio_service.errorOccurred.connect(self.show_status_message)
        
    def handle_playlist_selection(self, selection_type, item_id):
        """Maneja la selección de un elemento en el panel de playlists."""
        self.status_bar.showMessage(f"Cargando '{item_id}'...", 2000)
        if selection_type == 'library':
            self.track_list_view.load_all_tracks()
        elif selection_type == 'smart_playlist':
            rules, match_all = self.playlist_service.get_playlist_details(item_id)
            if rules is not None:
                track_ids = self.playlist_service.get_tracks(rules, match_all)
                self.track_list_view.load_tracks_by_ids(track_ids)
            else:
                self.track_list_view.clear_tracks()
                
    def _create_menu(self):
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("&Archivo")

        scan_action = QAction("Escanear Librería", self)
        scan_action.triggered.connect(self.scan_library)
        file_menu.addAction(scan_action)
        
        spl_action = QAction("Editor de Smart Playlists", self)
        spl_action.triggered.connect(self.open_smart_playlist_editor)
        file_menu.addAction(spl_action)

        api_action = QAction("Configurar APIs", self)
        api_action.triggered.connect(self.open_api_config)
        file_menu.addAction(api_action)

        file_menu.addSeparator()
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Ver
        view_menu = menubar.addMenu("&Ver")
        
        toggle_enrichment_action = QAction("Mostrar/Ocultar Panel de Metadatos", self)
        toggle_enrichment_action.setShortcut(QKeySequence("Ctrl+M"))
        toggle_enrichment_action.triggered.connect(self.toggle_enrichment_panel)
        view_menu.addAction(toggle_enrichment_action)
        
        toggle_playlist_action = QAction("Mostrar/Ocultar Panel de Playlists", self)
        toggle_playlist_action.setShortcut(QKeySequence("Ctrl+P"))
        toggle_playlist_action.triggered.connect(self.toggle_playlist_panel)
        view_menu.addAction(toggle_playlist_action)

    def scan_library(self):
        """Inicia el proceso de escaneo de la librería."""
        self.status_bar.showMessage("Escaneando librería...")
        scanner = LibraryScanner()
        scanner.finished.connect(self.scan_finished)
        scanner.start()

    def scan_finished(self):
        self.status_bar.showMessage("Escaneo completado.", 5000)
        self.track_list_view.load_all_tracks()

    def open_smart_playlist_editor(self):
        editor = SmartPlaylistEditor(service=self.playlist_service, parent=self)
        if editor.exec() == QDialog.Accepted:
            self.playlist_panel.refresh_playlists()

    def open_api_config(self):
        dialog = APIConfigDialog(parent=self)
        dialog.exec()

    def show_status_message(self, message, timeout=5000):
        self.statusBar().showMessage(message, timeout)
        
    def handle_enrichment_request(self, source: str):
        """Maneja las solicitudes de enriquecimiento de metadatos."""
        self.status_bar.showMessage(f"Enriqueciendo con {source}...", 2000)
        self.enrichment_panel.set_enriching(source)
        
        # Simular enriquecimiento (en una implementación real, esto sería asíncrono)
        QTimer.singleShot(2000, lambda: self._complete_enrichment(source))
        
    def _complete_enrichment(self, source: str):
        """Completa el proceso de enriquecimiento simulado."""
        self.enrichment_panel.set_enrichment_complete(source, True, "Completado exitosamente")
        self.status_bar.showMessage(f"Enriquecimiento con {source} completado", 3000)
        
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        self.audio_service.stop()
        self.db_conn.close()
        print("Aplicación cerrada limpiamente.")
        event.accept()
