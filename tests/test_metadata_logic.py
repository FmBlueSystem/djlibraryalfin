import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch

# Se necesita una instancia de la app para inicializar los estilos de ttk
# pero no necesitamos mostrarla.
root = tk.Tk()
root.withdraw()

from ui.metadata_panel import MetadataPanel

class TestMetadataPanelLogic(unittest.TestCase):

    def setUp(self):
        """Crea una instancia del panel para cada prueba."""
        self.mock_on_save = MagicMock()
        self.panel = MetadataPanel(root, on_save_callback=self.mock_on_save)

    @patch('ui.metadata_panel.update_track_field')
    @patch('ui.metadata_panel.write_metadata_tag')
    def test_save_changes_logic(self, mock_write_tag, mock_update_db):
        """
        Prueba la lógica de guardado del panel de metadatos.
        """
        # 1. Cargar datos de prueba en el panel
        initial_data = {
            'file_path': '/fake/song.mp3',
            'title': 'Old Title',
            'artist': 'Old Artist',
            'album': 'Old Album',
            'genre': '', # Campo vacío
            'year': '2023',
            'bpm': '120',
            'key': 'C'
        }
        self.panel.display_track(initial_data)

        # 2. Entrar en modo edición
        self.panel._toggle_edit_mode()

        # 3. Simular la edición de los campos (Entries)
        self.panel.track_data_widgets['title'].delete(0, tk.END)
        self.panel.track_data_widgets['title'].insert(0, 'New Title')
        
        self.panel.track_data_widgets['artist'].delete(0, tk.END)
        self.panel.track_data_widgets['artist'].insert(0, 'New Artist')
        
        # 4. Simular el clic en "Guardar"
        self.panel._save_changes()

        # --- Verificaciones ---
        # 5. Comprobar que solo se llamó a las funciones de guardado para los campos que cambiaron.
        self.assertEqual(mock_write_tag.call_count, 2)
        self.assertEqual(mock_update_db.call_count, 2)
        
        # Verificar llamadas para 'title'
        mock_write_tag.assert_any_call('/fake/song.mp3', 'title', 'New Title')
        mock_update_db.assert_any_call('/fake/song.mp3', 'title', 'New Title')
        
        # Verificar llamadas para 'artist'
        mock_write_tag.assert_any_call('/fake/song.mp3', 'artist', 'New Artist')
        mock_update_db.assert_any_call('/fake/song.mp3', 'artist', 'New Artist')

        # 6. Comprobar que el callback de guardado fue llamado una vez.
        self.mock_on_save.assert_called_once()

        # 7. Verificar que el panel salió del modo de edición.
        self.assertFalse(self.panel.is_editing)
        # Y que el widget de título ahora es una Label
        self.assertIsInstance(self.panel.track_data_widgets['title'], tk.Label)
        # Y que el texto de la label se actualizó
        self.assertEqual(self.panel.track_data_widgets['title'].cget("text"), 'New Title')


if __name__ == '__main__':
    unittest.main() 