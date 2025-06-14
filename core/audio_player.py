import simpleaudio as sa
from pydub import AudioSegment
import threading
import time

class AudioPlayer:
    """
    Un reproductor de audio robusto que utiliza Pydub para la carga de archivos
    y SimpleAudio para la reproducción, ofreciendo amplio soporte de formatos.
    """
    def __init__(self, update_callback=None, on_end_callback=None):
        self.audio = None
        self.play_obj = None
        self.current_track_path = None
        
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.paused_position = 0

        self.update_callback = update_callback
        self.on_end_callback = on_end_callback
        
        self._monitor_thread = None
        self._stop_monitor = threading.Event()

    def play(self, file_path):
        if self.play_obj and self.play_obj.is_playing():
            self.stop()
        
        try:
            print(f"Cargando con Pydub: {file_path}")
            self.audio = AudioSegment.from_file(file_path)
            self.current_track_path = file_path
            
            self._start_playback()

        except Exception as e:
            print(f"Error al cargar el archivo de audio {file_path}: {e}")
            self.audio = None

    def _start_playback(self, from_position=0):
        if not self.audio: return

        # Cortar el audio desde la posición deseada
        segment_to_play = self.audio[from_position:]
        
        self.play_obj = sa.play_buffer(
            segment_to_play.raw_data,
            num_channels=segment_to_play.channels,
            bytes_per_sample=segment_to_play.sample_width,
            sample_rate=segment_to_play.frame_rate
        )
        self.is_playing = True
        self.is_paused = False
        self.start_time = time.time()
        self.paused_position = from_position # Guardar desde dónde empezamos

        self._start_monitor_thread()
        print(f"Reproduciendo: {self.current_track_path}")

    def pause(self):
        if not self.is_playing or self.is_paused: return
        
        self._stop_monitor.set() # Detener el hilo de monitoreo y la reproducción
        self.play_obj.stop()
        
        # Calcular y guardar la posición exacta de la pausa
        elapsed_time_ms = (time.time() - self.start_time) * 1000
        self.paused_position += elapsed_time_ms
        
        self.is_paused = True
        print("Reproducción pausada.")

    def resume(self):
        if not self.is_paused: return
        
        print("Reanudando reproducción...")
        self.is_paused = False
        # Reanudar desde la posición guardada
        self._start_playback(from_position=int(self.paused_position))

    def stop(self):
        if not self.play_obj: return

        self._stop_monitor.set()
        if self.play_obj.is_playing():
            self.play_obj.stop()
        
        self.is_playing = False
        self.is_paused = False
        self.current_track_path = None
        self.audio = None
        self.paused_position = 0
        print("Reproducción detenida.")

    def shutdown(self):
        """Detiene toda la actividad de audio y se asegura de que los hilos terminen."""
        print("Cerrando el reproductor de audio de forma segura...")
        self.stop()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1) # Esperar hasta 1 segundo
        print("Reproductor de audio cerrado.")

    def seek(self, percentage):
        if not self.audio: return
        
        duration_ms = len(self.audio)
        target_position_ms = int(duration_ms * (percentage / 100.0))
        
        if self.is_playing and not self.is_paused:
            self.stop()
            self._start_playback(from_position=target_position_ms)
        else: # Si está pausado o detenido
            self.paused_position = target_position_ms
            if self.is_paused: # Si estaba pausado, reanudar desde la nueva posición
                self.resume()
    
    def get_progress(self):
        if self.is_playing and not self.is_paused:
            elapsed_time = (time.time() - self.start_time) * 1000 # en ms
            current_pos = self.paused_position + elapsed_time
            total_duration = len(self.audio)
            return current_pos / 1000.0, total_duration / 1000.0
        elif self.is_paused:
            total_duration = len(self.audio) if self.audio else 0
            return self.paused_position / 1000.0, total_duration / 1000.0
        return 0, 0

    def _start_monitor_thread(self):
        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
        self._monitor_thread.start()

    def _monitor_playback(self):
        while not self._stop_monitor.is_set():
            if self.is_playing and not self.is_paused:
                if self.update_callback:
                    current_s, total_s = self.get_progress()
                    percent = (current_s / total_s * 100) if total_s > 0 else 0
                    self.update_callback(
                        time.strftime('%M:%S', time.gmtime(current_s)),
                        time.strftime('%M:%S', time.gmtime(total_s)),
                        percent
                    )
                
                # Comprobar si la reproducción ha terminado
                if not self.play_obj.is_playing():
                    print("La canción ha terminado.")
                    self.stop() # Limpiar estado
                    if self.on_end_callback:
                        self.on_end_callback()
                    break # Salir del bucle
            time.sleep(0.2) 