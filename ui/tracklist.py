import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional


class Tracklist(ttk.Frame):
    def __init__(self, parent: tk.Widget, on_double_click: Callable[[Any], None]):
        super().__init__(parent)

        self.on_double_click_callback = on_double_click
        self.item_to_filepath: Dict[str, str] = {}
        
        self.column_definitions: Dict[str, Dict[str, Any]] = {
            "title": {"text": "Título", "width": 250},
            "artist": {"text": "Artista", "width": 150},
            "album": {"text": "Álbum", "width": 150},
            "duration": {"text": "Duración", "width": 80},
            "bpm": {"text": "BPM", "width": 60},
            "key": {"text": "Tonalidad", "width": 80},
            "genre": {"text": "Género", "width": 100},
            "file_type": {"text": "Tipo", "width": 50},
        }
        self.column_keys = list(self.column_definitions.keys())

        self.tracklist_tree = ttk.Treeview(
            self, columns=self.column_keys, show="headings"
        )
        
        for col, props in self.column_definitions.items():
            self.tracklist_tree.heading(col, text=props["text"])
            self.tracklist_tree.column(col, width=props["width"], minwidth=50, stretch=tk.YES)

        self.tracklist_tree.tag_configure("playing", background="#2C3E50", foreground="white")
        self.tracklist_tree.bind("<Double-1>", self.on_double_click_callback)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tracklist_tree.yview)
        self.tracklist_tree.configure(yscrollcommand=scrollbar.set)

        self.tracklist_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _format_duration(self, seconds: Any) -> str:
        try:
            seconds_float = float(seconds)
            if seconds_float < 0:
                return "00:00"
            minutes, sec = divmod(int(seconds_float), 60)
            return f"{minutes:02d}:{sec:02d}"
        except (ValueError, TypeError):
            return "00:00"

    def load_tracks_from_db(self, tracks: List[Dict[str, Any]]) -> None:
        """Limpia la tabla y la recarga con datos de la base de datos."""
        for i in self.tracklist_tree.get_children():
            self.tracklist_tree.delete(i)
        self.item_to_filepath.clear()

        for track in tracks:
            track["duration"] = self._format_duration(track.get("duration"))
            values = [track.get(col, "N/A") for col in self.column_keys]
            item_id = self.tracklist_tree.insert("", "end", values=values)
            self.item_to_filepath[item_id] = track.get("file_path", "")

    def get_selected_track_path(self) -> Optional[str]:
        """Devuelve la ruta del archivo de la pista seleccionada."""
        selected_items = self.tracklist_tree.selection()
        if not selected_items:
            return None
        selected_item_id = selected_items[0]
        return self.item_to_filepath.get(selected_item_id)

    def highlight_playing_track(self, track_index: Optional[int]) -> None:
        """Resalta la fila de la pista que se está reproduciendo actualmente."""
        # Limpiar resaltado anterior
        for item_id in self.tracklist_tree.get_children():
            self.tracklist_tree.item(item_id, tags=())

        if track_index is not None:
            all_items = self.tracklist_tree.get_children()
            if 0 <= track_index < len(all_items):
                item_to_highlight = all_items[track_index]
                self.tracklist_tree.item(item_to_highlight, tags=("playing",))
    
    def select_track_by_index(self, index: int) -> None:
        """Selecciona una pista en el Treeview por su índice."""
        all_items = self.tracklist_tree.get_children()
        if 0 <= index < len(all_items):
            item_id = all_items[index]
            self.tracklist_tree.selection_set(item_id)
            self.tracklist_tree.focus(item_id)
            self.tracklist_tree.see(item_id)
