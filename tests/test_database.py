import unittest
from unittest.mock import MagicMock
import sqlite3
from core.database import init_db, add_track, get_track_path

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Se ejecuta antes de cada prueba, estableciendo una conexión en memoria."""
        self.conn = sqlite3.connect(":memory:")
        
        # Inicializamos la DB pasándole nuestra conexión
        init_db(conn=self.conn) 
        
        test_track = {'file_path': '/fake/path/track1.mp3', 'title': 'Test Song'}
        # Pasamos la conexión a cada función que la necesite
        track_id = add_track(test_track, conn=self.conn)
        
        self.assertIsNotNone(track_id, "add_track no devolvió un ID después de la inicialización")
        self.track_id = track_id

    def tearDown(self):
        """Cierra la conexión después de cada prueba."""
        self.conn.close()

    def test_get_track_path_success(self):
        """Prueba que get_track_path devuelve la ruta correcta para un ID válido."""
        path = get_track_path(self.track_id, conn=self.conn)
        self.assertEqual(path, '/fake/path/track1.mp3')

    def test_get_track_path_failure(self):
        """Prueba que get_track_path devuelve None para un ID inválido."""
        path = get_track_path(9999, conn=self.conn) # Un ID que no existe
        self.assertIsNone(path)

if __name__ == '__main__':
    unittest.main() 