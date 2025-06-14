# core/metadata_enricher.py

import re
import musicbrainzngs as mb
from . import spotify_client

# Es una buena práctica establecer un User-Agent para identificarnos ante la API.
mb.set_useragent("DjAlfin", "0.1", "https://github.com/FmBlueSystem/djlibraryalfin")

# Valores que consideramos "basura" o no informativos
JUNK_TERMS = {'', 'N/A', 'Unknown', 'None', None, 'Unknown Album', '0'}

def _clean_text(text):
    """Limpia texto extra de los títulos y artistas para mejorar la búsqueda."""
    if not text:
        return ""
    # Elimina (text), [text], DJ Edit, Remix, etc.
    text = re.sub(r'\(.*?\)|\[.*?\]', '', text)
    # Elimina palabras clave comunes
    text = re.sub(r'(?i)\b(original mix|dj edit|remix|radio edit|club mix|extended)\b', '', text)
    # Elimina terminaciones comunes y espacios extra
    text = text.replace('_PN', '').strip()
    return text

def enrich_metadata(track_info: dict):
    """
    Busca metadatos en MusicBrainz si los campos clave faltan o contienen
    información genérica. Usa una búsqueda en dos fases (estricta y flexible).
    """
    artist = track_info.get('artist')
    title = track_info.get('title')

    if not all([artist, title]):
        return {}

    needs_enrichment = any(track_info.get(key) in JUNK_TERMS for key in ['album', 'year', 'genre'])
    if not needs_enrichment:
        return {}
    
    # --- 1. Búsqueda en MusicBrainz ---
    mb_data = _search_musicbrainz(track_info)
    
    # --- 2. Búsqueda en Spotify (especialmente para género, pero también año/álbum) ---
    spotify_data = _search_spotify(track_info)
    
    # --- 3. Fusionar resultados ---
    # Empezar con los datos de MusicBrainz, que son una buena base
    final_data = mb_data.copy()
    
    # Sobrescribir o añadir datos de Spotify. Spotify tiene prioridad porque
    # a menudo tiene mejor calidad de género, año y títulos de álbum.
    if spotify_data:
        # Hacemos una copia para no modificar el diccionario original de Spotify
        data_to_merge = spotify_data.copy()

        # Regla especial para el álbum: si ya tenemos uno, comparar y conservar el más largo (más específico).
        current_album = final_data.get('album')
        new_album = data_to_merge.get('album')
        if current_album and current_album not in JUNK_TERMS and new_album:
            if len(current_album) > len(new_album):
                # El álbum actual es mejor, así que no lo sobrescribimos.
                # Lo eliminamos de los datos a fusionar.
                del data_to_merge['album']
        
        # Fusionar el resto de los datos (o el álbum si el original era basura)
        final_data.update(data_to_merge)
        
    if final_data:
        print(f"-> Datos combinados encontrados: {final_data}")
        
    # Devolver solo los campos que realmente han cambiado o se han añadido
    return {k: v for k, v in final_data.items() if str(track_info.get(k)) != str(v)}

