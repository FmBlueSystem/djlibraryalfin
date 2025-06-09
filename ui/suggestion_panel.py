import tkinter as tk
from tkinter import ttk
from typing import Any, List, Dict, Optional, Callable

from core.database import DatabaseManager
from core.dj_utils import get_compatible_camelot_keys


class SuggestionPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Widget,
        db_manager: DatabaseManager,
        *,
        play_track_callback: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ):
        super().__init__(master, **kwargs)
        self.db_manager = db_manager
        self.play_track_callback = play_track_callback
        self.current_track_path: Optional[str] = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Crea los widgets del panel, incluyendo los filtros."""
        # --- Frame para los filtros ---
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=5, padx=5)

        self.suggestion_mode = tk.StringVar(value="bpm")  # Valor por defecto

        bpm_button = ttk.Radiobutton(
            filter_frame,
            text="BPM",
            variable=self.suggestion_mode,
            value="bpm",
            command=self.update_suggestions,
        )
        bpm_button.pack(side="left", padx=5)

        key_button = ttk.Radiobutton(
            filter_frame,
            text="Armónica",
            variable=self.suggestion_mode,
            value="key",
            command=self.update_suggestions,
        )
        key_button.pack(side="left", padx=5)

        energy_button = ttk.Radiobutton(
            filter_frame,
            text="Energía",
            variable=self.suggestion_mode,
            value="energy",
            command=self.update_suggestions,
        )
        energy_button.pack(side="left", padx=5)

        # --- Treeview para mostrar resultados ---
        self.tree = ttk.Treeview(
            self,
            columns=("diff", "bpm", "key", "title", "artist"),
            show="headings",
            style="Suggestion.Treeview",
        )
        self.tree.pack(fill="both", expand=True)

        self.tree.heading("diff", text="+/-%")
        self.tree.heading("bpm", text="BPM")
        self.tree.heading("key", text="Tonalidad")
        self.tree.heading("title", text="Título")
        self.tree.heading("artist", text="Artista")

        self.tree.column("diff", width=60, stretch=False, anchor="center")
        self.tree.column("bpm", width=70, stretch=False, anchor="center")
        self.tree.column("key", width=90, stretch=False, anchor="center")
        self.tree.column("title", width=150)
        self.tree.column("artist", width=120)

        self.tree.bind("<Double-1>", self._on_double_click)

        self.suggestions_data: List[Dict[str, Any]] = []

    def update_suggestions(self, current_track_path: Optional[str] = None) -> None:
        """Busca y muestra sugerencias para la pista actual según el modo."""
        if current_track_path:
            self.current_track_path = current_track_path

        if not self.current_track_path:
            self.clear()
            return

        current_track = self.db_manager.get_track_by_path(self.current_track_path)
        if not current_track:
            self.clear()
            return

        mode = self.suggestion_mode.get()
        suggestions = []
        target_bpm = current_track.get("bpm")

        if mode == "bpm" and target_bpm:
            suggestions = self.db_manager.get_tracks_by_bpm_range(target_bpm)
        elif mode == "key":
            current_key = current_track.get("key")
            if current_key and target_bpm:
                compatible_keys = get_compatible_camelot_keys(current_key)
                suggestions = self.db_manager.get_tracks_by_compatible_keys(
                    compatible_keys, target_bpm=target_bpm
                )
        elif mode == "energy":
            current_energy = current_track.get("energy")
            if current_energy is not None and target_bpm:
                suggestions = self.db_manager.get_tracks_by_energy_range(
                    current_energy, target_bpm=target_bpm
                )

        # Excluir la canción actual de las sugerencias
        suggestions = [
            s for s in suggestions if s["file_path"] != self.current_track_path
        ]

        self.set_suggestions(suggestions, target_bpm)

    def _on_double_click(self, event: Any) -> None:
        """Reproduce la pista seleccionada al hacer doble clic."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        item_index = self.tree.index(selected_item)
        track_info = self.suggestions_data[item_index]

        if self.play_track_callback and "file_path" in track_info:
            self.play_track_callback(track_info["file_path"])

    def set_suggestions(
        self, suggestions: List[Dict[str, Any]], target_bpm: Optional[float]
    ) -> None:
        """Limpia el panel y muestra las nuevas sugerencias."""
        self.clear()
        self.suggestions_data = suggestions

        for suggestion in suggestions:
            sugg_bpm = suggestion.get("bpm")

            diff_str = ""
            if sugg_bpm and target_bpm:
                diff_percent = ((sugg_bpm / target_bpm) - 1) * 100
                diff_str = f"{diff_percent:+.1f}%"

            bpm = sugg_bpm if sugg_bpm else "N/A"
            key = suggestion.get("key", "N/A")
            title = suggestion.get("title", "N/A")
            artist = suggestion.get("artist", "N/A")

            self.tree.insert("", "end", values=(diff_str, bpm, key, title, artist))

    def clear(self) -> None:
        """Limpia el panel de sugerencias."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.suggestions_data = []
