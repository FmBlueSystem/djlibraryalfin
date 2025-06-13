import tkinter as tk
from tkinter import ttk
from typing import Any, Callable


def _format_time(seconds: float) -> str:
    """Formatea la duración de segundos a una cadena MM:SS."""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "--:--"
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes:02d}:{sec:02d}"


class PlaybackPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Widget,
        *,
        play_command: Callable,
        pause_command: Callable,
        stop_command: Callable,
        seek_command: Callable[[float], None],
        prev_command: Callable,
        next_command: Callable,
        **kwargs: Any,
    ):
        super().__init__(master, **kwargs)
        self.play_command = play_command
        self.pause_command = pause_command
        self.stop_command = stop_command
        self.seek_command = seek_command
        self.prev_command = prev_command
        self.next_command = next_command

        self._create_widgets()
        self.is_playing = False
        self.duration_seconds = 0
        self.is_seeking = False

    def _create_widgets(self) -> None:
        """Crea los widgets del panel de control con estilo Mixed In Key Pro."""
        # --- Contenedor principal con espaciado ---
        main_container = ttk.Frame(self)
        main_container.pack(fill="x", pady=10)

        # --- Información de la pista actual ---
        info_frame = ttk.Frame(main_container)
        info_frame.pack(fill="x", pady=(0, 10))

        self.track_info_label = ttk.Label(
            info_frame,
            text="🎵 Ninguna pista seleccionada",
            style="Subtitle.TLabel",
            anchor="center"
        )
        self.track_info_label.pack(fill="x")

        # --- Contenedor de botones principales ---
        button_frame = ttk.Frame(main_container)
        button_frame.pack(pady=5)

        self.prev_button = ttk.Button(
            button_frame,
            text="⏮",
            command=self.prev_command,
            width=4
        )
        self.prev_button.pack(side="left", padx=3)

        self.play_button = ttk.Button(
            button_frame,
            text="▶",
            command=self.play_command,
            style="Accent.TButton",
            width=6
        )
        self.play_button.pack(side="left", padx=3)

        self.stop_button = ttk.Button(
            button_frame,
            text="⏹",
            command=self.stop_command,
            width=4
        )
        self.stop_button.pack(side="left", padx=3)

        self.next_button = ttk.Button(
            button_frame,
            text="⏭",
            command=self.next_command,
            width=4
        )
        self.next_button.pack(side="left", padx=3)

        # --- Barra de progreso y tiempo ---
        progress_frame = ttk.Frame(main_container)
        progress_frame.pack(fill="x", pady=(10, 0))

        # Tiempo actual
        self.current_time_label = ttk.Label(
            progress_frame,
            text="0:00",
            style="Subtitle.TLabel",
            width=6
        )
        self.current_time_label.pack(side="left", padx=(0, 5))

        # Barra de progreso
        self.progress_slider = ttk.Scale(
            progress_frame,
            from_=0,
            to=100,
            orient="horizontal",
            command=self._on_scale_change,
        )
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.progress_slider.bind("<Button-1>", self._on_scale_click)
        self.progress_slider.bind("<ButtonRelease-1>", self._on_scale_release)

        # Tiempo total
        self.total_time_label = ttk.Label(
            progress_frame,
            text="0:00",
            style="Subtitle.TLabel",
            width=6
        )
        self.total_time_label.pack(side="right", padx=(5, 0))

    def _on_seek_start(self, event: Any) -> None:
        self.is_seeking = True

    def _on_seek_end(self, event: Any) -> None:
        self.is_seeking = False
        self._on_seek(self.progress_slider.get())

    def _on_seek(self, value_str: str) -> None:
        """Llamado cuando el slider se mueve."""
        if self.seek_command and self.is_seeking:
            value = float(value_str)
            self.seek_command(value / 100)  # Enviar como porcentaje

    def _toggle_play_pause(self) -> None:
        """Alterna entre reproducir y pausar."""
        if self.is_playing:
            if self.pause_command:
                self.pause_command()
        else:
            if self.play_command:
                self.play_command()

    def update_state(self, is_playing: bool) -> None:
        """Actualiza el estado del botón Play/Pause."""
        self.is_playing = is_playing
        self.play_pause_button.config(text="❚❚ Pause" if is_playing else "▶ Play")

    def update_progress(self, current_seconds: float, duration_seconds: float) -> None:
        """Actualiza la barra de progreso y las etiquetas de tiempo."""
        self.duration_seconds = duration_seconds
        self.current_time_label.config(text=_format_time(current_seconds))
        self.total_time_label.config(text=_format_time(duration_seconds))

        if not self.is_seeking:
            if duration_seconds > 0:
                progress_percent = (current_seconds / duration_seconds) * 100
                self.progress_slider.set(progress_percent)
            else:
                self.progress_slider.set(0)

    def _on_scale_change(self, value: str) -> None:
        """Maneja los cambios en el slider de progreso."""
        # Solo procesar si el usuario está arrastrando el slider
        if self.is_seeking:
            try:
                position_percent = float(value)
                if self.seek_command:
                    self.seek_command(position_percent)
            except ValueError:
                pass

    def _on_scale_click(self, event: Any) -> None:
        """Maneja el clic en el slider de progreso."""
        _ = event  # Parámetro no utilizado
        self.is_seeking = True

    def _on_scale_release(self, event: Any) -> None:
        """Maneja la liberación del slider de progreso."""
        _ = event  # Parámetro no utilizado
        self.is_seeking = False

    def update_track_info(self, track_name: str, artist: str) -> None:
        """Actualiza la información de la pista actual."""
        if hasattr(self, 'track_info_label'):
            self.track_info_label.config(text=f"{artist} - {track_name}")

    def set_playing_state(self, is_playing: bool) -> None:
        """Actualiza el estado visual de reproducción."""
        if is_playing:
            self.play_button.config(text="⏸️", style="Success.TButton")
        else:
            self.play_button.config(text="▶️", style="Accent.TButton")
