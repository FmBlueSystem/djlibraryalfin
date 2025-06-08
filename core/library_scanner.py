import os
from core.metadata_reader import read_metadata
from core.database import add_track

SUPPORTED_EXTENSIONS = ['.mp3', '.flac', '.m4a', '.wav']

def scan_directory(directory_path, queue=None):
    """
    Escanea un directorio recursivamente en busca de archivos de audio,
    lee sus metadatos y los añade a la base de datos.
    Si se proporciona una cola (queue), se notificará al finalizar.
    """
    try:
        print(f"Iniciando escaneo en: {directory_path}")
        
        found_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                # Ignorar archivos ocultos de macOS
                if file.startswith('._'):
                    continue
                if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    found_files.append(os.path.join(root, file))

        total_files = len(found_files)
        print(f"Se encontraron {total_files} archivos de audio compatibles.")

        for index, file_path in enumerate(found_files):
            print(f"Procesando [{index + 1}/{total_files}]: {os.path.basename(file_path)}")
            
            metadata = read_metadata(file_path)
            
            if metadata:
                # Añadimos la ruta del archivo y el tipo de archivo al diccionario de metadatos.
                metadata['file_path'] = file_path
                _, extension = os.path.splitext(file_path)
                metadata['file_type'] = extension.replace('.', '').upper()
                
                add_track(metadata)
            else:
                print(f"  -> No se pudieron leer los metadatos. Omitiendo.")

        print("Escaneo completado.")
    finally:
        if queue:
            queue.put("scan_complete")

# Para pruebas directas
if __name__ == '__main__':
    # ATENCIÓN: Cambia esta ruta a una carpeta con música en tu sistema para probar.
    test_music_folder = os.path.expanduser("~/Music/test_library") # Ejemplo para macOS/Linux
    
    # Primero, asegúrate de que la DB esté inicializada
    from core.database import init_db
    init_db()

    if os.path.isdir(test_music_folder):
        scan_directory(test_music_folder)
    else:
        print(f"El directorio de prueba no existe: {test_music_folder}")
        print("Por favor, edita la variable 'test_music_folder' en library_scanner.py") 