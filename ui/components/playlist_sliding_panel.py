# ui/components/playlist_sliding_panel.py

from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTreeView, QHeaderView, QMenu
from PySide6.QtCore import Qt, Signal, QMimeData, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont
import json

from .loading_widget import LoadingOverlay, ProgressToast
from .playlist_importer import PlaylistExporter, PlaylistImporter

from .sliding_panel import SlidingPanel
from services.playlist_service import PlaylistService

try:
    import os
    os.environ['QT_API'] = 'pyside6'
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False


class PlaylistDropModel(QStandardItemModel):
    """Modelo personalizado que soporta drag & drop para playlists."""
    
    # Señal emitida cuando se dropean tracks en una playlist
    tracksDropped = Signal(int, list)  # playlist_id, track_ids
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def supportedDropActions(self):
        """Define las acciones de drop soportadas."""
        return Qt.DropAction.CopyAction
    
    def mimeTypes(self):
        """Define los tipos MIME aceptados."""
        return ['application/x-djlibrarytrack-ids']
    
    def canDropMimeData(self, data, action, row, column, parent):
        """Determina si se puede hacer drop de los datos MIME."""
        if not data.hasFormat('application/x-djlibrarytrack-ids'):
            return False
        
        # Solo permitir drop en items de playlists regulares (no smart playlists)
        if parent.isValid():
            item = self.itemFromIndex(parent)
            if item:
                playlist_data = item.data(Qt.ItemDataRole.UserRole)
                if playlist_data and playlist_data.get('type') == 'regular':
                    return True
        
        return False
    
    def dropMimeData(self, data, action, row, column, parent):
        """Maneja el drop de datos MIME."""
        if not self.canDropMimeData(data, action, row, column, parent):
            return False
        
        try:
            # Decodificar datos de tracks
            mime_data = data.data('application/x-djlibrarytrack-ids').data().decode('utf-8')
            track_data = json.loads(mime_data)
            track_ids = track_data.get('track_ids', [])
            
            if not track_ids:
                return False
            
            # Obtener información de la playlist
            item = self.itemFromIndex(parent)
            if item:
                playlist_data = item.data(Qt.ItemDataRole.UserRole)
                if playlist_data and playlist_data.get('type') == 'regular':
                    playlist_id = playlist_data.get('id')
                    
                    # Emitir señal para manejar la adición de tracks
                    self.tracksDropped.emit(playlist_id, track_ids)
                    return True
            
            return False
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Error procesando drop: {e}")
            return False

