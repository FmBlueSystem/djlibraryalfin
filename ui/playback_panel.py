# ui/playback_panel.py

import tkinter as tk
from tkinter import ttk
from . import theme
from .widgets import StyledButton

class PlaybackPanel(ttk.Frame):
    """
    Un panel con controles de reproducción de audio.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, style="TFrame", **kwargs)
        self.player = None # El player se inyectará después
        self.grid_columnconfigure(1, weight=1)

        # --- Variables ---
        self.current_time_var = tk.StringVar(value="00:00")
        self.total_time_var = tk.StringVar(value="00:00")
        self.track_title_var = tk.StringVar(value="Ninguna pista seleccionada")
        self.playback_position_var = tk.DoubleVar()

        self._create_widgets()
        self.set_play_pause_state(False)

    def set_player(self, player):
        """Asigna el objeto del reproductor a este panel para conectar los controles."""
        self.player = player
        self.play_pause_button.config(command=self._toggle_play_pause)
        self.prev_button.config(command=self.player.stop) # Simple stop for now
        self.next_button.config(command=self.player.stop) # Simple stop for now
        self.progress_slider.bind("<ButtonRelease-1>", self._on_seek)

    def set_commands(self, play_pause_cmd, next_cmd, prev_cmd):
        """Conecta los comandos de control a funciones externas."""
        self.play_pause_button.config(command=play_pause_cmd)
        self.next_button.config(command=next_cmd)
        self.prev_button.config(command=prev_cmd)

    def _create_widgets(self):
        """Crea los widgets del panel de reproducción."""
        # --- Fila Superior: Título y Tiempos ---
        top_frame = ttk.Frame(self, style="TFrame")
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(5,0))
        top_frame.grid_columnconfigure(1, weight=1)

        time_label = ttk.Label(top_frame, textvariable=self.current_time_var, font=theme.FONT_NORMAL)
        time_label.grid(row=0, column=0, sticky="w")
        
        title_label = ttk.Label(top_frame, textvariable=self.track_title_var, font=theme.FONT_BOLD, anchor="center")
        title_label.grid(row=0, column=1, sticky="ew")
        
        total_time_label = ttk.Label(top_frame, textvariable=self.total_time_var, font=theme.FONT_NORMAL)
        total_time_label.grid(row=0, column=2, sticky="e")

        # --- Fila Media: Barra de Progreso ---
        self.progress_slider = ttk.Scale(self, from_=0, to=100, orient="horizontal", variable=self.playback_position_var)
        self.progress_slider.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=0)

        # --- Fila Inferior: Botones y Volumen ---
        bottom_frame = ttk.Frame(self, style="TFrame")
        bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(0,5))
        bottom_frame.grid_columnconfigure(1, weight=1) # Centrar los botones de control

        controls_frame = ttk.Frame(bottom_frame, style="TFrame")
        controls_frame.grid(row=0, column=1)

        self.prev_button = StyledButton(controls_frame, text="⏪")
        self.prev_button.pack(side="left", padx=5)

        self.play_pause_button = StyledButton(controls_frame, text="▶")
        self.play_pause_button.pack(side="left", padx=5)

        self.next_button = StyledButton(controls_frame, text="⏩")
        self.next_button.pack(side="left", padx=5)

    def set_track_info(self, track_data):
        """Actualiza el título de la pista que se muestra a partir de un diccionario."""
        if not track_data:
            self.track_title_var.set("Ninguna pista seleccionada")
            self.current_time_var.set("00:00")
            self.total_time_var.set("00:00")
            self.progress_slider.set(0)
            return

        title = track_data.get('title', 'Título desconocido')
        artist = track_data.get('artist', 'Artista desconocido')
        display_text = f"{title} - {artist}"
        self.track_title_var.set(display_text)

    def update_playback_time(self, current_seconds, total_seconds):
        """Actualiza la barra de progreso y las etiquetas de tiempo."""
        self.current_time_var.set(self._format_time(current_seconds))
        self.total_time_var.set(self._format_time(total_seconds))
        
        # Actualizar la posición del slider
        if total_seconds > 0:
            percentage = (current_seconds / total_seconds) * 100
            self.progress_slider.set(percentage)

    def _format_time(self, seconds):
        """Formatea segundos a un string MM:SS."""
        try:
            seconds = int(seconds)
            minutes, sec = divmod(seconds, 60)
            return f"{minutes:02d}:{sec:02d}"
        except (ValueError, TypeError):
            return "00:00"
            
    def set_play_pause_state(self, is_playing):
        """Cambia el texto del botón Play/Pausa."""
        self.play_pause_button.config(text="⏸" if is_playing else "▶") 

    def _toggle_play_pause(self):
        if self.player:
            if self.player.is_playing and not self.player.is_paused:
                self.player.pause()
                self.set_play_pause_state(False)
            else:
                self.player.resume()
                self.set_play_pause_state(True)
    
    def _on_seek(self, event):
        if self.player:
            self.player.seek(self.progress_slider.get())

    def update_progress(self, current_time_str, total_time_str, progress_percent):
        self.current_time_var.set(current_time_str)
        self.total_time_var.set(total_time_str) # El formato ya incluye la barra
        self.progress_slider.set(progress_percent) 