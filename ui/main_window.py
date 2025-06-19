import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QDialog, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QAction
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from core.database import init_db, create_connection, get_db_path
from core.audio_service import AudioService
from core.library_scanner import LibraryScanner
from services.playlist_service import PlaylistService

from .track_list import TrackListView
from .playback_panel import PlaybackPanel
from .metadata_panel import MetadataPanel
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
        self.metadata_panel = MetadataPanel()
        self.playback_panel = PlaybackPanel(self.audio_service)
        self.playlist_panel = PlaylistPanel(service=self.playlist_service)
        self.setStatusBar(QStatusBar(self))

        # --- Layout ---
        self.setup_layout()
        
        # --- Connections ---
        self.connect_signals()
        
        # --- Menu ---
        self._create_menu()

        self.status_bar.showMessage("✅ Aplicación iniciada y lista.", 5000)
        self.track_list_view.load_all_tracks()

    def setup_layout(self):
        """Configura el layout principal de la aplicación."""
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.addWidget(self.playlist_panel)
        left_splitter.addWidget(self.track_list_view)
        left_splitter.setSizes([250, 750]) # Adjusted sizes

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(self.metadata_panel)
        main_splitter.setSizes([1300, 500]) # Adjusted sizes

        right_layout = QVBoxLayout()
        right_layout.addWidget(main_splitter)
        right_layout.addWidget(self.playback_panel)
        right_layout.setStretchFactor(main_splitter, 8)
        right_layout.setStretchFactor(self.playback_panel, 1)

        main_layout.addLayout(right_layout)
        self.setCentralWidget(main_widget)

    def connect_signals(self):
        """Conecta todas las señales y slots de la aplicación."""
        self.track_list_view.track_selected.connect(self.audio_service.load_track)
        self.track_list_view.track_selected.connect(self.metadata_panel.update_track_info)
        self.metadata_panel.metadata_changed.connect(self.track_list_view.refresh_current_row)
        self.playlist_panel.selection_changed.connect(self.handle_playlist_selection)
        self.audio_service.error_occurred.connect(self.show_status_message)
        
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
        if editor.exec_() == QDialog.Accepted:
            self.playlist_panel.refresh_playlists()

    def open_api_config(self):
        dialog = APIConfigDialog(parent=self)
        dialog.exec_()

    def show_status_message(self, message, timeout=5000):
        self.statusBar().showMessage(message, timeout)
        
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        self.audio_service.stop()
        self.db_conn.close()
        print("Aplicación cerrada limpiamente.")
        event.accept()
