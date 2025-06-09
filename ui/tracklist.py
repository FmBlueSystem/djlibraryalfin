import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional

from core.database import DatabaseManager
from core.metadata_writer import write_all_metadata


def _format_time(seconds: float) -> str:
    """Formatea la duración de segundos a una cadena MM:SS."""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "--:--"
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes:02d}:{sec:02d}"


class Tracklist(ttk.Frame):
    def __init__(
        self,
        master: tk.Widget,
        db_manager: DatabaseManager,
        play_selected_track_callback: Callable,
    ) -> None:
        super().__init__(master)
        self.db_manager = db_manager
        self.play_selected_track_callback = play_selected_track_callback
        self.item_to_filepath: Dict[str, str] = {}

        self._create_widgets()
        self._create_context_menu()
        self.load_all_tracks()

    def _create_widgets(self) -> None:
        """Crea todos los widgets del panel, incluyendo la búsqueda."""
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=5, padx=5)

        search_label = ttk.Label(search_frame, text="Buscar:")
        search_label.pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill="x", expand=True)

        # --- Contenedor para Treeview y Scrollbar ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        self.tracklist_tree = ttk.Treeview(
            tree_frame,
            columns=(
                "title",
                "artist",
                "album",
                "duration",
                "bpm",
                "key",
                "energy",
                "energy_tag",
            ),
            show="headings",
        )
        self.tracklist_tree.pack(side="left", fill="both", expand=True)

        # --- Definir Encabezados y Columnas ---
        columns = {
            "title": ("Título", 250, True),
            "artist": ("Artista", 180, True),
            "album": ("Álbum", 180, True),
            "duration": ("Duración", 80, False),
            "bpm": ("BPM", 70, False),
            "key": ("Camelot", 80, False),
            "energy": ("Energía", 80, False),
            "energy_tag": ("Energía 2", 80, False),
        }

        for col, (text, width, stretch) in columns.items():
            self.tracklist_tree.heading(col, text=text)
            self.tracklist_tree.column(col, width=width, stretch=stretch)

        # Anclas de texto específicas
        self.tracklist_tree.column("duration", anchor="e")
        self.tracklist_tree.column("bpm", anchor="center")
        self.tracklist_tree.column("key", anchor="center")
        self.tracklist_tree.column("energy", anchor="center")
        self.tracklist_tree.column("energy_tag", anchor="center")

        # --- Eventos ---
        self.tracklist_tree.bind("<Double-1>", self._on_double_click)
        self.tracklist_tree.tag_configure("playing", background="#4A6984")

        # Vincular el menú contextual
        self.tracklist_tree.bind("<Button-3>", self._show_context_menu)

        # --- Widget de Edición ---
        self.edit_widget = None

    def _create_context_menu(self) -> None:
        """Crea el menú contextual para las pistas."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="Guardar Metadatos en Archivo", command=self._save_tags_to_file
        )

    def _show_context_menu(self, event: Any) -> None:
        """Muestra el menú contextual en la posición del cursor."""
        # Seleccionar el item bajo el cursor antes de mostrar el menú
        item_id = self.tracklist_tree.identify_row(event.y)
        if item_id:
            self.tracklist_tree.selection_set(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    def _save_tags_to_file(self) -> None:
        """Guarda los metadatos de la canción seleccionada en su archivo."""
        selected_path = self.get_selected_track_path()
        if not selected_path:
            messagebox.showwarning(
                "Ninguna Selección", "Por favor, selecciona una canción primero."
            )
            return

        track_data = self.db_manager.get_track_by_path(selected_path)
        if not track_data:
            messagebox.showerror(
                "Error", "No se pudieron encontrar los datos de la canción en la BD."
            )
            return

        # Construir el diccionario de metadatos para escribir
        metadata_to_write = {
            "title": track_data.get("title"),
            "artist": track_data.get("artist"),
            "album": track_data.get("album"),
            "bpm": track_data.get("bpm"),
            "key": track_data.get("key"),
            "energy": track_data.get(
                "energy_tag"
            ),  # Priorizamos el tag de energía manual
        }

        # Eliminar claves con valores nulos para no escribir basura
        metadata_to_write = {
            k: v for k, v in metadata_to_write.items() if v is not None
        }

        success = write_all_metadata(selected_path, metadata_to_write)

        if success:
            messagebox.showinfo(
                "Éxito", "Metadatos guardados correctamente en el archivo."
            )
        else:
            messagebox.showerror(
                "Error",
                "Ocurrió un error al guardar los metadatos en el archivo.",
            )

    def _on_double_click(self, event: Any) -> None:
        """Maneja el doble clic: reproduce o inicia la edición."""
        if self.edit_widget:
            # Si ya se está editando, no hacer nada
            return

        region = self.tracklist_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column_id = self.tracklist_tree.identify_column(event.x)
        item_id = self.tracklist_tree.focus()

        # El ID de columna es #N, donde N es un índice basado en 1
        column_index = int(column_id.replace("#", "")) - 1
        column_name = self.tracklist_tree["columns"][column_index]

        # Si se hace doble clic en la primera columna, reproducir.
        # Si no, editar.
        if column_index == 0:
            if self.play_selected_track_callback:
                self.play_selected_track_callback(event)
        else:
            self._start_editing(item_id, column_name)

    def _start_editing(self, item_id: str, column_name: str) -> None:
        """Inicia la edición de una celda específica."""
        # Obtener las dimensiones de la celda para superponer el widget
        x, y, width, height = self.tracklist_tree.bbox(item_id, column=column_name)

        # Obtener el valor actual
        current_values = self.tracklist_tree.item(item_id, "values")
        column_index = self.tracklist_tree["columns"].index(column_name)
        original_value = current_values[column_index]

        # Crear y posicionar el widget de entrada
        entry_var = tk.StringVar(value=original_value)
        self.edit_widget = ttk.Entry(self, textvariable=entry_var)
        self.edit_widget.place(x=x, y=y, width=width, height=height)
        self.edit_widget.focus_force()
        self.edit_widget.select_range(0, "end")

        # Vincular eventos
        self.edit_widget.bind(
            "<Return>",
            lambda e: self._save_edit(item_id, column_name, entry_var.get()),
        )
        self.edit_widget.bind("<Escape>", lambda e: self._cancel_edit())
        self.edit_widget.bind("<FocusOut>", lambda e: self._cancel_edit())

    def _save_edit(self, item_id: str, column_name: str, new_value: str) -> None:
        """Guarda el valor editado en la base de datos y actualiza la vista."""
        file_path = self.item_to_filepath.get(item_id)
        if not file_path:
            self._cancel_edit()
            return

        # Actualizar la base de datos
        self.db_manager.update_track_field(file_path, column_name, new_value)

        # Actualizar el Treeview
        current_values = list(self.tracklist_tree.item(item_id, "values"))
        column_index = self.tracklist_tree["columns"].index(column_name)
        current_values[column_index] = new_value
        self.tracklist_tree.item(item_id, values=tuple(current_values))

        self._cancel_edit()

    def _cancel_edit(self) -> None:
        """Cancela la edición y destruye el widget."""
        if self.edit_widget:
            self.edit_widget.destroy()
            self.edit_widget = None

    def _on_search(self, *args: Any) -> None:
        """Callback que se ejecuta cuando el texto de búsqueda cambia."""
        # Cancelar cualquier edición en curso antes de buscar
        self._cancel_edit()
        search_term = self.search_var.get()
        tracks = self.db_manager.search_tracks(search_term)
        self.load_tracks_from_db(tracks)

    def load_all_tracks(self) -> None:
        """Carga todas las pistas de la base de datos en el Treeview."""
        all_tracks = self.db_manager.get_all_tracks()
        self.load_tracks_from_db(all_tracks)

    def load_tracks_from_db(self, tracks: List[Dict[str, Any]]) -> None:
        """Limpia la tabla y la recarga con datos de la base de datos."""
        self.tracklist_tree.delete(*self.tracklist_tree.get_children())
        self.item_to_filepath.clear()

        for track in tracks:
            duration_str = _format_time(track.get("duration", 0))
            bpm_str = str(track.get("bpm", "")) if track.get("bpm") is not None else ""
            key_str = str(track.get("key", "")) if track.get("key") is not None else ""

            energy_val = track.get("energy")
            energy_str = f"{energy_val:.3f}" if isinstance(energy_val, float) else ""

            energy_tag_val = track.get("energy_tag")
            energy_tag_str = (
                f"{energy_tag_val:.3f}" if isinstance(energy_tag_val, float) else ""
            )

            values = (
                track.get("title", "Desconocido"),
                track.get("artist", "Desconocido"),
                track.get("album", "Desconocido"),
                duration_str,
                bpm_str,
                key_str,
                energy_str,
                energy_tag_str,
            )
            item_id = self.tracklist_tree.insert("", "end", values=values)
            if "file_path" in track:
                self.item_to_filepath[item_id] = track["file_path"]

    def get_selected_track_path(self) -> Optional[str]:
        """Devuelve la ruta del archivo de la pista seleccionada."""
        selected_items = self.tracklist_tree.selection()
        if not selected_items:
            return None
        selected_item_id = selected_items[0]
        return self.item_to_filepath.get(selected_item_id)

    def highlight_playing_track(self, index: Optional[int]) -> None:
        # Eliminar el tag 'playing' de cualquier item que lo tenga
        for item_id in self.tracklist_tree.get_children():
            tags = list(self.tracklist_tree.item(item_id, "tags"))
            if "playing" in tags:
                tags.remove("playing")
                self.tracklist_tree.item(item_id, tags=tags)

        # Aplicar el tag al nuevo item si hay un index
        if index is not None:
            children = self.tracklist_tree.get_children()
            if 0 <= index < len(children):
                item_id = children[index]
                tags = list(self.tracklist_tree.item(item_id, "tags"))
                tags.append("playing")
                self.tracklist_tree.item(item_id, tags=tags)

    def select_track_by_index(self, index: int) -> None:
        """Selecciona una pista en el Treeview por su índice."""
        all_items = self.tracklist_tree.get_children()
        if 0 <= index < len(all_items):
            item_id = all_items[index]
            self.tracklist_tree.selection_set(item_id)
            self.tracklist_tree.focus(item_id)
            self.tracklist_tree.see(item_id)

    def find_track_index_by_path(self, file_path: str) -> Optional[int]:
        """Encuentra el índice de una pista en el Treeview por su ruta de archivo."""
        for index, item_id in enumerate(self.tracklist_tree.get_children()):
            track_path = self.item_to_filepath.get(item_id)
            if track_path == file_path:
                return index
        return None
