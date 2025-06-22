# core/audio_service.py

import os
from PySide6.QtCore import QObject, Signal, QUrl, QThreadPool, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from .threading import Worker
from .bpm_analyzer import analyze_track_bpm

def validate_audio_file(file_path):
    """
    Valida si un archivo de audio es válido y soportado.
    
    Returns:
        tuple: (is_valid, error_message, file_info)
    """
    if not file_path:
        return False, "No se proporcionó ruta de archivo", {}
    
    if not os.path.exists(file_path):
        return False, f"Archivo no encontrado: {file_path}", {}
    
    if not os.path.isfile(file_path):
        return False, f"La ruta no es un archivo: {file_path}", {}
    
    # Verificar tamaño del archivo
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, f"El archivo está vacío: {file_path}", {}
        if file_size < 1024:  # Menos de 1KB probablemente no es un archivo de audio válido
            return False, f"El archivo es demasiado pequeño ({file_size} bytes): {file_path}", {}
    except OSError as e:
        return False, f"Error al acceder al archivo: {e}", {}
    
    # Verificar extensión
    supported_extensions = {
        '.mp3': 'MPEG Audio Layer 3',
        '.m4a': 'MPEG-4 Audio',
        '.wav': 'Waveform Audio File', 
        '.flac': 'Free Lossless Audio Codec',
        '.ogg': 'Ogg Vorbis',
        '.aac': 'Advanced Audio Coding'
    }
    
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in supported_extensions:
        return False, f"Formato no soportado: {file_ext}", {}
    
    # Información del archivo
    file_info = {
        'path': file_path,
        'extension': file_ext,
        'format_name': supported_extensions[file_ext],
        'size_bytes': file_size,
        'size_mb': round(file_size / (1024 * 1024), 2),
        'basename': os.path.basename(file_path)
    }
    
    return True, "", file_info

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
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.positionChanged.connect(self.on_player_position_changed)
        self._player.durationChanged.connect(self.on_player_duration_changed)
        self._player.errorOccurred.connect(self._handle_player_error)
        
    def _on_playback_state_changed(self, state):
        """Maneja cambios de estado del reproductor con logging."""
        state_names = {
            QMediaPlayer.PlaybackState.StoppedState: "STOPPED",
            QMediaPlayer.PlaybackState.PlayingState: "PLAYING", 
            QMediaPlayer.PlaybackState.PausedState: "PAUSED"
        }
        state_name = state_names.get(state, f"UNKNOWN({state})")
        print(f"🎮 AudioService: Playback state changed to {state_name}")
        
        # Emitir la señal original
        self.playbackStateChanged.emit(state)

    def load_track(self, track_data: dict):
        print(f"🎮 AudioService: load_track() called with track_data type: {type(track_data)}")
        
        if not track_data:
            error_msg = "No se proporcionaron datos del track"
            print(f"❌ AudioService: {error_msg}")
            self.errorOccurred.emit(error_msg)
            return
            
        if 'file_path' not in track_data:
            error_msg = "El track no tiene ruta de archivo"
            print(f"❌ AudioService: {error_msg}")
            print(f"❌ AudioService: Track data keys: {list(track_data.keys())}")
            self.errorOccurred.emit(error_msg)
            return
        
        file_path = track_data.get('file_path')
        title = track_data.get('title', 'Unknown')
        artist = track_data.get('artist', 'Unknown')
        
        print(f"🎮 AudioService: Loading track - Title: '{title}', Artist: '{artist}', Path: '{file_path}'")
        
        # Validar archivo usando la nueva función
        is_valid, error_msg, file_info = validate_audio_file(file_path)
        
        if not is_valid:
            print(f"❌ AudioService: {error_msg}")
            self.errorOccurred.emit(error_msg)
            return
        
        print(f"✅ AudioService: File validated successfully")
        print(f"🎮 AudioService: File info - Format: {file_info['format_name']}, Size: {file_info['size_mb']}MB")
        
        self.current_file = file_path
        
        # Crear QUrl y cargar en el player
        url = QUrl.fromLocalFile(file_path)
        print(f"🎮 AudioService: Created QUrl: {url.toString()}")
        
        self._player.setSource(url)
        print(f"🎮 AudioService: Source set in player")
        
        # Intentar reproducir automáticamente
        print(f"🎮 AudioService: Attempting to play...")
        self._player.play()
        print(f"▶️ AudioService: Play command issued for: {os.path.basename(file_path)}")
        
        self.trackLoaded.emit(track_data)
        print(f"🎮 AudioService: trackLoaded signal emitted")

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
        volume_float = volume / 100.0
        self._audio_output.setVolume(volume_float)
        print(f"🎮 AudioService: Volume set to {volume}% ({volume_float:.2f})")

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
                'bpm': result.get('bpm'),
                'confidence': result.get('confidence', 0.0)
            }
            self.bpmAnalyzed.emit(analysis_result)
        else:
            self.errorOccurred.emit(f"No se pudo analizar el BPM: {result.get('error', 'Error desconocido')}")

    def _on_bpm_analysis_error(self, error_info):
        self.is_analyzing_bpm = False
        self.errorOccurred.emit(f"Fallo en el worker de análisis BPM: {error_info[1]}")

    def _handle_player_error(self, error: QMediaPlayer.Error):
        error_string = self._player.errorString()
        print(f"❌ QMediaPlayer Error: {error} - {error_string}")
        print(f"📁 Current file: {self.current_file}")
        
        # Mapear errores específicos a mensajes más útiles
        error_messages = {
            QMediaPlayer.Error.NoError: "Sin error",
            QMediaPlayer.Error.ResourceError: "Error de recurso - archivo no accesible o corrupto",
            QMediaPlayer.Error.FormatError: "Formato de archivo no soportado",
            QMediaPlayer.Error.NetworkError: "Error de red",
            QMediaPlayer.Error.AccessDeniedError: "Acceso denegado al archivo"
        }
        
        user_message = error_messages.get(error, error_string)
        if self.current_file:
            user_message += f" (Archivo: {self.current_file})"
            
        self.errorOccurred.emit(user_message)

    @Slot(int)
    def on_player_position_changed(self, position):
        self.positionChanged.emit(position)

    @Slot(int)
    def on_player_duration_changed(self, duration):
        self.durationChanged.emit(duration) 