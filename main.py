import tkinter as tk
from tkinter import ttk, filedialog, Menu
from typing import Optional
import threading

from core.database import DatabaseManager
from core.library_scanner import LibraryScanner
from core.audio_player import AudioPlayer
from ui.tracklist import Tracklist
from ui.suggestion_panel import SuggestionPanel
from ui.playback_panel import PlaybackPanel


class Application(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("DjAlfin - Asistente de DJ Inteligente")
        self.geometry("1200x700")
        self.state("zoomed")

        # --- Configuración de Estilos ---
        self.setup_styles()

        # Configuración inicial
        self.db_manager = DatabaseManager()
        self.audio_player = AudioPlayer(
            update_callback=self.update_playback_progress,
            on_song_end_callback=self.play_next_track,
        )
        self.current_playing_path: Optional[str] = None
        self.current_playing_index: Optional[int] = None

        self.create_menu()
        self.create_widgets()

        self.load_tracks()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self) -> None:
        """Configura un estilo oscuro y fijo para la aplicación."""
        self.configure(bg="#2B2B2B")

        style = ttk.Style(self)
        style.theme_use("default")

        # --- Colores ---
        BG_COLOR = "#2B2B2B"
        FG_COLOR = "#FFFFFF"
        WIDGET_BG = "#3C3F41"
        SELECT_BG = "#4A6984"

        # --- Estilos Generales ---
        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, borderwidth=0)
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR)
        style.configure("TButton", background=WIDGET_BG, foreground=FG_COLOR)
        style.map("TButton", background=[("active", SELECT_BG)])
        style.configure("TPanedWindow", background=BG_COLOR)

        # --- Estilo para la barra de progreso (Scale) ---
        style.configure(
            "Horizontal.TScale",
            background=BG_COLOR,
            troughcolor=WIDGET_BG,
        )
        style.map(
            "Horizontal.TScale",
            background=[("active", SELECT_BG)],
        )

        # --- Estilo para el Treeview ---
        style.configure(
            "Treeview",
            background=WIDGET_BG,
            foreground=FG_COLOR,
            fieldbackground=WIDGET_BG,
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", SELECT_BG)],
            foreground=[("selected", FG_COLOR)],
        )
        style.configure(
            "Treeview.Heading",
            background=BG_COLOR,
            foreground=FG_COLOR,
            relief="flat",
        )
        style.map(
            "Treeview.Heading",
            background=[("active", WIDGET_BG)],
        )

    def create_menu(self) -> None:
        menubar = Menu(
            self,
            tearoff=0,
            bg="#3C3F41",
            fg="#FFFFFF",
            activebackground="#4A6984",
            activeforeground="#FFFFFF",
            borderwidth=0,
        )
        self.config(menu=menubar)
        file_menu = Menu(
            menubar,
            tearoff=0,
            bg="#3C3F41",
            fg="#FFFFFF",
            activebackground="#4A6984",
            activeforeground="#FFFFFF",
            borderwidth=0,
        )
        file_menu.add_command(label="Escanear Biblioteca", command=self.scan_library)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.on_closing)
        menubar.add_cascade(label="Archivo", menu=file_menu)

    def create_widgets(self) -> None:
        # --- Contenedor principal (divide izquierda/derecha) ---
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Panel izquierdo (lista de canciones) ---
        left_pane = ttk.Frame(main_pane)
        self.tracklist = Tracklist(
            left_pane,
            db_manager=self.db_manager,
            play_selected_track_callback=self.play_selected_track,
        )
        self.tracklist.pack(fill="both", expand=True)
        main_pane.add(left_pane, weight=3)

        # --- Panel derecho (sugerencias) ---
        right_pane = ttk.Frame(main_pane)
        self.suggestion_panel = SuggestionPanel(
            right_pane,
            db_manager=self.db_manager,
            play_track_callback=self.play_track_from_suggestion,
        )
        self.suggestion_panel.pack(fill="both", expand=True)
        main_pane.add(right_pane, weight=1)

        # --- Panel de controles de reproducción (debajo de todo) ---
        self.playback_panel = PlaybackPanel(
            self,
            play_command=self.play_selected_track,
            pause_command=self.pause_audio,
            stop_command=self.stop_audio,
            seek_command=self.seek_audio,
            prev_command=self.play_previous_track,
            next_command=self.play_next_track,
        )
        self.playback_panel.pack(fill="x", side="bottom", pady=(0, 10), padx=10)

    def load_tracks(self) -> None:
        self.tracklist.load_all_tracks()

    def scan_library(self) -> None:
        path = filedialog.askdirectory()
        if path:
            scanner = LibraryScanner(path, self.db_manager)
            # Idealmente, esto correría en un hilo y actualizaría el UI
            scanner.scan()
            self.load_tracks()

    def on_closing(self) -> None:
        self.audio_player.stop_audio()
        self.destroy()

    def play_selected_track(self, event: Optional[tk.Event] = None) -> None:
        selected_path = self.tracklist.get_selected_track_path()
        if not selected_path:
            if self.audio_player.is_paused():
                self.audio_player.resume_audio()
                self.playback_panel.update_state(is_playing=True)
            return

        if self.current_playing_path != selected_path:
            self.current_playing_path = selected_path
            # Ejecutar la operación de reproducción (que es bloqueante) en un hilo
            threading.Thread(
                target=self.audio_player.play_audio, args=(selected_path,), daemon=True
            ).start()
        elif self.audio_player.is_paused():
            self.audio_player.resume_audio()

        self.playback_panel.update_state(is_playing=True)
        self.current_playing_index = self.get_current_track_index()
        self.tracklist.highlight_playing_track(self.current_playing_index)
        self.suggestion_panel.update_suggestions(self.current_playing_path)

    def get_current_track_index(self) -> Optional[int]:
        selected_item = self.tracklist.tracklist_tree.selection()
        if not selected_item:
            return (
                self.current_playing_index
            )  # Devolver el ultimo conocido si no hay seleccion

        try:
            return self.tracklist.tracklist_tree.index(selected_item[0])
        except Exception:
            # Si el item seleccionado ya no existe, por ejemplo
            return None

    def pause_audio(self) -> None:
        if self.audio_player.is_playing():
            self.audio_player.pause_audio()
            self.playback_panel.update_state(is_playing=False)
            # Mantenemos el highlight cuando está en pausa

    def stop_audio(self) -> None:
        self.audio_player.stop_audio()
        self.current_playing_path = None
        self.current_playing_index = None
        self.playback_panel.update_state(is_playing=False)
        self.playback_panel.update_progress(0, 0)
        self.tracklist.highlight_playing_track(None)
        self.suggestion_panel.clear()

    def seek_audio(self, position_percent: float) -> None:
        if self.current_playing_path:
            self.audio_player.seek_audio(position_percent)

    def play_next_track(self) -> None:
        if self.current_playing_index is None:
            return

        total_tracks = len(self.tracklist.tracklist_tree.get_children())
        if total_tracks == 0:
            return

        next_index = (self.current_playing_index + 1) % total_tracks

        self.tracklist.select_track_by_index(next_index)
        self.play_selected_track()

    def play_previous_track(self) -> None:
        if self.current_playing_index is None:
            return

        total_tracks = len(self.tracklist.tracklist_tree.get_children())
        if total_tracks == 0:
            return

        prev_index = (self.current_playing_index - 1 + total_tracks) % total_tracks

        self.tracklist.select_track_by_index(prev_index)
        self.play_selected_track()

    def update_playback_progress(
        self, current_seconds: float, duration_seconds: float
    ) -> None:
        """Callback para actualizar la UI de reproducción."""
        self.playback_panel.update_progress(current_seconds, duration_seconds)

    def play_track_from_suggestion(self, file_path: str) -> None:
        """Reproduce una pista seleccionada desde el panel de sugerencias."""
        # Encuentra el índice de la pista en la lista principal
        index_to_select = self.tracklist.find_track_index_by_path(file_path)
        if index_to_select is not None:
            self.tracklist.select_track_by_index(index_to_select)
            self.play_selected_track()


def main():
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
