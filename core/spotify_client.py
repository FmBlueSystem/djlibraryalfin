import requests
import base64
import time
from typing import Optional, Dict, Any
import logging

from .config_loader import load_spotify_credentials


class SpotifyConfigurationError(Exception):
    """Excepción para errores de configuración de Spotify."""
    pass


class SpotifyClient:
    """
    Cliente para interactuar con la API de Spotify.
    Gestiona la autenticación y las llamadas a la API.
    """

    _instance = None

    # Singleton para evitar múltiples instancias y re-autenticaciones innecesarias
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SpotifyClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):  # Evitar re-inicialización
            credentials = load_spotify_credentials()
            if not credentials:
                raise SpotifyConfigurationError(
                    "Credenciales de Spotify no encontradas o no configuradas en 'config.ini'."
                )
            
            self.client_id, self.client_secret = credentials
            self.access_token: Optional[str] = None
            self.token_expiry_time: float = 0
            self.initialized: bool = True

    def _get_access_token(self) -> Optional[str]:
        """
        Obtiene un token de acceso de la API de Spotify usando las credenciales del cliente.
        """
        if not self.client_id or not self.client_secret:
            raise SpotifyConfigurationError("Credenciales de Spotify no configuradas.")

        auth_url = "https://accounts.spotify.com/api/token"

        # Codificar client_id y client_secret en Base64
        message = f"{self.client_id}:{self.client_secret}"
        message_bytes = message.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode("ascii")

        headers = {
            "Authorization": f"Basic {base64_message}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {"grant_type": "client_credentials"}

        try:
            response = requests.post(
                auth_url, headers=headers, data=payload, timeout=10
            )
            response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx

            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry_time = time.time() + expires_in

            return self.access_token

        except requests.RequestException as e:
            raise SpotifyConfigurationError(f"No se pudo conectar con Spotify. Verifica tus credenciales y la conexión a internet. Error original: {e}")

    def get_artist_genres(self, artist_id: str) -> Optional[list[str]]:
        """Obtiene los géneros de un artista por su ID."""
        if not self.token:
            return None
        
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            artist_data = response.json()
            return artist_data.get("genres")
        except requests.RequestException:
            return None

    @property
    def token(self) -> Optional[str]:
        """
        Propiedad que devuelve un token de acceso válido, solicitándolo si es necesario.
        """
        if not self.access_token or time.time() >= self.token_expiry_time:
            self._get_access_token()
        return self.access_token

    def search_track(
        self, title: str, artist: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca una pista en Spotify por título y, opcionalmente, por artista.

        Returns:
            Un diccionario con los datos de la pista encontrada, o None si no hay resultados.
        """
        if not self.token:
            raise SpotifyConfigurationError("No hay token de acceso de Spotify disponible.")

        search_url = "https://api.spotify.com/v1/search"
        query = f"track:{title}"
        if artist:
            query += f" artist:{artist}"
        
        logging.info(f"Enviando consulta a Spotify API: {query}")

        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "q": query,
            "type": "track",
            "limit": 5,  # Pedimos 5 resultados para tener margen de selección
        }

        try:
            response = requests.get(
                search_url, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()

            results = response.json()
            tracks = results.get("tracks", {}).get("items", [])

            if not tracks:
                return None

            # Por ahora, devolvemos el primer resultado, que suele ser el más relevante.
            best_match = tracks[0]
            
            # --- Enriquecer con datos adicionales ---
            enriched_data = {"spotify_id": best_match.get("id")}

            # Extraer Género (del artista)
            artists = best_match.get("artists", [])
            if artists:
                main_artist_id = artists[0].get("id")
                if main_artist_id:
                    genres = self.get_artist_genres(main_artist_id)
                    if genres:
                        # Tomamos el primer género como el principal
                        enriched_data["genre"] = genres[0].title()

            return enriched_data

        except requests.RequestException as e:
            print(f"Error al buscar en Spotify: {e}")
            return None


if __name__ == "__main__":
    # Código de prueba para verificar la obtención del token y la búsqueda
    print("Intentando obtener el token de Spotify...")
    client = SpotifyClient()
    access_token = client.token

    if access_token:
        print("\nPrueba de autenticación exitosa.")

        print("\n--- Probando búsqueda de canción ---")
        # Ejemplo de búsqueda
        test_title = "Stayin' Alive"
        test_artist = "Bee Gees"
        track_info = client.search_track(test_title, test_artist)

        if track_info:
            print(f"Información encontrada para '{test_title}' - '{test_artist}':")
            print(f"  - Nombre: {track_info.get('name')}")
            print(f"  - Álbum: {track_info.get('album', {}).get('name')}")
            print(f"  - Popularidad: {track_info.get('popularity')}")
            print(f"  - URL: {track_info.get('external_urls', {}).get('spotify')}")
            print(f"  - Género: {track_info.get('genre')}")
        else:
            print(f"No se encontró información para '{test_title}' - '{test_artist}'.")

    else:
        print("\nPrueba de autenticación fallida.")
        print(
            "Asegúrate de que tu archivo 'config.ini' es correcto y tienes conexión a internet."
        )
