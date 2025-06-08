import os
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import TIT2, TPE1, TALB, TCON, TRCK, COMM, TXXX

def write_metadata_tag(file_path, field, value):
    """
    Escribe un valor en un tag de metadatos específico de un archivo de audio.
    Devuelve True si fue exitoso, False en caso contrario.
    """
    try:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()
        
        audio = None
        
        if extension == '.mp3':
            audio = MP3(file_path)
            tag_map = {
                'title': TIT2(encoding=3, text=value),
                'artist': TPE1(encoding=3, text=value),
                'album': TALB(encoding=3, text=value),
                'genre': TCON(encoding=3, text=value),
                'comment': COMM(encoding=3, lang='eng', desc='comment', text=value)
            }
            if field in tag_map:
                audio[tag_map[field].__class__.__name__] = tag_map[field]
            elif field == 'bpm':
                audio.add(TXXX(encoding=3, desc='BPM', text=str(value)))
            elif field == 'key':
                audio.add(TXXX(encoding=3, desc='Initial key', text=value))

        elif extension == '.flac':
            audio = FLAC(file_path)
            audio[field] = str(value)

        elif extension == '.m4a':
            audio = MP4(file_path)
            tag_map = {
                'title': '\xa9nam', 'artist': '\xa9ART', 'album': '\xa9alb',
                'genre': '\xa9gen', 'comment': '\xa9com',
                'bpm': '----:com.apple.iTunes:BPM',
                'key': '----:com.apple.iTunes:initialkey'
            }
            if field in tag_map:
                tag_key = tag_map[field]
                if field == 'bpm':
                     audio[tag_key] = str(value).encode('utf-8')
                else:
                    audio[tag_key] = [value]

        if audio:
            audio.save()
            print(f"Metadato '{field}' actualizado a '{value}' en {os.path.basename(file_path)}")
            return True
        else:
            print(f"Formato no soportado para escritura: {extension}")
            return False

    except Exception as e:
        print(f"Error escribiendo metadatos en {file_path}: {e}")
        return False 