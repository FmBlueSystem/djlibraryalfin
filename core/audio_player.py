import threading
import time
from typing import Any, Optional, Callable

from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio


class AudioPlayer:
    def __init__(
        self,
        update_callback: Optional[Callable[[float, float], None]] = None,
        on_song_end_callback: Optional[Callable[[], None]] = None,
    ):
        self.audio: Optional[AudioSegment] = None
        self.playback_handle: Optional[threading.Thread] = None
        self.play_obj: Optional[Any] = None  # Para guardar la referencia a simpleaudio
        self._is_playing = False
        self._is_paused = False
        self.start_time = 0.0
        self.paused_position_ms = 0.0

        # Callback que se llama con (current_seconds, duration_seconds)
        self.update_callback = update_callback
        self.on_song_end_callback = on_song_end_callback
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

    def play_audio(self, file_path: str) -> None:
        """
        Detiene la reproducción actual, carga un nuevo archivo y lo reproduce.
        Esta es una operación bloqueante y debe ser llamada desde un hilo secundario.
        """
        with self.lock:
            # 1. Detener completamente la reproducción actual (bloqueante)
            self._stop_internal()

            # 2. Cargar el nuevo audio
            try:
                self.audio = AudioSegment.from_file(file_path)
            except Exception as e:
                print(f"Error al cargar el archivo de audio {file_path}: {e}")
                self.audio = None
                return

            # 3. Resetear estado y empezar a reproducir
            self._is_playing = True
            self._is_paused = False
            self.stop_event.clear()
            self.paused_position_ms = 0.0
            self.start_time = time.time()

            self.playback_handle = threading.Thread(
                target=self._play_thread, daemon=True
            )
            self.playback_handle.start()

            update_thread = threading.Thread(target=self._update_ui_thread, daemon=True)
            update_thread.start()

    def _play_thread(self) -> None:
        """Hilo que reproduce el audio."""
        if not self.audio:
            return

        self.play_obj = _play_with_simpleaudio(self.audio[self.paused_position_ms :])
        self.play_obj.wait_done()  # Espera aquí hasta que termine o se detenga

        if not self.stop_event.is_set() and not self._is_paused:
            self._is_playing = False
            if self.on_song_end_callback:
                self.on_song_end_callback()

    def _update_ui_thread(self) -> None:
        """Hilo que actualiza la UI."""
        while self.is_playing() and not self.stop_event.is_set():
            if not self._is_paused and self.update_callback:
                current_seconds = self.get_current_position()
                duration_seconds = self.get_duration()
                self.update_callback(current_seconds, duration_seconds)
            time.sleep(0.1)

    def _stop_internal(self) -> None:
        """Lógica de parada interna. Asume que el lock ya ha sido adquirido."""
        if not self._is_playing and not self.play_obj:
            return

        self.stop_event.set()
        if self.play_obj:
            self.play_obj.stop()  # Detiene explícitamente el audio

        if self.playback_handle and self.playback_handle.is_alive():
            self.playback_handle.join()

        self._is_playing = False
        self._is_paused = False
        self.playback_handle = None
        self.play_obj = None
        self.paused_position_ms = 0.0

    def stop_audio(self) -> None:
        """Detiene la reproducción (accesible desde el exterior)."""
        with self.lock:
            self._stop_internal()

    def pause_audio(self) -> None:
        """Pausa la reproducción."""
        with self.lock:
            if not self._is_playing or self._is_paused:
                return

            self._is_paused = True
            self.paused_position_ms = (
                time.time() - self.start_time
            ) * 1000 + self.paused_position_ms

            if self.play_obj:
                self.play_obj.stop()
            self.stop_event.set()
            if self.playback_handle and self.playback_handle.is_alive():
                self.playback_handle.join()

    def resume_audio(self) -> None:
        """Reanuda la reproducción."""
        with self.lock:
            if not self._is_playing or not self._is_paused:
                return

            self._is_paused = False
            self.stop_event.clear()
            self.start_time = time.time()

            self.playback_handle = threading.Thread(
                target=self._play_thread, daemon=True
            )
            self.playback_handle.start()
            update_thread = threading.Thread(target=self._update_ui_thread, daemon=True)
            update_thread.start()

    def seek_audio(self, position_percent: float) -> None:
        """Busca una posición en el audio."""
        with self.lock:
            if not self.audio:
                return

            is_currently_playing = self.is_playing()
            self._stop_internal()
            self.paused_position_ms = len(self.audio) * position_percent

            if is_currently_playing:
                self._is_playing = True
                self._is_paused = False
                self.stop_event.clear()
                self.start_time = time.time()
                self.playback_handle = threading.Thread(
                    target=self._play_thread, daemon=True
                )
                self.playback_handle.start()
                update_thread = threading.Thread(
                    target=self._update_ui_thread, daemon=True
                )
                update_thread.start()

    def get_duration(self) -> float:
        """Devuelve la duración total del audio en segundos."""
        if self.audio:
            return len(self.audio) / 1000.0
        return 0.0

    def get_current_position(self) -> float:
        """Devuelve el tiempo de reproducción actual en segundos."""
        if self._is_paused or not self._is_playing:
            return self.paused_position_ms / 1000.0

        return (
            (time.time() - self.start_time) * 1000 + self.paused_position_ms
        ) / 1000.0

    def is_playing(self) -> bool:
        """Devuelve True si se está reproduciendo activamente (no pausado)."""
        return self._is_playing and not self._is_paused

    def is_paused(self) -> bool:
        """Devuelve True si el reproductor está en pausa."""
        return self._is_paused

    def load(self, file_path: str) -> bool:
        """Carga un archivo de audio. Detiene la reproducción actual si la hay."""
        self.stop_audio()
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

        if self._is_playing and not self._is_paused:
            return  # Ya se está reproduciendo

        if self._is_paused:  # Reanudar
            from_ms = self.paused_position_ms
        else:  # Empezar de nuevo o desde una posición
            self.paused_position_ms = from_ms

        self._is_paused = False
        self._is_playing = True
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

    def _update_ui(self) -> None:
        """Hilo para enviar actualizaciones periódicas a la UI."""
        while self._is_playing and not self._is_paused and not self.stop_event.is_set():
            current_pos_ms = self.get_current_time_ms()
            total_duration_ms = self.get_duration_ms()
            if self.update_callback:
                self.update_callback(current_pos_ms, total_duration_ms)
            time.sleep(0.1)

    def pause(self) -> None:
        """Pausa la reproducción actual."""
        if not self._is_playing or self._is_paused:
            return

        self._is_paused = True
        self.paused_position_ms = self.get_current_time_ms()
        self.stop_event.set()  # Detener el hilo de reproducción
        if self.playback_handle:
            self.playback_handle.join()

    def stop(self) -> None:
        """Detiene la reproducción por completo."""
        if not self._is_playing and self.playback_handle is None:
            return

        self._is_playing = False
        self._is_paused = False
        self.stop_event.set()
        if self.playback_handle:
            self.playback_handle.join()
            self.playback_handle = None

        self.paused_position_ms = 0.0
        if self.update_callback:
            self.update_callback(0, self.get_duration_ms())

    def seek(self, position_ms: int) -> None:
        """Salta a una posición específica en el audio."""
        if not self.audio:
            return

        was_playing = self._is_playing and not self._is_paused
        self.stop()  # Detiene la reproducción actual

        # Clamp position to valid range
        position_ms = max(0, min(position_ms, self.get_duration_ms()))

        self.paused_position_ms = position_ms
        if was_playing:
            self._is_playing = True
            self.resume_audio()
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
        if not self._is_playing:
            return int(self.paused_position_ms)
        if self._is_paused:
            return int(self.paused_position_ms)

        elapsed_seconds = time.time() - self.start_time
        return int(elapsed_seconds * 1000)
