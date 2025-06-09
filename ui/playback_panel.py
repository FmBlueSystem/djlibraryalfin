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
        """Crea los widgets del panel de control."""
        # --- Contenedor de botones ---
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)

        self.prev_button = ttk.Button(
            button_frame, text="⏮ Prev", command=self.prev_command
        )
        self.prev_button.pack(side="left", padx=5)

        self.play_pause_button = ttk.Button(
            button_frame, text="▶ Play", command=self._toggle_play_pause
        )
        self.play_pause_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            button_frame, text="■ Stop", command=self.stop_command
        )
        self.stop_button.pack(side="left", padx=5)

        self.next_button = ttk.Button(
            button_frame, text="Next ⏭", command=self.next_command
        )
        self.next_button.pack(side="left", padx=5)

        # --- Contenedor de la barra de progreso ---
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill="x", expand=True, padx=10)

        self.current_time_label = ttk.Label(progress_frame, text="00:00")
        self.current_time_label.pack(side="left")

        self.progress_slider = ttk.Scale(
            progress_frame, from_=0, to=100, orient="horizontal", command=self._on_seek
        )
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.progress_slider.bind("<ButtonPress-1>", self._on_seek_start)
        self.progress_slider.bind("<ButtonRelease-1>", self._on_seek_end)

        self.total_time_label = ttk.Label(progress_frame, text="--:--")
        self.total_time_label.pack(side="left")

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
