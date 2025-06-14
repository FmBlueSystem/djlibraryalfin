from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.mp4 import MP4
import os

def read_metadata(file_path):
    """
    Lee los metadatos de un archivo de audio (MP3, FLAC, WAV, M4A).
    """
    try:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        audio = None
        metadata = {
            "title": "N/A", "artist": "N/A", "album": "N/A",
            "genre": "N/A", "year": "N/A", "track_number": "N/A",
            "comment": "N/A", "bpm": "N/A", "key": "N/A",
            "duration": 0
        }

        if extension == '.mp3':
            audio = MP3(file_path)
            metadata["title"] = audio.get('TIT2', [None])[0] or "N/A"
            metadata["artist"] = audio.get('TPE1', [None])[0] or "N/A"
            metadata["album"] = audio.get('TALB', [None])[0] or "N/A"
            metadata["genre"] = audio.get('TCON', [None])[0] or "N/A"
            metadata["year"] = audio.get('TDRC', [None])[0].text if audio.get('TDRC') else "N/A"
            metadata["track_number"] = audio.get('TRCK', [None])[0] or "N/A"
            metadata["comment"] = audio.get('COMM::XXX', [None])[0] or "N/A"
            metadata["bpm"] = audio.get('TBPM', [None])[0] or "N/A"
            metadata["key"] = audio.get('TKEY', [None])[0] or "N/A"

        elif extension == '.flac':
            audio = FLAC(file_path)
            metadata["title"] = audio.get('title', [None])[0] or "N/A"
            metadata["artist"] = audio.get('artist', [None])[0] or "N/A"
            metadata["album"] = audio.get('album', [None])[0] or "N/A"
            metadata["genre"] = audio.get('genre', [None])[0] or "N/A"
            metadata["year"] = audio.get('date', [None])[0] or "N/A"
            metadata["track_number"] = audio.get('tracknumber', [None])[0] or "N/A"
            metadata["comment"] = audio.get('description', [None])[0] or "N/A"
            metadata["bpm"] = audio.get('bpm', [None])[0] or "N/A"
            metadata["key"] = audio.get('initialkey', [None])[0] or "N/A"

        elif extension == '.m4a':
            audio = MP4(file_path)
            tags = audio.tags or {}

            metadata["title"] = tags.get('\xa9nam', [None])[0] or "N/A"
            metadata["artist"] = tags.get('\xa9ART', [None])[0] or "N/A"
            metadata["album"] = tags.get('\xa9alb', [None])[0] or "N/A"
            metadata["genre"] = tags.get('\xa9gen', [None])[0] or "N/A"
            metadata["year"] = tags.get('\xa9day', [None])[0] or "N/A"
            track_info = tags.get('trkn', [(0, 0)])[0]
            metadata["track_number"] = str(track_info[0]) if track_info else "N/A"
            metadata["comment"] = tags.get('\xa9com', [None])[0] or "N/A"

            # Captura directa del tag estándar de tempo (tmpo)
            if 'tmpo' in tags:
                metadata["bpm"] = str(tags['tmpo'][0])

            # Búsqueda mejorada de tags personalizados
            for key in tags:
                key_lower = key.lower()
                # El valor puede ser bytes o string, nos aseguramos de que sea string
                value = tags[key][0]
                if isinstance(value, bytes):
                    value = value.decode('utf-8', 'ignore')
                else:
                    value = str(value)

                if 'initialkey' in key_lower:
                    metadata["key"] = value
                elif key_lower == 'tmpo' or 'bpm' in key_lower or 'tempo' in key_lower:
                    numeric_part = ''.join(filter(str.isdigit, value.split(' ')[0]))
                    if numeric_part:
                        metadata["bpm"] = numeric_part

        elif extension == '.wav':
            audio = WAVE(file_path)
            # WAV has limited standard metadata support, often in INFO chunks
            # Mutagen's WAVE support is more for audio data length
            metadata["title"] = "N/A (WAV)"


        if audio:
            metadata["duration"] = round(audio.info.length, 2)

        # --- NORMALIZACIÓN FINAL ---
        # Asegurarse de que todos los valores de texto sean strings decodificados
        for key, value in metadata.items():
            if isinstance(value, bytes):
                metadata[key] = value.decode('utf-8', 'ignore')
            elif value is not None and not isinstance(value, (str, int, float)):
                 metadata[key] = str(value)

        return metadata

    except Exception as e:
        print(f"Error reading metadata for {file_path}: {e}")
        return None
