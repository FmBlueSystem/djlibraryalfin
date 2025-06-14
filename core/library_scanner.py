import os
import re
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


def auto_fix_metadata(metadata: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """
    Aplica correcciones automáticas a metadatos problemáticos
    """
    invalid_values = {'N/A', 'N A', 'NA', 'Unknown', 'unknown', 'UNKNOWN', '', None}
    
    # Mapeo de géneros por artista
    artist_genre_map = {
        'spice girls': 'Pop',
        'coldplay': 'Alternative Rock',
        'the chainsmokers': 'Electronic',
        'stephane deschezeaux': 'Electronic',
        'alice cooper': 'Rock',
        'status quo': 'Rock',
        'oasis': 'Rock',
        'rolling stones': 'Rock',
        'blue oyster cult': 'Rock',
        'rihanna': 'R&B',
        'drake': 'Hip Hop',
        'whitney houston': 'R&B',
        'dolly parton': 'Country',
        'mavericks': 'Country Rock',
        'apache indian': 'Reggae',
        'sean paul': 'Reggae',
    }
    
    # Patrones de título que sugieren géneros
    title_genre_patterns = {
        'club mix': 'Electronic',
        'remix': 'Electronic',
        'dj beats': 'Electronic',
        'original mix': 'Electronic',
        'extended': 'Electronic',
        'radio edit': 'Pop',
    }
    
    # Extraer información del nombre del archivo si es necesario
    filename = os.path.basename(file_path)
    filename_without_ext = os.path.splitext(filename)[0]
    
    # Patrones comunes: "Artist - Title"
    patterns = [
        r'^(.+?)\s*-\s*(.+)$',  # Artist - Title
        r'^(.+?)_(.+)$',        # Artist_Title
    ]
    
    extracted_artist = None
    extracted_title = None
    
    for pattern in patterns:
        match = re.match(pattern, filename_without_ext)
        if match:
            extracted_artist = match.group(1).strip()
            extracted_title = match.group(2).strip()
            break
    
    # Limpiar nombres extraídos
    if extracted_artist:
        extracted_artist = re.sub(r'_PN$', '', extracted_artist)
        extracted_artist = re.sub(r'\(.*\)$', '', extracted_artist).strip()
    
    if extracted_title:
        extracted_title = re.sub(r'_PN$', '', extracted_title)
        extracted_title = re.sub(r'\(.*\)$', '', extracted_title).strip()
    
    # Corregir artista
    if metadata.get('artist') in invalid_values and extracted_artist:
        metadata['artist'] = extracted_artist
        print(f"  🎤 Artista corregido: {extracted_artist}")
    
    # Corregir título
    if metadata.get('title') in invalid_values and extracted_title:
        metadata['title'] = extracted_title
        print(f"  🎵 Título corregido: {extracted_title}")
    
    # Corregir álbum
    if metadata.get('album') in invalid_values:
        metadata['album'] = 'Unknown Album'
        print(f"  💿 Álbum corregido: Unknown Album")
    
    # Corregir género
    if metadata.get('genre') in invalid_values:
        new_genre = 'Pop'  # Género por defecto
        
        # Buscar por artista
        if metadata.get('artist'):
            artist_lower = metadata['artist'].lower()
            for artist_key, genre in artist_genre_map.items():
                if artist_key in artist_lower:
                    new_genre = genre
                    break
        
        # Si no se encontró, buscar por patrones en el título
        if new_genre == 'Pop' and metadata.get('title'):
            title_lower = metadata['title'].lower()
            filename_lower = filename.lower()
            
            for pattern, genre in title_genre_patterns.items():
                if pattern in title_lower or pattern in filename_lower:
                    new_genre = 'Electronic'
                    break
        
        # Inferencia por año
        if new_genre == 'Pop' and metadata.get('year'):
            year = metadata['year']
            if year < 1980:
                new_genre = 'Rock'
            elif year < 1990:
                new_genre = 'Pop'
            elif year < 2000:
                new_genre = 'Pop'
            else:
                new_genre = 'Electronic'
        
        metadata['genre'] = new_genre
        print(f"  🎼 Género corregido: {new_genre}")
    
    return metadata


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
                # 2. Aplicar correcciones automáticas a metadatos problemáticos
                metadata = auto_fix_metadata(metadata, file_path)
                
                # 3. Analizar características de audio (BPM, etc.)
                audio_features = analyze_audio_features(file_path)
                metadata.update(audio_features)

                # 4. Añadir info adicional y guardar en DB
                metadata["file_path"] = file_path
                _, extension = os.path.splitext(file_path)
                metadata["file_type"] = extension.replace(".", "").upper()

                self.db_manager.add_track(metadata)
            else:
                print("  -> No se pudieron leer los metadatos. Omitiendo.")

        print("Escaneo completado.")