class PlaylistSlidingPanel(SlidingPanel):
    """
    Panel deslizante para gestión de playlists que se muestra desde el borde izquierdo.
    """
    
    # Señales específicas del panel de playlists
    playlistSelected = Signal(str, object)  # nombre_playlist, tracks
    createPlaylistRequested = Signal()
    editPlaylistRequested = Signal(int)  # playlist_id
    deletePlaylistRequested = Signal(int)  # playlist_id
    exportPlaylistRequested = Signal(int)  # playlist_id
    tracksAddedToPlaylist = Signal(int, list)  # playlist_id, track_ids
    
    def __init__(self, playlist_service: PlaylistService, parent=None):
        # Inicializar panel base (lado izquierdo, 320px de ancho)
        super().__init__(parent=parent, side='left', width=320, auto_hide_delay=3000)
        
        self.playlist_service = playlist_service
        self.playlist_exporter = PlaylistExporter(playlist_service)
        self.playlist_importer = PlaylistImporter(playlist_service)
        
        self.setup_ui()
        self.populate_playlists()
        
    def setup_ui(self):
        """Configura la interfaz del panel de playlists."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # Sin loading overlay para simplificar
        
        # --- Header del Panel ---
        header_layout = QHBoxLayout()
        
        # Título
        title_label = QLabel("🎵 PLAYLISTS")
        title_label.setProperty("class", "sliding_panel_title")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        
        # Botón de nueva playlist
        self.new_playlist_btn = QPushButton()
        if HAS_QTAWESOME:
            self.new_playlist_btn.setIcon(qta.icon("fa5s.plus", color="white"))
        else:
            self.new_playlist_btn.setText("+")
        self.new_playlist_btn.setProperty("class", "sliding_panel_button")
        self.new_playlist_btn.setFixedSize(30, 30)
        self.new_playlist_btn.setToolTip("Nueva Playlist")
        self.new_playlist_btn.clicked.connect(self.createPlaylistRequested.emit)
        
        # Botón de refresh
        self.refresh_btn = QPushButton()
        if HAS_QTAWESOME:
            self.refresh_btn.setIcon(qta.icon("fa5s.sync-alt", color="white"))
        else:
            self.refresh_btn.setText("↻")
        self.refresh_btn.setProperty("class", "sliding_panel_button")
        self.refresh_btn.setFixedSize(30, 30)
        self.refresh_btn.setToolTip("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_playlists)
        
        # Botón de importar
        self.import_btn = QPushButton()
        if HAS_QTAWESOME:
            self.import_btn.setIcon(qta.icon("fa5s.file-import", color="white"))
        else:
            self.import_btn.setText("📥")
        self.import_btn.setProperty("class", "sliding_panel_button")
        self.import_btn.setFixedSize(30, 30)
        self.import_btn.setToolTip("Importar Playlist")
        self.import_btn.clicked.connect(self.import_playlist)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.new_playlist_btn)
        header_layout.addWidget(self.import_btn)
        header_layout.addWidget(self.refresh_btn)
        
        # --- Sección de Biblioteca ---
        library_label = QLabel("📚 BIBLIOTECA")
        library_label.setProperty("class", "sliding_panel_section")
        
        # Botón "Todos los tracks"
        self.all_tracks_btn = QPushButton("Todos los Tracks")
        self.all_tracks_btn.setProperty("class", "sliding_panel_list_item")
        self.all_tracks_btn.clicked.connect(lambda: self.playlistSelected.emit("all_tracks", None))
        
        # --- Lista de Playlists ---
        playlists_label = QLabel("📋 MIS PLAYLISTS")
        playlists_label.setProperty("class", "sliding_panel_section")
        
        # Tree view para playlists
        self.setup_playlist_tree()
        
        # --- Sección de Smart Playlists ---
        smart_label = QLabel("🤖 SMART PLAYLISTS")
        smart_label.setProperty("class", "sliding_panel_section")
        
        # Botón para crear smart playlist
        self.new_smart_btn = QPushButton("+ Nueva Smart Playlist")
        self.new_smart_btn.setProperty("class", "sliding_panel_list_item")
        self.new_smart_btn.clicked.connect(self.create_smart_playlist)
        
        # --- Ensamblar Layout ---
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self._create_separator())
        
        main_layout.addWidget(library_label)
        main_layout.addWidget(self.all_tracks_btn)
        main_layout.addWidget(self._create_separator())
        
        main_layout.addWidget(playlists_label)
        main_layout.addWidget(self.playlist_tree, 1)  # Se expande
        main_layout.addWidget(self._create_separator())
        
        main_layout.addWidget(smart_label)
        main_layout.addWidget(self.new_smart_btn)
        
        main_layout.addStretch(0)  # Espacio al final
        
    def setup_playlist_tree(self):
        """Configura el árbol de playlists."""
        self.playlist_model = PlaylistDropModel()
        self.playlist_model.setHorizontalHeaderLabels(['Playlists'])
        
        # Conectar señal de tracks dropeados
        self.playlist_model.tracksDropped.connect(self.handle_tracks_dropped)
        
        self.playlist_tree = QTreeView()
        self.playlist_tree.setModel(self.playlist_model)
        self.playlist_tree.setHeaderHidden(True)
        self.playlist_tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.playlist_tree.setRootIsDecorated(False)
        self.playlist_tree.setIndentation(15)
        self.playlist_tree.setProperty("class", "sliding_panel_tree")
        
        # Configurar drag & drop
        self.playlist_tree.setAcceptDrops(True)
        self.playlist_tree.setDropIndicatorShown(True)
        self.playlist_tree.setDragDropMode(QTreeView.DragDropMode.DropOnly)
        
        # Conectar selección
        self.playlist_tree.clicked.connect(self.on_playlist_selected)
        self.playlist_tree.doubleClicked.connect(self.on_playlist_double_clicked)
        
        # Configurar menú contextual
        self.playlist_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # Configurar header
        header = self.playlist_tree.header()
        header.setStretchLastSection(True)
        
    def _create_separator(self):
        """Crea un separador visual."""
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setProperty("class", "sliding_panel_separator")
        return separator
        
    def populate_playlists(self):
        """Llena el árbol con las playlists disponibles."""
        self.playlist_model.clear()
        self.playlist_model.setHorizontalHeaderLabels(['Playlists'])
        
        try:
            # Obtener playlists regulares
            playlists = self.playlist_service.get_all_playlists()
            for playlist in playlists:
                item = QStandardItem(f"📋 {playlist['name']}")
                item.setData(playlist, Qt.ItemDataRole.UserRole)
                item.setToolTip(f"{playlist.get('track_count', 0)} tracks")
                self.playlist_model.appendRow(item)
                
            # Obtener smart playlists
            smart_playlists = self.playlist_service.get_smart_playlists()
            for smart_playlist in smart_playlists:
                item = QStandardItem(f"🤖 {smart_playlist['name']}")
                item.setData(smart_playlist, Qt.ItemDataRole.UserRole)
                item.setToolTip(f"Smart: {smart_playlist.get('criteria', 'Sin criterios')}")
                self.playlist_model.appendRow(item)
                
            # Mensaje si no hay playlists
            if len(playlists) == 0 and len(smart_playlists) == 0:
                info_item = QStandardItem("ℹ️ No hay playlists")
                info_item.setEnabled(False)
                self.playlist_model.appendRow(info_item)
                
        except Exception as e:
            print(f"Error cargando playlists: {e}")
            error_item = QStandardItem(f"❌ Error: {str(e)}")
            error_item.setEnabled(False)
            self.playlist_model.appendRow(error_item)
            
    def on_playlist_selected(self, index):
        """Maneja la selección de una playlist."""
        item = self.playlist_model.itemFromIndex(index)
        if item:
            playlist_data = item.data(Qt.ItemDataRole.UserRole)
            if playlist_data:
                playlist_name = playlist_data['name']
                print(f"🎵 Playlist seleccionada: {playlist_name}")
                
                # Obtener tracks de la playlist
                try:
                    tracks = self.playlist_service.get_playlist_tracks(playlist_data['id'])
                    self.playlistSelected.emit(playlist_name, tracks)
                except Exception as e:
                    print(f"Error al cargar tracks de playlist: {e}")
                    
    def on_playlist_double_clicked(self, index):
        """Maneja el doble clic en una playlist."""
        item = self.playlist_model.itemFromIndex(index)
        if item:
            playlist_data = item.data(Qt.ItemDataRole.UserRole)
            if playlist_data:
                self.editPlaylistRequested.emit(playlist_data['name'])
                
    def refresh_playlists(self):
        """Actualiza la lista de playlists."""
        print("🔄 Actualizando playlists...")
        self.populate_playlists()
        
    def create_smart_playlist(self):
        """Abre el editor de smart playlists."""
        print("🤖 Creando nueva smart playlist...")
        # Aquí se podría abrir un diálogo específico para smart playlists
        self.createPlaylistRequested.emit()
        
    # --- Métodos públicos para control externo ---
    
    def select_playlist(self, playlist_name):
        """Selecciona una playlist específica."""
        for row in range(self.playlist_model.rowCount()):
            item = self.playlist_model.item(row)
            if item:
                playlist_data = item.data(Qt.ItemDataRole.UserRole)
                if playlist_data and playlist_data['name'] == playlist_name:
                    index = self.playlist_model.indexFromItem(item)
                    self.playlist_tree.setCurrentIndex(index)
                    self.on_playlist_selected(index)
                    break
    
    def handle_tracks_dropped(self, playlist_id, track_ids):
        """Maneja cuando se dropean tracks en una playlist."""
        print(f"🎵 Agregando {len(track_ids)} tracks a playlist {playlist_id}")
        
        # Agregar tracks usando el servicio (triggers actualizan stats automáticamente)
        success = self.playlist_service.add_tracks_to_playlist(playlist_id, track_ids)
        
        if success:
            self.tracksAddedToPlaylist.emit(playlist_id, track_ids)
            self.refresh_playlists()  # Actualizar para mostrar nuevo count
            print(f"✅ {len(track_ids)} tracks agregados exitosamente")
        else:
            print(f"❌ Error agregando tracks a playlist {playlist_id}")
    
    def show_context_menu(self, position):
        """Muestra el menú contextual para playlists."""
        index = self.playlist_tree.indexAt(position)
        if not index.isValid():
            return
        
        item = self.playlist_model.itemFromIndex(index)
        if not item:
            return
        
        playlist_data = item.data(Qt.ItemDataRole.UserRole)
        if not playlist_data:
            return
        
        # Crear menú contextual
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 12px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #2196F3;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 4px 0px;
            }
        """)
        
        playlist_type = playlist_data.get('type', 'smart')
        playlist_id = playlist_data.get('id')
        playlist_name = playlist_data.get('name', 'Unknown')
        
        if playlist_type == 'regular':
            # Menú para playlists regulares
            play_action = menu.addAction("▶️ Reproducir Playlist")
            play_action.triggered.connect(lambda: self.on_playlist_selected(index))
            
            menu.addSeparator()
            
            edit_action = menu.addAction("✏️ Editar Playlist")
            edit_action.triggered.connect(lambda: self.editPlaylistRequested.emit(playlist_id))
            
            rename_action = menu.addAction("📝 Renombrar")
            rename_action.triggered.connect(lambda: self.rename_playlist(playlist_id, playlist_name))
            
            menu.addSeparator()
            
            export_action = menu.addAction("📤 Exportar Playlist")
            export_action.triggered.connect(lambda: self.export_playlist(playlist_id))
            
            menu.addSeparator()
            
            delete_action = menu.addAction("🗑️ Eliminar Playlist")
            delete_action.triggered.connect(lambda: self.deletePlaylistRequested.emit(playlist_id))
            
        else:
            # Menú para smart playlists
            play_action = menu.addAction("▶️ Reproducir Smart Playlist")
            play_action.triggered.connect(lambda: self.on_playlist_selected(index))
            
            menu.addSeparator()
            
            edit_action = menu.addAction("⚙️ Editar Reglas")
            edit_action.triggered.connect(lambda: self.editPlaylistRequested.emit(playlist_id))
            
            menu.addSeparator()
            
            freeze_action = menu.addAction("❄️ Congelar como Playlist Regular")
            freeze_action.triggered.connect(lambda: self.freeze_smart_playlist(playlist_id))
        
        # Mostrar menú
        menu.exec(self.playlist_tree.mapToGlobal(position))
    
    def rename_playlist(self, playlist_id, current_name):
        """Renombra una playlist usando un diálogo simple."""
        from PySide6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self, 
            "Renombrar Playlist",
            "Nuevo nombre:",
            text=current_name
        )
        
        if ok and new_name.strip() and new_name.strip() != current_name:
            success = self.playlist_service.rename_playlist(playlist_id, new_name.strip())
            if success:
                self.refresh_playlists()
                print(f"✅ Playlist renombrada a '{new_name.strip()}'")
            else:
                print(f"❌ Error renombrando playlist")
    
    def freeze_smart_playlist(self, smart_playlist_id):
        """Convierte una smart playlist en una playlist regular."""
        # Obtener tracks de la smart playlist
        try:
            smart_info = self.playlist_service.get_playlist_info(smart_playlist_id)
            if smart_info and smart_info.get('type') != 'regular':
                # Obtener tracks que coinciden con las reglas
                rules = smart_info.get('rules', [])
                match_all = smart_info.get('match_all', True)
                track_ids = self.playlist_service.get_tracks(rules, match_all)
                
                if track_ids:
                    # Crear nueva playlist regular
                    frozen_name = f"{smart_info['name']} (Congelada)"
                    new_playlist_id = self.playlist_service.create_playlist(
                        name=frozen_name,
                        description=f"Playlist congelada de smart playlist '{smart_info['name']}'"
                    )
                    
                    if new_playlist_id:
                        # Agregar todos los tracks
                        success = self.playlist_service.add_tracks_to_playlist(new_playlist_id, track_ids)
                        if success:
                            self.refresh_playlists()
                            print(f"✅ Smart playlist congelada como '{frozen_name}' con {len(track_ids)} tracks")
                        else:
                            print(f"❌ Error agregando tracks a la playlist congelada")
                    else:
                        print(f"❌ Error creando playlist congelada")
                else:
                    print(f"⚠️ Smart playlist no tiene tracks para congelar")
        except Exception as e:
            print(f"❌ Error congelando smart playlist: {e}")
    
    def import_playlist(self):
        """Importa una playlist desde archivo."""
        try:
            from PySide6.QtWidgets import QFileDialog, QInputDialog
            
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Importar Playlist", "",
                "Playlists (*.m3u *.pls *.json)"
            )
            
            if not file_path:
                return
            
            import os
            default_name = os.path.splitext(os.path.basename(file_path))[0]
            playlist_name, ok = QInputDialog.getText(
                self, "Nombre de Playlist", "Nombre:", text=default_name
            )
            
            if not ok or not playlist_name.strip():
                return
            
            # Importar playlist (sin loading overlay)
            success, message, playlist_id = self.playlist_importer.import_playlist_file(
                file_path, playlist_name.strip()
            )
            
            if success:
                self.refresh_playlists()
                print(f"✅ Playlist importada: {message}")
            else:
                print(f"❌ Error importando: {message}")
                
        except Exception as e:
            print(f"❌ Error en importación: {e}")
    
    def export_playlist(self, playlist_id):
        """Exporta una playlist a archivo."""
        try:
            # Usar el exportador para manejar la exportación
            success = self.playlist_exporter.export_playlist(playlist_id, parent_widget=self)
            
            if success:
                print(f"✅ Iniciando exportación de playlist {playlist_id}")
            else:
                print(f"❌ Error iniciando exportación de playlist {playlist_id}")
                
        except Exception as e:
            print(f"❌ Error exportando playlist: {e}")
                    
    def get_selected_playlist(self):
        """Retorna la playlist actualmente seleccionada."""
        current_index = self.playlist_tree.currentIndex()
        if current_index.isValid():
            item = self.playlist_model.itemFromIndex(current_index)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None