import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

from core.database import get_all_tracks, update_track_field
from core.metadata_reader import read_metadata


class Tracklist(ttk.Treeview):
    def __init__(
        self,
        master: tk.Widget,
        *,
        track_select_callback: Optional[Callable[[str], None]] = None,
        track_play_callback: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)

        self.track_select_callback = track_select_callback
        self.track_play_callback = track_play_callback
        self.item_to_filepath: Dict[str, str] = (
            {}
        )  # Diccionario para mapear item_id a file_path
        self.currently_playing_item: Optional[str] = None
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
        self.column_definitions_keys: List[str] = list(self.column_definitions.keys())

        self.configure_columns()
        self.load_data()

    def configure_columns(self) -> None:
        """Configura las columnas del Treeview."""
        self["columns"] = self.column_definitions_keys
        self["show"] = "headings"  # Ocultar la primera columna fantasma

        for col, props in self.column_definitions.items():
            self.heading(col, text=props["text"])
            self.column(col, width=props["width"], minwidth=50, stretch=tk.YES)

        # Configurar un tag para resaltar la fila en reproducción
        # Color distintivo para resaltar la canción en reproducción
        self.tag_configure("playing", background="#007ACC", foreground="white")

        self.bind("<Double-1>", self.on_double_click)
        self.bind("<<TreeviewSelect>>", self.on_track_select)
        self.bind("<Button-3>", self.show_context_menu)  # Clic derecho (estándar)
        self.bind("<Button-2>", self.show_context_menu)  # Clic derecho (común en macOS)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="Re-escanear metadatos del archivo",
            command=self.rescan_selected_track,
        )

    # Navegación ------------------------------------------------------------
    def get_current_file_path(self) -> Optional[str]:
        """Devuelve la ruta del archivo del elemento enfocado."""
        item_id = self.focus()
        return self.item_to_filepath.get(item_id) if item_id else None

    def select_next(self) -> Optional[str]:
        """Selecciona la siguiente fila y devuelve su ruta."""
        items = list(self.get_children())
        if not items:
            return None

        current = self.focus()
        if current in items:
            idx = items.index(current)
            next_idx = min(idx + 1, len(items) - 1)
        else:
            next_idx = 0

        next_item = items[next_idx]
        self.selection_set(next_item)
        self.focus(next_item)
        return self.item_to_filepath.get(next_item)

    def select_previous(self) -> Optional[str]:
        """Selecciona la fila anterior y devuelve su ruta."""
        items = list(self.get_children())
        if not items:
            return None

        current = self.focus()
        if current in items:
            idx = items.index(current)
            prev_idx = max(idx - 1, 0)
        else:
            prev_idx = len(items) - 1

        prev_item = items[prev_idx]
        self.selection_set(prev_item)
        self.focus(prev_item)
        return self.item_to_filepath.get(prev_item)

    def on_track_select(self, event: tk.Event) -> None:
        """Se llama cuando un usuario selecciona una pista en la lista."""
        selected_item = self.focus()
        if not selected_item:
            return

        file_path = self.item_to_filepath.get(selected_item)
        if file_path and self.track_select_callback:
            self.track_select_callback(file_path)

    def show_context_menu(self, event: tk.Event) -> None:
        """Muestra el menú contextual en la posición del cursor."""
        item_id = self.identify_row(event.y)
        if item_id:
            self.selection_set(item_id)
            self.focus(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    def rescan_selected_track(self) -> None:
        """Re-escanea los metadatos de la pista seleccionada y actualiza la DB y la UI."""
        selected_item = self.focus()
        if not selected_item:
            return

        file_path = self.item_to_filepath.get(selected_item)
        if not file_path:
            print(f"Error: No se encontró la ruta para el item {selected_item}")
            return

        print(f"Re-escaneando metadatos para: {file_path}")
        new_metadata = read_metadata(file_path)

        if new_metadata:
            # Actualizar cada campo en la base de datos
            for field, value in new_metadata.items():
                # Solo actualizamos los campos que están en nuestra tabla
                if (
                    field in self.column_definitions or field == "comment"
                ):  # Incluir comentario aunque no se vea
                    update_track_field(file_path, field, value)

            # Recargar la fila en el Treeview
            self.load_data()  # Manera más simple de asegurar la consistencia visual
            print("Metadatos actualizados y vista refrescada.")
        else:
            print("No se pudieron leer los nuevos metadatos.")

    def _format_duration(self, seconds: Any) -> str:
        """Formatea la duración de segundos a una cadena MM:SS."""
        try:
            # Asegurarse de que los segundos sean un número válido
            seconds_float = float(seconds)
            if seconds_float < 0:
                return "00:00"
            minutes, sec = divmod(int(seconds_float), 60)
            return f"{minutes:02d}:{sec:02d}"
        except (ValueError, TypeError):
            return "00:00"  # Devolver un valor por defecto si la conversión falla

    def on_double_click(self, event: tk.Event) -> None:
        """Manejador para el evento de doble clic, inicia la reproducción."""
        selected_item = self.focus()
        if not selected_item:
            return

        file_path = self.item_to_filepath.get(selected_item)
        if file_path and self.track_play_callback:
            self.track_play_callback(file_path)

    def set_playing_track(self, file_path: Optional[str]) -> None:
        """Resalta la fila correspondiente al archivo que se está reproduciendo."""
        # Quitar el resaltado del item anterior
        if self.currently_playing_item:
            self.item(self.currently_playing_item, tags=())

        if file_path is None:
            self.currently_playing_item = None
            return

        # Encontrar el nuevo item y resaltarlo
        for item_id, path in self.item_to_filepath.items():
            if path == file_path:
                self.item(item_id, tags=("playing",))
                self.currently_playing_item = item_id
                break

    def load_data(self) -> None:
        """Limpia la tabla y la recarga con datos de la base de datos."""
        # Guardar la ruta del archivo que se está reproduciendo para no perder el resaltado
        playing_path = None
        if self.currently_playing_item:
            playing_path = self.item_to_filepath.get(self.currently_playing_item)

        for i in self.get_children():
            self.delete(i)
        self.item_to_filepath.clear()

        tracks = get_all_tracks()
        for track in tracks:
            track["duration"] = self._format_duration(track.get("duration"))
            values = [track.get(col, "N/A") for col in self.column_definitions_keys]
            item_id = self.insert("", "end", values=values)
            self.item_to_filepath[item_id] = track.get("file_path", "")

        # Restaurar el resaltado si la pista sigue en la lista
        if playing_path:
            self.set_playing_track(playing_path)
