# core/audio_service.py

from PySide6.QtCore import QObject, Signal, QUrl, QThreadPool, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from .threading import Worker
from .bpm_analyzer import analyze_track_bpm

class AudioService(QObject):
    """
    Servicio de audio desacoplado para manejar la lógica de reproducción.
    """
    # Señales para notificar a la UI de los cambios de estado
    playbackStateChanged = Signal(QMediaPlayer.PlaybackState)
    positionChanged = Signal(int) # Posición en milisegundos
    durationChanged = Signal(int) # Duración en milisegundos
    trackLoaded = Signal(dict)
    bpmAnalyzed = Signal(dict) # Emitirá un diccionario con file_path y bpm
    errorOccurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        
        self.current_file = None
        self.is_analyzing_bpm = False

        # Conectar señales internas del QMediaPlayer a las nuestras usando @Slot
        self._player.playbackStateChanged.connect(self.playbackStateChanged)
        self._player.positionChanged.connect(self.on_player_position_changed)
        self._player.durationChanged.connect(self.on_player_duration_changed)
        self._player.errorOccurred.connect(self._handle_player_error)

    def load_track(self, track_data: dict):
        if not track_data or 'file_path' not in track_data:
            return
        
        file_path = track_data.get('file_path')
        self.current_file = file_path
        self._player.setSource(QUrl.fromLocalFile(file_path))
        self.trackLoaded.emit(track_data)
        print(f"🎵 Pista cargada en el servicio de audio: {file_path}")

    def play(self):
        if self._player.source().isEmpty():
            self.errorOccurred.emit("No hay ninguna pista cargada.")
            return
        self._player.play()

    def pause(self):
        self._player.pause()

    def play_pause(self):
        """Alterna entre reproducir y pausar."""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def stop(self):
        self._player.stop()

    def set_position(self, position_ms: int):
        self._player.setPosition(position_ms)

    def set_volume(self, volume: int):
        """Establece el volumen (0-100)."""
        # QAudioOutput usa una escala de 0.0 a 1.0
        self._audio_output.setVolume(volume / 100.0)

    def analyze_bpm(self):
        if self.current_file and not self.is_analyzing_bpm:
            self.is_analyzing_bpm = True
            
            worker = Worker(analyze_track_bpm, file_path=self.current_file)
            worker.signals.result.connect(self._on_bpm_analysis_complete)
            worker.signals.error.connect(self._on_bpm_analysis_error)
            
            QThreadPool.globalInstance().start(worker)
        elif self.is_analyzing_bpm:
            self.errorOccurred.emit("Ya se está analizando el BPM.")
        else:
            self.errorOccurred.emit("No hay pista para analizar.")

    def _on_bpm_analysis_complete(self, result: dict):
        self.is_analyzing_bpm = False
        if result and result.get('bpm'):
            # Adjuntar el file_path al resultado para que el receptor sepa qué pista se actualizó
            analysis_result = {
                'file_path': self.current_file,
                'bpm': result.get('bpm')
            }
            self.bpmAnalyzed.emit(analysis_result)
        else:
            self.errorOccurred.emit(f"No se pudo analizar el BPM: {result.get('error', 'Error desconocido')}")

    def _on_bpm_analysis_error(self, error_info):
        self.is_analyzing_bpm = False
        self.errorOccurred.emit(f"Fallo en el worker de análisis BPM: {error_info[1]}")

    def _handle_player_error(self, error: QMediaPlayer.Error):
        self.errorOccurred.emit(self._player.errorString())

    @Slot(int)
    def on_player_position_changed(self, position):
        self.positionChanged.emit(position)

    @Slot(int)
    def on_player_duration_changed(self, duration):
        self.durationChanged.emit(duration) 