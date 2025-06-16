import os
import threading
from mutagen.flac import FLAC
from mutagen.mp3 import EasyMP3
from mutagen.mp4 import MP4
from mutagen import MutagenError
from . import database as db
from .metadata_enricher import enrich_metadata # Ahora consulta múltiples fuentes
from .metadata_reader import read_metadata

# Mapeo de claves de EasyMP3/Mutagen a las claves de nuestra DB
TAG_TO_DB_MAP = {
    'artist': 'artist', 'album': 'album', 'title': 'title',
    'genre': 'genre', 'date': 'year', 'tracknumber': 'track_number'
}

def _infer_tags_from_filename(filename):
    """Intenta adivinar el artista y el título desde el nombre de un archivo."""
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split(' - ', 1)
    if len(parts) == 2:
        return {'artist': parts[0].strip(), 'title': parts[1].strip()}
    return {}

class LibraryScanner(threading.Thread):
    def __init__(self, directory, on_complete_callback, progress_callback=None):
        super().__init__(daemon=True)
        self.directory = directory
        self.on_complete_callback = on_complete_callback
        self.progress_callback = progress_callback
        self.running = False

    def stop(self):
        """Detiene el escaneo de forma segura."""
        print("Deteniendo escáner de biblioteca...")
        self.running = False
        # self.wait() # Eliminado para evitar AttributeError en este entorno.

    def run(self):
        print(f"Iniciando escaneo: {self.directory}")
        if self.progress_callback:
            self.progress_callback("Buscando archivos de música...")

        files_to_scan = []
        for root, _, files in os.walk(self.directory):
            for filename in files:
                if filename.lower().endswith(('.mp3', '.flac', '.m4a', '.wav')) and not filename.startswith('._'):
                    files_to_scan.append(os.path.join(root, filename))
        
        total_files = len(files_to_scan)
        
        self.running = True # Asegurar que el flag esté activo al iniciar
        for i, file_path in enumerate(files_to_scan):
            if not self.running: # Permitir detener el escaneo
                print("Escaneo detenido por el usuario.")
                break
            if self.progress_callback:
                self.progress_callback(f"Escaneando [{i+1}/{total_files}]: {os.path.basename(file_path)}")
            self._process_file(file_path)
        
        if self.progress_callback:
            self.progress_callback("Escaneo finalizado. Recargando la lista de pistas...")
        
        if self.on_complete_callback:
            self.on_complete_callback()
        
        self.running = False # Marcar como no corriendo al finalizar
        print("Escaneo de librería finalizado.")

    def _should_process_file(self, file_path: str) -> bool:
        try:
            last_modified = os.path.getmtime(file_path)
            existing_track = db.get_track_by_path(file_path)
            if not existing_track:
                return True
            if existing_track.get('last_modified_date') != last_modified:
                return True
            # Podríamos añadir una lógica para re-enriquecer si faltan campos clave de API
            # if not all(existing_track.get(k) for k in ['spotify_track_id', 'musicbrainz_recording_id', 'album_art_url']):
            # return True 
            return False
        except FileNotFoundError:
            return False

    def _process_file(self, file_path):
        try:
            if self._should_process_file(file_path):
                # 1. Leer tags locales del archivo
                track_info_local = self._read_tags_from_file(file_path)
                # file_path ya está en track_info_local desde _read_tags_from_file
                track_info_local['last_modified_date'] = os.path.getmtime(file_path)

                # 2. Inferir del nombre de archivo si es necesario
                if not track_info_local.get('artist') or not track_info_local.get('title'):
                    inferred_tags = _infer_tags_from_filename(os.path.basename(file_path))
                    if inferred_tags:
                        track_info_local.setdefault('artist', inferred_tags.get('artist'))
                        track_info_local.setdefault('title', inferred_tags.get('title'))

                # 3. Enriquecer con APIs externas
                # Se pasa una copia de los datos locales para que enrich_metadata no los modifique directamente.
                # enrich_metadata ahora devuelve un diccionario con los datos *adicionales* o *mejorados* de las APIs.
                api_derived_data = enrich_metadata(track_info_local.copy())

                # 4. Fusionar datos para la base de datos
                # Empezar con los datos derivados de las APIs como base.
                final_data_for_db = api_derived_data.copy()
                
                # Luego, actualizar/sobrescribir con los datos locales (tags, nombre de archivo).
                # Esto asegura que los datos locales (ej. 'comment', 'bpm' manual, 'key' manual) 
                # siempre tengan la máxima prioridad si existen y son válidos.
                # Los campos específicos de API (ej. spotify_track_id, album_art_url de Spotify)
                # se mantendrán si fueron añadidos por api_derived_data y no existen en track_info_local.
                final_data_for_db.update(track_info_local)
                
                # Asegurar que file_path y last_modified_date (de track_info_local) estén presentes.
                # La operación update anterior ya debería haberlos incluido.
                # No es necesario reasignarlos explícitamente si track_info_local los tiene.
                # final_data_for_db['file_path'] = track_info_local['file_path']
                # final_data_for_db['last_modified_date'] = track_info_local['last_modified_date']


                # 5. Añadir/actualizar en la base de datos
                db.add_track(final_data_for_db)
                print(f"Procesado y guardado: {os.path.basename(file_path)}")
            # else:
                # print(f"Omitiendo (sin cambios): {os.path.basename(file_path)}")

        except Exception as e:
            print(f"❌ Error procesando {os.path.basename(file_path)}: {e}")

    def _read_tags_from_file(self, file_path):
        raw_metadata = read_metadata(file_path)
        # Asegurar que track_info siempre tenga 'file_path'
        track_info = {'file_path': file_path}
        if not raw_metadata:
            return track_info 

        ADAPTER_MAP = {
            'title': 'title', 'artist': 'artist', 'album': 'album',
            'genre': 'genre', 'year': 'year', 'track_number': 'track_number',
            'comments': 'comment', 'bpm': 'bpm', 'key': 'key',
            'duration': 'duration'
            # Campos como album_art_url, spotify_track_id, etc., vendrán de enrich_metadata
        }

        for source_key, db_key in ADAPTER_MAP.items():
            value = raw_metadata.get(source_key)
            # Evitar 'N/A' y cadenas vacías, pero permitir 0 para año o track_number si es numérico
            if value is not None and str(value).strip() != "N/A" and str(value).strip() != "":
                track_info[db_key] = value
        
        _, extension = os.path.splitext(file_path)
        track_info['file_type'] = extension.lower().replace('.', '')

        return track_info

