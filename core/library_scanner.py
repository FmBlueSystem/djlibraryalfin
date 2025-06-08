import os
from typing import List, Dict, Any
from core.metadata_reader import read_metadata
from core.database import DatabaseManager

SUPPORTED_EXTENSIONS: List[str] = [".mp3", ".flac", ".m4a", ".wav"]

class LibraryScanner:
    def __init__(self, directory_path: str, db_manager: DatabaseManager):
        self.directory_path = directory_path
        self.db_manager = db_manager

    def scan(self) -> None:
        """
        Escanea el directorio recursivamente, lee metadatos y los guarda en la DB.
        """
        print(f"Iniciando escaneo en: {self.directory_path}")

        found_files: List[str] = []
        for root, _, files in os.walk(self.directory_path):
            for file in files:
                # Ignorar archivos ocultos de macOS
                if file.startswith("._"):
                    continue
                if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    found_files.append(os.path.join(root, file))

        total_files = len(found_files)
        print(f"Se encontraron {total_files} archivos de audio compatibles.")

        for index, file_path in enumerate(found_files):
            print(
                f"Procesando [{index + 1}/{total_files}]: {os.path.basename(file_path)}"
            )

            metadata = read_metadata(file_path)

            if metadata:
                # Añadimos la ruta del archivo y el tipo de archivo al diccionario de metadatos.
                metadata["file_path"] = file_path
                _, extension = os.path.splitext(file_path)
                metadata["file_type"] = extension.replace(".", "").upper()

                self.db_manager.add_track(metadata)
            else:
                print("  -> No se pudieron leer los metadatos. Omitiendo.")

        print("Escaneo completado.")