def _search_musicbrainz(track_info: dict):
    """
    Busca en MusicBrainz usando una estrategia de dos pasos: primero con texto
    limpio, y si falla, con el texto original.
    """
    cleaned_artist = _clean_text(track_info.get('artist'))
    cleaned_title = _clean_text(track_info.get('title'))
    original_title = track_info.get('title', '')

    def _perform_search(artist, title):
        """Función anidada para ejecutar la búsqueda y parsear los resultados."""
        if not artist or not title:
            return {}
        
        enriched_data = {}
        try:
            print(f"Buscando en MusicBrainz: '{artist}' - '{title}'")
            # El include 'tags' no funciona en search, se debe hacer un lookup posterior
            result = mb.search_recordings(query=title, artist=artist, limit=1, strict=False)
            
            if not result.get('recording-list'):
                return {}
            
            recording = result['recording-list'][0]
            
            # Extraer año y álbum de la lista de lanzamientos
            if 'release-list' in recording and recording['release-list']:
                release = recording['release-list'][0]
                if 'date' in release and track_info.get('year') in JUNK_TERMS:
                    enriched_data['year'] = release['date'].split('-')[0]
                if 'title' in release and track_info.get('album') in JUNK_TERMS:
                    enriched_data['album'] = release['title']

            # Extraer género desde las etiquetas del artista (más común en MusicBrainz)
            if 'artist-credit' in recording and recording['artist-credit']:
                artist_id = recording['artist-credit'][0]['artist']['id']
                artist_info = mb.get_artist_by_id(artist_id, includes=['tags'])
                if artist_info.get('artist', {}).get('tag-list'):
                    tags = [tag['name'].capitalize() for tag in artist_info['artist']['tag-list']]
                    enriched_data['genre'] = ", ".join(tags)

        except Exception as e:
            print(f"Error durante la búsqueda en MusicBrainz: {e}")
        
        return enriched_data

    # 1. Búsqueda con texto limpio
    data = _perform_search(cleaned_artist, cleaned_title)
    
    # 2. Fallback a búsqueda con texto original si la limpia no arrojó resultados
    if not data and original_title != cleaned_title:
        print(f"INFO: Búsqueda limpia en MusicBrainz falló. Reintentando con título original.")
        data = _perform_search(cleaned_artist, original_title)

    return data

def _search_spotify(track_info):
    """
    Busca en Spotify usando una estrategia de dos fases y extrae metadatos
    de la pista y del artista.
    """
    # No buscar si ya tenemos un género que no sea un valor "basura"
    if track_info.get('genre') not in JUNK_TERMS:
        return {} 
        
    cleaned_artist = _clean_text(track_info.get('artist'))
    cleaned_title = _clean_text(track_info.get('title'))
    original_title = track_info.get('title', '')
    
    spotify_track = None

    # 1. Búsqueda con texto limpio
    if cleaned_artist and cleaned_title:
        print(f"Buscando en Spotify: '{cleaned_artist}' - '{cleaned_title}'")
        spotify_track = spotify_client.search_track(cleaned_artist, cleaned_title)
    
    # 2. Fallback a búsqueda con texto original
    if not spotify_track and original_title != cleaned_title:
        print(f"INFO: Búsqueda limpia en Spotify falló. Reintentando con título original.")
        spotify_track = spotify_client.search_track(cleaned_artist, original_title)
    
    if not spotify_track:
        return {}
    
    # Contenedor para todos los datos que encontremos en Spotify
    spotify_data = {}
    
    # 3. Extraer Género desde el Artista (más fiable)
    try:
        # Usar el primer artista de la lista de la pista encontrada
        artist_id = spotify_track['artists'][0]['id']
        artist_info = spotify_client.spotify_client.artist(artist_id)
        if artist_info and artist_info.get('genres'):
            # Capitalizar cada género para un formato limpio
            genres = [g.capitalize() for g in artist_info['genres']]
            spotify_data['genre'] = ", ".join(genres)
    except (IndexError, TypeError, KeyError) as e:
        print(f"ADVERTENCIA: No se pudo obtener el género del artista de Spotify: {e}")

    # 4. Extraer Año y Álbum desde la Pista (pueden ser más precisos)
    try:
        if 'album' in spotify_track:
            album_info = spotify_track['album']
            # Extraer el año de la fecha de lanzamiento
            if 'release_date' in album_info:
                release_date = album_info['release_date']
                spotify_data['year'] = release_date.split('-')[0]
            # Extraer el nombre del álbum
            if 'name' in album_info:
                spotify_data['album'] = album_info['name']
    except (TypeError, KeyError) as e:
        print(f"ADVERTENCIA: No se pudo obtener año/álbum de Spotify: {e}")

    if spotify_data:
        print(f"-> Datos de Spotify encontrados: {spotify_data}")

    return spotify_data