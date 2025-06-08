import tkinter as tk
from tkinter import ttk
from typing import Any, List, Dict, Optional, Callable


class SuggestionPanel(ttk.Frame):
    def __init__(self, master: tk.Widget, *, play_track_callback: Optional[Callable[[str], None]] = None, **kwargs: Any):
        super().__init__(master, **kwargs)
        self.play_track_callback = play_track_callback

        # Configurar estilo para el Treeview
        style = ttk.Style(self)
        style.configure("Suggestion.Treeview", rowheight=40) # Aumentar altura de fila

        self.tree = ttk.Treeview(
            self,
            columns=("reason", "title", "artist"),
            show="headings",
            style="Suggestion.Treeview"
        )
        self.tree.pack(fill="both", expand=True)

        self.tree.heading("reason", text="Razón")
        self.tree.heading("title", text="Título")
        self.tree.heading("artist", text="Artista")

        self.tree.column("reason", width=150, stretch=False)
        self.tree.column("title", width=200)
        self.tree.column("artist", width=150)
        
        self.tree.bind("<Double-1>", self._on_double_click)
        
        self.suggestions_data: List[Dict[str, Any]] = []

    def _on_double_click(self, event: Any) -> None:
        """Reproduce la pista seleccionada al hacer doble clic."""
        selected_item = self.tree.focus()
        if not selected_item:
            return
            
        item_index = self.tree.index(selected_item)
        track_info = self.suggestions_data[item_index]
        
        if self.play_track_callback and "file_path" in track_info:
            self.play_track_callback(track_info["file_path"])


    def set_suggestions(self, suggestions: List[Dict[str, Any]]) -> None:
        """Limpia el panel y muestra las nuevas sugerencias."""
        # Limpiar vista anterior
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        self.suggestions_data = suggestions

        # Poblar con nuevas sugerencias
        for suggestion in suggestions:
            reason = suggestion.get("reason", "N/A")
            title = suggestion.get("title", "N/A")
            artist = suggestion.get("artist", "N/A")
            
            self.tree.insert("", "end", values=(reason, title, artist))

    def clear(self) -> None:
        """Limpia el panel de sugerencias."""
        self.set_suggestions([]) 