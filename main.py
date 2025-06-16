import sys
import time
import os # Necesario para os.path.getmtime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QDockWidget
)
from PySide6.QtCore import Qt, QItemSelectionModel, QObject, Signal, QRunnable, Slot, QThreadPool

from ui.track_list import TrackListView, TrackListModel
from core.library_scanner import LibraryScanner
from core import database as db # Usar alias db
from ui.metadata_panel import MetadataPanel
from core.metadata_writer import write_metadata
import core.metadata_enricher
from core.metadata_reader import read_metadata
from ui.playback_panel import PlaybackPanel
from core.audio_player import AudioPlayer
from ui.theme import get_complete_style, COLORS

# --- Clases para Trabajo en Segundo Plano (Threading) ---

class WorkerSignals(QObject):
    finished = Signal(dict)

class EnrichmentWorker(QRunnable):
    def __init__(self, track_info: dict):
        super().__init__()
        self.track_info = track_info
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        print("⚙️ Worker de enriquecimiento iniciado en un hilo secundario.")
        # Pasamos una copia para evitar efectos secundarios si track_info se modifica en otro lugar
        result = core.metadata_enricher.enrich_metadata(self.track_info.copy())
        self.signals.finished.emit(result)
        print("🏁 Worker de enriquecimiento finalizado.")

