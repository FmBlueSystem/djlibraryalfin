# core/metadata_enricher.py
# VERSIÓN INTEGRADA CON SISTEMA MULTI-FUENTE

import re
import musicbrainzngs as mb
from . import spotify_client
from . import discogs_client
from .lastfm_client import search_lastfm_genres

# Importar nuevo sistema de agregación
from .multi_source_genre_aggregator import MultiSourceGenreAggregator
from .genre_confidence_scorer import SourceData

# Importar sistema de análisis de audio
from .audio_enrichment_service import get_audio_enrichment_service

# Es una buena práctica establecer un User-Agent para identificarnos ante la API.
mb.set_useragent("DjAlfin", "0.1", "https://github.com/FmBlueSystem/djlibraryalfin")

# Valores que consideramos "basura" o no informativos
JUNK_TERMS = {'', 'N/A', 'Unknown', 'None', None, 'Unknown Album', '0', 0}

# Sistema de agregación global
aggregator = MultiSourceGenreAggregator()

# Sistema de enriquecimiento de audio
audio_enrichment = get_audio_enrichment_service()

def _clean_text(text):
    """Limpia texto extra de los títulos y artistas para mejorar la búsqueda."""
    if not text:
        return ""
    text = str(text) # Asegurar que sea string
    # Elimina (text), [text], DJ Edit, Remix, etc.
    text = re.sub(r'\(.*?\)|\[.*?\]', '', text)
    # Elimina palabras clave comunes
    text = re.sub(r'(?i)\b(original mix|dj edit|remix|radio edit|club mix|extended|official video|lyric video)\b', '', text)
    # Elimina terminaciones comunes y espacios extra
    text = text.replace('_PN', '').strip()
    return text

def enrich_metadata(track_info: dict, include_audio_analysis: bool = True):
    """
    NUEVA VERSIÓN: Busca metadatos usando el sistema de agregación multi-fuente
    con scoring de confianza, encadenamiento contextual y análisis de audio.
    
    Args:
        track_info: Información básica del track
        include_audio_analysis: Si incluir análisis de características de audio
    """
    artist = track_info.get('artist')
    title = track_info.get('title')

    # Si no hay artista o título base, no podemos hacer mucho.
    if not all([artist, title]) or artist in JUNK_TERMS or title in JUNK_TERMS:
        print(f"Enrichment skipped for {artist} - {title} due to missing core info.")
        return {}

    print(f"🔄 Iniciando enriquecimiento completo para: {artist} - {title}")

    # === FASE 1: ENRIQUECIMIENTO DE METADATOS ===
    # Definir funciones de enriquecimiento para cada fuente
    enrichment_functions = {
        'musicbrainz': _search_musicbrainz_wrapper,
        'spotify': _search_spotify_wrapper,
        'discogs': _search_discogs_wrapper,
        'lastfm': _search_lastfm_wrapper
    }

    # Ejecutar agregación multi-fuente
    final_enriched_data = {}
    try:
        result = aggregator.aggregate_genres(track_info, enrichment_functions)
        
        # Si obtuvimos géneros del sistema agregado, usarlos
        if result.final_genres:
            final_enriched_data['genre'] = '; '.join(result.final_genres)
            print(f"🎵 Géneros agregados: {final_enriched_data['genre']}")
            print(f"📊 Confianza: {result.confidence_score:.2f}")
            print(f"🔗 Fuentes: {', '.join(result.sources_used)}")
        
        # Agregar otros metadatos del primer resultado exitoso
        for source_data in [sd for sd in aggregator.confidence_scorer.score_genres([]) if hasattr(sd, 'metadata')]:
            for key, value in source_data.metadata.items():
                if key != 'genre' and value not in JUNK_TERMS and key not in final_enriched_data:
                    final_enriched_data[key] = value
        
    except Exception as e:
        print(f"❌ Error en sistema multi-fuente: {e}")
    
    # Fallback al sistema original si el nuevo falla
    if not final_enriched_data:
        print("⚠️ Sistema multi-fuente sin resultados, usando sistema original...")
        try:
            final_enriched_data = _legacy_enrich_metadata(track_info)
        except Exception as e:
            print(f"❌ Error en sistema legacy: {e}")
            final_enriched_data = {}

    # === FASE 2: ANÁLISIS DE AUDIO ===
    if include_audio_analysis and track_info.get('file_path'):
        try:
            print(f"🎵 Iniciando análisis de audio para: {title}")
            
            # Combinar datos existentes con track_info para el análisis
            combined_track_info = track_info.copy()
            combined_track_info.update(final_enriched_data)
            
            # Enriquecer con características de audio
            audio_enriched = audio_enrichment.enrich_track_audio_features(combined_track_info)
            
            # Extraer solo las características de audio nuevas
            audio_fields = [
                'energy', 'danceability', 'valence', 'acousticness', 'instrumentalness',
                'liveness', 'speechiness', 'loudness',
                'spectral_centroid', 'spectral_rolloff', 'zero_crossing_rate', 'mfcc_features',
                'beat_strength', 'rhythm_consistency', 'dynamic_range',
                'intro_length', 'outro_length', 'mix_in_point', 'mix_out_point',
                'audio_analysis_confidence', 'audio_features_version', 'audio_analyzed_date'
            ]
            
            # Añadir características de audio al resultado final
            for field in audio_fields:
                if field in audio_enriched:
                    final_enriched_data[field] = audio_enriched[field]
            
            # Actualizar BPM y key si el análisis de audio es más confiable
            if 'bpm' in audio_enriched and audio_enriched.get('audio_analysis_confidence', 0) > 0.7:
                if not final_enriched_data.get('bpm') or audio_enriched.get('bpm_confidence', 0) > 0.8:
                    final_enriched_data['bpm'] = audio_enriched['bpm']
                    final_enriched_data['bpm_confidence'] = audio_enriched.get('bpm_confidence')
            
            if 'key' in audio_enriched and audio_enriched['key'] != "Unknown":
                final_enriched_data['key'] = audio_enriched['key']
            
            print(f"✅ Análisis de audio completado - Energy: {audio_enriched.get('energy', 'N/A'):.2f}, Danceability: {audio_enriched.get('danceability', 'N/A'):.2f}")
            
        except Exception as e:
            print(f"⚠️ Error en análisis de audio: {e}")
            # Continúar sin análisis de audio
    
    return final_enriched_data

