import os
import threading
from mutagen.flac import FLAC
from mutagen.mp3 import EasyMP3
from mutagen.mp4 import MP4
from mutagen import MutagenError
from . import database as db
from .metadata_enricher import enrich_metadata

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

    def run(self):
        print(f"Iniciando escaneo: {self.directory}")
        if self.progress_callback:
            self.progress_callback("Buscando archivos de música...")

        # Primero, contamos cuántos archivos vamos a procesar
        files_to_scan = []
        for root, _, files in os.walk(self.directory):
            for filename in files:
                if filename.lower().endswith(('.mp3', '.flac', '.m4a', '.wav')) and not filename.startswith('._'):
                    files_to_scan.append(os.path.join(root, filename))
        
        total_files = len(files_to_scan)
        
        for i, file_path in enumerate(files_to_scan):
            if self.progress_callback:
                self.progress_callback(f"Escaneando [{i+1}/{total_files}]: {os.path.basename(file_path)}")
            self._process_file(file_path)
        
        if self.on_complete_callback:
            # Usamos el callback de progreso una última vez para el mensaje final antes de recargar
            if self.progress_callback:
                self.progress_callback("Escaneo finalizado. Recargando la lista de pistas...")
            self.on_complete_callback()
        print("Escaneo de librería finalizado.")

    def _process_file(self, file_path):
        try:
            # Comprobar si el archivo ha sido modificado desde el último escaneo
            last_modified = os.path.getmtime(file_path)
            existing_track = db.get_track_by_path(file_path)
            if existing_track and existing_track.get('last_modified_date') == last_modified:
                return

            # Leer metadatos del archivo
            track_info = self._read_tags_from_file(file_path)
            track_info['last_modified_date'] = last_modified

            # Si después de leer las etiquetas, aún faltan datos, intentar inferirlos del nombre.
            if not track_info.get('artist') or not track_info.get('title'):
                inferred_tags = _infer_tags_from_filename(os.path.basename(file_path))
                # Actualizar solo si el campo no estaba ya presente
                if inferred_tags:
                    track_info.setdefault('artist', inferred_tags.get('artist'))
                    track_info.setdefault('title', inferred_tags.get('title'))

            # Enriquecer con MusicBrainz si es necesario
            enriched_data = enrich_metadata(track_info)
            track_info.update(enriched_data)

            # Añadir/actualizar en la base de datos
            db.add_track(track_info)
            print(f"Procesado: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"❌ Error procesando {os.path.basename(file_path)}: {e}")

    def _read_tags_from_file(self, file_path):
        track_info = {'file_path': file_path}
        try:
            _, extension = os.path.splitext(file_path)
            if extension.lower() == '.mp3':
                audio = EasyMP3(file_path)
            elif extension.lower() == '.flac':
                audio = FLAC(file_path)
            elif extension.lower() == '.m4a':
                audio = MP4(file_path)
            else: # .wav u otros
                return track_info # No podemos leer tags de forma estándar

            track_info['duration'] = audio.info.length
            track_info['file_type'] = extension.lower()

            for tag_key, db_key in TAG_TO_DB_MAP.items():
                if tag_key in audio:
                    value = audio[tag_key][0]
                    # Limpiar el año si viene con hora/fecha
                    if db_key == 'year' and isinstance(value, str):
                        track_info[db_key] = value.split('-')[0]
                    else:
                        track_info[db_key] = value

        except MutagenError as e:
            print(f"Warning: No se pudieron leer los metadatos de {os.path.basename(file_path)}. Puede estar corrupto. Error: {e}")
        
        return track_info

# Para pruebas directas
if __name__ == '__main__':
    # ATENCIÓN: Cambia esta ruta a una carpeta con música en tu sistema para probar.
    test_music_folder = os.path.expanduser("~/Music/test_library") # Ejemplo para macOS/Linux
    
    # Primero, asegúrate de que la DB esté inicializada
    from core.database import init_db
    init_db()

    if os.path.isdir(test_music_folder):
        scanner = LibraryScanner(test_music_folder, lambda: print("Escaneo completado"))
        scanner.start()
    else:
        print(f"El directorio de prueba no existe: {test_music_folder}")
        print("Por favor, edita la variable 'test_music_folder' en library_scanner.py") 