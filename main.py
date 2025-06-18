import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QSplitter, QDialog, QHBoxLayout, QMenuBar, QMenu, QMessageBox, QStatusBar
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtCore import Qt, Signal, QTimer
from core.database import init_db, create_connection, get_db_path
from core.library_scanner import LibraryScanner
from core.audio_player import AudioPlayer
from core.audio_service import AudioService
from ui.theme import get_complete_style
from ui.track_list import TrackListView
from ui.playback_panel import PlaybackPanel
from ui.metadata_panel import MetadataPanel
from ui.smart_playlist_editor import SmartPlaylistEditor
from services import PlaylistService
from ui.playlist_panel import PlaylistPanel
from ui.api_config_dialog import APIConfigDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DjAlfin - Professional DJ Library")
        self.setGeometry(100, 100, 1600, 900)

        # Inicializar base de datos y componentes del core
        init_db()
        self.db_conn = create_connection() # Mantener una conexión para la UI
        self.audio_service = AudioService(self)
        self.playlist_service = PlaylistService(get_db_path())

        # --- Inicialización de Componentes UI ---
        self.track_list_view = TrackListView(db_connection=self.db_conn)
        self.metadata_panel = MetadataPanel()
        self.playback_panel = PlaybackPanel(self.audio_service)
        self.playlist_panel = PlaylistPanel(service=self.playlist_service)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # --- Conexiones de Señales y Slots ---
        self.connect_signals()
        
        # --- Teclas Rápidas ---
        self.setup_shortcuts()
        
        # --- Layout Principal ---
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.addWidget(self.playlist_panel)
        left_splitter.addWidget(self.track_list_view)
        left_splitter.setSizes([200, 600])

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(self.metadata_panel)
        main_splitter.setSizes([1200, 400])

        right_layout = QVBoxLayout()
        right_layout.addWidget(main_splitter)
        right_layout.addWidget(self.playback_panel)
        right_layout.setStretchFactor(main_splitter, 8)
        right_layout.setStretchFactor(self.playback_panel, 1)
        
        main_layout.addLayout(right_layout)
        self.setCentralWidget(main_widget)
        
        self.setStyleSheet(get_complete_style())
        self.status_bar.showMessage("✅ Aplicación iniciada y lista.", 5000)
        self.track_list_view.load_all_tracks()

    def connect_signals(self):
        """Centraliza todas las conexiones de señales."""
        # Cuando se selecciona una pista, notificar al servicio de audio y al panel de metadatos.
        self.track_list_view.track_selected.connect(self.audio_service.load_track)
        self.track_list_view.track_selected.connect(self.metadata_panel.update_track_info)

        # Cuando el panel de metadatos guarda cambios, refrescar la lista.
        self.metadata_panel.metadataChanged.connect(self.track_list_view.refresh_current_row)

        # Cuando el servicio de audio analiza BPM, guardar los resultados.
        self.playback_panel.bpmAnalyzed.connect(self._on_bpm_analyzed)

        # Mostrar errores del servicio en la barra de estado.
        self.audio_service.errorOccurred.connect(self.status_bar.showMessage)

    def _on_track_selection_changed(self, selected, deselected):
        """Maneja la selección de pistas en la tabla."""
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            # Mapear del proxy model al source model
            source_index = self.track_list_view.proxy_model.mapToSource(indexes[0])
            track_data = self.track_list_view.model.get_track_at(source_index.row())
            if track_data:
                # Actualizar tracking de navegación
                self.current_track_index = source_index.row()
                self.current_playlist_tracks = self.track_list_view.model._data
                
                # Cargar metadatos en el panel derecho
                self.metadata_panel.update_track_info(track_data)
                # Cargar archivo en el reproductor
                self.audio_player.load(track_data.get('file_path', ''))
                # Actualizar info en playback panel
                self.playback_panel.update_track_info(track_data)

    def _on_playlist_selection_changed(self, selection_type, item_id):
        """Se activa cuando se selecciona un elemento en el panel de playlists."""
        print(f"DEBUG: Selección de playlist: Tipo='{selection_type}', ID={item_id}")
        if selection_type == 'library':
            self.track_list_view.load_all_tracks()
        elif selection_type == 'smart_playlist':
            rules, match_all = self.playlist_service.get_playlist_details(item_id)
            if rules is not None:
                track_ids = self.playlist_service.get_tracks(rules, match_all)
                self.track_list_view.load_tracks_by_ids(track_ids)
            else:
                self.track_list_view.load_tracks_by_ids([])

    def _create_menu(self):
        """Crea la barra de menú de la aplicación."""
        menubar = self.menuBar()
        
        # Menú File
        file_menu = menubar.addMenu("&File")
        
        # Acción para Smart Playlists
        smart_playlist_action = QAction("Smart Playlists", self)
        smart_playlist_action.triggered.connect(self.open_smart_playlist_editor)
        file_menu.addAction(smart_playlist_action)
        
        file_menu.addSeparator()
        
        # Acción para configurar APIs
        api_config_action = QAction("🌐 Configurar APIs", self)
        api_config_action.triggered.connect(self.open_api_config)
        file_menu.addAction(api_config_action)
        
        file_menu.addSeparator()
        
        # Acción para salir
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_smart_playlist_editor(self):
        """Abre el diálogo del editor de Smart Playlists."""
        try:
            spl_editor = SmartPlaylistEditor(service=self.playlist_service, parent=self)
            if spl_editor.exec() == QDialog.Accepted:
                print("Editor cerrado con éxito, refrescando playlists...")
                self.playlist_panel.refresh_playlists()
        except Exception as e:
            print(f"Error opening smart playlist editor: {e}")
            # Continue without error to avoid crashing the app

    def _on_seek_requested(self, position_seconds: float):
        """Maneja las solicitudes de búsqueda desde el slider de posición."""
        self.audio_player.seek(position_seconds)

    def _on_audio_position_changed(self, position_seconds: float):
        """Actualiza la posición en el panel sin enviar señal de vuelta."""
        self.playback_panel.set_position_silent(position_seconds)

    def _on_track_finished(self):
        """Maneja la finalización de una pista."""
        # Auto-reproducir siguiente pista si existe
        if self.current_playlist_tracks and self.current_track_index < len(self.current_playlist_tracks) - 1:
            print("🎵 Auto-reproduciendo siguiente pista...")
            self._on_next_track()
            # Pequeña pausa antes de reproducir automáticamente
            QTimer.singleShot(500, self.audio_player.play)
        else:
            print("🎵 Lista de reproducción terminada")

    def _on_previous_track(self):
        """Navega a la pista anterior."""
        if not self.current_playlist_tracks or self.current_track_index <= 0:
            print("🔚 No hay pista anterior")
            return
            
        self.current_track_index -= 1
        self._load_track_by_index(self.current_track_index)
        print(f"⏮️ Pista anterior: {self.current_track_index + 1}/{len(self.current_playlist_tracks)}")

    def _on_next_track(self):
        """Navega a la pista siguiente."""
        if not self.current_playlist_tracks or self.current_track_index >= len(self.current_playlist_tracks) - 1:
            print("🔚 No hay pista siguiente")
            return
            
        self.current_track_index += 1
        self._load_track_by_index(self.current_track_index)
        print(f"⏭️ Pista siguiente: {self.current_track_index + 1}/{len(self.current_playlist_tracks)}")

    def _load_track_by_index(self, index: int):
        """Carga una pista por su índice en la lista actual."""
        if 0 <= index < len(self.current_playlist_tracks):
            track_data = self.current_playlist_tracks[index]
            
            # Actualizar selección en la vista
            model_index = self.track_list_view.model.index(index, 0)
            proxy_index = self.track_list_view.proxy_model.mapFromSource(model_index)
            self.track_list_view.table_view.selectRow(proxy_index.row())
            
            # Cargar en reproductor y paneles
            self.metadata_panel.update_track_info(track_data)
            self.audio_player.load(track_data.get('file_path', ''))
            self.playback_panel.update_track_info(track_data)

    def closeEvent(self, event):
        """Se ejecuta al cerrar la aplicación."""
        print("🛑 Cerrando aplicación DjAlfin...")
        try:
            self.audio_player.stop()
        except:
            pass
        self.db_conn.close()
        event.accept()

    def setup_shortcuts(self):
        """Configura las teclas rápidas para control con teclado."""
        # Spacebar: Play/Pause
        self.play_pause_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.play_pause_shortcut.activated.connect(self._toggle_play_pause)
        
        # Flechas para navegación
        self.prev_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.prev_shortcut.activated.connect(self._on_previous_track)
        
        self.next_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.next_shortcut.activated.connect(self._on_next_track)
        
        # Flechas arriba/abajo para volumen
        self.volume_up_shortcut = QShortcut(QKeySequence(Qt.Key_Up), self)
        self.volume_up_shortcut.activated.connect(self._volume_up)
        
        self.volume_down_shortcut = QShortcut(QKeySequence(Qt.Key_Down), self)
        self.volume_down_shortcut.activated.connect(self._volume_down)

    def _toggle_play_pause(self):
        """Alterna entre play y pause."""
        if self.playback_panel.is_playing:
            self.audio_player.pause()
        else:
            self.audio_player.play()

    def _volume_up(self):
        """Aumenta el volumen en 5%."""
        current_volume = self.playback_panel.volume_slider.value()
        new_volume = min(100, current_volume + 5)
        self.playback_panel.volume_slider.setValue(new_volume)

    def _volume_down(self):
        """Disminuye el volumen en 5%."""
        current_volume = self.playback_panel.volume_slider.value()
        new_volume = max(0, current_volume - 5)
        self.playback_panel.volume_slider.setValue(new_volume)

    def open_api_config(self):
        """Abre el dialog de configuración de APIs."""
        try:
            dialog = APIConfigDialog(self)
            dialog.exec()
        except Exception as e:
            print(f"Error opening API config dialog: {e}")

    def _on_volume_changed(self, volume: int):
        """Maneja cambios en el volumen."""
        self.audio_player.set_volume(volume / 100.0)
        print(f"🎚️ Volumen establecido a {volume}%")
        # Sincronizar con el slider si es necesario
        if self.playback_panel.volume_slider.value() != volume:
            self.playback_panel.volume_slider.setValue(volume)

    def _on_bpm_analyzed(self, result: dict):
        """Maneja resultados de análisis BPM."""
        if self.current_track_info and result.get('bpm'):
            file_path = self.current_track_info.get('file_path')
            if file_path:
                # Actualizar la base de datos con los datos BPM
                try:
                    from core.database import update_track_field
                    
                    # Guardar BPM principal
                    update_track_field(file_path, 'bpm', result['bpm'])
                    
                    # Guardar datos adicionales si existen
                    if result.get('confidence'):
                        update_track_field(file_path, 'bpm_confidence', result['confidence'])
                    
                    if result.get('beat_track', {}).get('beat_count'):
                        update_track_field(file_path, 'beat_count', result['beat_track']['beat_count'])
                    
                    if result.get('beat_track', {}).get('stability'):
                        update_track_field(file_path, 'rhythm_stability', result['beat_track']['stability'])
                    
                    # Marca de tiempo del análisis
                    import datetime
                    analysis_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    update_track_field(file_path, 'bpm_analyzed_date', analysis_date)
                    
                    print(f"🎵 BPM guardado: {result['bpm']:.1f} (Confidence: {result['confidence']:.1%})")
                    
                    # Actualizar la vista de tracks si está visible
                    self.track_list.refresh_view()
                    
                except Exception as e:
                    print(f"❌ Error guardando BPM en DB: {e}")
        else:
            print("⚠️ No se puede guardar BPM: falta información del track o BPM")

    def _on_pitch_changed(self, pitch_percent: float):
        """Maneja cambios en el pitch/tempo."""
        # Aquí implementaremos control de pitch cuando tengamos el reproductor
        # Por ahora solo logeamos el cambio
        print(f"🎛️ Pitch ajustado: {pitch_percent:+.1f}%")
        
        # TODO: Implementar pitch shifting real en el audio player
        # Esto requeriría modificar PyDub o usar una librería como 
        # librosa con phase vocoder para time stretching
        if hasattr(self.audio_player, 'set_pitch'):
            self.audio_player.set_pitch(pitch_percent / 100.0)
        else:
            # Placeholder: simular cambio de velocidad (no es pitch real)
            # speed_factor = 1.0 + (pitch_percent / 100.0)
            pass
    
    def _on_metadata_changed(self, metadata: dict):
        """Maneja cambios en los metadatos desde el MetadataPanel."""
        try:
            file_path = metadata.get('file_path')
            if not file_path:
                print("❌ No se puede guardar metadatos: falta file_path")
                return
            
            # Actualizar en la base de datos
            from core.database import update_track_metadata
            
            # Preparar datos para actualizar
            update_data = {
                'title': metadata.get('title', ''),
                'artist': metadata.get('artist', ''),
                'album': metadata.get('album', ''),
                'genre': metadata.get('genre', ''),
                'year': metadata.get('year', ''),
                'comment': metadata.get('comment', '')
            }
            
            # Filtrar campos vacíos
            update_data = {k: v for k, v in update_data.items() if v}
            
            if update_data:
                success = update_track_metadata(file_path, update_data)
                if success:
                    print(f"✅ Metadatos actualizados para: {metadata.get('title', file_path)}")
                    # Refrescar la vista de tracks
                    self.track_list_view.load_all_tracks()
                else:
                    print(f"❌ Error actualizando metadatos para: {file_path}")
            else:
                print("⚠️ No hay cambios de metadatos para guardar")
                
        except Exception as e:
            print(f"❌ Error procesando cambios de metadatos: {e}")
            import traceback
            traceback.print_exc()

def main():
    app = QApplication(sys.argv)
    
    print("🚀 Iniciando aplicación DjAlfin...")
    init_db()
    
    window = MainWindow()
    window.show()
    print("✅ MainWindow mostrada")
    
    print("🔄 Iniciando bucle de eventos...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
