import os
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import (
    ID3,
    ID3NoHeaderError,
    TIT2,
    TPE1,
    TALB,
    TCON,
    COMM,
    TXXX,
    TBPM,
    TKEY,
)
from typing import Any, Dict


def write_all_metadata(file_path: str, metadata: Dict[str, Any]) -> bool:
    """
    Escribe un diccionario completo de metadatos en un archivo de audio.
    Reutiliza la lógica de `write_metadata_tag` para cada campo.
    """
    success = True
    for field, value in metadata.items():
        if value is not None:  # Solo escribir si hay un valor
            if not write_metadata_tag(file_path, field, value):
                success = False
    return success


def write_metadata_tag(file_path: str, field: str, value: Any) -> bool:
    """
    Escribe un valor en un tag de metadatos específico de un archivo de audio.
    Devuelve True si fue exitoso, False en caso contrario.
    """
    try:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        audio: Any = None

        if extension == ".mp3":
            try:
                audio = MP3(file_path, ID3=ID3)
            except ID3NoHeaderError:
                audio = MP3(file_path)
                audio.add_tags()

            # Mapeo de campos a clases de frames ID3
            tag_map = {
                "title": lambda v: TIT2(encoding=3, text=str(v)),
                "artist": lambda v: TPE1(encoding=3, text=str(v)),
                "album": lambda v: TALB(encoding=3, text=str(v)),
                "genre": lambda v: TCON(encoding=3, text=str(v)),
                "comment": lambda v: COMM(
                    encoding=3, lang="eng", desc="comment", text=str(v)
                ),
                "bpm": lambda v: TBPM(encoding=3, text=str(v)),
                "key": lambda v: TKEY(encoding=3, text=str(v)),
            }

            if field in tag_map:
                frame = tag_map[field](value)
                audio.tags.add(frame)
            else:
                audio.tags.add(TXXX(encoding=3, desc=field, text=str(value)))

        elif extension == ".flac":
            audio = FLAC(file_path)
            # Para FLAC (Vorbis Comments), el mapeo es directo
            audio[field] = str(value)

        elif extension == ".m4a":
            audio = MP4(file_path)
            # Mapeo de campos a claves de átomos MP4
            tag_map = {
                "title": "\xa9nam",
                "artist": "\xa9ART",
                "album": "\xa9alb",
                "genre": "\xa9gen",
                "comment": "\xa9com",
                "bpm": "tmpo",  # Usar el átomo estándar para BPM
                "key": "----:com.apple.iTunes:initialkey",
            }
            if field in tag_map:
                tag_key = tag_map[field]
                # Los BPMs en MP4 a menudo se guardan como un entero de 16 bits.
                if field == "bpm":
                    try:
                        # Convertir a entero si es posible
                        bpm_value = int(float(value))
                        audio[tag_key] = [bpm_value]
                    except (ValueError, TypeError):
                        print(f"Valor de BPM no válido para M4A: {value}")
                        return False
                else:
                    audio[tag_key] = [str(value)]

        if audio:
            if extension == ".mp3":
                audio.save(v2_version=3)
            else:
                audio.save()
            print(
                f"Metadato '{field}' actualizado a '{value}' en {os.path.basename(file_path)}"
            )
            return True
        else:
            print(f"Formato no soportado para escritura: {extension}")
            return False

    except Exception as e:
        print(f"Error escribiendo metadatos en {file_path}: {e}")
        return False
