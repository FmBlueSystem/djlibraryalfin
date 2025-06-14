import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

def get_spotify_client():
    """
    Crea y devuelve un cliente de Spotipy autenticado.
    
    Returns:
        spotipy.Spotify: Un objeto cliente de Spotipy, o None si las
                         credenciales no están configuradas.
    """
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    if not client_id or not client_secret or client_id == 'TU_CLIENT_ID_DE_SPOTIFY_AQUI':
        print("AVISO: Las credenciales de Spotify no están configuradas en el archivo .env.")
        print("El enriquecimiento con Spotify estará deshabilitado.")
        return None

    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        # Probar la conexión haciendo una petición ligera
        sp.search(q='test', type='track', limit=1)
        print("Cliente de Spotify autenticado y conectado con éxito.")
        return sp
    except Exception as e:
        print(f"Error al conectar con Spotify: {e}")
        print("Asegúrate de que tus credenciales en el archivo .env son correctas.")
        return None

# Crear una instancia global del cliente para ser usada por otros módulos
spotify_client = get_spotify_client()

def search_track(artist, title):
    """
    Busca una pista en Spotify por artista y título.
    
    Returns:
        dict: Un diccionario con los datos de la pista de Spotify, o None.
    """
    if not spotify_client:
        return None
        
    query = f"artist:{artist} track:{title}"
    try:
        results = spotify_client.search(q=query, type='track', limit=1)
        if results and results['tracks']['items']:
            return results['tracks']['items'][0]
    except Exception as e:
        print(f"Error durante la búsqueda en Spotify: {e}")
    
    return None 