# Para pruebas directas
if __name__ == '__main__':
    # ATENCIÓN: Cambia esta ruta a una carpeta con música en tu sistema para probar.
    # Se recomienda una carpeta PEQUEÑA para pruebas iniciales.
    test_music_folder = os.path.expanduser("~/Music/test_library_small") 
    
    # Primero, asegúrate de que la DB esté inicializada
    from core.database import init_db
    init_db() # Asegurar que la DB y la tabla existen

    if os.path.isdir(test_music_folder):
        print(f"Iniciando escáner de prueba en: {test_music_folder}")
        # Crear un callback simple para progreso
        def simple_progress(message):
            print(f"PROGRESO: {message}")

        scanner = LibraryScanner(test_music_folder, 
                                 lambda: print("Escaneo de prueba completado."),
                                 progress_callback=simple_progress)
        # scanner.running = True # El flag 'running' se maneja dentro de run() y stop()
        scanner.start() # Inicia el hilo, que establece self.running = True
        
        # Para probar la detención, podrías hacer algo como:
        # import time
        # time.sleep(5) # Dejar que escanee por 5 segundos
        # scanner.stop()
        
        scanner.join() # Esperar a que el hilo termine para la prueba
        print("Proceso de prueba del escáner finalizado.")
    else:
        print(f"El directorio de prueba no existe: {test_music_folder}")
        print("Por favor, edita la variable 'test_music_folder' en library_scanner.py y crea el directorio con algunos archivos de audio.")