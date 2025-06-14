import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
from tkinter import ttk
import os
import shutil
import time
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

# Añadir el directorio raíz al path para que encuentre los módulos
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import MainApplication
from core import database as db
from core.metadata_reader import read_metadata

class TestEnrichmentWorkflow(unittest.TestCase):
    TEST_DB_PATH = "config/test_library.db"
    ORIGINAL_AUDIO_DIR = "/Volumes/KINGSTON/Audio"
    TEST_AUDIO_DIR = "tests/temp_audio"
    
    # Esta variable se establecerá dinámicamente en setUpClass
    test_file_path = None
    file_handler = None
    file_extension = None

    @classmethod
    def setUpClass(cls):
        """ Se ejecuta una vez antes de todas las pruebas de la clase. """
        # Configurar la base de datos de prueba
        db.DATABASE_PATH = cls.TEST_DB_PATH
        if os.path.exists(cls.TEST_DB_PATH):
            os.remove(cls.TEST_DB_PATH)
        db.init_db()

        # Crear un directorio de audio de prueba, limpiando restos anteriores si los hubiera
        if os.path.exists(cls.TEST_AUDIO_DIR):
            shutil.rmtree(cls.TEST_AUDIO_DIR, ignore_errors=True)
        os.makedirs(cls.TEST_AUDIO_DIR)

        # Buscar un archivo de audio real (cualquier formato compatible) para usarlo en la prueba
        supported_extensions = ['.mp3', '.flac', '.m4a']
        search_dirs = [cls.ORIGINAL_AUDIO_DIR] # Apuntar solo a la carpeta correcta
        source_file_path = None
        
        for directory in search_dirs:
            if not os.path.isdir(directory):
                continue
            for file in os.listdir(directory):
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_extensions:
                    source_file_path = os.path.join(directory, file)
                    cls.file_extension = ext
                    print(f"INFO: Usando archivo de prueba encontrado en: {source_file_path}")
                    break
            if source_file_path:
                break

        if not source_file_path:
            raise FileNotFoundError(f"No se encontró un archivo compatible {supported_extensions} en '{cls.ORIGINAL_AUDIO_DIR}' para la prueba.")

        # Copiar y limpiar metadatos del archivo de prueba
        test_file_name = f"test_song{cls.file_extension}"
        cls.test_file_path = os.path.join(cls.TEST_AUDIO_DIR, test_file_name)
        shutil.copy(source_file_path, cls.test_file_path)

        # Limpiar el género y el año del archivo para asegurar que el enriquecimiento sea necesario
        if cls.file_extension == '.mp3':
            cls.file_handler = MP3(cls.test_file_path)
            if 'TCON' in cls.file_handler: del cls.file_handler['TCON']
            if 'TDRC' in cls.file_handler: del cls.file_handler['TDRC']
        elif cls.file_extension == '.flac':
            cls.file_handler = FLAC(cls.test_file_path)
            if 'genre' in cls.file_handler: del cls.file_handler['genre']
            if 'date' in cls.file_handler: del cls.file_handler['date']
        elif cls.file_extension == '.m4a':
            cls.file_handler = MP4(cls.test_file_path)
            if '\xa9gen' in cls.file_handler: del cls.file_handler['\xa9gen']
            if '\xa9day' in cls.file_handler: del cls.file_handler['\xa9day']
        
        cls.file_handler.save()

        # Usar los metadatos leídos del propio archivo para la DB
        metadata = read_metadata(cls.test_file_path)

        # Añadir la pista a la DB de prueba
        db.add_track({
            "file_path": cls.test_file_path,
            "artist": metadata.get('artist', 'Unknown Artist'),
            "title": metadata.get('title', 'Unknown Title'),
            "album": metadata.get('album', 'Unknown Album'),
            "genre": "",
            "year": "",
            "duration": metadata.get('duration', 180),
            "bpm": metadata.get('bpm', '120'),
            "key": metadata.get('key', 'C')
        })


    @classmethod
    def tearDownClass(cls):
        """ Se ejecuta una vez después de todas las pruebas de la clase. """
        # Limpiar el directorio de audio de prueba y la base de datos
        if os.path.exists(cls.TEST_AUDIO_DIR):
            # Usar ignore_errors=True para evitar problemas con archivos ._ de macOS
            shutil.rmtree(cls.TEST_AUDIO_DIR, ignore_errors=True)
        if os.path.exists(cls.TEST_DB_PATH):
            os.remove(cls.TEST_DB_PATH)

    def setUp(self):
        """ Se ejecuta antes de cada prueba. """
        self.app = MainApplication()
        # Dar tiempo a la UI para que se renderice
        self.app.update()

    def tearDown(self):
        """ Se ejecuta después de cada prueba. """
        self.app.destroy()

    @patch('core.metadata_enricher.enrich_metadata')
    def test_full_workflow(self, mock_enrich_metadata):
        """
        Valida el flujo completo: Seleccionar -> Editar -> Enriquecer -> Guardar
        """
        # 1. Configurar el mock para simular la respuesta de la API
        mock_enrich_metadata.return_value = {
            'genre': 'Pop Rock Simulado',
            'year': '2023'
        }

        # 2. Seleccionar la pista en el Treeview
        track_id = "1" # Nuestra pista de prueba tendrá el ID 1
        self.app.tracklist.tree.selection_set(track_id)
        self.app.tracklist.tree.focus(track_id)
        self.app.update() # Procesar eventos para que se llame a _on_track_select

        # El panel puede no tener datos si la selección falla, añadimos un assert
        self.assertIsNotNone(self.app.metadata_panel.current_track_data, "El panel de metadatos no se cargó con datos de la pista.")
        
        # Leemos el título del archivo real para la comparación
        real_metadata = read_metadata(self.test_file_path)
        expected_title = real_metadata.get('title', 'Unknown Title')
        
        self.assertEqual(self.app.metadata_panel.current_track_data['title'], expected_title)
        
        # 3. Simular clic en "Editar"
        self.app.metadata_panel.edit_button.invoke()
        self.app.update()

        # Verificar que estamos en modo edición (los widgets son ahora ttk.Entry)
        self.assertIsInstance(self.app.metadata_panel.track_data_widgets['title'], ttk.Entry)
        
        # 4. Simular clic en "Enriquecer"
        self.app.metadata_panel.enrich_button.invoke()
        
        # Esperar a que el hilo de enriquecimiento termine y actualice la UI
        # Damos un tiempo corto para que se ejecute el self.after(0, ...)
        time.sleep(0.2) 
        self.app.update()

        # Verificar que el mock fue llamado
        mock_enrich_metadata.assert_called_once()
        
        # Verificar que los campos de texto se han rellenado con los datos simulados
        self.assertEqual(self.app.metadata_panel.track_data_widgets['genre'].get(), 'Pop Rock Simulado')
        self.assertEqual(self.app.metadata_panel.track_data_widgets['year'].get(), '2023')
        
        # 5. Simular clic en "Guardar"
        self.app.metadata_panel.save_button.invoke()
        self.app.update()

        # --- VALIDACIÓN FINAL ---
        # 6. Validar que el archivo de audio fue modificado
        if self.file_extension == '.mp3':
            audio = MP3(self.test_file_path)
            self.assertEqual(audio.get('TCON').text[0], 'Pop Rock Simulado')
            self.assertEqual(audio.get('TDRC').text[0], '2023')
        elif self.file_extension == '.flac':
            audio = FLAC(self.test_file_path)
            self.assertEqual(audio.get('genre')[0], 'Pop Rock Simulado')
            self.assertEqual(audio.get('date')[0], '2023')
        elif self.file_extension == '.m4a':
            audio = MP4(self.test_file_path)
            self.assertEqual(audio.get('\xa9gen')[0], 'Pop Rock Simulado')
            self.assertEqual(audio.get('\xa9day')[0], '2023')

        # 7. Validar que la base de datos fue actualizada
        conn = db.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT genre, year FROM tracks WHERE id = ?", (track_id,))
        db_genre, db_year = cursor.fetchone()
        conn.close()
        
        self.assertEqual(db_genre, 'Pop Rock Simulado')
        self.assertEqual(db_year, '2023')

        # 8. Validar que la lista de canciones en la UI fue actualizada
        tree_item = self.app.tracklist.tree.item(track_id)
        # El índice de 'genre' es 4, 'year' es 5
        self.assertEqual(tree_item['values'][4], 'Pop Rock Simulado')
        self.assertEqual(tree_item['values'][5], '2023')

if __name__ == '__main__':
    unittest.main() 