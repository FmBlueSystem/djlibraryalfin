from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.mp4 import MP4
import os
from typing import Any, Dict, Optional


def _clean_value(value: Any) -> Optional[str]:
    """Limpia un valor de metadato, decodificándolo si es bytes y convirtiéndolo a string."""
    if value is None:
        return None
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8").strip()
        except UnicodeDecodeError:
            return str(
                value
            )  # Fallback a la representación de string si la decodificación falla
    return str(value).strip()


def read_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Lee los metadatos de un archivo de audio (MP3, FLAC, WAV, M4A).
    Devuelve un diccionario con los metadatos o None si ocurre un error.
    """
    try:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        audio = None
        metadata: Dict[str, Any] = {
            "title": None,
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "track_number": None,
            "comment": None,
            "bpm": None,
            "key": None,
            "duration": 0,
            "energy_tag": None,
        }

        if extension == ".mp3":
            audio = MP3(file_path)
            metadata["title"] = _clean_value(audio.get("TIT2", [None])[0])
            metadata["artist"] = _clean_value(audio.get("TPE1", [None])[0])
            metadata["album"] = _clean_value(audio.get("TALB", [None])[0])
            metadata["genre"] = _clean_value(audio.get("TCON", [None])[0])
            metadata["year"] = _clean_value(
                audio.get("TDRC", [None])[0].text if audio.get("TDRC") else None
            )
            metadata["track_number"] = _clean_value(audio.get("TRCK", [None])[0])
            metadata["comment"] = _clean_value(audio.get("COMM::XXX", [None])[0])
            metadata["bpm"] = _clean_value(audio.get("TBPM", [None])[0])
            metadata["key"] = _clean_value(audio.get("TKEY", [None])[0])

        elif extension == ".flac":
            audio = FLAC(file_path)
            metadata["title"] = _clean_value(audio.get("title", [None])[0])
            metadata["artist"] = _clean_value(audio.get("artist", [None])[0])
            metadata["album"] = _clean_value(audio.get("album", [None])[0])
            metadata["genre"] = _clean_value(audio.get("genre", [None])[0])
            metadata["year"] = _clean_value(audio.get("date", [None])[0])
            metadata["track_number"] = _clean_value(audio.get("tracknumber", [None])[0])
            metadata["comment"] = _clean_value(audio.get("description", [None])[0])
            metadata["bpm"] = _clean_value(audio.get("bpm", [None])[0])
            metadata["key"] = _clean_value(audio.get("initialkey", [None])[0])

        elif extension == ".m4a":
            audio = MP4(file_path)
            tags = audio.tags or {}

            metadata["title"] = _clean_value(tags.get("\xa9nam", [None])[0])
            metadata["artist"] = _clean_value(tags.get("\xa9ART", [None])[0])
            metadata["album"] = _clean_value(tags.get("\xa9alb", [None])[0])
            metadata["genre"] = _clean_value(tags.get("\xa9gen", [None])[0])
            metadata["year"] = _clean_value(tags.get("\xa9day", [None])[0])
            track_info = tags.get("trkn", [(None, 0)])[0]
            if track_info and track_info[0] is not None:
                metadata["track_number"] = str(track_info[0])
            metadata["comment"] = _clean_value(tags.get("\xa9com", [None])[0])

            # Captura directa del tag estándar de tempo (tmpo)
            if "tmpo" in tags:
                metadata["bpm"] = _clean_value(str(tags["tmpo"][0]))

            # Búsqueda mejorada de tags personalizados
            for key in tags:
                key_lower = key.lower()
                if "initialkey" in key_lower:
                    metadata["key"] = _clean_value(tags[key][0])
                elif "bpm" in key_lower or "tempo" in key_lower:
                    val_str = str(tags[key][0])
                    numeric_part = "".join(filter(str.isdigit, val_str.split(" ")[0]))
                    if numeric_part:
                        metadata["bpm"] = numeric_part

        elif extension == ".wav":
            audio = WAVE(file_path)
            # WAV tiene soporte limitado para metadatos estándar
            metadata["title"] = f"{os.path.basename(file_path)}"

        if audio:
            metadata["duration"] = round(audio.info.length, 2)

        # Reemplazar None con "N/A" para la visualización final si es necesario,
        # aunque es mejor manejar None en la capa de la base de datos/UI.
        for key, value in metadata.items():
            if value is None:
                metadata[key] = "N/A"

        # --- Lógica para leer el tag de energía específico del archivo ---
        try:
            energy_val = None
            ext = os.path.splitext(file_path)[1].lower()

            if ext == ".mp3":
                # Para MP3, los tags personalizados suelen estar en TXXX
                for frame in audio.tags.getall("TXXX"):
                    if frame.desc == "EnergyLevel":
                        energy_val = frame.text[0]
                        break
            elif ext == ".m4a":
                # Para M4A, los tags a veces están prefijados
                if "----:com.apple.iTunes:energylevel" in audio.tags:
                    energy_val = audio.tags["----:com.apple.iTunes:energylevel"][0]
                # Podría haber otras variaciones, pero esta es común
            elif ext == ".flac":
                # Para FLAC, los tags son directos
                if "ENERGYLEVEL" in audio:
                    energy_val = audio["ENERGYLEVEL"][0]

            if energy_val:
                metadata["energy_tag"] = float(energy_val)

        except (KeyError, IndexError, ValueError, TypeError):
            # Si el tag no existe o no es un número, se ignora silenciosamente
            pass

        return metadata

    except Exception as e:
        print(f"Error leyendo metadatos para {file_path}: {e}")
        return None
