import configparser
import json
from typing import Optional, Tuple, Dict
import os

CONFIG_DIR = "config"
API_KEYS_PATH = os.path.join(CONFIG_DIR, "api_keys.json")

def _load_json_config() -> Optional[Dict]:
    """Carga el archivo de configuración JSON."""
    if not os.path.exists(API_KEYS_PATH):
        return None
    try:
        with open(API_KEYS_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error al leer o procesar '{API_KEYS_PATH}': {e}")
        return None

def load_spotify_credentials() -> Optional[Tuple[str, str]]:
    """
    Carga las credenciales de Spotify (Client ID y Client Secret) desde api_keys.json.
    """
    config = _load_json_config()
    if not config:
        print(f"ADVERTENCIA: No se encontró o no se pudo leer '{API_KEYS_PATH}'.")
        return None

    spotify_config = config.get("spotify")
    if not spotify_config:
        print(f"Error: La sección [spotify] no se encontró en '{API_KEYS_PATH}'.")
        return None

    client_id = spotify_config.get("client_id")
    client_secret = spotify_config.get("client_secret")

    if not client_id or not client_secret:
        print(f"ADVERTENCIA: 'client_id' o 'client_secret' de Spotify no están en '{API_KEYS_PATH}'.")
        return None

    return client_id, client_secret


def load_musicbrainz_config() -> Optional[Dict[str, str]]:
    """
    Carga la configuración de la aplicación para la API de MusicBrainz desde api_keys.json.
    """
    config = _load_json_config()
    if not config:
        return None
    
    mb_config = config.get("musicbrainz")
    if not mb_config:
        return None

    app_name = mb_config.get("app_name")
    app_version = mb_config.get("version")
    contact_email = mb_config.get("email")
    
    if not all([app_name, app_version, contact_email is not None]):
        return None

    return {
        "app_name": app_name,
        "app_version": app_version,
        "contact_email": contact_email,
    }


if __name__ == "__main__":
    # Asegurarse de que el directorio de trabajo es el del script para pruebas
    if os.path.basename(os.getcwd()) == "core":
        os.chdir("..")

    # Código de prueba para verificar si las credenciales se cargan correctamente.
    print("--- Probando carga desde api_keys.json ---")
    credentials = load_spotify_credentials()
    if credentials:
        print("Credenciales de Spotify cargadas exitosamente.")
    else:
        print(
            f"No se pudieron cargar las credenciales de Spotify. Por favor, revisa tu archivo '{API_KEYS_PATH}'."
        )
    
    mb_config = load_musicbrainz_config()
    if mb_config:
        print("Configuración de MusicBrainz cargada exitosamente.")
    else:
        print(f"No se pudo cargar la configuración de MusicBrainz desde '{API_KEYS_PATH}'.")