# --- Ventana Principal ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DjAlfin - Qt Edition")
        self.setGeometry(50, 50, 1200, 750)
        self.setMinimumSize(1000, 600)
        self.threadpool = QThreadPool()
        print(f"🧵 ThreadPool iniciado con un máximo de {self.threadpool.maxThreadCount()} hilos.")
        self.player = AudioPlayer()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setStyleSheet(get_complete_style())
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        self.track_list_view = TrackListView()
        self.track_list_model = TrackListModel()
        self.track_list_view.setModel(self.track_list_model)
        main_splitter.addWidget(self.track_list_view)

        db.init_db()
        self.load_tracks_from_db()
        self.start_library_scan()
        self.track_list_view.clearSelection()

        self.metadata_panel = MetadataPanel()
        metadata_dock = QDockWidget("", self)
        metadata_dock.setWidget(self.metadata_panel)
        metadata_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, metadata_dock)
        metadata_dock.setFloating(False)
        metadata_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        metadata_dock.setTitleBarWidget(QWidget())
        metadata_dock.setMinimumWidth(380) # Ajustado al nuevo mínimo del panel
        metadata_dock.setMaximumWidth(450) # Un poco más de espacio si es necesario

        self.playback_panel = PlaybackPanel()
        playback_dock = QDockWidget("", self)
        playback_dock.setWidget(self.playback_panel)
        playback_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, playback_dock)
        playback_dock.setFloating(False)
        playback_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        playback_dock.setTitleBarWidget(QWidget())
        playback_dock.setMinimumHeight(120)
        playback_dock.setMaximumHeight(180)

        main_splitter.setSizes([self.width()])

        self.track_list_view.selectionModel().selectionChanged.connect(self.on_track_selection_changed)
        self.track_list_view.doubleClicked.connect(self.on_track_double_clicked)
        
        self.metadata_panel.metadataChanged.connect(self.on_metadata_changed)
        self.metadata_panel.enrichRequested.connect(self.on_enrich_clicked)
        self.metadata_panel.refreshRequested.connect(self.on_refresh_requested)
        
        self.playback_panel.playRequested.connect(self.on_play_requested)
        self.playback_panel.pauseRequested.connect(self.on_pause_requested)
        self.playback_panel.stopRequested.connect(self.on_stop_requested)
        self.playback_panel.positionChanged.connect(self.on_position_changed)
        self.playback_panel.volumeChanged.connect(self.on_volume_changed)
        self.playback_panel.previousRequested.connect(self.on_previous_requested)
        self.playback_panel.nextRequested.connect(self.on_next_requested)

        self.player.signals.positionChanged.connect(self.update_playback_position)
        self.player.signals.durationChanged.connect(self.update_playback_duration)
        self.player.signals.stateChanged.connect(self.update_playback_state)

    def start_library_scan(self):
        print("🚀 Iniciando escáner de biblioteca en segundo plano...")
        # TODO: Hacer configurable el directorio de música
        music_dir = os.path.expanduser("~/Music/test_library_small") 
        if not os.path.isdir(music_dir):
            print(f"⚠️ Directorio de música de prueba no encontrado: {music_dir}. Creando...")
            try:
                os.makedirs(music_dir, exist_ok=True)
                print(f"ℹ️ Por favor, añade archivos de música a: {music_dir}")
            except OSError as e:
                print(f"❌ Error al crear directorio de música: {e}")
                # Podríamos usar un directorio por defecto o pedir al usuario
                music_dir = os.path.expanduser("~") # Fallback muy genérico

        self.scanner = LibraryScanner(
            directory=music_dir, 
            on_complete_callback=self.on_scan_complete,
            progress_callback=self.update_scan_progress # Añadir callback de progreso
        )
        self.scanner.start()

    def update_scan_progress(self, message):
        # Aquí podrías actualizar una barra de estado o un label en la UI
        print(f"🔍 Progreso del escaneo: {message}")
        # Ejemplo: self.statusBar().showMessage(message, 2000) si tienes una barra de estado

    def on_scan_complete(self):
        print("✅ Escaneo de biblioteca completado. Refrescando la vista.")
        self.load_tracks_from_db()

    def load_tracks_from_db(self):
        all_tracks = db.get_all_tracks()
        self.track_list_model.load_data(all_tracks)
        print(f"💿 {len(all_tracks)} pistas cargadas desde la base de datos.")

    def on_track_selection_changed(self, selected=None, deselected=None):
        indexes = self.track_list_view.selectedIndexes()
        if not indexes:
            self.metadata_panel.clear_fields()
            self.playback_panel.set_track_info("No track selected", "")
            return

        selected_row = indexes[0].row()
        track_data = self.track_list_model.get_track_at(selected_row)
        
        if track_data:
            if track_data.get('file_path'):
                self.player.load(track_data['file_path'])
            
            # track_data de get_track_at ya debería ser completo con todos los campos de la DB
            self.metadata_panel.update_track_info(track_data)
            self.playback_panel.set_track_info(
                track_data.get('title', 'Unknown Title'),
                track_data.get('artist', 'Unknown Artist')
            )
        else:
            self.metadata_panel.clear_fields()
            self.playback_panel.set_track_info("No track selected", "")
            
    def on_track_double_clicked(self, index):
        selected_row = index.row()
        track_data = self.track_list_model.get_track_at(selected_row)
        if track_data and 'file_path' in track_data:
            self.player.load(track_data['file_path'])
            self.player.play()

    def on_play_requested(self): self.player.play()
    def on_pause_requested(self): self.player.pause()
    def on_stop_requested(self): self.player.stop()

    def on_previous_requested(self):
        current_index = self.track_list_view.currentIndex().row()
        if current_index <= 0:
            next_index = self.track_list_model.rowCount() - 1
        else:
            next_index = current_index - 1
        if next_index >= 0: # Asegurar que el índice sea válido
            self.track_list_view.selectRow(next_index)
            self.on_track_selection_changed() # Carga los detalles y prepara el reproductor

    def on_next_requested(self):
        current_index = self.track_list_view.currentIndex().row()
        if current_index < 0 or current_index >= self.track_list_model.rowCount() - 1:
            next_index = 0
        else:
            next_index = current_index + 1
        if self.track_list_model.rowCount() > 0: # Asegurar que haya pistas
             self.track_list_view.selectRow(next_index)
             self.on_track_selection_changed()

    def on_position_changed(self, position_percent):
        if hasattr(self.player, '_audio_segment') and self.player._audio_segment:
            duration_seconds = len(self.player._audio_segment) / 1000.0
            seek_position = (position_percent / 100.0) * duration_seconds
            self.player.seek(seek_position)
    
    def on_volume_changed(self, volume): pass # Implementar si es necesario
        
    def on_metadata_changed(self, metadata_from_ui: dict):
        selected_indexes = self.track_list_view.selectedIndexes()
        if not selected_indexes: return
        selected_row = selected_indexes[0].row()
        
        original_track_data_from_model = self.track_list_model.get_track_at(selected_row)
        if not original_track_data_from_model: return
            
        file_path = original_track_data_from_model.get('file_path')
        if not file_path: return

        # 1. Escribir los cambios manuales a los tags del archivo
        success_write_tags = write_metadata(file_path, metadata_from_ui.copy())

        if success_write_tags:
            print(f"✅ Metadatos (tags) guardados en archivo: {os.path.basename(file_path)}")
            
            # 2. Actualizar la base de datos
            data_for_db_update = original_track_data_from_model.copy()
            data_for_db_update.update(metadata_from_ui)
            
            try: # Actualizar fecha de modificación del archivo
                data_for_db_update['last_modified_date'] = os.path.getmtime(file_path)
            except OSError as e:
                print(f"⚠️ No se pudo obtener la fecha de modificación para {file_path}: {e}")
            
            db.add_track(data_for_db_update) # UPSERT en la DB
            print(f"💾 Cambios manuales guardados en DB para: {os.path.basename(file_path)}")

            # 3. Refrescar la UI desde la fuente de verdad (archivo y DB)
            # Esto asegura que lo que se muestra es lo que realmente está en el archivo y DB.
            self.on_refresh_requested() 
        else:
            print(f"⚠️ Error al guardar metadatos (tags) en el archivo: {os.path.basename(file_path)}")

    def on_refresh_requested(self):
        selected_indexes = self.track_list_view.selectedIndexes()
        if not selected_indexes: return
        selected_row = selected_indexes[0].row()
        
        track_data_from_model = self.track_list_model.get_track_at(selected_row)
        if not track_data_from_model or not track_data_from_model.get('file_path'): return

        file_path = track_data_from_model['file_path']
        print(f"🔄 Refrescando metadatos para: {os.path.basename(file_path)}")

        # Leer los metadatos directamente del archivo (tags básicos)
        tags_from_file = read_metadata(file_path)
        
        # Obtener los datos completos actuales de la DB (que incluye IDs, URLs de arte, etc.)
        data_from_db = db.get_track_by_path(file_path)
        
        if data_from_db:
            final_refreshed_data = data_from_db.copy()
            if tags_from_file: # Si se pudieron leer tags del archivo, fusionarlos
                final_refreshed_data.update(tags_from_file)
            # Asegurar que file_path y last_modified_date (del archivo) estén actualizados
            final_refreshed_data['file_path'] = file_path
            try:
                final_refreshed_data['last_modified_date'] = os.path.getmtime(file_path)
            except OSError: pass
        elif tags_from_file: # Si no está en DB pero sí se leyeron tags (caso raro post-borrado de DB?)
            final_refreshed_data = tags_from_file
            final_refreshed_data['file_path'] = file_path
            try:
                final_refreshed_data['last_modified_date'] = os.path.getmtime(file_path)
            except OSError: pass
        else: # No se pudo leer nada
            print(f"⚠️ No se pudieron refrescar los metadatos para: {os.path.basename(file_path)}")
            return

        # Actualizar el modelo de la lista de pistas y el panel de metadatos
        self.track_list_model.update_track_data(selected_row, final_refreshed_data)
        self.metadata_panel.update_track_info(final_refreshed_data)
        print(f"✨ Metadatos refrescados para: {os.path.basename(file_path)}")


    def on_enrich_clicked(self):
        selected_indexes = self.track_list_view.selectedIndexes()
        if not selected_indexes: return
        selected_row = selected_indexes[0].row()
        
        track_data_for_enrichment = self.track_list_model.get_track_at(selected_row)
        if not track_data_for_enrichment: return

        self.metadata_panel.enrich_button.setDisabled(True)
        # Pasamos una copia de los datos actuales para el worker
        worker = EnrichmentWorker(track_data_for_enrichment.copy()) 
        worker.signals.finished.connect(self.on_enrichment_finished)
        self.threadpool.start(worker)

    def on_enrichment_finished(self, api_data_results: dict):
        selected_indexes = self.track_list_view.selectedIndexes()
        if not selected_indexes:
            self.metadata_panel.enrich_button.setDisabled(False)
            return
        selected_row = selected_indexes[0].row()
        
        current_track_data_from_model = self.track_list_model.get_track_at(selected_row)
        if not current_track_data_from_model:
            self.metadata_panel.enrich_button.setDisabled(False)
            return

        if api_data_results: # Si el enriquecedor devolvió algo
            # Crear una copia para no modificar el original del modelo directamente antes de tiempo
            data_to_update_in_db = current_track_data_from_model.copy()
            
            # Fusionar los datos de la API. api_data_results tiene prioridad.
            data_to_update_in_db.update(api_data_results) 
            
            # Asegurar que file_path se mantenga (no debería cambiar por enriquecimiento)
            data_to_update_in_db['file_path'] = current_track_data_from_model['file_path']
            # last_modified_date no debería cambiar por enriquecimiento, solo por escritura de tags
            if 'last_modified_date' in current_track_data_from_model:
                 data_to_update_in_db.setdefault('last_modified_date', current_track_data_from_model['last_modified_date'])
            
            # 1. Guardar en la base de datos
            db.add_track(data_to_update_in_db) 
            print(f"💾 Datos enriquecidos guardados en DB para: {data_to_update_in_db.get('title')}")

            # 2. Actualizar el modelo de la lista de pistas
            self.track_list_model.update_track_data(selected_row, data_to_update_in_db)
            
            # 3. Actualizar el panel de metadatos con los datos completamente fusionados
            self.metadata_panel.update_track_info(data_to_update_in_db)
            print(f"✨ Panel de metadatos actualizado con datos enriquecidos.")
        else:
            print("ℹ️ No se encontraron datos adicionales durante el enriquecimiento.")
        
        self.metadata_panel.enrich_button.setDisabled(False)

    @Slot(float)
    def update_playback_position(self, position_seconds):
        self.playback_panel.set_position(position_seconds)

    @Slot(float)
    def update_playback_duration(self, duration_seconds):
        self.playback_panel.set_duration(duration_seconds)

    @Slot(bool)
    def update_playback_state(self, is_playing):
        self.playback_panel.set_playing_state(is_playing)
            
    def closeEvent(self, event):
        print("🛑 Cerrando aplicación DjAlfin...")
        if hasattr(self, 'scanner') and self.scanner.running:
            print("⏳ Deteniendo escáner de biblioteca...")
            self.scanner.stop()
            self.scanner.wait(5000) # Esperar máx 5 segundos
        
        self.player.cleanup()
        print("⏳ Esperando que los hilos del ThreadPool finalicen...")
        self.threadpool.waitForDone(-1) # Esperar indefinidamente
        print("✅ Hilos finalizados.")
        super().closeEvent(event)


if __name__ == "__main__":
    print("🚀 Iniciando aplicación DjAlfin...")
    app = QApplication(sys.argv)
    print("✅ QApplication creada")
    
    try:
        window = MainWindow()
        print("✅ MainWindow creada")
        window.show()
        # window.showMaximized() # Descomentar para abrir maximizado por defecto
        print("✅ MainWindow mostrada")
        print("🔄 Iniciando bucle de eventos...")
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ Error crítico al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