def _search_musicbrainz_wrapper(track_info: dict, source: str) -> dict:
    """Wrapper para compatibilidad con el sistema de agregación."""
    try:
        result = _search_musicbrainz(track_info)
        return result if result else {}
    except Exception as e:
        print(f"❌ Error en MusicBrainz wrapper: {e}")
        return {}

def _search_spotify_wrapper(track_info: dict, source: str) -> dict:
    """Wrapper para compatibilidad con el sistema de agregación."""
    try:
        result = _search_spotify(track_info)
        return result if result else {}
    except Exception as e:
        print(f"❌ Error en Spotify wrapper: {e}")
        return {}

def _search_discogs_wrapper(track_info: dict, source: str) -> dict:
    """Wrapper para compatibilidad con el sistema de agregación."""
    try:
        result = _search_discogs(track_info)
        return result if result else {}
    except Exception as e:
        print(f"❌ Error en Discogs wrapper: {e}")
        return {}

def _search_lastfm_wrapper(track_info: dict, source: str) -> dict:
    """Wrapper para Last.fm compatible con el sistema de agregación."""
    try:
        artist = track_info.get('artist', '')
        title = track_info.get('title', '')
        result = search_lastfm_genres(artist, title)
        return result if result else {}
    except Exception as e:
        print(f"❌ Error en Last.fm wrapper: {e}")
        return {}

