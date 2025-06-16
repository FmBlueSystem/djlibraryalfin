# core/metadata_enricher.py

import re
import musicbrainzngs as mb
from . import spotify_client # Ya modificado para incluir album_id, main_artist_id y get_album_art_url
from . import discogs_client # Nuevo cliente

# Es una buena práctica establecer un User-Agent para identificarnos ante la API.
mb.set_useragent("DjAlfin", "0.1", "https://github.com/FmBlueSystem/djlibraryalfin")

# Valores que consideramos "basura" o no informativos
JUNK_TERMS = {'', 'N/A', 'Unknown', 'None', None, 'Unknown Album', '0', 0} # Añadido 0 numérico

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

def enrich_metadata(track_info: dict):
    """
    Busca metadatos en MusicBrainz, Spotify y Discogs si los campos clave faltan 
    o contienen información genérica.
    """
    artist = track_info.get('artist')
    title = track_info.get('title')

    # Si no hay artista o título base, no podemos hacer mucho.
    if not all([artist, title]) or artist in JUNK_TERMS or title in JUNK_TERMS:
        print(f"Enrichment skipped for {artist} - {title} due to missing core info.")
        return {} # Devuelve un diccionario vacío si no se puede enriquecer

    # Datos que se intentarán enriquecer si son "junk"
    keys_to_check_for_junk = ['album', 'year', 'genre', 'album_art_url']
    
    # Comprobar si alguno de los campos importantes es "junk" o si faltan IDs clave
    needs_enrichment = any(str(track_info.get(key, '')).strip() in JUNK_TERMS for key in keys_to_check_for_junk)
    if not needs_enrichment and all(k in track_info for k in ['musicbrainz_recording_id', 'spotify_track_id', 'discogs_release_id']):
        # Si no hay nada "junk" y ya tenemos todos los IDs, podríamos saltar
        # Pero por ahora, procedemos si hay algo junk, para asegurar que se intenten llenar todos los campos.
        pass

    print(f"Attempting enrichment for: {artist} - {title}")

    # --- 1. Búsqueda en MusicBrainz ---
    mb_data = _search_musicbrainz(track_info)
    
    # --- 2. Búsqueda en Spotify ---
    spotify_data = _search_spotify(track_info, mb_data) # Pasar mb_data por si tiene IDs útiles
    
    # --- 3. Búsqueda en Discogs ---
    # Podríamos pasar spotify_data también si Discogs se beneficia de IDs de Spotify
    discogs_data = _search_discogs(track_info, mb_data, spotify_data)

    # --- 4. Fusionar resultados ---
    # Empezar con una copia de los datos originales para no perder nada
    final_enriched_data = {}

    # Prioridad: MusicBrainz -> Spotify -> Discogs para la mayoría de los campos.
    # Los datos originales (track_info) tendrán la máxima prioridad en el library_scanner.
    # Aquí solo estamos recolectando datos *adicionales* o *mejores*.

    # Fusionar MusicBrainz
    if mb_data:
        final_enriched_data.update(mb_data)

    # Fusionar Spotify, dando prioridad a ciertos campos de Spotify si existen y son mejores
    if spotify_data:
        for key, value in spotify_data.items():
            if value not in JUNK_TERMS:
                # Si el campo ya existe de MB y no es junk, decidir si Spotify es mejor
                if key in final_enriched_data and final_enriched_data[key] not in JUNK_TERMS:
                    if key == 'album': # Regla especial para álbum: conservar el más largo
                        if len(str(value)) > len(str(final_enriched_data[key])):
                            final_enriched_data[key] = value
                    elif key == 'year': # Spotify a veces tiene años más precisos para lanzamientos digitales
                        final_enriched_data[key] = value 
                    elif key == 'genre': # El género de Spotify puede ser más moderno/relevante
                         final_enriched_data[key] = value # Se curará después
                    # Para otros campos, MB podría tener prioridad si ya existe.
                    # Por ahora, si Spotify tiene algo no-junk, lo usamos si MB no lo tenía o era junk.
                    else: 
                        pass # Mantener el valor de MB
                else: # Si no estaba en MB o era junk, tomar el de Spotify
                    final_enriched_data[key] = value

    # Fusionar Discogs, similar a Spotify
    if discogs_data:
        for key, value in discogs_data.items():
            if value not in JUNK_TERMS:
                if key in final_enriched_data and final_enriched_data[key] not in JUNK_TERMS:
                    if key == 'album':
                        if len(str(value)) > len(str(final_enriched_data[key])):
                            final_enriched_data[key] = value
                    elif key == 'year': # Discogs es bueno para años de ediciones específicas
                        # Podríamos tener una lógica más compleja aquí, ej. si el año de Discogs es más específico
                        final_enriched_data[key] = value 
                    elif key == 'genre': # Discogs tiene géneros y estilos muy detallados
                        # Combinar con existente si es diferente, o reemplazar si el existente es genérico
                        current_genre = final_enriched_data.get('genre', "")
                        if current_genre in JUNK_TERMS or len(str(value)) > len(current_genre):
                             final_enriched_data[key] = value # Se curará después
                else:
                    final_enriched_data[key] = value
    
    # Curación final del género
    if 'genre' in final_enriched_data and final_enriched_data['genre'] not in JUNK_TERMS:
        final_enriched_data['genre'] = _curate_genres(final_enriched_data['genre'])
    
    if final_enriched_data:
        print(f"-> Datos enriquecidos combinados para '{artist} - {title}': {final_enriched_data}")
        
    return final_enriched_data

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
                    data['title'] = recording['title'] # MB puede tener mejor capitalización o versiones

                if 'artist-credit' in recording and recording['artist-credit']:
                    artist_credit = recording['artist-credit'][0]['artist']
                    data['musicbrainz_artist_id'] = artist_credit.get('id')
                    if artist_credit.get('name') not in JUNK_TERMS:
                        data['artist'] = artist_credit['name']
                    
                    # Extraer género del artista si no hay uno mejor de otra fuente
                    artist_info = mb.get_artist_by_id(artist_credit.get('id'), includes=['tags'])
                    if artist_info.get('artist', {}).get('tag-list'):
                        tags = [tag['name'] for tag in artist_info['artist']['tag-list']]
                        if tags:
                            data['genre'] = ", ".join(tags) # Se curará después

                if 'release-list' in recording and recording['release-list']:
                    release = recording['release-list'][0] # Tomar el primer lanzamiento asociado
                    if release.get('date') and str(release['date']).split('-')[0] not in JUNK_TERMS:
                        data['year'] = str(release['date']).split('-')[0]
                    if release.get('title') not in JUNK_TERMS:
                        data['album'] = release['title']
                    if release.get('id'):
                        data['musicbrainz_release_id'] = release.get('id')
                        # Intentar obtener arte de portada de Cover Art Archive
                        try:
                            cover_art = mb.get_release_group_image_list(release.get('release-group', {}).get('id'))
                            if cover_art and cover_art.get('images'):
                                for image_info in cover_art['images']:
                                    if image_info.get('front') and image_info.get('image'):
                                        data['album_art_url'] = image_info['image']
                                        break # Tomar la primera imagen frontal
                        except mb.ResponseError:
                            pass # No hay arte o error
        except Exception as e:
            print(f"Error durante la búsqueda en MusicBrainz ('{search_artist_term}' - '{search_title_term}'): {e}")
        return data

    data = _perform_mb_search(cleaned_artist, cleaned_title)
    if not data.get('musicbrainz_recording_id') and (original_artist != cleaned_artist or original_title != cleaned_title) :
        print(f"INFO: Búsqueda limpia en MusicBrainz falló. Reintentando con términos originales.")
        data.update(_perform_mb_search(original_artist, original_title)) # update para no perder datos parciales

    if data:
        print(f"-> Datos de MusicBrainz: {data}")
    return data

