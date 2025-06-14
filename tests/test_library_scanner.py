import unittest
from unittest.mock import patch
import os
import tempfile
import shutil
from core import library_scanner

class TestLibraryScanner(unittest.TestCase):

    def setUp(self):
        """Crea un directorio temporal para las pruebas."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Elimina el directorio temporal después de las pruebas."""
        shutil.rmtree(self.test_dir)

    @patch('core.library_scanner.add_track')
    @patch('core.library_scanner.read_metadata')
    def test_scan_directory_resilience(self, mock_read_metadata, mock_add_track):
        """
        Prueba que el escáner ignora archivos no soportados y maneja
        errores de lectura en archivos soportados sin detenerse.
        """
        # --- Configuración ---
        good_file_path = os.path.join(self.test_dir, "good_song.mp3")
        bad_mp3_path = os.path.join(self.test_dir, "bad.mp3")
        irrelevant_file_path = os.path.join(self.test_dir, "document.txt")
        
        with open(good_file_path, "w") as f: f.write("good")
        with open(bad_mp3_path, "w") as f: f.write("bad")
        with open(irrelevant_file_path, "w") as f: f.write("text")
        
        # Configurar el mock: si lee el archivo bueno, devuelve metadatos.
        # Si lee el archivo .mp3 malo, devuelve None (simulando fallo de lectura).
        def read_metadata_side_effect(path):
            if path == good_file_path:
                return {'title': 'Good Song'}
            elif path == bad_mp3_path:
                # Simula un error que hace que la función devuelva None
                return None
            return None # Por defecto
            
        mock_read_metadata.side_effect = read_metadata_side_effect

        # --- Ejecución ---
        library_scanner.scan_directory(self.test_dir)

        # --- Verificación ---
        # 1. read_metadata debe ser llamado para los dos .mp3, pero no para el .txt
        self.assertEqual(mock_read_metadata.call_count, 2)
        mock_read_metadata.assert_any_call(good_file_path)
        mock_read_metadata.assert_any_call(bad_mp3_path)
        
        # 2. add_track SOLO debe ser llamado para el archivo bueno.
        self.assertEqual(mock_add_track.call_count, 1)
        
        expected_metadata = {
            'title': 'Good Song',
            'file_path': good_file_path,
            'file_type': 'MP3'
        }
        mock_add_track.assert_called_once_with(expected_metadata)

if __name__ == '__main__':
    unittest.main() 