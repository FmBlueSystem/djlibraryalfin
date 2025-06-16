import os
import json
import subprocess
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.wave import WAVE

def write_metadata(file_path: str, metadata: dict):
    """
    Guarda metadatos en archivos de audio.
    Usa eyeD3 para MP3 para asegurar compatibilidad ID3v2.3.
    Usa mutagen para otros formatos.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.mp3':
            # --- Lógica de escritura para MP3 usando eyeD3 ---
            # Forzar reescritura a v2.3, eliminando todo lo demás para evitar conflictos.
            cmd = ['eyeD3', '--force-update', '--to-v2.3', '--remove-all', file_path]
            
            if 'title' in metadata: cmd.extend(['--title', metadata['title']])
            if 'artist' in metadata: cmd.extend(['--artist', metadata['artist']])
            if 'album' in metadata: cmd.extend(['--album', metadata['album']])
            if 'genre' in metadata: cmd.extend(['--genre', metadata['genre']])
            if 'year' in metadata: cmd.extend(['--release-year', str(metadata['year'])])
            if 'comments' in metadata:
                # eyeD3 usa el formato 'description:text' para comentarios
                cmd.extend(['--comment', f'eng:{metadata["comments"]}'])
            if 'bpm' in metadata:
                cmd.extend(['--bpm', str(metadata['bpm'])])
            if 'key' in metadata:
                # La opción correcta es --text-frame con el formato FID:TEXT
                cmd.extend(['--text-frame', f'TKEY:{metadata["key"]}'])
            
            # Ejecutar el comando
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"eyeD3 output: {result.stdout}")
            return True

        elif ext == '.flac':
            audio = FLAC(file_path)
            for key, value in metadata.items():
                # Mapeo simple para FLAC
                tag_name = key.upper()
                if key == 'comments': tag_name = 'COMMENT'
                if key == 'key': tag_name = 'INITIALKEY'
                audio[tag_name] = str(value)
            audio.save()
            return True

        elif ext == '.m4a' or ext == '.mp4':
            audio = MP4(file_path)
            if 'title' in metadata: audio['\xa9nam'] = [metadata['title']]
            if 'artist' in metadata: audio['\xa9ART'] = [metadata['artist']]
            if 'album' in metadata: audio['\xa9alb'] = [metadata['album']]
            if 'genre' in metadata: audio['\xa9gen'] = [metadata['genre']]
            if 'year' in metadata: audio['\xa9day'] = [str(metadata['year'])]
            if 'comments' in metadata: audio['\xa9cmt'] = [metadata['comments']]
            if 'key' in metadata: audio['----:com.apple.iTunes:initialkey'] = [metadata['key'].encode('utf-8')]
            if 'bpm' in metadata: audio['tmpo'] = [int(float(metadata['bpm']))]
            audio.save()
            return True

        elif ext == '.wav':
            # Guardar en .json auxiliar para WAV, ya que el soporte de tags es pobre
            json_path = os.path.splitext(file_path)[0] + '.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return True
            
        else:
            print(f"Formato de archivo no soportado para escritura directa: {ext}.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar eyeD3 en {file_path}:")
        print(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error al guardar metadatos en {file_path}: {e}")
        return False

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

if __name__ == '__main__':
    # Bloque de prueba
    # IMPORTANTE: Esta prueba MODIFICARÁ las etiquetas del archivo que especifiques.
    # Usa una copia de un archivo de audio para probar.
    
    # 1. Copia un archivo de audio a la raíz del proyecto y renómbralo a 'test_track.mp3'
    test_file = 'test_track.mp3'
    
    if os.path.exists(test_file):
        print(f"Probando la escritura de metadatos en '{test_file}'...")
        
        # Leer metadatos originales
        original_audio = mutagen.File(test_file, easy=True)
        original_title = original_audio.get('title', ['N/A'])[0]
        print(f"Título Original: '{original_title}'")

        # Escribir nuevos metadatos
        new_data = {'title': f'Test Title {int(time.time())}', 'album': 'DjAlfin Test Album'}
        success = write_metadata(test_file, new_data)

        if success:
            # Verificar que los metadatos se escribieron
            updated_audio = mutagen.File(test_file, easy=True)
            updated_title = updated_audio.get('title', ['ERROR'])[0]
            print(f"Nuevo Título: '{updated_title}'")
            
            # Restaurar título original
            print("Restaurando título original...")
            write_metadata(test_file, {'title': original_title})
            final_audio = mutagen.File(test_file, easy=True)
            print(f"Título restaurado a: '{final_audio.get('title', ['ERROR'])[0]}'")
    else:
        print(f"Archivo de prueba '{test_file}' no encontrado. "
              "Por favor, crea uno para ejecutar la prueba de escritura.") 