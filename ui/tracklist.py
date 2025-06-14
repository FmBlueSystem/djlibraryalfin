import tkinter as tk
from tkinter import ttk
from core.database import get_all_tracks, update_track_field
from core.metadata_writer import write_metadata_tag
from core.metadata_reader import read_metadata

class Tracklist(ttk.Treeview):
    def __init__(self, master, waveform_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.waveform_callback = waveform_callback
        
        self.item_to_filepath = {} # Diccionario para mapear item_id a file_path
        self.column_definitions = {
            "title": {"text": "Título", "width": 250},
            "artist": {"text": "Artista", "width": 150},
            "album": {"text": "Álbum", "width": 150},
            "duration": {"text": "Duración", "width": 80},
            "bpm": {"text": "BPM", "width": 60},
            "key": {"text": "Tonalidad", "width": 80},
            "genre": {"text": "Género", "width": 100},
            "file_type": {"text": "Tipo", "width": 50}
        }

        self.configure_columns()
        self.load_data()

    def configure_columns(self):
        """Configura las columnas del Treeview."""
        columns = list(self.column_definitions.keys())
        self["columns"] = columns
        self["show"] = "headings"  # Ocultar la primera columna fantasma

        for col, props in self.column_definitions.items():
            self.heading(col, text=props["text"])
            self.column(col, width=props["width"], minwidth=50, stretch=tk.YES)

        self.bind("<Double-1>", self.on_double_click)
        self.bind("<Button-3>", self.show_context_menu) # Clic derecho (estándar)
        self.bind("<Button-2>", self.show_context_menu) # Clic derecho (común en macOS)
        self.bind("<<TreeviewSelect>>", self.on_track_select)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Re-escanear metadatos del archivo", command=self.rescan_selected_track)

    def show_context_menu(self, event):
        """Muestra el menú contextual en la posición del cursor."""
        # Seleccionar el item bajo el cursor
        item_id = self.identify_row(event.y)
        if item_id:
            self.selection_set(item_id)
            self.focus(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    def on_track_select(self, event):
        """Se llama cuando se selecciona una pista. Llama al callback para actualizar la forma de onda."""
        selected_item = self.focus()
        if not selected_item:
            return

        file_path = self.item_to_filepath.get(selected_item)
        if file_path and self.waveform_callback:
            self.waveform_callback(file_path)

    def rescan_selected_track(self):
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
                if field in self.column_definitions or field == "comment": # Incluir comentario aunque no se vea
                    update_track_field(file_path, field, value)
            
            # Recargar la fila en el Treeview
            self.load_data() # Manera más simple de asegurar la consistencia visual
            print("Metadatos actualizados y vista refrescada.")
        else:
            print("No se pudieron leer los nuevos metadatos.")

    def _format_duration(self, seconds):
        """Formatea la duración de segundos a una cadena MM:SS."""
        try:
            # Asegurarse de que los segundos sean un número válido
            seconds = float(seconds)
            if seconds < 0:
                return "00:00"
            minutes, sec = divmod(int(seconds), 60)
            return f"{minutes:02d}:{sec:02d}"
        except (ValueError, TypeError):
            return "00:00" # Devolver un valor por defecto si la conversión falla

    def on_double_click(self, event):
        """Manejador para el evento de doble clic, permite editar una celda."""
        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return

        column_id = self.identify_column(event.x)
        column_index = int(column_id.replace("#", "")) - 1
        item_id = self.focus()
        
        if not item_id:
            return

        # Obtener las coordenadas de la celda
        x, y, width, height = self.bbox(item_id, column_id)
        
        # Obtener el valor actual
        current_value = self.item(item_id, "values")[column_index]

        # Crear un widget de entrada de texto temporal
        entry = ttk.Entry(self.master, justify="left")
        entry.place(x=x, y=y, width=width, height=height)
        
        entry.insert(0, current_value)
        entry.select_range(0, "end")
        entry.focus_set()

        def save_edit(event):
            new_value = entry.get()
            
            # Obtener la ruta del archivo desde nuestro mapeo
            file_path = self.item_to_filepath.get(item_id)
            if not file_path:
                print("Error: No se pudo encontrar la ruta del archivo para este item.")
                entry.destroy()
                return

            column_name = list(self.column_definitions.keys())[column_index]
            
            # 1. Escribir en el archivo de audio
            success_write = write_metadata_tag(file_path, column_name, new_value)
            
            # 2. Si la escritura fue exitosa, actualizar la base de datos
            if success_write:
                update_track_field(file_path, column_name, new_value)
                # 3. Actualizar el valor en el Treeview
                self.set(item_id, column_id, new_value)
            
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())
        entry.bind("<Escape>", lambda e: entry.destroy())

    def load_data(self):
        """Limpia la tabla y la recarga con datos de la base de datos."""
        # Limpiar datos existentes
        for i in self.get_children():
            self.delete(i)
        
        self.item_to_filepath.clear() # Limpiar el mapeo
            
        # Cargar nuevos datos
        tracks = get_all_tracks()
        # Guardar las claves de las columnas en el orden correcto para referencia futura
        self.column_definitions_keys = list(self.column_definitions.keys())
        for track in tracks:
            # Formatear la duración antes de mostrarla
            track['duration'] = self._format_duration(track.get('duration'))
            values = [track.get(col, "N/A") for col in self.column_definitions_keys]
            item_id = self.insert("", "end", values=values)
            self.item_to_filepath[item_id] = track.get('file_path') 