def _search_spotify(track_info: dict, mb_data: dict = None):
    # mb_data es opcional, pero puede ayudar a refinar la búsqueda si tenemos IDs
    artist_to_search = _clean_text(track_info.get('artist'))
    title_to_search = _clean_text(track_info.get('title'))
    
    spotify_enriched_data = {}

    if not artist_to_search or not title_to_search:
        return spotify_enriched_data

    print(f"Buscando en Spotify: '{artist_to_search}' - '{title_to_search}'")
    spotify_track_data = spotify_client.search_track(artist_to_search, title_to_search)
    
    if not spotify_track_data:
        # Fallback si la búsqueda limpia falla
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
            
            # Obtener URL de arte de portada
            if album_info.get('id'):
                art_url = spotify_client.get_album_art_url(album_info['id'])
                if art_url:
                    spotify_enriched_data['album_art_url'] = art_url

        if spotify_track_data.get('artists'):
            main_spotify_artist = spotify_track_data['artists'][0]
            spotify_enriched_data['spotify_artist_id'] = main_spotify_artist.get('id')
            if main_spotify_artist.get('name') not in JUNK_TERMS:
                 spotify_enriched_data['artist'] = main_spotify_artist.get('name')

            # Obtener género del artista principal de Spotify
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
    # mb_data y spotify_data son opcionales
    artist_to_search = _clean_text(track_info.get('artist'))
    title_to_search = _clean_text(track_info.get('title')) # Aquí title se refiere al título de la pista
    album_title_to_search = _clean_text(track_info.get('album'))

    # Priorizar búsqueda por álbum si está disponible y no es genérico
    search_term_for_discogs = album_title_to_search if album_title_to_search not in JUNK_TERMS else title_to_search

    discogs_enriched_data = {}

    if not artist_to_search or not search_term_for_discogs:
        return discogs_enriched_data

    print(f"Buscando en Discogs (release): '{artist_to_search}' - '{search_term_for_discogs}'")
    # Discogs busca por "release_title" que es más para álbumes/EPs
    discogs_release_data = discogs_client.search_release(artist_to_search, search_term_for_discogs)

    if discogs_release_data:
        discogs_enriched_data['discogs_release_id'] = discogs_release_data.get('id')
        
        # Discogs 'title' en la búsqueda es a menudo "Artista - Título del Álbum"
        # Necesitamos parsearlo o usar los campos específicos si están.
        # Por ahora, tomamos los campos que Discogs devuelve directamente.
        
        if discogs_release_data.get('year') and str(discogs_release_data.get('year')) not in JUNK_TERMS :
            discogs_enriched_data['year'] = str(discogs_release_data.get('year'))
        
        # El 'title' de Discogs puede ser el nombre del álbum.
        # Si el 'title' de la pista original es muy diferente, no lo sobrescribimos con el del álbum.
        # Pero si el campo 'album' original era junk, el 'title' de Discogs (que es el del release) puede ser un buen candidato para 'album'.
        discogs_api_title = discogs_release_data.get('title', '').replace(f"{discogs_release_data.get('artist', '')} - ", '') # Limpiar artista del título
        if track_info.get('album') in JUNK_TERMS and discogs_api_title not in JUNK_TERMS:
            discogs_enriched_data['album'] = discogs_api_title


        if discogs_release_data.get('genre'): # Lista de géneros
            discogs_enriched_data['genre'] = ", ".join(discogs_release_data.get('genre', []))
        if discogs_release_data.get('style'): # Lista de estilos
            # Añadir estilos al género si no están ya
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