def _legacy_enrich_metadata(track_info: dict):
    """Sistema de enriquecimiento original como fallback."""
    # ... (código original del metadata_enricher)
    # Esta función contendría la lógica original para casos de emergencia
    
    print(f"Attempting legacy enrichment for: {track_info.get('artist')} - {track_info.get('title')}")
    
    # --- 1. Búsqueda en MusicBrainz ---
    mb_data = _search_musicbrainz(track_info)
    
    # --- 2. Búsqueda en Spotify ---
    spotify_data = _search_spotify(track_info, mb_data)
    
    # --- 3. Búsqueda en Discogs ---
    discogs_data = _search_discogs(track_info, mb_data, spotify_data)

    # --- 4. Fusionar resultados (lógica original) ---
    final_enriched_data = {}

    # Fusionar MusicBrainz
    if mb_data:
        final_enriched_data.update(mb_data)

    # Fusionar Spotify
    if spotify_data:
        for key, value in spotify_data.items():
            if value not in JUNK_TERMS:
                if key in final_enriched_data and final_enriched_data[key] not in JUNK_TERMS:
                    if key == 'album':
                        if len(str(value)) > len(str(final_enriched_data[key])):
                            final_enriched_data[key] = value
                    elif key == 'year':
                        final_enriched_data[key] = value 
                    elif key == 'genre':
                         final_enriched_data[key] = value
                    else: 
                        pass
                else:
                    final_enriched_data[key] = value

    # Fusionar Discogs
    if discogs_data:
        for key, value in discogs_data.items():
            if value not in JUNK_TERMS:
                if key in final_enriched_data and final_enriched_data[key] not in JUNK_TERMS:
                    if key == 'album':
                        if len(str(value)) > len(str(final_enriched_data[key])):
                            final_enriched_data[key] = value
                    elif key == 'year':
                        final_enriched_data[key] = value 
                    elif key == 'genre':
                        current_genre = final_enriched_data.get('genre', "")
                        if current_genre in JUNK_TERMS or len(str(value)) > len(current_genre):
                             final_enriched_data[key] = value
                else:
                    final_enriched_data[key] = value
    
    # Curación final del género
    if 'genre' in final_enriched_data and final_enriched_data['genre'] not in JUNK_TERMS:
        final_enriched_data['genre'] = _curate_genres(final_enriched_data['genre'])
    
    return final_enriched_data

# Resto de funciones originales (sin cambios)
def _search_musicbrainz(track_info: dict):
    cleaned_artist = _clean_text(track_info.get('artist'))
    cleaned_title = _clean_text(track_info.get('title'))
    original_artist = track_info.get('artist', '')
    original_title = track_info.get('title', '')
    
    enriched_data = {}

    def _perform_mb_search(search_artist_term, search_title_term):
        data = {}
        if not search_artist_term or not search_title_term:
            return data
        try:
            print(f"Buscando en MusicBrainz: '{search_artist_term}' - '{search_title_term}'")
            result = mb.search_recordings(query=search_title_term, artist=search_artist_term, limit=1, strict=False)
            
            if result.get('recording-list'):
                recording = result['recording-list'][0]
                data['musicbrainz_recording_id'] = recording.get('id')

                if 'title' in recording and recording['title'] not in JUNK_TERMS:
                    data['title'] = recording['title']

                if 'artist-credit' in recording and recording['artist-credit']:
                    artist_credit = recording['artist-credit'][0]['artist']
                    data['musicbrainz_artist_id'] = artist_credit.get('id')
                    if artist_credit.get('name') not in JUNK_TERMS:
                        data['artist'] = artist_credit['name']
                    
                    # Extraer género del artista
                    try:
                        artist_info = mb.get_artist_by_id(artist_credit.get('id'), includes=['tags'])
                        if artist_info.get('artist', {}).get('tag-list'):
                            tags = [tag['name'] for tag in artist_info['artist']['tag-list']]
                            if tags:
                                data['genre'] = ", ".join(tags)
                    except:
                        pass

                if 'release-list' in recording and recording['release-list']:
                    release = recording['release-list'][0]
                    if release.get('date') and str(release['date']).split('-')[0] not in JUNK_TERMS:
                        data['year'] = str(release['date']).split('-')[0]
                    if release.get('title') not in JUNK_TERMS:
                        data['album'] = release['title']
                    if release.get('id'):
                        data['musicbrainz_release_id'] = release.get('id')
                        try:
                            cover_art = mb.get_release_group_image_list(release.get('release-group', {}).get('id'))
                            if cover_art and cover_art.get('images'):
                                for image_info in cover_art['images']:
                                    if image_info.get('front') and image_info.get('image'):
                                        data['album_art_url'] = image_info['image']
                                        break
                        except mb.ResponseError:
                            pass
        except Exception as e:
            print(f"Error durante la búsqueda en MusicBrainz: {e}")
        return data

    data = _perform_mb_search(cleaned_artist, cleaned_title)
    if not data.get('musicbrainz_recording_id') and (original_artist != cleaned_artist or original_title != cleaned_title):
        print(f"INFO: Búsqueda limpia en MusicBrainz falló. Reintentando con términos originales.")
        data.update(_perform_mb_search(original_artist, original_title))

    if data:
        print(f"-> Datos de MusicBrainz: {data}")
    return data

