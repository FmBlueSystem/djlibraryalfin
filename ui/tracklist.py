import tkinter as tk
from tkinter import ttk
from core.database import get_all_tracks, update_track_field
from core.metadata_writer import write_metadata_tag
from core.metadata_reader import read_metadata
from ui import theme

class Tracklist(ttk.Frame):
    """
    Un widget Frame que contiene un Treeview para mostrar la lista de pistas
    y maneja la interacción del usuario como la edición y el menú contextual.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.tree = ttk.Treeview(self, style="Treeview")
        self._setup_widgets()
        # La carga de datos se hará desde MainApplication

    def _setup_widgets(self):
        """Configura las columnas, el layout y los bindings del Treeview."""
        self.columns = {
            "id": ("ID", 30), "title": ("Título", 250), "artist": ("Artista", 200),
            "album": ("Álbum", 200), "genre": ("Género", 120), "year": ("Año", 60),
            "duration": ("Tiempo", 70), "bpm": ("BPM", 50), "key": ("Tono", 50), 
            "file_path": ("Ruta", 0) # Oculta
        }
        
        self.tree["columns"] = list(self.columns.keys())
        self.tree["displaycolumns"] = [col for col in self.columns if col != 'file_path' and col != 'id']
        self.tree["show"] = "headings"

        for col, (text, width) in self.columns.items():
            self.tree.heading(col, text=text, anchor=tk.W)
            self.tree.column(col, width=width, anchor=tk.W, stretch=tk.NO)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def bind_on_select(self, callback):
        """Vincula un callback al evento de selección de una fila."""
        def _callback_wrapper(event):
            data = self.get_selected_track_data()
            if data:
                callback(data)
        self.tree.bind("<<TreeviewSelect>>", _callback_wrapper)

    def bind_on_double_click(self, callback):
        """Vincula un callback al evento de doble clic en una fila."""
        def _callback_wrapper(event):
            # Comprobar que el doble clic fue en una celda para evitar activar en el encabezado
            region = self.tree.identify_region(event.x, event.y)
            if region == "cell":
                data = self.get_selected_track_data()
                if data:
                    callback(data)
        self.tree.bind("<Double-1>", _callback_wrapper)

    def _format_duration(self, seconds):
        """Formatea la duración de segundos a una cadena MM:SS."""
        try:
            seconds = float(seconds)
            minutes, sec = divmod(int(seconds), 60)
            return f"{minutes:02d}:{sec:02d}"
        except (ValueError, TypeError):
            return "00:00"

    def populate(self, tracks):
        """(Re)Carga los datos desde una lista de diccionarios en el Treeview."""
        # Limpiar vista anterior
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        for track in tracks:
            values = [
                track.get('id', ''),
                track.get('title', 'N/A'),
                track.get('artist', 'N/A'),
                track.get('album', 'N/A'),
                track.get('genre', 'N/A'),
                track.get('year', ''),
                self._format_duration(track.get('duration')),
                track.get('bpm', ''),
                track.get('key', ''),
                track.get('file_path', '')
            ]
            self.tree.insert("", "end", values=values, iid=track.get('id'))
    
    def refresh_track(self, track_id, new_data):
        """Actualiza una fila específica en el Treeview con nuevos datos."""
        item_id = str(track_id)
        
        # Formatear los valores en el orden correcto de las columnas
        values_dict = {col: new_data.get(col, '') for col in self.columns}
        values_dict['duration'] = self._format_duration(new_data.get('duration'))
        
        # Convertir a lista en el orden correcto
        final_values = [values_dict.get(col_id, '') for col_id in self.columns]
        
        self.tree.item(item_id, values=final_values)

    def get_selected_track_id(self):
        """Devuelve el ID de la pista seleccionada, o None si no hay selección."""
        selected_item = self.tree.focus()
        if selected_item:
            return self.tree.item(selected_item, "values")[0]
        return None

    def get_selected_track_data(self):
        """Devuelve un diccionario con los datos de la pista seleccionada."""
        selected_item = self.tree.focus()
        if not selected_item:
            return None
        
        values = self.tree.item(selected_item, "values")
        # Asegurarse de que el ID es un entero para la búsqueda
        track_id = int(values[0])
        track_data = self.get_track_data_by_id(track_id)
        return track_data

    def get_track_data_by_id(self, track_id):
        """Busca los datos de una pista en el treeview por su ID."""
        try:
            item_values = self.tree.item(str(track_id), "values")
            return {col: item_values[i] for i, col in enumerate(self.columns)}
        except tk.TclError:
            return None # El item no existe

    def get_next_track_data(self):
        """Devuelve los datos de la siguiente pista en la lista."""
        selected_item = self.tree.focus()
        if not selected_item:
            return None
        
        next_item = self.tree.next(selected_item)
        if not next_item:
            return None # No hay siguiente
            
        values = self.tree.item(next_item, "values")
        return {col: values[i] for i, col in enumerate(self.columns)}

    def get_previous_track_data(self):
        """Devuelve los datos de la pista anterior en la lista."""
        selected_item = self.tree.focus()
        if not selected_item:
            return None
            
        prev_item = self.tree.prev(selected_item)
        if not prev_item:
            return None # No hay anterior

        values = self.tree.item(prev_item, "values")
        return {col: values[i] for i, col in enumerate(self.columns)}

    def select_track_by_id(self, track_id):
        """Selecciona una pista en el Treeview por su ID."""
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == track_id:
                self.tree.selection_set(item)
                self.tree.see(item)
                break

    def add_track(self, track_data):
        """Añade una única pista al final de la lista."""
        values = [
            track_data.get('id', ''),
            track_data.get('title', 'N/A'),
            track_data.get('artist', 'N/A'),
            track_data.get('album', 'N/A'),
            track_data.get('genre', 'N/A'),
            track_data.get('year', ''),
            self._format_duration(track_data.get('duration')),
            track_data.get('bpm', ''),
            track_data.get('key', ''),
            track_data.get('file_path', '')
        ]
        self.tree.insert("", "end", values=values)