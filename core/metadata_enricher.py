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
    
    # --- 2. Búsqueda en Spotify (especialmente para género) ---
    spotify_data = _search_spotify(track_info)
    
    # --- 3. Fusionar resultados (Spotify tiene prioridad para género) ---
    final_data = mb_data
    if spotify_data.get('genre'):
        final_data['genre'] = spotify_data['genre']
        
    if final_data:
        print(f"-> Datos combinados encontrados: {final_data}")
        
    return final_data

def _search_musicbrainz(track_info):
    cleaned_artist = _clean_text(track_info.get('artist'))
    cleaned_title = _clean_text(track_info.get('title'))
    if not cleaned_artist or not cleaned_title: return {}
    
    enriched_data = {}
    try:
        print(f"Buscando en MusicBrainz: '{cleaned_artist}' - '{cleaned_title}'")
        result = mb.search_recordings(query=cleaned_title, artist=cleaned_artist, limit=1, strict=False)
        
        if not result.get('recording-list'): return {}
        
        recording = result['recording-list'][0]
        if track_info.get('year') in JUNK_TERMS and 'release-list' in recording and recording['release-list']:
            release = recording['release-list'][0]
            if 'date' in release: enriched_data['year'] = release['date'].split('-')[0]
        if track_info.get('album') in JUNK_TERMS and 'release-list' in recording and recording['release-list']:
             release = recording['release-list'][0]
             if 'title' in release: enriched_data['album'] = release['title']
    except Exception as e:
        print(f"Error en MusicBrainz: {e}")
        
    return enriched_data

def _search_spotify(track_info):
    """Busca en Spotify, principalmente para obtener el género."""
    if track_info.get('genre') not in JUNK_TERMS:
        return {} # Ya tenemos un género, no buscar
        
    artist = _clean_text(track_info.get('artist'))
    title = _clean_text(track_info.get('title'))
    if not artist or not title: return {}

    print(f"Buscando en Spotify: '{artist}' - '{title}'")
    spotify_track = spotify_client.search_track(artist, title)
    
    if not spotify_track:
        return {}
    
    # Spotify a menudo asigna géneros al artista, no a la pista. Es un buen fallback.
    artist_id = spotify_track['artists'][0]['id']
    artist_info = spotify_client.spotify_client.artist(artist_id)
    
    if artist_info and artist_info.get('genres'):
        genres = [g.capitalize() for g in artist_info['genres']]
        return {'genre': ", ".join(genres)}
        
    return {} 