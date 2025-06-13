import tkinter as tk
from tkinter import ttk, Menu, filedialog, messagebox
import threading
from typing import Optional

from core.database import DatabaseManager
from core.audio_player import AudioPlayer
from core.smart_playlist_manager import SmartPlaylistManager
from ui.tracklist import Tracklist
from ui.playback_panel import PlaybackPanel
from ui.suggestion_panel import SuggestionPanel
from ui.smart_playlist_panel import SmartPlaylistPanel
from ui.metadata_panel import MetadataPanel


# === CONSTANTES DE TEMA MIXED IN KEY PRO ===
class MixedInKeyTheme:
    """Constantes de colores inspiradas en Mixed In Key Pro."""
    BG_MAIN = "#1a1a1a"          # Fondo principal negro profundo
    BG_PANEL = "#2a2a2a"         # Paneles secundarios gris oscuro
    BG_WIDGET = "#333333"        # Widgets gris medio
    FG_PRIMARY = "#ffffff"       # Texto principal blanco
    FG_SECONDARY = "#cccccc"     # Texto secundario gris claro
    ACCENT_BLUE = "#00d4ff"      # Azul brillante para acentos
    ACCENT_GREEN = "#00ff88"     # Verde para elementos activos
    SELECT_BG = "#0066cc"        # Selección azul oscuro


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
        self.smart_playlist_manager = SmartPlaylistManager(self.db_manager.db_path)
        self.current_playing_path: Optional[str] = None
        self.current_playing_index: Optional[int] = None

        self.create_menu()
        self.setup_keyboard_shortcuts()
        self.create_widgets()

        self.load_tracks()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self) -> None:
        """
        Configura un estilo visual inspirado en Mixed In Key Pro.

        Aplica un tema oscuro profesional con:
        - Colores inspirados en Mixed In Key Pro
        - Tipografía clara y legible
        - Elementos de UI bien contrastados
        - Botones con estados visuales claros
        """
        # Configurar fondo principal
        self.configure(bg=MixedInKeyTheme.BG_MAIN)

        style = ttk.Style(self)
        style.theme_use("default")

        # --- Configurar Estilos TTK ---

        # Frame principal
        style.configure("TFrame", background=MixedInKeyTheme.BG_MAIN)
        style.configure("Card.TFrame",
                       background=MixedInKeyTheme.BG_PANEL,
                       relief="solid",
                       borderwidth=1)

        # Labels
        style.configure("TLabel",
                       background=MixedInKeyTheme.BG_MAIN,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       font=("Segoe UI", 9))
        style.configure("Title.TLabel",
                       background=MixedInKeyTheme.BG_MAIN,
                       foreground=MixedInKeyTheme.ACCENT_BLUE,
                       font=("Segoe UI", 12, "bold"))
        style.configure("Subtitle.TLabel",
                       background=MixedInKeyTheme.BG_PANEL,
                       foreground=MixedInKeyTheme.FG_SECONDARY,
                       font=("Segoe UI", 8))

        # Buttons
        style.configure("TButton",
                       background=MixedInKeyTheme.BG_WIDGET,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       borderwidth=1,
                       relief="solid",
                       font=("Segoe UI", 9))
        style.map("TButton",
                 background=[("active", "#444444"), ("pressed", "#555555")])

        # Accent buttons
        style.configure("Accent.TButton",
                       background=MixedInKeyTheme.ACCENT_BLUE,
                       foreground="#ffffff",
                       borderwidth=0,
                       font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton",
                 background=[("active", "#0099ff"), ("pressed", "#0055aa")])

        # Success buttons
        style.configure("Success.TButton",
                       background=MixedInKeyTheme.ACCENT_GREEN,
                       foreground="#000000",
                       borderwidth=0,
                       font=("Segoe UI", 9, "bold"))
        style.map("Success.TButton",
                 background=[("active", "#00cc66"), ("pressed", "#00aa55")])

        # Notebook (pestañas)
        style.configure("TNotebook",
                       background=MixedInKeyTheme.BG_MAIN,
                       borderwidth=0)
        style.configure("TNotebook.Tab",
                       background=MixedInKeyTheme.BG_WIDGET,
                       foreground=MixedInKeyTheme.FG_SECONDARY,
                       padding=[20, 8],
                       borderwidth=1,
                       font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                 background=[("selected", MixedInKeyTheme.BG_PANEL), ("active", "#3a3a3a")],
                 foreground=[("selected", MixedInKeyTheme.ACCENT_BLUE)])

        # Treeview
        style.configure("Treeview",
                       background=MixedInKeyTheme.BG_PANEL,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       fieldbackground=MixedInKeyTheme.BG_PANEL,
                       borderwidth=1,
                       relief="solid",
                       font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                       background=MixedInKeyTheme.BG_WIDGET,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       relief="flat",
                       font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                 background=[("selected", MixedInKeyTheme.SELECT_BG)],
                 foreground=[("selected", "#ffffff")])

        # Entry
        style.configure("TEntry",
                       fieldbackground=MixedInKeyTheme.BG_WIDGET,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       borderwidth=1,
                       relief="solid",
                       insertcolor=MixedInKeyTheme.FG_PRIMARY,
                       font=("Segoe UI", 9))

        # Scale (slider)
        style.configure("TScale",
                       background=MixedInKeyTheme.BG_MAIN,
                       troughcolor=MixedInKeyTheme.BG_WIDGET,
                       borderwidth=0,
                       lightcolor=MixedInKeyTheme.ACCENT_BLUE,
                       darkcolor=MixedInKeyTheme.ACCENT_BLUE)

        # Listbox (no es TTK, se configura por separado)
        self.option_add("*TkListbox*Background", MixedInKeyTheme.BG_PANEL)
        self.option_add("*TkListbox*Foreground", MixedInKeyTheme.FG_PRIMARY)
        self.option_add("*TkListbox*SelectBackground", MixedInKeyTheme.SELECT_BG)
        self.option_add("*TkListbox*SelectForeground", "#ffffff")

        style = ttk.Style(self)
        style.theme_use("default")

        # --- Configurar Estilos TTK ---

        # Frame principal
        style.configure("TFrame", background=MixedInKeyTheme.BG_MAIN)
        style.configure("Card.TFrame",
                       background=MixedInKeyTheme.BG_PANEL,
                       relief="solid",
                       borderwidth=1)

        # Labels
        style.configure("TLabel",
                       background=MixedInKeyTheme.BG_MAIN,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       font=("Segoe UI", 9))
        style.configure("Title.TLabel",
                       background=MixedInKeyTheme.BG_MAIN,
                       foreground=MixedInKeyTheme.ACCENT_BLUE,
                       font=("Segoe UI", 12, "bold"))
        style.configure("Subtitle.TLabel",
                       background=MixedInKeyTheme.BG_PANEL,
                       foreground=MixedInKeyTheme.FG_SECONDARY,
                       font=("Segoe UI", 8))

        # Buttons
        style.configure("TButton",
                       background=MixedInKeyTheme.BG_WIDGET,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       borderwidth=1,
                       relief="solid",
                       font=("Segoe UI", 9))
        style.map("TButton",
                 background=[("active", "#444444"), ("pressed", "#555555")])

        # Accent buttons
        style.configure("Accent.TButton",
                       background=MixedInKeyTheme.ACCENT_BLUE,
                       foreground="#ffffff",
                       borderwidth=0,
                       font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton",
                 background=[("active", "#0099ff"), ("pressed", "#0055aa")])

        # Success buttons
        style.configure("Success.TButton",
                       background=MixedInKeyTheme.ACCENT_GREEN,
                       foreground="#000000",
                       borderwidth=0,
                       font=("Segoe UI", 9, "bold"))
        style.map("Success.TButton",
                 background=[("active", "#00cc66"), ("pressed", "#00aa55")])

        # Notebook (pestañas)
        style.configure("TNotebook",
                       background=MixedInKeyTheme.BG_MAIN,
                       borderwidth=0)
        style.configure("TNotebook.Tab",
                       background=MixedInKeyTheme.BG_WIDGET,
                       foreground=MixedInKeyTheme.FG_SECONDARY,
                       padding=[20, 8],
                       borderwidth=1,
                       font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                 background=[("selected", MixedInKeyTheme.BG_PANEL), ("active", "#3a3a3a")],
                 foreground=[("selected", MixedInKeyTheme.ACCENT_BLUE)])

        # Treeview
        style.configure("Treeview",
                       background=MixedInKeyTheme.BG_PANEL,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       fieldbackground=MixedInKeyTheme.BG_PANEL,
                       borderwidth=1,
                       relief="solid",
                       font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                       background=MixedInKeyTheme.BG_WIDGET,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       relief="flat",
                       font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                 background=[("selected", MixedInKeyTheme.SELECT_BG)],
                 foreground=[("selected", "#ffffff")])

        # Entry
        style.configure("TEntry",
                       fieldbackground=MixedInKeyTheme.BG_WIDGET,
                       foreground=MixedInKeyTheme.FG_PRIMARY,
                       borderwidth=1,
                       relief="solid",
                       insertcolor=MixedInKeyTheme.FG_PRIMARY,
                       font=("Segoe UI", 9))

        # Scale (slider)
        style.configure("TScale",
                       background=MixedInKeyTheme.BG_MAIN,
                       troughcolor=MixedInKeyTheme.BG_WIDGET,
                       borderwidth=0,
                       lightcolor=MixedInKeyTheme.ACCENT_BLUE,
                       darkcolor=MixedInKeyTheme.ACCENT_BLUE)



    def create_menu(self) -> None:
        """Crea la barra de menú principal."""
        menubar = Menu(self, bg="#2a2a2a", fg="#ffffff", borderwidth=0)
        self.config(menu=menubar)

        # Menú de Archivo
        file_menu = Menu(
            menubar,
            tearoff=0,
            bg="#2a2a2a",
            fg="#ffffff",
            activebackground="#00d4ff",
            activeforeground="#000000",
            borderwidth=0,
        )
        file_menu.add_command(label="Escanear Biblioteca (Ctrl+O)", command=self.scan_library)
        file_menu.add_command(label="Recargar Lista (F5)", command=self.load_tracks)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.on_closing)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú de Reproducción
        playback_menu = Menu(
            menubar,
            tearoff=0,
            bg="#2a2a2a",
            fg="#ffffff",
            activebackground="#00d4ff",
            activeforeground="#000000",
            borderwidth=0,
        )
        playback_menu.add_command(label="Reproducir/Pausar (Espacio)", command=self.toggle_play_pause)
        playback_menu.add_command(label="Detener (Ctrl+S)", command=self.stop_audio)
        playback_menu.add_separator()
        playback_menu.add_command(label="Anterior (Ctrl+←)", command=self.play_previous_track)
        playback_menu.add_command(label="Siguiente (Ctrl+→)", command=self.play_next_track)
        menubar.add_cascade(label="Reproducción", menu=playback_menu)

        # Menú de Herramientas
        tools_menu = Menu(
            menubar,
            tearoff=0,
            bg="#2a2a2a",
            fg="#ffffff",
            activebackground="#00d4ff",
            activeforeground="#000000",
            borderwidth=0,
        )
        tools_menu.add_command(label="🔍 Buscar Metadatos Faltantes", command=self.open_metadata_enrichment)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)

        # Menú de Ayuda
        help_menu = Menu(
            menubar,
            tearoff=0,
            bg="#2a2a2a",
            fg="#ffffff",
            activebackground="#00d4ff",
            activeforeground="#000000",
            borderwidth=0,
        )
        help_menu.add_command(label="Atajos de Teclado", command=self.show_keyboard_shortcuts)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        # Guardar referencia al menubar para las pruebas
        self.menubar = menubar

    def setup_keyboard_shortcuts(self) -> None:
        """Configura los atajos de teclado globales."""
        # Atajos de archivo
        self.bind_all("<Control-o>", lambda e: self.scan_library())
        self.bind_all("<F5>", lambda e: self.load_tracks())
        self.bind_all("<Control-q>", self.on_closing)

        # Atajos de reproducción
        self.bind_all("<space>", self.toggle_play_pause)
        self.bind_all("<Control-s>", lambda e: self.stop_audio())
        self.bind_all("<Control-Left>", lambda e: self.play_previous_track())
        self.bind_all("<Control-Right>", lambda e: self.play_next_track())

        # Atajos de navegación
        self.bind_all("<Up>", lambda e: self.tracklist.select_previous_track())
        self.bind_all("<Down>", lambda e: self.tracklist.select_next_track())
        self.bind_all("<Return>", lambda e: self.play_selected_track())

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

        # --- Panel derecho (pestañas para sugerencias, smart playlists y metadatos) ---
        right_pane = ttk.Frame(main_pane)

        # Notebook para pestañas
        right_notebook = ttk.Notebook(right_pane)
        right_notebook.pack(fill="both", expand=True)

        # Pestaña de sugerencias
        suggestions_frame = ttk.Frame(right_notebook)
        self.suggestion_panel = SuggestionPanel(
            suggestions_frame,
            db_manager=self.db_manager,
            play_track_callback=self.play_track_from_suggestion,
        )
        self.suggestion_panel.pack(fill="both", expand=True)
        right_notebook.add(suggestions_frame, text="🎯 Sugerencias")

        # Pestaña de smart playlists
        smart_playlists_frame = ttk.Frame(right_notebook)
        self.smart_playlist_panel = SmartPlaylistPanel(
            smart_playlists_frame,
            db_manager=self.db_manager,
            play_track_callback=self.play_track_from_suggestion,
        )
        self.smart_playlist_panel.pack(fill="both", expand=True)
        right_notebook.add(smart_playlists_frame, text="🎵 Smart Playlists")

        # Pestaña de metadatos
        metadata_frame = ttk.Frame(right_notebook)
        self.metadata_panel = MetadataPanel(
            metadata_frame,
            db_path=self.db_manager.db_path
        )
        self.metadata_panel.pack(fill="both", expand=True)
        right_notebook.add(metadata_frame, text="🔍 Metadatos")

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
        _ = event  # Required parameter for binding but not used
        selected_path = self.tracklist.get_selected_track_path()
        if not selected_path:
            if self.audio_player.is_paused():
                self.audio_player.resume_audio()
                self.playback_panel.set_playing_state(True)
            return

        if self.current_playing_path != selected_path:
            self.current_playing_path = selected_path
            # Obtener información de la pista para mostrar en el panel
            track_info = self.tracklist.get_selected_track_info()
            if track_info:
                self.playback_panel.update_track_info(
                    track_info.get('title', 'Desconocido'),
                    track_info.get('artist', 'Desconocido')
                )

            # Ejecutar la operación de reproducción (que es bloqueante) en un hilo
            threading.Thread(
                target=self.audio_player.play_audio, args=(selected_path,), daemon=True
            ).start()

            # Record playback start in smart playlist manager
            self.smart_playlist_manager.record_playback(selected_path)
        elif self.audio_player.is_paused():
            self.audio_player.resume_audio()

        self.playback_panel.set_playing_state(True)
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
            self.playback_panel.set_playing_state(False)
            # Mantenemos el highlight cuando está en pausa

    def stop_audio(self) -> None:
        self.audio_player.stop_audio()
        self.current_playing_path = None
        self.current_playing_index = None
        self.playback_panel.set_playing_state(False)
        self.playback_panel.update_progress(0, 0)
        self.playback_panel.update_track_info()
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
            # Si no hay pista reproduciéndose, intentar reproducir la seleccionada
            selected_items = self.tracklist.tracklist_tree.selection()
            if selected_items:
                self.play_selected_track()
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
        else:
            # If track not found in main list, play directly and record
            self.current_playing_path = file_path
            # Get track info from database
            track_info = self.db_manager.get_track_by_path(file_path)
            if track_info:
                self.playback_panel.update_track_info(
                    track_info.get('title', 'Desconocido'),
                    track_info.get('artist', 'Desconocido')
                )

            # Play the track
            threading.Thread(
                target=self.audio_player.play_audio, args=(file_path,), daemon=True
            ).start()

            # Record playback
            self.smart_playlist_manager.record_playback(file_path)

            self.playback_panel.set_playing_state(True)
            self.suggestion_panel.update_suggestions(file_path)

    def toggle_play_pause(self, event: Optional[tk.Event] = None) -> None:
        """Alterna entre reproducir y pausar la pista actual."""
        _ = event  # Parámetro requerido por el binding pero no utilizado
        if self.audio_player.is_playing():
            self.pause_audio()
        else:
            self.play_selected_track()

    def show_keyboard_shortcuts(self) -> None:
        """Muestra una ventana con los atajos de teclado disponibles."""
        from tkinter import messagebox
        shortcuts_text = """
🎹 ATAJOS DE TECLADO DISPONIBLES:

📁 ARCHIVO:
• Ctrl+O: Escanear biblioteca
• F5: Recargar lista

🎵 REPRODUCCIÓN:
• Espacio: Reproducir/Pausar
• Ctrl+S: Detener
• Ctrl+←: Pista anterior
• Ctrl+→: Pista siguiente

⚙️ GENERAL:
• Ctrl+Q: Salir de la aplicación
        """
        messagebox.showinfo("Atajos de Teclado", shortcuts_text)

    def show_about(self) -> None:
        """Muestra información sobre la aplicación."""
        from tkinter import messagebox
        about_text = """
🎵 DjAlfin - Asistente de DJ Inteligente

Versión: 2.0
Desarrollado con Python + Tkinter

Características:
• Biblioteca de música inteligente
• Sugerencias automáticas
• Smart Playlists
• Interfaz inspirada en Mixed In Key Pro
• Controles de reproducción avanzados

© 2024 DjAlfin Project
        """
        messagebox.showinfo("Acerca de DjAlfin", about_text)

    def open_metadata_enrichment(self) -> None:
        """Abre el diálogo de enriquecimiento de metadatos."""
        if hasattr(self, 'metadata_panel'):
            self.metadata_panel.open_enrichment_dialog()
        else:
            messagebox.showwarning(
                "Panel no disponible",
                "El panel de metadatos no está disponible en este momento."
            )

    def on_closing(self, event: Optional[tk.Event] = None) -> None:
        """Maneja el cierre de la aplicación."""
        _ = event  # Parámetro requerido por el binding pero no utilizado
        if self.audio_player.is_playing():
            self.audio_player.stop_audio()
        self.destroy()

    def on_audio_finished(self) -> None:
        """Callback cuando termina la reproducción de audio."""
        # Record that the track was completed
        if self.current_playing_path:
            # Get track duration to record completion
            track_info = self.tracklist.get_selected_track_info()
            duration = track_info.get('duration', 0) if track_info else 0
            self.smart_playlist_manager.record_playback(
                self.current_playing_path,
                duration_played=duration,
                completed=True
            )

        # Auto-play: reproducir la siguiente pista automáticamente
        self.play_next_track()


def main():
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
