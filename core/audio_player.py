import threading
import time
from typing import Optional, Callable

from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio


class AudioPlayer:
    def __init__(self, update_callback: Optional[Callable[[int, int], None]] = None):
        self.audio: Optional[AudioSegment] = None
        self.playback_handle: Optional[threading.Thread] = None
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0.0
        self.paused_position = 0.0
        self.update_callback = update_callback  # Llama a (current_ms, total_ms)
        self.stop_event = threading.Event()

    def load(self, file_path: str) -> bool:
        """Carga un archivo de audio. Detiene la reproducción actual si la hay."""
        self.stop()
        try:
            # Pydub puede necesitar que la ruta de ffmpeg se especifique explícitamente a veces
            # AudioSegment.converter = "/path/to/your/ffmpeg" 
            print(f"Cargando archivo: {file_path}")
            self.audio = AudioSegment.from_file(file_path)
            print("Archivo cargado correctamente.")
            return True
        except Exception as e:
            print(f"ERROR DETALLADO AL CARGAR AUDIO con pydub en {file_path}: {e}")
            import traceback
            traceback.print_exc()
            self.audio = None
            return False

    def play(self, from_ms: int = 0) -> None:
        """Inicia la reproducción desde una posición específica (en ms)."""
        if not self.audio:
            return

        if self.is_playing and not self.is_paused:
            return  # Ya se está reproduciendo

        if self.is_paused:  # Reanudar
            from_ms = self.paused_position
        else:  # Empezar de nuevo o desde una posición
            self.paused_position = from_ms

        self.is_paused = False
        self.is_playing = True
        self.stop_event.clear()

        segment_to_play = self.audio[from_ms:]
        self.start_time = time.time() - (from_ms / 1000.0)

        self.playback_handle = threading.Thread(
            target=self._play_thread, args=(segment_to_play,), daemon=True
        )
        self.playback_handle.start()

        # Iniciar el hilo de actualización de la UI
        if self.update_callback:
            update_thread = threading.Thread(target=self._update_ui, daemon=True)
            update_thread.start()

    def _play_thread(self, segment: AudioSegment) -> None:
        """Hilo interno para la reproducción de audio."""
        play_obj = _play_with_simpleaudio(segment)
        while play_obj.is_playing() and not self.stop_event.is_set():
            time.sleep(0.05)
        
        if not self.is_paused:
            self.is_playing = False
        # Si se completó la reproducción, notificar una última vez
        if self.update_callback and not self.stop_event.is_set() and not self.is_paused:
            total_duration_ms = self.get_duration_ms()
            self.update_callback(total_duration_ms, total_duration_ms)


    def _update_ui(self) -> None:
        """Hilo para enviar actualizaciones periódicas a la UI."""
        while self.is_playing and not self.is_paused and not self.stop_event.is_set():
            current_pos_ms = self.get_current_time_ms()
            total_duration_ms = self.get_duration_ms()
            if self.update_callback:
                self.update_callback(current_pos_ms, total_duration_ms)
            time.sleep(0.1)

    def pause(self) -> None:
        """Pausa la reproducción actual."""
        if not self.is_playing or self.is_paused:
            return
        
        self.is_paused = True
        self.paused_position = self.get_current_time_ms()
        self.stop_event.set() # Detener el hilo de reproducción
        if self.playback_handle:
            self.playback_handle.join()

    def stop(self) -> None:
        """Detiene la reproducción por completo."""
        if not self.is_playing and self.playback_handle is None:
            return
            
        self.is_playing = False
        self.is_paused = False
        self.stop_event.set()
        if self.playback_handle:
            self.playback_handle.join()
            self.playback_handle = None

        self.paused_position = 0.0
        if self.update_callback:
            self.update_callback(0, self.get_duration_ms())
            
    def seek(self, position_ms: int) -> None:
        """Salta a una posición específica en el audio."""
        if not self.audio:
            return
        
        was_playing = self.is_playing and not self.is_paused
        self.stop() # Detiene la reproducción actual
        
        # Clamp position to valid range
        position_ms = max(0, min(position_ms, self.get_duration_ms()))
        
        self.paused_position = position_ms
        if was_playing:
            self.play(from_ms=position_ms)
        elif self.update_callback:
            # Si estaba pausado, solo actualiza la UI a la nueva posición
            self.update_callback(position_ms, self.get_duration_ms())

    def get_duration_ms(self) -> int:
        """Devuelve la duración total del audio en milisegundos."""
        if self.audio:
            return len(self.audio)
        return 0

    def get_current_time_ms(self) -> int:
        """Devuelve el tiempo de reproducción actual en milisegundos."""
        if not self.is_playing:
            return int(self.paused_position)
        if self.is_paused:
            return int(self.paused_position)
        
        elapsed_seconds = time.time() - self.start_time
        return int(elapsed_seconds * 1000) 