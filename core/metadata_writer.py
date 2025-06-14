import os
from mutagen.mp3 import MP3, EasyMP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import TIT2, TPE1, TALB, TCON, TRCK, TDRC, COMM, TXXX

# Mapeo de campos amigables a claves de tags de Mutagen para diferentes formatos
TAG_MAP = {
    '.mp3': {
        'artist': 'artist', 'album': 'album', 'title': 'title',
        'genre': 'genre', 'year': 'date', 'tracknumber': 'tracknumber'
    },
    '.flac': {
        'artist': 'ARTIST', 'album': 'ALBUM', 'title': 'TITLE',
        'genre': 'GENRE', 'year': 'DATE', 'tracknumber': 'TRACKNUMBER'
    },
    '.m4a': {
        'artist': '\xa9ART', 'album': '\xa9alb', 'title': '\xa9nam',
        'genre': '\xa9gen', 'year': '\xa9day', 'tracknumber': 'trkn'
    }
}

def write_metadata_tags(file_path, metadata: dict):
    """
    Escribe un diccionario de metadatos en un archivo de audio.
    Intenta escribir todos los campos y reporta los errores.
    
    Args:
        file_path (str): Ruta al archivo de audio.
        metadata (dict): Diccionario con los campos y valores a escribir.
        
    Returns:
        bool: True si al menos un tag se escribió correctamente, False si no.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: El archivo no existe en la ruta: {file_path}")
        return False

    success = False
    for field, value in metadata.items():
        if value is not None: # Solo escribir si hay un valor
            if write_metadata_tag(file_path, field, value):
                success = True
    return success

def write_metadata_tag(file_path, field, value):
    """
    Escribe un valor en un tag de metadatos específico de un archivo de audio
    utilizando un mapeo de tags para diferentes formatos.
    Devuelve True si fue exitoso, False en caso contrario.
    """
    try:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        if extension not in TAG_MAP:
            print(f"-> Formato de archivo no soportado para escritura: {extension}")
            return False

        field_key = TAG_MAP[extension].get(field.lower())
        
        if not field_key:
            # Manejar campos no estándar como BPM y Key por separado
            if field.lower() == 'bpm':
                return _write_custom_tag(file_path, extension, 'BPM', str(value))
            elif field.lower() == 'key':
                return _write_custom_tag(file_path, extension, 'INITIALKEY', str(value))
            else:
                print(f"-> Campo '{field}' no mapeado para formato {extension}")
                return False

        if extension == '.mp3':
            audio = EasyMP3(file_path)
            audio[field_key] = str(value)
            audio.save()
        elif extension == '.flac':
            audio = FLAC(file_path)
            audio[field_key] = str(value)
            audio.save()
        elif extension == '.m4a':
            audio = MP4(file_path)
            if field.lower() == 'tracknumber':
                # El tracknumber en M4A es una tupla (número, total)
                try:
                    num, total = map(int, str(value).split('/'))
                    audio[field_key] = [(num, total)]
                except ValueError:
                    audio[field_key] = [(int(value), 0)] # Si no hay total
            else:
                audio[field_key] = [str(value)]
            audio.save()

        print(f"✅ Metadato '{field}' guardado en el archivo: {os.path.basename(file_path)}")
        return True

    except Exception as e:
        print(f"❌ Error al escribir '{field}' en {os.path.basename(file_path)}: {e}")
        return False

def _write_custom_tag(file_path, extension, key, value):
    """Función auxiliar para escribir tags no estándar (TXXX para MP3)."""
    try:
        if extension == '.mp3':
            audio = MP3(file_path)
            # Eliminar tag existente para evitar duplicados
            audio.pop(f'TXXX:{key}', None)
            audio.add(TXXX(encoding=3, desc=key, text=value))
            audio.save()
        elif extension == '.m4a':
            tag_key = f'----:com.apple.iTunes:{key.upper()}'
            audio = MP4(file_path)
            audio[tag_key] = value.encode('utf-8')
            audio.save()
        elif extension == '.flac':
            audio = FLAC(file_path)
            audio[key.upper()] = value
            audio.save()
        else:
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error al escribir tag personalizado '{key}' en {os.path.basename(file_path)}: {e}")
        return False 