def _curate_genres(genre_string: str, max_genres=5): # Aumentado a 5
    if not genre_string or genre_string in JUNK_TERMS:
        return ""

    blacklist = [
        'music', 'audio', 'sound', 'artist', 'band', 'universal fire victim',
        'british', 'english', 'american', 'swedish', 'uk', 'us', 'german', 'french', 'canadian', 'japanese', # más nacionalidades
        's', 'early', 'late', 'contemporary', 'various', 'album', 'single',
        'background', 'easy listening', 'new age', 'satire', 'show tunes', 'soundtrack', 'ost', # Añadido soundtrack
        'christmas', 'workout', 'sleep', 'chill', 'ambient', 'instrumental', 'meditation', 'focus' # Añadidos
    ]
    year_regex = r'\b\d{4}s?\b|\b\d{2,3}s\b' # e.g., '80s', '2010s', '1990s'

    genres = [g.strip().lower() for g in genre_string.replace(';', ',').replace('/',',').split(',')] # Reemplazar también /
    
    curated_genres = []
    for genre in genres:
        genre = re.sub(year_regex, '', genre).strip()
        
        is_blacklisted = False
        for blacklisted_term in blacklist:
            if blacklisted_term in genre: # Si alguna parte del género está en la lista negra
                # Podríamos ser más específicos, ej. solo si es la palabra completa
                # Por ahora, si contiene el término, lo marcamos.
                # Ejemplo: "japanese electronic music" -> "electronic" (si "music" y "japanese" se eliminan)
                genre = genre.replace(blacklisted_term, '').strip() # Intentar limpiar
        
        if not genre or genre in blacklist or len(genre) < 2 : # Omitir si vacío, en lista negra o muy corto
            continue
            
        curated_genres.append(genre)

    unique_genres = list(dict.fromkeys(curated_genres)) # Mantiene orden y elimina duplicados
    
    ACRONYMS = {'edm', 'r&b', 'idm', 'ebm', 'u.k. garage', 'u.s. garage', 'nu-disco'} # Añadidos
    
    formatted_genres = []
    for genre in unique_genres:
        if genre.lower() in ACRONYMS:
            # Para acrónimos específicos, usar un mapeo para la capitalización correcta
            if genre.lower() == 'u.k. garage': formatted_genres.append('UK Garage')
            elif genre.lower() == 'u.s. garage': formatted_genres.append('US Garage')
            elif genre.lower() == 'nu-disco': formatted_genres.append('Nu-Disco')
            else: formatted_genres.append(genre.upper())
            continue
        
        # Capitalización de título, maneja guiones y espacios.
        # Ej: "dance-pop" -> "Dance-Pop", "electro house" -> "Electro House"
        # Podríamos querer evitar que "hip hop" se convierta en "Hip Hop" y sea "Hip-Hop"
        # Esto es complejo. Por ahora, title() es un buen compromiso.
        genre_title_case = genre.title()
        if "R&b" in genre_title_case: genre_title_case = genre_title_case.replace("R&b", "R&B") # Caso especial
        if "Uk " in genre_title_case: genre_title_case = genre_title_case.replace("Uk ", "UK ") 
        if "Us " in genre_title_case: genre_title_case = genre_title_case.replace("Us ", "US ") 
        
        formatted_genres.append(genre_title_case)

    final_list = formatted_genres[:max_genres]
    return "; ".join(final_list)