# ui/metadata_panel.py

import tkinter as tk
from tkinter import ttk
from . import theme
from .widgets import HeaderLabel, StyledButton
from core.database import update_track_field
from core.metadata_writer import write_metadata_tag
from core import metadata_enricher
import threading

class MetadataPanel(ttk.Frame):
    """
    Un panel para mostrar y editar los metadatos de una pista seleccionada.
    """
    def __init__(self, master, on_save_callback=None, **kwargs):
        super().__init__(master, style="TFrame", **kwargs)
        self.grid_columnconfigure(1, weight=1)

        self.on_save_callback = on_save_callback
        self.current_track_data = None
        self.is_editing = False

        self.track_data_widgets = {} # Almacenará Labels y Entries
        self._create_widgets()

    def _create_widgets(self):
        """Crea las etiquetas y campos estáticos del panel."""
        HeaderLabel(self, text="Metadatos de la Pista").grid(row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")
        
        fields = {
            "title": "Título:", "artist": "Artista:", "album": "Álbum:",
            "genre": "Género:", "year": "Año:", "bpm": "BPM:", "key": "Tono:"
        }
        
        for i, (key, text) in enumerate(fields.items()):
            row_num = i + 1
            label = ttk.Label(self, text=text, font=theme.FONT_BOLD, anchor="e")
            label.grid(row=row_num, column=0, sticky="ne", padx=(10, 5), pady=5)
            
            value_widget = ttk.Label(self, text="N/A", font=theme.FONT_NORMAL, anchor="w", wraplength=250)
            value_widget.grid(row=row_num, column=1, sticky="nw", padx=(0, 10), pady=5)
            self.track_data_widgets[key] = value_widget
        
        # --- Botones ---
        button_frame = ttk.Frame(self, style="TFrame")
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.edit_button = StyledButton(button_frame, text="Editar", command=self._toggle_edit_mode)
        self.edit_button.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.save_button = StyledButton(button_frame, text="Guardar", command=self._save_changes)
        self.cancel_button = StyledButton(button_frame, text="Cancelar", command=self._toggle_edit_mode)
        
        self.edit_button.config(state="disabled")

        # Botón para enriquecer metadatos
        self.enrich_button = StyledButton(self, text="Enriquecer", command=self.enrich_metadata)
        self.enrich_button.grid(row=len(fields) + 2, column=0, columnspan=2, pady=5)
        self.enrich_button.config(state="disabled")

    def set_save_callback(self, callback):
        """Asigna una función que se llamará después de guardar los cambios."""
        self.on_save_callback = callback

    def display_track(self, track_data):
        """Muestra los metadatos de una pista y habilita la edición."""
        if self.is_editing:
            self._toggle_edit_mode() # Salir del modo edición si se cambia de pista

        self.current_track_data = track_data
        if not track_data:
            self.clear_panel()
            return

        for key, widget in self.track_data_widgets.items():
            value = track_data.get(key, "N/A")
            widget.config(text=str(value) if value else "N/A")
        
        # Habilitar botones solo si hay datos válidos
        self.edit_button.config(state="normal" if track_data else "disabled")
        can_enrich = track_data and track_data.get('artist') and track_data.get('title')
        self.enrich_button.config(state="normal" if can_enrich else "disabled")

    def clear_panel(self):
        """Limpia todos los campos y deshabilita los botones."""
        self.current_track_data = None
        for widget in self.track_data_widgets.values():
            widget.config(text="N/A")
        self.edit_button.config(state="disabled")
        self.enrich_button.config(state="disabled")

    def _toggle_edit_mode(self):
        """Cambia entre el modo de visualización y el modo de edición."""
        self.is_editing = not self.is_editing

        if self.is_editing:
            # --- Entrar en modo edición ---
            self.edit_button.grid_remove()
            self.save_button.grid(row=0, column=0, padx=5, sticky="ew")
            self.cancel_button.grid(row=0, column=1, padx=5, sticky="ew")

            for key, old_widget in self.track_data_widgets.items():
                row_info = old_widget.grid_info()
                old_widget.grid_remove()

                current_value = self.current_track_data.get(key, "")
                entry = ttk.Entry(self, font=theme.FONT_NORMAL)
                entry.insert(0, str(current_value))
                entry.grid(row=row_info['row'], column=row_info['column'], sticky="ew", padx=(0, 10), pady=2)
                self.track_data_widgets[key] = entry
        else:
            # --- Salir del modo edición (vista) ---
            self.save_button.grid_remove()
            self.cancel_button.grid_remove()
            self.edit_button.grid()

            for key, old_widget in self.track_data_widgets.items():
                row_info = old_widget.grid_info()
                old_widget.destroy() # Eliminar el Entry

                current_value = self.current_track_data.get(key, "N/A")
                label = ttk.Label(self, text=str(current_value), font=theme.FONT_NORMAL, anchor="w", wraplength=250)
                label.grid(row=row_info['row'], column=row_info['column'], sticky="nw", padx=(0, 10), pady=5)
                self.track_data_widgets[key] = label
    
    def _save_changes(self):
        """Recopila los datos de los campos de entrada y llama al callback para guardarlos."""
        if not self.current_track_data:
            return

        new_metadata = {}
        for key, widget in self.track_data_widgets.items():
            if isinstance(widget, ttk.Entry):
                new_value = widget.get()
                # Comparar con el valor original para ver si hubo cambios
                if str(new_value) != str(self.current_track_data.get(key, "")):
                    new_metadata[key] = new_value
        
        if new_metadata: # Solo guardar si hubo cambios
            track_id = self.current_track_data.get('id')
            if self.on_save_callback:
                self.on_save_callback(track_id, new_metadata)
            
            # Actualizar el diccionario de datos interno para reflejar los cambios
            self.current_track_data.update(new_metadata)
        
        # Salir siempre del modo edición, haya habido cambios o no
        self._toggle_edit_mode()

    def enrich_metadata(self):
        """
        Inicia el enriquecimiento de metadatos en un hilo separado para no bloquear la UI.
        """
        if not self.current_track_data:
            return

        artist = self.current_track_data.get('artist')
        title = self.current_track_data.get('title')

        if not artist or not title:
            # Esta comprobación es una salvaguarda. El botón ya debería estar deshabilitado.
            print("Error: No se puede enriquecer sin artista y título.")
            return
            
        print(f"Iniciando enriquecimiento para: {artist} - {title}")
        self.enrich_button.config(state="disabled")

        def _enrich_and_update():
            # Esta función se ejecuta en un hilo nuevo
            enriched_data = metadata_enricher.enrich_metadata(self.current_track_data)
            
            # Para actualizar la UI, volvemos al hilo principal
            self.after(0, self.update_fields_with_enriched_data, enriched_data)

        # Crear y empezar el hilo
        threading.Thread(target=_enrich_and_update, daemon=True).start()

    def update_fields_with_enriched_data(self, enriched_data):
        """
        Callback que se ejecuta cuando el enriquecedor termina.
        Rellena los campos de entrada (Entry) con los datos encontrados.
        """
        print("Enriquecimiento completado. Actualizando campos de edición.")
        
        if enriched_data:
            for key, widget in self.track_data_widgets.items():
                # Asegurarse de que el widget es un campo de texto editable
                if isinstance(widget, ttk.Entry):
                    # Solo rellenar si el campo está vacío y tenemos un dato para él
                    if not widget.get() and key in enriched_data:
                        widget.delete(0, tk.END)
                        widget.insert(0, str(enriched_data[key]))
        else:
            print("No se encontraron datos de enriquecimiento.")

        # Rehabilitar los botones
        self.enrich_button.config(state="normal")
        self.save_button.config(state="normal") 