def _search_spotify(track_info: dict, mb_data: dict = None):
    artist_to_search = _clean_text(track_info.get('artist'))
    title_to_search = _clean_text(track_info.get('title'))
    
    spotify_enriched_data = {}

    if not artist_to_search or not title_to_search:
        return spotify_enriched_data

    print(f"Buscando en Spotify: '{artist_to_search}' - '{title_to_search}'")
    spotify_track_data = spotify_client.search_track(artist_to_search, title_to_search)
    
    if not spotify_track_data:
        original_artist = track_info.get('artist', '')
        original_title = track_info.get('title', '')
        if original_artist != artist_to_search or original_title != title_to_search:
            print(f"INFO: Búsqueda limpia en Spotify falló. Reintentando con título original.")
            spotify_track_data = spotify_client.search_track(original_artist, original_title)

    if spotify_track_data:
        spotify_enriched_data['spotify_track_id'] = spotify_track_data.get('id')
        
        if spotify_track_data.get('name') not in JUNK_TERMS:
             spotify_enriched_data['title'] = spotify_track_data.get('name')

        album_info = spotify_track_data.get('album', {})
        if album_info:
            spotify_enriched_data['spotify_album_id'] = album_info.get('id')
            if album_info.get('name') not in JUNK_TERMS:
                spotify_enriched_data['album'] = album_info.get('name')
            if album_info.get('release_date') and str(album_info['release_date']).split('-')[0] not in JUNK_TERMS:
                spotify_enriched_data['year'] = str(album_info['release_date']).split('-')[0]
            
            if album_info.get('id'):
                art_url = spotify_client.get_album_art_url(album_info['id'])
                if art_url:
                    spotify_enriched_data['album_art_url'] = art_url

        if spotify_track_data.get('artists'):
            main_spotify_artist = spotify_track_data['artists'][0]
            spotify_enriched_data['spotify_artist_id'] = main_spotify_artist.get('id')
            if main_spotify_artist.get('name') not in JUNK_TERMS:
                 spotify_enriched_data['artist'] = main_spotify_artist.get('name')

            try:
                client = spotify_client.get_spotify_client()
                if client and main_spotify_artist.get('id'):
                    artist_details = client.artist(main_spotify_artist['id'])
                    if artist_details and artist_details.get('genres'):
                        spotify_enriched_data['genre'] = ", ".join(artist_details['genres'])
            except Exception as e:
                print(f"ADVERTENCIA: No se pudo obtener el género del artista de Spotify: {e}")
        
        if spotify_enriched_data:
            print(f"-> Datos de Spotify: {spotify_enriched_data}")
            
    return spotify_enriched_data

def _search_discogs(track_info: dict, mb_data: dict = None, spotify_data: dict = None):
    artist_to_search = _clean_text(track_info.get('artist'))
    title_to_search = _clean_text(track_info.get('title'))
    album_title_to_search = _clean_text(track_info.get('album'))

    search_term_for_discogs = album_title_to_search if album_title_to_search not in JUNK_TERMS else title_to_search

    discogs_enriched_data = {}

    if not artist_to_search or not search_term_for_discogs:
        return discogs_enriched_data

    print(f"Buscando en Discogs (release): '{artist_to_search}' - '{search_term_for_discogs}'")
    discogs_release_data = discogs_client.search_release(artist_to_search, search_term_for_discogs)

    if discogs_release_data:
        discogs_enriched_data['discogs_release_id'] = discogs_release_data.get('id')
        
        if discogs_release_data.get('year') and str(discogs_release_data.get('year')) not in JUNK_TERMS :
            discogs_enriched_data['year'] = str(discogs_release_data.get('year'))
        
        discogs_api_title = discogs_release_data.get('title', '').replace(f"{discogs_release_data.get('artist', '')} - ", '')
        if track_info.get('album') in JUNK_TERMS and discogs_api_title not in JUNK_TERMS:
            discogs_enriched_data['album'] = discogs_api_title

        if discogs_release_data.get('genre'):
            discogs_enriched_data['genre'] = ", ".join(discogs_release_data.get('genre', []))
        if discogs_release_data.get('style'):
            current_genres = discogs_enriched_data.get('genre', "")
            styles_str = ", ".join(discogs_release_data.get('style', []))
            if styles_str:
                if current_genres:
                    discogs_enriched_data['genre'] = f"{current_genres}, {styles_str}"
                else:
                    discogs_enriched_data['genre'] = styles_str
        
        if discogs_release_data.get('cover_image'):
            discogs_enriched_data['album_art_url'] = discogs_release_data.get('cover_image')
        
        if discogs_enriched_data:
            print(f"-> Datos de Discogs: {discogs_enriched_data}")

    return discogs_enriched_data

