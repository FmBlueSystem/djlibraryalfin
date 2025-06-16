import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading

# Importaciones de la aplicación
from ui.tracklist import Tracklist
from ui.metadata_panel import MetadataPanel
from ui.playback_panel import PlaybackPanel
from ui.status_bar import StatusBar
from ui import theme

from core.audio_player import AudioPlayer
from core import database as db
from core.library_scanner import LibraryScanner
from core.metadata_writer import write_metadata_tags

from config.config import AppConfig

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.app_config = AppConfig()
        self.title("DjAlfin Pro")
        self.geometry(self.app_config.get('window_geometry', '1200x800'))

        self.audio_player = None # Inicialización perezosa
        
        self.style = ttk.Style(self)
        self.setStyleSheet(theme.get_complete_style())

        self._create_widgets()
        self._load_initial_data()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _get_or_create_player(self):
        """Inicializa el AudioPlayer la primera vez que se necesita."""
        if self.audio_player is None:
            print("Creando instancia de AudioPlayer por primera vez...")
            self.audio_player = AudioPlayer(
                update_callback=self._update_playback_progress,
                on_end_callback=self._play_next_track
            )
            # Si el playback_panel ya existe, asignarle el nuevo player
            if hasattr(self, 'playback_panel'):
                self.playback_panel.set_player(self.audio_player)
        return self.audio_player

    def _create_widgets(self):
        main_frame = ttk.Frame(self, style="TFrame")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)

        self.tracklist = Tracklist(main_frame)
        self.tracklist.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.tracklist.tree.bind("<Double-1>", self._on_track_double_click)
        self.tracklist.tree.bind("<<TreeviewSelect>>", self._on_track_select)

        self.metadata_panel = MetadataPanel(main_frame)
        self.metadata_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.metadata_panel.set_save_callback(self._save_metadata)

        self.playback_panel = PlaybackPanel(self)
        self.playback_panel.pack(fill="x", side="bottom", pady=(5, 0))
        self.playback_panel.set_commands(
            play_pause_cmd=self._handle_play_pause,
            stop_cmd=self._handle_stop,
            next_cmd=self._play_next_track,
            prev_cmd=self._play_prev_track,
            seek_cmd=self._handle_seek
        )

        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x", side="bottom")

        self.config(menu=self._create_menu())

    def _create_menu(self, scanning=False):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        
        scan_state = "disabled" if scanning else "normal"
        file_menu.add_command(label="Escanear carpeta...", command=self.show_library_path_dialog, state=scan_state)
        
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._on_closing)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        return menubar

    def _load_initial_data(self):
        tracks = db.get_all_tracks()
        self.tracklist.populate(tracks)
        self.status_bar.set_status(f"{len(tracks)} pistas en la librería.")

    def _on_track_select(self, event):
        track_data = self.tracklist.get_selected_track_data()
        if track_data:
            self.metadata_panel.display_track(track_data)
            
    def _on_track_double_click(self, event):
        track_data = self.tracklist.get_selected_track_data()
        if track_data and 'file_path' in track_data:
            player = self._get_or_create_player()
            player.play(track_data['file_path'])
            self.playback_panel.set_track_info(track_data)
            self.playback_panel.set_play_pause_state(True)
    
    def _handle_play_pause(self):
        player = self._get_or_create_player()
        if player.is_playing and not player.is_paused:
            player.pause()
            self.playback_panel.set_play_pause_state(False)
        else:
            if not player.is_playing:
                self._on_track_double_click(None)
            else:
                player.resume()
            self.playback_panel.set_play_pause_state(True)
    
    def _handle_stop(self):
        if self.audio_player:
            self.audio_player.stop()
            self.playback_panel.set_play_pause_state(False)

    def _handle_seek(self, event):
        if self.audio_player:
            seek_percentage = self.playback_panel.playback_position_var.get()
            self.audio_player.seek(seek_percentage)

    def _save_metadata(self, track_id, new_metadata):
        file_path = db.get_track_path(track_id)
        if not file_path:
            messagebox.showerror("Error", f"No se encontró la ruta para el track ID {track_id}")
            return

        print(f"Guardando metadatos para: {os.path.basename(file_path)}")
        
        if not write_metadata_tags(file_path, new_metadata):
            messagebox.showwarning("Aviso", "Algunos tags no se pudieron escribir en el archivo.")

        for field, value in new_metadata.items():
            db.update_track_field(file_path, field, value)

        self.tracklist.refresh_track(track_id, new_metadata)
        messagebox.showinfo("Éxito", "Metadatos actualizados.")

    def _update_playback_progress(self, current_time_str, total_time_str, progress_percent):
        self.playback_panel.update_progress(current_time_str, total_time_str, progress_percent)

    def _play_next_track(self):
        next_track_data = self.tracklist.get_next_track_data()
        if next_track_data:
            player = self._get_or_create_player()
            self.tracklist.select_track_by_id(next_track_data['id'])
            player.play(next_track_data['file_path'])
            self.playback_panel.set_track_info(next_track_data)
            self.playback_panel.set_play_pause_state(True)
    
    def _play_prev_track(self):
        print("Funcionalidad de pista anterior no implementada.")

    def show_library_path_dialog(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.app_config.set('library_path', folder_selected)
            self.app_config.save()
            if messagebox.askyesno("Escanear", "¿Escanear la nueva carpeta ahora?"):
                self.start_library_scan(folder_selected)

    def start_library_scan(self, path):
        self.config(menu=self._create_menu(scanning=True))
        scanner = LibraryScanner(
            path, 
            on_complete_callback=self._on_scan_complete,
            progress_callback=self._on_scan_progress
        )
        scanner.start()

    def _on_scan_progress(self, message):
        self.status_bar.set_status(message)

    def _on_scan_complete(self):
        self._load_initial_data()
        self.status_bar.set_status(f"Librería actualizada con {self.tracklist.get_track_count()} pistas.")
        self.config(menu=self._create_menu(scanning=False))

    def _on_closing(self):
        self.app_config.set('window_geometry', self.geometry())
        self.app_config.save()
        if self.audio_player:
            self.audio_player.shutdown()
        self.destroy()

if __name__ == "__main__":
    db.init_db()
    app = MainApplication()
    app.mainloop()
