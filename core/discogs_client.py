# core/discogs_client.py
import requests
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

DISCOGS_USER_TOKEN = os.getenv("DISCOGS_USER_TOKEN")
DISCOGS_API_BASE_URL = "https://api.discogs.com"

_discogs_session = None
_client_initialized = False

def get_discogs_session():
    """
    Crea y devuelve una sesión de requests configurada para la API de Discogs.
    """
    global _discogs_session, _client_initialized

    if _client_initialized:
        return _discogs_session

    _client_initialized = True

    if not DISCOGS_USER_TOKEN or DISCOGS_USER_TOKEN == 'TU_DISCOGS_USER_TOKEN_AQUI':
        print("AVISO: El token de usuario de Discogs no está configurado en el archivo .env.")
        print("El enriquecimiento con Discogs estará deshabilitado.")
        _discogs_session = None
        return None

    session = requests.Session()
    session.headers.update({
        "User-Agent": "DjAlfin/0.1 +https://github.com/FmBlueSystem/djlibraryalfin",
        "Authorization": f"Discogs token={DISCOGS_USER_TOKEN}"
    })
    
    # Probar la conexión (opcional, pero bueno para verificar el token)
    try:
        response = session.get(f"{DISCOGS_API_BASE_URL}/database/search?q=test&type=release&per_page=1")
        response.raise_for_status() # Lanza una excepción para errores HTTP 4xx/5xx
        print("Cliente de Discogs conectado y token verificado con éxito.")
        _discogs_session = session
        return session
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Discogs o verificar token: {e}")
        if e.response is not None:
            print(f"Respuesta de Discogs: {e.response.status_code} - {e.response.text}")
        print("Asegúrate de que tu DISCOGS_USER_TOKEN en .env es correcto y tiene permisos.")
        _discogs_session = None
        return None

def search_release(artist, title, release_type="release"):
    """
    Busca un lanzamiento (álbum, sencillo, etc.) en Discogs por artista y título.

    Args:
        artist (str): Nombre del artista.
        title (str): Título del lanzamiento.
        release_type (str): Tipo de búsqueda en Discogs (ej. "release", "master"). 
                            Por defecto "release".

    Returns:
        dict: Un diccionario con los datos del primer lanzamiento encontrado, o None.
    """
    session = get_discogs_session()
    if not session:
        return None

    params = {
        "artist": artist,
        "release_title": title, # 'release_title' es más específico para el título del álbum/EP
        "type": release_type,
        "per_page": 1 
    }
    
    try:
        response = session.get(f"{DISCOGS_API_BASE_URL}/database/search", params=params)
        response.raise_for_status()
        data = response.json()
        if data and data.get("results"):
            return data["results"][0] # Devuelve el primer resultado
    except requests.exceptions.RequestException as e:
        print(f"Error durante la búsqueda en Discogs: {e}")
        if e.response is not None:
            print(f"Respuesta de Discogs: {e.response.status_code} - {e.response.text}")
    except ValueError: # Error al decodificar JSON
        print("Error al decodificar la respuesta JSON de Discogs.")
        
    return None

if __name__ == '__main__':
    # Ejemplo de uso (requiere que DISCOGS_USER_TOKEN esté configurado en .env)
    if DISCOGS_USER_TOKEN and DISCOGS_USER_TOKEN != 'TU_DISCOGS_USER_TOKEN_AQUI':
        print("Probando búsqueda en Discogs...")
        # Intenta buscar un lanzamiento conocido
        # Reemplaza con un artista y título que esperes encontrar para una mejor prueba
        test_artist = "Daft Punk"
        test_title = "Random Access Memories"
        
        release_info = search_release(test_artist, test_title)
        if release_info:
            print(f"\nEncontrado en Discogs para '{test_artist} - {test_title}':")
            print(f"  Título: {release_info.get('title')}")
            print(f"  ID: {release_info.get('id')}")
            print(f"  Año: {release_info.get('year')}")
            print(f"  Géneros: {release_info.get('genre')}")
            print(f"  Estilos: {release_info.get('style')}")
            print(f"  URL de portada: {release_info.get('cover_image')}")
        else:
            print(f"No se encontró '{test_artist} - {test_title}' en Discogs o hubo un error.")
    else:
        print("Para probar core/discogs_client.py directamente, configura DISCOGS_USER_TOKEN en tu archivo .env.")