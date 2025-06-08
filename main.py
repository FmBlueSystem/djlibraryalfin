import tkinter as tk
from tkinter import ttk, filedialog, Menu
import threading
import queue
import os
from typing import Optional

from core.database import init_db
from core.library_scanner import scan_directory
from core.waveform_generator import generate_waveform_data
from core.audio_player import AudioPlayer
from ui.tracklist import Tracklist
from ui.waveform_display import WaveformDisplay
from ui.playback_panel import PlaybackPanel


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("DjAlfin - Biblioteca de Audio Inteligente")
        self.geometry("1200x800")

        self.scan_queue: "queue.Queue[str]" = queue.Queue()
        self.current_track_path: Optional[str] = None
        self.audio_player = AudioPlayer(update_callback=self._update_playback_ui)

        # Declaración de widgets para que el type checker los conozca
        self.tracklist: Tracklist
        self.waveform_display: WaveformDisplay
        self.playback_panel: PlaybackPanel
        self.status_var: tk.StringVar

        self.create_menu()
        self.create_main_widgets()
        self.create_status_bar()

        self.process_scan_queue()

    def create_menu(self) -> None:
        """Crea la barra de menú superior de la aplicación."""
        menubar = Menu(self)
        self.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Escanear Biblioteca...", command=self.scan_library)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

    def create_main_widgets(self) -> None:
        """Crea los widgets principales de la aplicación."""
        # PanedWindow para dividir la lista de la forma de onda
        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Frame superior para la lista de pistas ---
        tracklist_frame = ttk.Frame(main_pane)
        main_pane.add(tracklist_frame, weight=5)  # Darle más peso a la lista

        self.tracklist = Tracklist(
            tracklist_frame,
            track_select_callback=self.on_track_selected,
            track_play_callback=self.play_track,
        )
        self.tracklist.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            tracklist_frame, orient="vertical", command=self.tracklist.yview
        )
        self.tracklist.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # --- Frame intermedio para controles de reproducción ---
        self.playback_panel = PlaybackPanel(
            main_pane,
            play_callback=self._play_or_resume_track,
            pause_callback=self.audio_player.pause,
            stop_callback=self.stop_track,
            seek_callback=self._seek_track,
            prev_callback=self.play_previous_track,
            next_callback=self.play_next_track,
        )
        main_pane.add(self.playback_panel, weight=1)

        # --- Frame inferior para la forma de onda ---
        waveform_frame = ttk.Frame(main_pane)
        self.waveform_display = WaveformDisplay(waveform_frame, height=100)
        self.waveform_display.pack(fill="both", expand=True)
        main_pane.add(waveform_frame, weight=2)

        # Cargar datos al inicio
        self.tracklist.load_data()

    def create_status_bar(self) -> None:
        """Crea una barra de estado en la parte inferior de la ventana."""
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = ttk.Label(
            self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w"
        )
        status_bar.pack(side="bottom", fill="x")

    def on_track_selected(self, file_path: str) -> None:
        """Callback que se ejecuta cuando una pista es seleccionada en el Tracklist."""
        self.status_var.set(
            f"Generando forma de onda para {os.path.basename(file_path)}..."
        )
        # Limpiar la forma de onda anterior mientras se genera la nueva
        self.waveform_display.set_data([])

        # Generar en un hilo separado
        threading.Thread(
            target=self._generate_and_display_waveform, args=(file_path,), daemon=True
        ).start()

    def _generate_and_display_waveform(self, file_path: str) -> None:
        """Genera los datos y agenda el dibujado en el hilo principal."""
        waveform_data = generate_waveform_data(file_path)

        # Agendar la actualización de la UI en el hilo principal
        self.after(0, self.waveform_display.set_data, waveform_data)
        self.after(0, self.status_var.set, "Listo.")

    def scan_library(self) -> None:
        """Abre un diálogo para seleccionar un directorio y lo escanea."""
        directory_path = filedialog.askdirectory(
            title="Selecciona la carpeta de tu música"
        )
        if not directory_path:
            self.status_var.set("Escaneo cancelado.")
            return

        self.status_var.set(f"Escaneando {directory_path}...")

        # Ejecutar el escaneo en un hilo separado para no bloquear la UI
        threading.Thread(
            target=scan_directory, args=(directory_path, self.scan_queue), daemon=True
        ).start()

    def process_scan_queue(self) -> None:
        """Procesa los mensajes de la cola del escáner y actualiza la UI."""
        try:
            message = self.scan_queue.get_nowait()
            if message == "scan_complete":
                self.status_var.set("Escaneo completado. Actualizando lista...")
                self.tracklist.load_data()
                self.status_var.set("Listo.")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_scan_queue)

    def play_track(self, file_path: str) -> None:
        """Carga y reproduce una pista."""
        self.current_track_path = file_path
        if self.audio_player.load(file_path):
            self.audio_player.play()
            self.tracklist.set_playing_track(file_path)
            self.playback_panel.update_state(is_playing=True)

    def _play_or_resume_track(self) -> None:
        """Reproduce la pista actual o la seleccionada."""
        if self.audio_player.audio:
            self.audio_player.play()
            if self.current_track_path:
                self.tracklist.set_playing_track(self.current_track_path)
            self.playback_panel.update_state(is_playing=True)
            return

        # Si no hay audio cargado, intentar con la pista seleccionada
        file_path = self.current_track_path or self.tracklist.get_current_file_path()
        if file_path:
            self.play_track(file_path)

    def stop_track(self) -> None:
        """Detiene la reproducción y limpia el estado."""
        self.audio_player.stop()
        self.tracklist.set_playing_track(None)
        self.current_track_path = None
        self.playback_panel.update_state(is_playing=False)
        self.playback_panel.update_progress(0, 0)
        self.waveform_display.set_data([])

    def play_next_track(self) -> None:
        """Reproduce la pista siguiente en la lista."""
        file_path = self.tracklist.select_next()
        if file_path:
            self.play_track(file_path)

    def play_previous_track(self) -> None:
        """Reproduce la pista anterior en la lista."""
        file_path = self.tracklist.select_previous()
        if file_path:
            self.play_track(file_path)

    def _seek_track(self, percentage: float) -> None:
        """Busca una posición en la pista basada en un porcentaje."""
        duration_ms = self.audio_player.get_duration_ms()
        if duration_ms > 0:
            position_ms = int(duration_ms * percentage)
            self.audio_player.seek(position_ms)

    def _update_playback_ui(self, current_ms: int, total_ms: int) -> None:
        """Callback del player para actualizar la UI. Se ejecuta en el hilo principal."""

        def task():
            self.playback_panel.update_progress(current_ms / 1000.0, total_ms / 1000.0)

            # Si la reproducción terminó, actualizar estado
            if current_ms >= total_ms and total_ms > 0:
                self.playback_panel.update_state(is_playing=False)
                self.tracklist.set_playing_track(None)

        # Agendar la ejecución en el hilo principal de Tkinter
        self.after(0, task)


def main() -> None:
    # La inicialización de la base de datos no necesita un path,
    # la función get_db_path() lo resuelve internamente.
    init_db()

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
