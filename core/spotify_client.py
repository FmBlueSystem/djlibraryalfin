import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Variable global para el cliente (se inicializará cuando sea necesario)
_spotify_client = None
_client_initialized = False

def get_spotify_client():
    """
    Crea y devuelve un cliente de Spotipy autenticado.
    
    Returns:
        spotipy.Spotify: Un objeto cliente de Spotipy, o None si las
                         credenciales no están configuradas.
    """
    global _spotify_client, _client_initialized
    
    # Si ya intentamos inicializar, devolver el resultado cached
    if _client_initialized:
        return _spotify_client
    
    _client_initialized = True
    
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    if not client_id or not client_secret or client_id == 'TU_CLIENT_ID_DE_SPOTIFY_AQUI':
        print("AVISO: Las credenciales de Spotify no están configuradas en el archivo .env.")
        print("El enriquecimiento con Spotify estará deshabilitado.")
        _spotify_client = None
        return None

    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        # Probar la conexión haciendo una petición ligera
        sp.search(q='test', type='track', limit=1)
        print("Cliente de Spotify autenticado y conectado con éxito.")
        _spotify_client = sp
        return sp
    except Exception as e:
        print(f"Error al conectar con Spotify: {e}")
        print("Asegúrate de que tus credenciales en el archivo .env son correctas.")
        _spotify_client = None
        return None

# Propiedad para acceso lazy al cliente
@property
def spotify_client():
    """Acceso lazy al cliente de Spotify."""
    return get_spotify_client()

def search_track(artist, title):
    """
    Busca una pista en Spotify por artista y título.
    
    Returns:
        dict: Un diccionario con los datos de la pista de Spotify, 
              incluyendo 'album_id' y 'main_artist_id' si se encuentran, o None.
    """
    client = get_spotify_client()
    if not client:
        return None
        
    query = f"artist:{artist} track:{title}"
    try:
        results = client.search(q=query, type='track', limit=1)
        if results and results['tracks']['items']:
            track_data = results['tracks']['items'][0]
            # Añadir IDs útiles para facilitar otras operaciones
            if track_data.get('album') and track_data['album'].get('id'):
                track_data['album_id'] = track_data['album']['id']
            if track_data.get('artists') and len(track_data['artists']) > 0 and track_data['artists'][0].get('id'):
                track_data['main_artist_id'] = track_data['artists'][0]['id']
            return track_data
    except Exception as e:
        print(f"Error durante la búsqueda de pista en Spotify: {e}")
    
    return None

def search_artist(artist_name):
    """
    Busca un artista en Spotify por su nombre.
    
    Args:
        artist_name (str): El nombre del artista a buscar.
        
    Returns:
        dict: Un diccionario con los datos del primer artista encontrado, o None.
    """
    client = get_spotify_client()
    if not client:
        return None
    
    query = f"artist:{artist_name}"
    try:
        results = client.search(q=query, type='artist', limit=1)
        if results and results['artists']['items']:
            return results['artists']['items'][0]
    except Exception as e:
        print(f"Error durante la búsqueda de artista en Spotify: {e}")
        
    return None

def get_album_art_url(album_id, min_width=300):
    """
    Obtiene la URL del arte de portada de un álbum de Spotify.
    Intenta obtener la imagen más grande disponible, o una que cumpla con min_width.
    
    Args:
        album_id (str): El ID del álbum de Spotify.
        min_width (int): Ancho mínimo deseado para la imagen.
        
    Returns:
        str: La URL de la imagen de portada, o None si no se encuentra.
    """
    client = get_spotify_client()
    if not client:
        return None
        
    try:
        album_details = client.album(album_id)
        if album_details and album_details['images']:
            # Las imágenes suelen estar ordenadas de mayor a menor resolución
            # Seleccionar la primera (más grande) por defecto
            best_image = album_details['images'][0]
            # Iterar para encontrar una imagen que cumpla con min_width,
            # prefiriendo la más pequeña que aún lo cumpla para ahorrar datos,
            # o la más grande si ninguna cumple.
            # Si se prefiere la más grande que cumpla el mínimo, se debe ajustar la lógica.
            # Para este caso, la primera que cumpla o la más grande (primera en la lista) está bien.
            for img in album_details['images']:
                if img['width'] >= min_width:
                    best_image = img 
                    # Si queremos la más pequeña que cumpla, rompemos aquí.
                    # Si queremos la más grande que cumpla, no rompemos y dejamos que itere.
                    # Para este caso, la primera que cumpla está bien.
                    # break # Descomentar si se prefiere la primera imagen que cumpla el min_width
            return best_image['url']
    except Exception as e:
        print(f"Error al obtener arte del álbum de Spotify (ID: {album_id}): {e}")
        
    return None