def _curate_genres(genre_string: str, max_genres=4):
    """Función de curación original (sin cambios)."""
    if not genre_string or genre_string in JUNK_TERMS:
        return ""

    # More precise blacklist - only remove terms that add no musical value
    blacklist = [
        # Non-musical terms
        'music', 'audio', 'sound', 'artist', 'band', 'universal fire victim',
        # Geographic terms (but preserve musical geography like "uk garage")
        'british', 'english', 'american', 'swedish', 'german', 'french', 
        'canadian', 'japanese', 'australian', 'european', 'latin', 'nordic', 'western',
        # Size/quality adjectives that add no musical information
        'big', 'little', 'small', 'large', 'great', 'super', 'mega', 'ultra',
        'modern', 'classic', 'original', 'mainstream', 'underground',
        # Time periods - be more selective
        'early', 'late', 'contemporary', 'retro', 'vintage', 'current',
        'various', 'album', 'single', 'ep', 'compilation', 'collection',
        # Functional/mood categories that aren't true genres
        'background', 'easy listening', 'satire', 'show tunes', 'soundtrack', 'ost',
        'christmas', 'holiday', 'workout', 'sleep', 'meditation', 'focus', 'relaxation', 'study',
        # Chart/popularity terms  
        'and', 'chart', 'charts', 'top', 'hits', 'hit', 'popular', 'greatest', 'best',
        'platinum', 'gold', 'billboard', 'radio', 'fm', 'commercial'
    ]
    
    # Preserve compound genres as single units - expanded list
    compound_genres = [
        'art pop', 'art rock', 'dream pop', 'indie pop', 'indie rock', 'indie folk',
        'hard rock', 'soft rock', 'yacht rock', 'arena rock', 'garage rock',
        'folk rock', 'country rock', 'blues rock', 'psychedelic rock',
        'new wave', 'dark wave', 'cold wave', 'minimal wave',
        'deep house', 'tech house', 'progressive house', 'tribal house', 'funky house',
        'disco house', 'future house', 'bass house', 'electro house',
        'drum and bass', 'drum n bass', 'liquid drum and bass',
        'trip hop', 'hip hop', 'boom bap', 'trap music',
        'post punk', 'post rock', 'post hardcore', 'post metal',
        'black metal', 'death metal', 'power metal', 'heavy metal',
        'nu disco', 'nu metal', 'nu jazz', 'uk garage', 'us garage',
        'alternative rock', 'progressive rock', 'classic rock'
    ]
    
    year_regex = r'\b\d{4}s?\b|\b\d{2,3}s\b'

    # Split and normalize
    genres = [g.strip().lower() for g in genre_string.replace(';', ',').replace('/',',').split(',')]
    
    curated_genres = []
    for genre in genres:
        original_genre = genre
        genre = re.sub(year_regex, '', genre).strip()
        
        if not genre:
            continue
            
        # Check if this is a compound genre we want to preserve
        is_compound = any(compound in genre for compound in compound_genres)
        
        if is_compound:
            geographic_terms = ['british', 'english', 'american', 'uk', 'us', 'european']
            for geo_term in geographic_terms:
                pattern = r'\b' + re.escape(geo_term) + r'\b'
                genre = re.sub(pattern, '', genre, flags=re.IGNORECASE).strip()
            genre = ' '.join(genre.split())
        else:
            for blacklisted_term in blacklist:
                if blacklisted_term in ['us', 'uk']:
                    pattern = r'\b' + re.escape(blacklisted_term) + r'\b(?!\w)'
                else:
                    pattern = r'\b' + re.escape(blacklisted_term) + r'\b'
                genre = re.sub(pattern, '', genre, flags=re.IGNORECASE).strip()
        
        genre = ' '.join(genre.split())
        
        if not genre:
            continue
            
        if genre.lower() in blacklist:
            continue
            
        known_short_genres = ['pop', 'rock', 'folk', 'jazz', 'soul', 'funk', 'r&b', 'edm', 'dnb']
        if len(genre) < 3 and genre.lower() not in known_short_genres:
            continue
            
        if ' ' not in genre and genre.lower() in ['big', 'little', 'new', 'old', 'alternative']:
            continue
            
        curated_genres.append(genre)

    unique_genres = list(dict.fromkeys(curated_genres))
    
    # Quality filter
    quality_filtered = []
    for genre in unique_genres:
        is_duplicate = False
        for existing in quality_filtered:
            if genre in existing or existing in genre:
                if len(genre) > len(existing):
                    quality_filtered[quality_filtered.index(existing)] = genre
                is_duplicate = True
                break
        
        if not is_duplicate:
            quality_filtered.append(genre)
    
    ACRONYMS = {'edm', 'r&b', 'idm', 'ebm', 'dnb', 'uk garage', 'us garage', 'nu-disco'} 
    
    SPECIAL_CAPS = {
        'art pop': 'Art Pop', 'art rock': 'Art Rock', 'dream pop': 'Dream Pop',
        'indie pop': 'Indie Pop', 'indie rock': 'Indie Rock', 'hard rock': 'Hard Rock',
        'soft rock': 'Soft Rock', 'folk rock': 'Folk Rock', 'country rock': 'Country Rock',
        'blues rock': 'Blues Rock', 'hip hop': 'Hip-Hop', 'trip hop': 'Trip-Hop',
        'drum and bass': 'Drum & Bass', 'drum n bass': 'Drum & Bass',
        'post punk': 'Post-Punk', 'post rock': 'Post-Rock', 'new wave': 'New Wave',
        'dark wave': 'Darkwave', 'deep house': 'Deep House', 'tech house': 'Tech House',
        'progressive house': 'Progressive House'
    }
    
    formatted_genres = []
    for genre in quality_filtered:
        if genre.lower() in SPECIAL_CAPS:
            formatted_genres.append(SPECIAL_CAPS[genre.lower()])
            continue
            
        if genre.lower() in ACRONYMS:
            if genre.lower() == 'uk garage': 
                formatted_genres.append('UK Garage')
            elif genre.lower() == 'us garage': 
                formatted_genres.append('US Garage')
            elif genre.lower() == 'nu-disco': 
                formatted_genres.append('Nu-Disco')
            elif genre.lower() == 'dnb':
                formatted_genres.append('DnB')
            else: 
                formatted_genres.append(genre.upper())
            continue
        
        genre_title_case = genre.title()
        
        fixes = [
            ("R&b", "R&B"), ("Uk ", "UK "), ("Us ", "US "), ("Dj ", "DJ "),
            ("Edm", "EDM"), ("Idm", "IDM"), ("Ebm", "EBM"), ("Dnb", "DnB"),
            ("And", "&"), (" And ", " & ")
        ]
        
        for old, new in fixes:
            genre_title_case = genre_title_case.replace(old, new)
        
        formatted_genres.append(genre_title_case)

    def genre_priority(genre):
        if ' ' in genre or '-' in genre or '&' in genre:
            return 0
        elif len(genre) > 6:
            return 1
        else:
            return 2
    
    formatted_genres.sort(key=genre_priority)
    
    final_list = formatted_genres[:max_genres]
    return "; ".join(final_list)

# Función para obtener estadísticas del nuevo sistema
def get_aggregation_performance_stats():
    """Retorna estadísticas de rendimiento del sistema de agregación."""
    return aggregator.get_performance_stats()

def optimize_aggregation_priorities():
    """Optimiza prioridades del sistema de agregación basándose en estadísticas."""
    aggregator.optimize_source_priorities()
