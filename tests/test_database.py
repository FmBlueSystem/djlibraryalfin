import unittest
from unittest.mock import patch
import os
import sqlite3
from core.database import init_db, add_track, get_track_path

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Se ejecuta antes de cada prueba."""
        # Usamos patch aquí en el setup para asegurar que init_db y add_track
        # usen la base de datos en memoria.
        with patch('core.database.get_db_path', return_value=":memory:"):
            init_db()
            test_track = {'file_path': '/fake/path/track1.mp3', 'title': 'Test Song'}
            add_track(test_track)

        # Conexión directa para obtener el ID de prueba
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT id FROM tracks WHERE file_path=?", ('/fake/path/track1.mp3',))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result, "La pista de prueba no se insertó correctamente")
        self.track_id = result[0]

    def tearDown(self):
        """Se ejecuta después de cada prueba."""
        self.conn.close()

    @patch('core.database.get_db_path', return_value=":memory:")
    def test_get_track_path_success(self, mock_get_db_path):
        """Prueba que get_track_path devuelve la ruta correcta para un ID válido."""
        path = get_track_path(self.track_id)
        self.assertEqual(path, '/fake/path/track1.mp3')

    @patch('core.database.get_db_path', return_value=":memory:")
    def test_get_track_path_failure(self, mock_get_db_path):
        """Prueba que get_track_path devuelve None para un ID inválido."""
        path = get_track_path(9999) # Un ID que no existe
        self.assertIsNone(path)

if __name__ == '__main__':
    unittest.main() 