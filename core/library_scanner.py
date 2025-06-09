import os
from typing import Dict, List, Any
import librosa
import numpy as np

from core.metadata_reader import read_metadata
from core.database import DatabaseManager

SUPPORTED_EXTENSIONS: List[str] = [".mp3", ".flac", ".m4a", ".wav"]


def analyze_audio_features(file_path: str) -> Dict[str, Any]:
    """
    Analiza un archivo de audio para extraer características como BPM y tonalidad.
    """
    features: Dict[str, Any] = {"bpm": None, "key": None, "energy": None}
    try:
        y, sr = librosa.load(file_path, sr=None, duration=120)  # Cargar solo 2 mins

        # --- Calcular Energía (RMS) ---
        rms = librosa.feature.rms(y=y)
        if rms is not None:
            features["energy"] = round(float(np.mean(rms)), 4)

        # --- Calcular BPM ---
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if tempo:
            features["bpm"] = round(float(tempo), 2)

        # --- Analizar Tonalidad (Sistema Camelot) ---
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)

        # Mapa de notas a número Camelot (la letra A/B depende de si es mayor/menor)
        camelot_map = {
            "C": 8,
            "G": 9,
            "D": 10,
            "A": 11,
            "E": 12,
            "B": 1,
            "F#": 2,
            "G♭": 2,
            "C#": 3,
            "D♭": 3,
            "G#": 4,
            "A♭": 4,
            "D#": 5,
            "E♭": 5,
            "A#": 6,
            "B♭": 6,
            "F": 7,
        }

        # Perfiles de tonalidades Krumhansl-Schmuckler
        major_profile = np.array(
            [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        )
        minor_profile = np.array(
            [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        )

        # Promedio de la cromaticidad a través del tiempo
        chroma_mean = np.mean(chroma, axis=1)

        # Calcular correlación con perfiles de todas las 24 tonalidades (12 Mayores, 12 menores)
        major_corrs = [
            np.corrcoef(chroma_mean, np.roll(major_profile, i))[0, 1] for i in range(12)
        ]
        minor_corrs = [
            np.corrcoef(chroma_mean, np.roll(minor_profile, i))[0, 1] for i in range(12)
        ]

        # Encontrar la mejor correlación
        best_major_idx = np.argmax(major_corrs)
        best_minor_idx = np.argmax(minor_corrs)

        # Nombres de las notas base
        keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

        # Determinar si la mejor tonalidad es Mayor o menor
        if np.max(major_corrs) > np.max(minor_corrs):
            key_name = keys[best_major_idx]
            camelot_number = camelot_map.get(key_name)
            if camelot_number:
                features["key"] = f"{camelot_number}B"  # B para Mayor
        else:
            key_name = keys[best_minor_idx]
            camelot_number = camelot_map.get(key_name)
            if camelot_number:
                features["key"] = f"{camelot_number}A"  # A para menor

    except Exception as e:
        print(f"  -> Error al analizar con librosa {os.path.basename(file_path)}: {e}")

    return features


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

            # 1. Leer metadatos básicos (tags ID3, etc.)
            metadata = read_metadata(file_path)

            if metadata:
                # 2. Analizar características de audio (BPM, etc.)
                audio_features = analyze_audio_features(file_path)
                metadata.update(audio_features)

                # 3. Añadir info adicional y guardar en DB
                metadata["file_path"] = file_path
                _, extension = os.path.splitext(file_path)
                metadata["file_type"] = extension.replace(".", "").upper()

                self.db_manager.add_track(metadata)
            else:
                print("  -> No se pudieron leer los metadatos. Omitiendo.")

        print("Escaneo completado.")
