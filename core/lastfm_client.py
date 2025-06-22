# core/lastfm_client.py

import requests
import time
from typing import Dict, List, Optional
from urllib.parse import urlencode

class LastFmClient:
    """
    Cliente para la API de Last.fm para obtener información de géneros y tags musicales.
    """
    
    BASE_URL = "http://ws.audioscrobbler.com/2.0/"
    
    def __init__(self, api_key: str = None):
        """
        Inicializa el cliente de Last.fm.
        
        Args:
            api_key: Clave de API de Last.fm. Si es None, se intenta obtener de variables de entorno.
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DjAlfin/1.0 (https://github.com/FmBlueSystem/djlibraryalfin)'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms entre requests
        
    def _get_api_key_from_env(self) -> Optional[str]:
        """Obtiene la API key desde variables de entorno o archivo de configuración."""
        import os
        
        # Intentar desde variables de entorno
        api_key = os.getenv('LASTFM_API_KEY')
        if api_key:
            return api_key
            
        # Intentar desde archivo de configuración
        try:
            from ..config.secure_config import LASTFM_API_KEY
            return LASTFM_API_KEY
        except ImportError:
            pass
            
        print("⚠️ Last.fm API key no encontrada. Configurar LASTFM_API_KEY en variables de entorno o secure_config.py")
        return None
    
    def _rate_limit(self):
        """Implementa rate limiting para respetar límites de la API."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Realiza una petición a la API de Last.fm con manejo de errores."""
        if not self.api_key:
            print("❌ Last.fm API key no disponible")
            return None
            
        self._rate_limit()
        
        # Parámetros base
        base_params = {
            'api_key': self.api_key,
            'format': 'json'
        }
        base_params.update(params)
        
        try:
            response = self.session.get(self.BASE_URL, params=base_params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar errores de la API
            if 'error' in data:
                print(f"❌ Error de Last.fm API: {data.get('message', 'Error desconocido')}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en petición a Last.fm: {e}")
            return None
        except ValueError as e:
            print(f"❌ Error parseando respuesta JSON de Last.fm: {e}")
            return None
    
    def get_artist_top_tags(self, artist: str, limit: int = 10) -> List[str]:
        """
        Obtiene los top tags de un artista desde Last.fm.
        
        Args:
            artist: Nombre del artista
            limit: Número máximo de tags a retornar
            
        Returns:
            Lista de strings con los tags/géneros más populares
        """
        params = {
            'method': 'artist.getTopTags',
            'artist': artist,
            'limit': limit
        }
        
        data = self._make_request(params)
        if not data:
            return []
            
        try:
            tags_data = data.get('toptags', {}).get('tag', [])
            
            # Asegurar que sea una lista
            if isinstance(tags_data, dict):
                tags_data = [tags_data]
                
            # Extraer nombres de tags y filtrar
            tags = []
            for tag_info in tags_data:
                tag_name = tag_info.get('name', '').strip()
                if tag_name and self._is_valid_music_tag(tag_name):
                    tags.append(tag_name)
                    
            return tags[:limit]
            
        except (KeyError, TypeError) as e:
            print(f"❌ Error procesando tags de artista desde Last.fm: {e}")
            return []
    
    def get_track_top_tags(self, artist: str, track: str, limit: int = 10) -> List[str]:
        """
        Obtiene los top tags de un track específico desde Last.fm.
        
        Args:
            artist: Nombre del artista
            track: Nombre del track
            limit: Número máximo de tags a retornar
            
        Returns:
            Lista de strings con los tags/géneros más populares del track
        """
        params = {
            'method': 'track.getTopTags',
            'artist': artist,
            'track': track,
            'limit': limit
        }
        
        data = self._make_request(params)
        if not data:
            return []
            
        try:
            tags_data = data.get('toptags', {}).get('tag', [])
            
            # Asegurar que sea una lista
            if isinstance(tags_data, dict):
                tags_data = [tags_data]
                
            # Extraer nombres de tags y filtrar
            tags = []
            for tag_info in tags_data:
                tag_name = tag_info.get('name', '').strip()
                if tag_name and self._is_valid_music_tag(tag_name):
                    tags.append(tag_name)
                    
            return tags[:limit]
            
        except (KeyError, TypeError) as e:
            print(f"❌ Error procesando tags de track desde Last.fm: {e}")
            return []
    
    def search_artist(self, artist: str) -> Optional[Dict]:
        """
        Busca información básica de un artista.
        
        Args:
            artist: Nombre del artista a buscar
            
        Returns:
            Dict con información del artista o None si no se encuentra
        """
        params = {
            'method': 'artist.search',
            'artist': artist,
            'limit': 1
        }
        
        data = self._make_request(params)
        if not data:
            return None
            
        try:
            artists = data.get('results', {}).get('artistmatches', {}).get('artist', [])
            
            if not artists:
                return None
                
            # Tomar el primer resultado
            if isinstance(artists, list):
                artist_info = artists[0]
            else:
                artist_info = artists
                
            return {
                'name': artist_info.get('name', ''),
                'mbid': artist_info.get('mbid', ''),
                'url': artist_info.get('url', ''),
                'listeners': artist_info.get('listeners', '0')
            }
            
        except (KeyError, TypeError) as e:
            print(f"❌ Error procesando búsqueda de artista desde Last.fm: {e}")
            return None
    
    def _is_valid_music_tag(self, tag: str) -> bool:
        """
        Valida si un tag es relevante para géneros musicales.
        
        Args:
            tag: Tag a validar
            
        Returns:
            True si el tag es válido para géneros musicales
        """
        tag_lower = tag.lower().strip()
        
        # Filtrar tags muy genéricos o no musicales
        invalid_tags = {
            'seen live', 'favorite', 'albums i own', 'beautiful', 'awesome',
            'love', 'cool', 'amazing', 'perfect', 'best', 'great', 'good',
            'listened', 'heard', 'played', 'radio', 'cd', 'vinyl', 'mp3',
            'download', 'buy', 'purchase', 'own', 'collection', 'library',
            'playlist', 'mix', 'compilation', 'album', 'single', 'ep',
            'new', 'old', 'classic', 'modern', 'recent', 'latest', 'current',
            'popular', 'mainstream', 'underground', 'indie', 'major', 'minor',
            'male', 'female', 'group', 'band', 'solo', 'duo', 'trio',
            'american', 'british', 'english', 'canadian', 'australian', 'german',
            'french', 'italian', 'spanish', 'japanese', 'korean', 'swedish'
        }
        
        if tag_lower in invalid_tags:
            return False
            
        # Filtrar tags muy cortos o muy largos
        if len(tag_lower) < 3 or len(tag_lower) > 30:
            return False
            
        # Filtrar tags que son solo números o años
        if tag_lower.isdigit() or tag_lower.endswith('s') and tag_lower[:-1].isdigit():
            return False
            
        return True
    
    def get_combined_genres(self, artist: str, track: str = None) -> List[str]:
        """
        Obtiene géneros combinados del artista y track (si se proporciona).
        
        Args:
            artist: Nombre del artista
            track: Nombre del track (opcional)
            
        Returns:
            Lista combinada de géneros del artista y track
        """
        genres = []
        
        # Obtener tags del artista
        artist_tags = self.get_artist_top_tags(artist, limit=8)
        genres.extend(artist_tags)
        
        # Obtener tags del track si se proporciona
        if track:
            track_tags = self.get_track_top_tags(artist, track, limit=5)
            # Agregar tags del track que no estén ya en la lista
            for tag in track_tags:
                if tag not in genres:
                    genres.append(tag)
        
        return genres[:10]  # Limitar a 10 géneros máximo

# Función de conveniencia para integración con el sistema existente
def search_lastfm_genres(artist: str, title: str) -> Dict:
    """
    Función de conveniencia para buscar géneros en Last.fm.
    Compatible con el sistema de enriquecimiento existente.
    
    Args:
        artist: Nombre del artista
        title: Título del track
        
    Returns:
        Dict con géneros encontrados en formato compatible
    """
    client = LastFmClient()
    
    try:
        genres = client.get_combined_genres(artist, title)
        
        if genres:
            return {
                'genre': ', '.join(genres),
                'lastfm_artist_info': client.search_artist(artist),
                'source': 'lastfm'
            }
        else:
            return {}
            
    except Exception as e:
        print(f"❌ Error buscando géneros en Last.fm: {e}")
        return {}

# Para pruebas directas
if __name__ == '__main__':
    # Ejemplo de uso
    client = LastFmClient()
    
    if client.api_key:
        print("🎵 Probando cliente de Last.fm...")
        
        # Probar búsqueda de artista
        artist_info = client.search_artist("Daft Punk")
        if artist_info:
            print(f"✅ Artista encontrado: {artist_info['name']}")
            
            # Obtener tags del artista
            tags = client.get_artist_top_tags("Daft Punk")
            print(f"🎯 Tags del artista: {', '.join(tags)}")
            
            # Obtener tags de un track específico
            track_tags = client.get_track_top_tags("Daft Punk", "Get Lucky")
            print(f"🎵 Tags del track: {', '.join(track_tags)}")
            
        else:
            print("❌ No se pudo encontrar el artista")
    else:
        print("❌ API key de Last.fm no configurada")
        print("📝 Para configurar, agregar LASTFM_API_KEY a variables de entorno")
        print("📝 O crear config/secure_config.py con LASTFM_API_KEY = 'tu_api_key'")