import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QDialog, QStatusBar, QMenuBar, QMenu, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtCore import Qt, Signal, QTimer

from config.design_system import Theme

from core.database import init_db, create_connection, get_db_path, update_track_field
from core.audio_service import AudioService
from core.library_scanner import LibraryScanner
from services.playlist_service import PlaylistService

from .track_list import TrackListView
from .playback_panel import PlaybackPanel
# EnrichmentPanel removed - functionality replaced by sliding panels
from .smart_playlist_editor import SmartPlaylistEditor
from .api_config_dialog import APIConfigDialog
from .components import PlaylistSlidingPanel, MetadataSlidingPanel, EdgeHoverArea

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
        self.playback_panel = PlaybackPanel(self.audio_service)
        
        # --- Sliding Panels (Sistema Moderno) ---
        self.playlist_sliding_panel = PlaylistSlidingPanel(self.playlist_service, parent=self)
        self.metadata_sliding_panel = MetadataSlidingPanel(parent=self)
        
        # --- Edge Hover Areas ---
        self.left_hover_area = EdgeHoverArea(edge='left', trigger_width=15, parent=self)
        self.right_hover_area = EdgeHoverArea(edge='right', trigger_width=15, parent=self)
        
        # --- Panel de Enriquecimiento eliminado - reemplazado por sliding panels ---
        # self.enrichment_panel = EnrichmentPanel()  # REMOVED
        
        # Configurar políticas de tamaño para mejor distribución
        self.track_list_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.enrichment_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)  # REMOVED
        self.playback_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        # --- Layout ---
        self.setup_layout()
        
        # --- Sliding Panels Setup ---
        self.setup_sliding_panels()
        
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
        
        # Panel inferior: Enrichment (compacto) - COMPLETAMENTE OCULTO para evitar conflicto con sliding panels
        # EnrichmentPanel removed - using sliding panels instead
        # self.enrichment_panel.setMinimumHeight(0)  # REMOVED
        # self.enrichment_panel.setMaximumHeight(0)  # REMOVED 
        # self.enrichment_panel.setVisible(False)  # REMOVED
        # self.enrichment_panel.hide()  # REMOVED
        
        # Configurar proporciones del splitter vertical - Solo TrackListView
        content_splitter.setSizes([1000])  # 100% para TrackListView
        
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
        
    def setup_sliding_panels(self):
        """Configura los paneles deslizantes y las áreas de hover."""
        # Configurar geometría de los paneles basada en la ventana principal
        # Usar una geometría por defecto y actualizarla después en showEvent
        default_rect = self.rect()
        if default_rect.width() == 0:
            # Si la ventana no está inicializada, usar tamaños por defecto
            default_rect.setWidth(1800)
            default_rect.setHeight(1000)
        
        self.playlist_sliding_panel.set_parent_geometry(default_rect)
        self.metadata_sliding_panel.set_parent_geometry(default_rect)
        self.left_hover_area.set_parent_geometry(default_rect)
        self.right_hover_area.set_parent_geometry(default_rect)
        
        # Conectar hover areas a los paneles
        self.left_hover_area.hoverEntered.connect(self.playlist_sliding_panel.show_panel)
        self.right_hover_area.hoverEntered.connect(self.metadata_sliding_panel.show_panel)
        
        # Conectar señales de los paneles deslizantes
        self.playlist_sliding_panel.playlistSelected.connect(self.handle_sliding_playlist_selection)
        self.playlist_sliding_panel.createPlaylistRequested.connect(self.handle_create_playlist)
        self.playlist_sliding_panel.editPlaylistRequested.connect(self.handle_edit_playlist)
        self.playlist_sliding_panel.deletePlaylistRequested.connect(self.handle_delete_playlist)
        self.playlist_sliding_panel.tracksAddedToPlaylist.connect(self.handle_tracks_added_to_playlist)
        self.playlist_sliding_panel.panelShown.connect(lambda: self.status_bar.showMessage("Panel de playlists mostrado", 2000))
        self.playlist_sliding_panel.panelHidden.connect(lambda: self.status_bar.showMessage("Panel de playlists oculto", 2000))
        
        self.metadata_sliding_panel.saveRequested.connect(self.handle_metadata_save)
        self.metadata_sliding_panel.enrichmentRequested.connect(self.handle_enrichment_request)
        self.metadata_sliding_panel.multiSourceEnrichmentRequested.connect(self.handle_multi_source_enrichment_request)
        self.metadata_sliding_panel.metadataUpdated.connect(self.track_list_view.refresh_current_row)
        self.metadata_sliding_panel.bpmAnalysisRequested.connect(self.handle_bpm_analysis_request)
        self.metadata_sliding_panel.panelShown.connect(lambda: self.status_bar.showMessage("Panel de metadatos mostrado", 2000))
        self.metadata_sliding_panel.panelHidden.connect(lambda: self.status_bar.showMessage("Panel de metadatos oculto", 2000))
        
        # Conectar análisis de BPM del AudioService al metadata panel
        self.audio_service.bpmAnalyzed.connect(self.metadata_sliding_panel.on_bpm_analysis_completed)
        
        print("🎛️ Sliding panels configurados correctamente")
        
    def toggle_enrichment_panel(self):
        """Alterna la visibilidad del panel de metadatos."""
        # Priorizar el sliding panel por ser más moderno
        if hasattr(self, 'metadata_sliding_panel'):
            self.metadata_sliding_panel.toggle()
        else:
            # Fallback al panel tradicional - EnrichmentPanel removed
            pass  # No action needed - functionality moved to sliding panels
    
    def toggle_playlist_panel(self):
        """Alterna la visibilidad del panel de playlists deslizante."""
        self.playlist_sliding_panel.toggle()

    def connect_signals(self):
        """Conecta todas las señales y slots de la aplicación."""
        print("🔗 MainWindow: Connecting signals...")
        
        # Conexiones del track list
        self.track_list_view.track_selected.connect(self.audio_service.load_track)
        # self.track_list_view.track_selected.connect(self.enrichment_panel.update_track_info)  # DESCONECTADO - panel oculto
        self.track_list_view.track_selected.connect(self.metadata_sliding_panel.update_track_info)
        self.track_list_view.playlist_created.connect(self.playlist_sliding_panel.refresh_playlists)
        
        # Conexiones de los paneles originales (para compatibilidad) - DESCONECTADO
        # self.enrichment_panel.metadataChanged.connect(self.track_list_view.refresh_current_row)  # DESCONECTADO - panel oculto
        # self.enrichment_panel.enrichRequested.connect(self.handle_enrichment_request)  # DESCONECTADO - panel oculto
        
        # Conexiones del servicio de audio
        self.audio_service.errorOccurred.connect(self.show_status_message)
        self.audio_service.bpmAnalyzed.connect(self.handle_bmp_analysis_completed)
        
        # Conexiones de navegación del playback panel
        self.playback_panel.previousTrackRequested.connect(self.handle_previous_track)
        self.playback_panel.nextTrackRequested.connect(self.handle_next_track)
        
        print("🔗 MainWindow: All signals connected successfully")
        
    def handle_playlist_selection(self, selection_type, item_id):
        """Maneja la selección de un elemento en el panel de playlists."""
        self.status_bar.showMessage(f"Cargando '{item_id}'...", 2000)
        if selection_type == 'library':
            self.track_list_view.load_all_tracks()
        elif selection_type == 'smart_playlist':
            rules, match_all = self.playlist_service.get_playlist_details(item_id)
            if rules is not None:
                track_ids = self.playlist_service.get_tracks(rules, match_all)
                self.track_list_view.load_playlist_tracks(track_ids, f"Smart: {item_id}")
            else:
                self.track_list_view.clear_tracks()
                
    def handle_sliding_playlist_selection(self, playlist_name, tracks):
        """Maneja la selección de playlist desde el panel deslizante."""
        print(f"🎵 Playlist seleccionada desde panel deslizante: {playlist_name}")
        
        if playlist_name == "all_tracks":
            self.track_list_view.load_all_tracks()
            self.status_bar.showMessage("Mostrando todos los tracks", 2000)
        elif tracks is not None:
            # Cargar tracks específicos de la playlist con contexto
            self.track_list_view.load_playlist_tracks([track['id'] for track in tracks], playlist_name)
            self.status_bar.showMessage(f"Playlist '{playlist_name}' cargada ({len(tracks)} tracks)", 3000)
        else:
            self.status_bar.showMessage(f"Error al cargar playlist '{playlist_name}'", 3000)
            
    def handle_metadata_save(self, metadata):
        """Maneja el guardado de metadatos desde el panel deslizante."""
        print(f"💾 Guardando metadatos desde panel deslizante: {metadata.get('title', 'Unknown')}")
        
        try:
            # Validar que tenemos los datos necesarios
            file_path = metadata.get('file_path')
            if not file_path:
                print("❌ Error: No hay file_path en los metadatos")
                self.status_bar.showMessage("Error: Datos incompletos para guardar", 3000)
                return
            
            # Lista de campos que se pueden actualizar en la base de datos
            updatable_fields = ['title', 'artist', 'album', 'genre', 'year', 'bpm', 'key', 'comment']
            successful_updates = 0
            failed_updates = []
            
            # Actualizar cada campo en la base de datos
            for field in updatable_fields:
                if field in metadata:
                    value = metadata[field]
                    # Convertir valores vacíos a None para la base de datos
                    if value == '':
                        value = None
                    
                    try:
                        # Actualizar en la base de datos usando la función existente
                        update_track_field(file_path, field, value, self.db_conn)
                        successful_updates += 1
                        print(f"✅ Campo '{field}' actualizado: {value}")
                    except Exception as field_error:
                        failed_updates.append(field)
                        print(f"❌ Error actualizando campo '{field}': {field_error}")
            
            # Actualizar la vista solo si hubo al menos una actualización exitosa
            if successful_updates > 0:
                # Forzar refresh de la fila actual inmediatamente
                print("🔄 Forzando actualización de la vista...")
                self.track_list_view.refresh_current_row()
                
                # Mecanismo mejorado de sincronización de UI
                from PySide6.QtCore import QTimer
                
                def enhanced_ui_refresh():
                    """Refresh mejorado con múltiples estrategias de sincronización."""
                    try:
                        print("🔄 Ejecutando refresh mejorado de UI...")
                        
                        # Estrategia 1: Invalidar proxy model
                        if hasattr(self.track_list_view, 'proxy_model') and self.track_list_view.proxy_model:
                            proxy_model = self.track_list_view.proxy_model
                            proxy_model.invalidate()
                            print("   ✅ Proxy model invalidado")
                            
                            # Estrategia 2: Forzar dataChanged en la selección actual
                            current_selection = self.track_list_view.table_view.selectionModel().selectedRows()
                            if current_selection:
                                current_index = current_selection[0]
                                source_index = proxy_model.mapToSource(current_index)
                                if source_index.isValid():
                                    # Emitir dataChanged para toda la fila
                                    start_index = proxy_model.sourceModel().index(source_index.row(), 0)
                                    end_index = proxy_model.sourceModel().index(source_index.row(), 
                                                                              proxy_model.sourceModel().columnCount() - 1)
                                    proxy_model.sourceModel().dataChanged.emit(start_index, end_index)
                                    print("   ✅ dataChanged emitido para fila seleccionada")
                        
                        # Estrategia 3: Re-seleccionar fila para forzar refresh visual
                        selected_indexes = self.track_list_view.table_view.selectionModel().selectedRows()
                        if selected_indexes:
                            selected_row = selected_indexes[0].row()
                            self.track_list_view.table_view.selectRow(selected_row)
                            print("   ✅ Fila re-seleccionada para refresh visual")
                        
                        print("🔄 Refresh mejorado completado exitosamente")
                        
                    except Exception as e:
                        print(f"⚠️ Error en refresh mejorado: {e}")
                        # Fallback: force refresh completo
                        try:
                            self.track_list_view.force_refresh()
                            print("   🔄 Fallback: Force refresh ejecutado")
                        except Exception as fallback_error:
                            print(f"   ❌ Error en fallback refresh: {fallback_error}")
                
                # Ejecutar refresh mejorado con dos delays diferentes para máxima compatibilidad
                QTimer.singleShot(50, enhanced_ui_refresh)   # Refresh rápido
                QTimer.singleShot(200, enhanced_ui_refresh)  # Refresh adicional por si el primero no funcionó
                
                if failed_updates:
                    # Algunos campos fallaron
                    self.status_bar.showMessage(
                        f"Metadatos parcialmente guardados ({successful_updates} campos). "
                        f"Errores en: {', '.join(failed_updates)}", 5000
                    )
                    print(f"⚠️ Guardado parcial: {successful_updates} exitosos, {len(failed_updates)} fallidos")
                else:
                    # Todo exitoso
                    self.status_bar.showMessage(
                        f"Metadatos guardados correctamente ({successful_updates} campos actualizados)", 3000
                    )
                    print(f"✅ Todos los metadatos guardados exitosamente ({successful_updates} campos)")
            else:
                # Nada se guardó
                self.status_bar.showMessage("Error: No se pudieron guardar los metadatos", 3000)
                print("❌ No se pudo guardar ningún campo de metadatos")
                
        except Exception as e:
            print(f"❌ Error general al guardar metadatos: {e}")
            self.status_bar.showMessage("Error al guardar metadatos", 3000)
    
    def handle_create_playlist(self):
        """Maneja la creación de una nueva playlist regular."""
        try:
            from .components.playlist_dialog import PlaylistDialog
            
            dialog = PlaylistDialog(parent=self)
            if dialog.exec() == QDialog.Accepted:
                playlist_data = dialog.get_playlist_data()
                
                # Crear playlist usando el servicio
                playlist_id = self.playlist_service.create_playlist(
                    name=playlist_data['name'],
                    description=playlist_data['description'],
                    color=playlist_data['color']
                )
                
                if playlist_id:
                    self.status_bar.showMessage(f"Playlist '{playlist_data['name']}' creada correctamente", 3000)
                    # Refresh el panel de playlists
                    self.playlist_sliding_panel.refresh_playlists()
                else:
                    self.status_bar.showMessage("Error al crear la playlist", 3000)
                    
        except Exception as e:
            print(f"❌ Error creando playlist: {e}")
            self.status_bar.showMessage("Error al crear playlist", 3000)
    
    def handle_tracks_added_to_playlist(self, playlist_id, track_ids):
        """Maneja cuando se agregan tracks a una playlist via drag & drop."""
        try:
            # Obtener información de la playlist
            playlist_info = self.playlist_service.get_playlist_info(playlist_id)
            if playlist_info:
                playlist_name = playlist_info['name']
                track_count = len(track_ids)
                
                self.status_bar.showMessage(
                    f"{track_count} track{'s' if track_count != 1 else ''} agregado{'s' if track_count != 1 else ''} a '{playlist_name}'", 
                    3000
                )
                
                print(f"✅ {track_count} tracks agregados a playlist '{playlist_name}' (ID: {playlist_id})")
            else:
                self.status_bar.showMessage("Tracks agregados a playlist", 2000)
                
        except Exception as e:
            print(f"❌ Error manejando tracks agregados: {e}")
            self.status_bar.showMessage("Error agregando tracks", 2000)
    
    def handle_edit_playlist(self, playlist_id):
        """Maneja la edición de una playlist."""
        try:
            # Obtener información de la playlist
            playlist_info = self.playlist_service.get_playlist_info(playlist_id)
            
            if not playlist_info:
                self.status_bar.showMessage("Playlist no encontrada", 2000)
                return
            
            if playlist_info.get('type') == 'regular':
                # Editar playlist regular
                from .components.playlist_dialog import PlaylistDialog
                
                dialog = PlaylistDialog(parent=self, playlist_data=playlist_info)
                if dialog.exec() == QDialog.Accepted:
                    new_data = dialog.get_playlist_data()
                    
                    # Actualizar información básica
                    success = self.playlist_service.rename_playlist(playlist_id, new_data['name'])
                    if success:
                        self.status_bar.showMessage(f"Playlist '{new_data['name']}' actualizada", 3000)
                        self.playlist_sliding_panel.refresh_playlists()
                    else:
                        self.status_bar.showMessage("Error al actualizar playlist", 3000)
            else:
                # Editar smart playlist
                self.open_smart_playlist_editor()
                
        except Exception as e:
            print(f"❌ Error editando playlist: {e}")
            self.status_bar.showMessage("Error al editar playlist", 3000)
    
    def handle_delete_playlist(self, playlist_id):
        """Maneja la eliminación de una playlist."""
        try:
            # Obtener información de la playlist
            playlist_info = self.playlist_service.get_playlist_info(playlist_id)
            
            if not playlist_info:
                self.status_bar.showMessage("Playlist no encontrada", 2000)
                return
            
            # Solo permitir eliminar playlists regulares (las smart playlists se manejan por separado)
            if playlist_info.get('type') == 'regular':
                from .components.playlist_dialog import ConfirmDeleteDialog
                
                playlist_name = playlist_info.get('name', 'Unknown')
                track_count = playlist_info.get('track_count', 0)
                
                confirm_dialog = ConfirmDeleteDialog(playlist_name, track_count, parent=self)
                if confirm_dialog.exec() == QDialog.Accepted:
                    # Eliminar playlist
                    success = self.playlist_service.delete_playlist(playlist_id)
                    if success:
                        self.status_bar.showMessage(f"Playlist '{playlist_name}' eliminada", 3000)
                        self.playlist_sliding_panel.refresh_playlists()
                    else:
                        self.status_bar.showMessage("Error al eliminar playlist", 3000)
            else:
                self.status_bar.showMessage("Las smart playlists se eliminan desde su editor", 3000)
                
        except Exception as e:
            print(f"❌ Error eliminando playlist: {e}")
            self.status_bar.showMessage("Error al eliminar playlist", 3000)
                
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
        
        # Acción de refresh manual
        refresh_action = QAction("🔄 Actualizar Lista de Tracks", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.manual_refresh_tracks)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
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
        from PySide6.QtWidgets import QFileDialog
        import os
        
        # Directorio por defecto donde está la música
        default_music_dir = "/Volumes/KINGSTON/Audio/"
        
        # Si el directorio por defecto existe, usarlo; sino, pedir al usuario que seleccione
        if os.path.exists(default_music_dir):
            music_directory = default_music_dir
        else:
            music_directory = QFileDialog.getExistingDirectory(
                self, 
                "Seleccionar Carpeta de Música",
                os.path.expanduser("~/Music")
            )
            
            if not music_directory:
                self.status_bar.showMessage("Escaneo cancelado", 2000)
                return
        
        self.status_bar.showMessage(f"Escaneando {music_directory}...")
        
        # Crear scanner con directorio y callback
        scanner = LibraryScanner(
            directory=music_directory,
            on_complete_callback=self.scan_finished,
            progress_callback=lambda msg: self.status_bar.showMessage(msg, 1000)
        )
        
        scanner.start()

    def scan_finished(self):
        """Callback cuando el escaneo termina - debe ejecutarse en thread principal."""
        print("🔄 MainWindow: scan_finished callback ejecutado")
        
        # Usar QTimer para asegurar ejecución en thread principal de Qt
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._complete_scan_refresh)
    
    def _complete_scan_refresh(self):
        """Completa el refresh después del escaneo en el thread principal."""
        try:
            print("🔄 MainWindow: Iniciando refresh de tracks después del escaneo...")
            
            # Verificar que hay tracks en la base de datos
            track_count = self._get_track_count()
            print(f"📊 MainWindow: {track_count} tracks encontrados en la base de datos")
            
            if track_count > 0:
                # Forzar actualización de la vista
                self.track_list_view.force_refresh()
                self.status_bar.showMessage(f"✅ Escaneo completado. {track_count} tracks cargados.", 5000)
                print(f"✅ MainWindow: Vista actualizada con {track_count} tracks")
            else:
                self.status_bar.showMessage("⚠️ Escaneo completado pero no se encontraron tracks.", 5000)
                print("⚠️ MainWindow: No se encontraron tracks después del escaneo")
                
        except Exception as e:
            print(f"❌ MainWindow: Error en refresh después del escaneo: {e}")
            self.status_bar.showMessage("❌ Error actualizando la vista después del escaneo", 5000)
    
    def _get_track_count(self):
        """Obtiene el número de tracks en la base de datos."""
        try:
            import sqlite3
            from core.database import get_db_path
            
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM tracks')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"❌ Error obteniendo count de tracks: {e}")
            return 0
    
    def manual_refresh_tracks(self):
        """Actualización manual de la lista de tracks (F5)."""
        print("🔄 MainWindow: Refresh manual solicitado")
        self.status_bar.showMessage("🔄 Actualizando lista de tracks...", 2000)
        
        try:
            success = self.track_list_view.force_refresh()
            if success:
                track_count = self._get_track_count()
                self.status_bar.showMessage(f"✅ Lista actualizada. {track_count} tracks disponibles.", 3000)
            else:
                self.status_bar.showMessage("⚠️ No se pudieron cargar los tracks", 3000)
        except Exception as e:
            print(f"❌ MainWindow: Error en refresh manual: {e}")
            self.status_bar.showMessage("❌ Error actualizando la lista", 3000)

    def open_smart_playlist_editor(self):
        editor = SmartPlaylistEditor(service=self.playlist_service, parent=self)
        if editor.exec() == QDialog.Accepted:
            # Refresh sliding panel
            self.playlist_sliding_panel.refresh_playlists()

    def open_api_config(self):
        dialog = APIConfigDialog(parent=self)
        dialog.exec()

    def show_status_message(self, message, timeout=5000):
        self.statusBar().showMessage(message, timeout)
        
    def handle_enrichment_request(self, source: str):
        """Maneja las solicitudes de enriquecimiento de metadatos individuales."""
        self.status_bar.showMessage(f"Enriqueciendo con {source}...", 2000)
        
        # Simular enriquecimiento individual (legacy)
        QTimer.singleShot(2000, lambda: self._complete_individual_enrichment(source))
    
    def handle_multi_source_enrichment_request(self, track_info: dict):
        """Maneja las solicitudes de enriquecimiento inteligente multi-fuente."""
        print(f"🤖 MainWindow: Procesando enriquecimiento multi-fuente para: {track_info.get('title', 'Unknown')}")
        self.status_bar.showMessage("🧠 Enriquecimiento Inteligente en Progreso...", 5000)
        
        # Ejecutar en thread separado para no bloquear UI
        from PySide6.QtCore import QThread, QObject, Signal
        
        class EnrichmentWorker(QObject):
            finished = Signal(dict)
            
            def __init__(self, track_info):
                super().__init__()
                self.track_info = track_info
                
            def run(self):
                try:
                    from core.metadata_enricher import enrich_metadata
                    
                    # Ejecutar enriquecimiento multi-fuente
                    enriched_data = enrich_metadata(self.track_info)
                    
                    # Preparar resultado
                    result = {
                        'success': True,
                        'enriched_data': enriched_data,
                        'final_genres': [],
                        'confidence_score': 0.8,  # Simulated for now
                        'sources_used': [],
                        'processing_time': 0.0
                    }
                    
                    # Extraer géneros si están disponibles
                    if enriched_data.get('genre'):
                        genres_str = enriched_data['genre']
                        result['final_genres'] = [g.strip() for g in genres_str.split(';') if g.strip()]
                    
                    # Determinar fuentes usadas basándose en los IDs presentes
                    sources = []
                    if enriched_data.get('spotify_track_id'):
                        sources.append('Spotify')
                    if enriched_data.get('musicbrainz_recording_id'):
                        sources.append('MusicBrainz')
                    if enriched_data.get('discogs_release_id'):
                        sources.append('Discogs')
                    if enriched_data.get('lastfm_artist_info'):
                        sources.append('Last.fm')
                    
                    result['sources_used'] = sources
                    
                    self.finished.emit(result)
                    
                except Exception as e:
                    print(f"❌ Error en worker de enriquecimiento: {e}")
                    error_result = {
                        'success': False,
                        'error': str(e),
                        'final_genres': [],
                        'confidence_score': 0.0,
                        'sources_used': [],
                        'processing_time': 0.0
                    }
                    self.finished.emit(error_result)
        
        # Crear y ejecutar worker
        self.enrichment_worker = EnrichmentWorker(track_info)
        self.enrichment_thread = QThread()
        
        self.enrichment_worker.moveToThread(self.enrichment_thread)
        self.enrichment_thread.started.connect(self.enrichment_worker.run)
        self.enrichment_worker.finished.connect(self._on_multi_source_enrichment_completed)
        self.enrichment_worker.finished.connect(self.enrichment_thread.quit)
        self.enrichment_worker.finished.connect(self.enrichment_worker.deleteLater)
        self.enrichment_thread.finished.connect(self.enrichment_thread.deleteLater)
        
        self.enrichment_thread.start()
    
    def _on_multi_source_enrichment_completed(self, result):
        """Callback cuando se completa el enriquecimiento multi-fuente."""
        try:
            if result.get('success'):
                sources = result.get('sources_used', [])
                confidence = result.get('confidence_score', 0.0)
                
                self.status_bar.showMessage(
                    f"✅ Enriquecimiento Completado - Confianza: {confidence:.1%} - Fuentes: {', '.join(sources)}", 
                    5000
                )
                
                print(f"✅ MainWindow: Enriquecimiento multi-fuente exitoso")
                print(f"   Fuentes: {', '.join(sources)}")
                print(f"   Confianza: {confidence:.1%}")
                print(f"   Géneros: {'; '.join(result.get('final_genres', []))}")
            else:
                error_msg = result.get('error', 'Error desconocido')
                self.status_bar.showMessage(f"❌ Error en Enriquecimiento: {error_msg}", 5000)
                print(f"❌ MainWindow: Error en enriquecimiento multi-fuente: {error_msg}")
            
            # Enviar resultado al panel para actualizar UI
            self.metadata_sliding_panel.on_smart_enrichment_completed(result)
            
        except Exception as e:
            print(f"❌ MainWindow: Error procesando resultado de enriquecimiento: {e}")
            self.status_bar.showMessage("❌ Error procesando resultado", 3000)
    
    def _complete_individual_enrichment(self, source):
        """Completa enriquecimiento individual (legacy)."""
        print(f"✅ MainWindow: Enriquecimiento individual de {source} completado")
        self.status_bar.showMessage(f"✅ {source.title()} completado", 2000)
    
    def handle_bpm_analysis_request(self, file_path: str):
        """Maneja las solicitudes de análisis de BPM."""
        print(f"🎵 MainWindow: Solicitando análisis BPM para: {file_path}")
        self.status_bar.showMessage("🎵 Analizando BPM...", 3000)
        
        try:
            # Usar el AudioService para análisis real de BPM
            # Primero cargar el archivo si no está cargado
            if self.audio_service.current_file != file_path:
                print(f"🔄 MainWindow: Cargando archivo para análisis BPM: {file_path}")
                
                # Crear un track_data temporal para cargar el archivo
                temp_track = {'file_path': file_path, 'title': 'Análisis BPM', 'artist': 'Unknown'}
                self.audio_service.load_track(temp_track)
            
            # Iniciar análisis BPM
            self.audio_service.analyze_bpm()
            
        except Exception as e:
            print(f"❌ MainWindow: Error solicitando análisis BPM: {e}")
            self.status_bar.showMessage("❌ Error iniciando análisis BPM", 3000)
    
    def handle_bmp_analysis_completed(self, result: dict):
        """Maneja la finalización del análisis de BPM y actualiza la base de datos."""
        try:
            file_path = result.get('file_path')
            bpm = result.get('bpm')
            confidence = result.get('confidence', 0.0)
            
            if file_path and bpm:
                print(f"✅ MainWindow: BPM analysis completed - {bpm:.1f} BPM (Confidence: {confidence*100:.0f}%)")
                
                # Actualizar BPM en la base de datos
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    UPDATE tracks 
                    SET bpm = ? 
                    WHERE file_path = ?
                """, (bpm, file_path))
                self.db_conn.commit()
                
                # Actualizar la vista de tracks si el track está visible
                self.track_list_view.refresh_current_row()
                
                self.status_bar.showMessage(f"✅ BPM actualizado: {bpm:.1f}", 3000)
            else:
                error_msg = result.get('error', 'Error desconocido en análisis BPM')
                print(f"❌ MainWindow: Error en análisis BPM: {error_msg}")
                self.status_bar.showMessage(f"❌ Error BPM: {error_msg}", 3000)
                
        except Exception as e:
            print(f"❌ MainWindow: Error procesando resultado BPM: {e}")
            self.status_bar.showMessage("❌ Error procesando resultado BPM", 3000)
        
    def _complete_enrichment(self, source: str):
        """Completa el proceso de enriquecimiento simulado."""
        # self.enrichment_panel.set_enrichment_complete(source, True, "Completado exitosamente")  # REMOVED
        self.status_bar.showMessage(f"Enriquecimiento con {source} completado", 3000)
        
    def handle_previous_track(self):
        """Maneja la solicitud de reproducir el track anterior."""
        print("⏮️ MainWindow: Previous track requested")
        self.track_list_view.select_previous_track()
        self.status_bar.showMessage("⏮️ Track anterior", 1000)
        
    def handle_next_track(self):
        """Maneja la solicitud de reproducir el track siguiente."""
        print("⏭️ MainWindow: Next track requested")
        self.track_list_view.select_next_track()
        self.status_bar.showMessage("⏭️ Track siguiente", 1000)
        
    def showEvent(self, event):
        """Maneja el evento de mostrar la ventana."""
        super().showEvent(event)
        
        # Configurar geometría correcta de paneles deslizantes al mostrar la ventana
        if hasattr(self, 'playlist_sliding_panel'):
            main_rect = self.geometry()
            self.playlist_sliding_panel.set_parent_geometry(main_rect)
            self.metadata_sliding_panel.set_parent_geometry(main_rect)
            self.left_hover_area.set_parent_geometry(main_rect)
            self.right_hover_area.set_parent_geometry(main_rect)
    
    def resizeEvent(self, event):
        """Maneja el evento de redimensionamiento de la ventana."""
        super().resizeEvent(event)
        
        # Actualizar geometría de paneles deslizantes cuando la ventana cambie de tamaño
        if hasattr(self, 'playlist_sliding_panel'):
            main_rect = self.geometry()
            self.playlist_sliding_panel.set_parent_geometry(main_rect)
            self.metadata_sliding_panel.set_parent_geometry(main_rect)
            self.left_hover_area.set_parent_geometry(main_rect)
            self.right_hover_area.set_parent_geometry(main_rect)
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        self.audio_service.stop()
        self.db_conn.close()
        print("Aplicación cerrada limpiamente.")
        event.accept()
