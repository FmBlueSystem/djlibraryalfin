import simpleaudio as sa
from pydub import AudioSegment
import threading
import time
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class AudioPlayerSignals(QObject):
    """Señales emitidas por el reproductor de audio."""
    positionChanged = Signal(float)  # current_pos_seconds
    durationChanged = Signal(float)  # total_duration_seconds
    stateChanged = Signal(bool)      # is_playing

class AudioPlayer(QObject):
    """Un reproductor de audio robusto usando Pydub y SimpleAudio."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = AudioPlayerSignals()
        self._audio_segment = None
        self._play_obj = None
        self._current_file = None
        
        self._is_playing = False
        self._is_paused = False
        self._start_time = 0
        self._paused_position_ms = 0
        
        # Timer para actualizar la posición
        self._position_timer = QTimer(self)
        self._position_timer.setInterval(100) # 10 Hz
        self._position_timer.timeout.connect(self._update_position)

    def load(self, file_path: str):
        if self._is_playing or self._is_paused:
            self.stop()
        try:
            print(f"🎵 Cargando con Pydub: {file_path}")
            self._audio_segment = AudioSegment.from_file(file_path)
            self._current_file = file_path
            duration_sec = len(self._audio_segment) / 1000.0
            self.signals.durationChanged.emit(duration_sec)
            print(f"✅ Archivo cargado. Duración: {duration_sec:.2f}s")
        except Exception as e:
            print(f"❌ Error al cargar archivo con Pydub: {e}")
            self._current_file = None
            self._audio_segment = None

    @Slot()
    def play(self):
        if not self._audio_segment:
            return
        
        if self._is_paused: # Reanudar desde la pausa
            segment_to_play = self._audio_segment[self._paused_position_ms:]
        else: # Empezar desde el principio
            self._paused_position_ms = 0
            segment_to_play = self._audio_segment

        self._play_obj = sa.play_buffer(
            segment_to_play.raw_data,
            num_channels=segment_to_play.channels,
            bytes_per_sample=segment_to_play.sample_width,
            sample_rate=segment_to_play.frame_rate
        )
        
        self._start_time = time.time()
        self._is_playing = True
        self._is_paused = False
        self.signals.stateChanged.emit(True)
        self._position_timer.start()
        print("▶️ Reproduciendo")

    @Slot()
    def pause(self):
        if not self._is_playing:
            return
            
        self._play_obj.stop()
        elapsed_time_ms = (time.time() - self._start_time) * 1000
        self._paused_position_ms += elapsed_time_ms
        
        self._is_playing = False
        self._is_paused = True
        self.signals.stateChanged.emit(False)
        self._position_timer.stop()
        print("⏸️ Pausado")
        
    @Slot()
    def stop(self):
        if self._play_obj:
            self._play_obj.stop()
            self._play_obj = None

        self._is_playing = False
        self._is_paused = False
        self._paused_position_ms = 0
        self.signals.stateChanged.emit(False)
        self.signals.positionChanged.emit(0)
        self._position_timer.stop()
        print("⏹️ Detenido")

    def seek(self, position_seconds: float):
        if not self._audio_segment:
            return
            
        was_playing = self._is_playing
        if self._is_playing or self._is_paused:
            self.stop()

        self._paused_position_ms = int(position_seconds * 1000)
        
        if was_playing:
            self.play()

    def _update_position(self):
        if self._is_playing and self._play_obj:
            if self._play_obj.is_playing():
                elapsed_time_ms = (time.time() - self._start_time) * 1000
                current_pos_ms = self._paused_position_ms + elapsed_time_ms
                self.signals.positionChanged.emit(current_pos_ms / 1000.0)
            else:
                # La canción terminó
                self.stop()
                
    def cleanup(self):
        print("🧹 Limpiando reproductor de audio...")
        self.stop()
        sa.stop_all() 