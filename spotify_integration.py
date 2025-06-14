#!/usr/bin/env python3
"""
🎵 DjAlfin - Integración con Spotify
Módulo para obtener metadatos musicales y análisis de audio desde Spotify
"""

import os
import json
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import requests
import base64

@dataclass
class SpotifyTrack:
    """Información de track desde Spotify."""
    id: str
    name: str
    artist: str
    album: str
    duration_ms: int
    popularity: int
    preview_url: Optional[str]
    external_urls: Dict[str, str]
    audio_features: Optional[Dict[str, Any]] = None

@dataclass
class AudioFeatures:
    """Características de audio desde Spotify."""
    danceability: float
    energy: float
    key: int
    loudness: float
    mode: int
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float
    valence: float
    tempo: float
    time_signature: int

class SpotifyIntegration:
    """Integración con Spotify Web API."""
    
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.token_expires_at = 0
        
        self.load_credentials()
        
    def load_credentials(self):
        """Cargar credenciales desde archivo .env."""
        try:
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                value = value.strip("'\"")
                                
                                if key == 'SPOTIPY_CLIENT_ID':
                                    self.client_id = value
                                elif key == 'SPOTIPY_CLIENT_SECRET':
                                    self.client_secret = value
            
            if not self.client_id or not self.client_secret:
                print("⚠️ Credenciales de Spotify no encontradas en .env")
                return False
            
            print("✅ Credenciales de Spotify cargadas correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando credenciales: {e}")
            return False
    
    def get_access_token(self) -> bool:
        """Obtener token de acceso usando Client Credentials Flow."""
        if not self.client_id or not self.client_secret:
            print("❌ Credenciales no disponibles")
            return False
        
        # Verificar si el token actual sigue válido
        if self.access_token and time.time() < self.token_expires_at:
            return True
        
        try:
            # Preparar autenticación
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('utf-8')
            auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            # Headers para la petición
            headers = {
                'Authorization': f'Basic {auth_base64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Datos para la petición
            data = {
                'grant_type': 'client_credentials'
            }
            
            # Realizar petición
            response = requests.post(
                'https://accounts.spotify.com/api/token',
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in - 60  # 60s buffer
                
                print("✅ Token de acceso obtenido correctamente")
                return True
            else:
                print(f"❌ Error obteniendo token: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en autenticación: {e}")
            return False
    
    def search_track(self, artist: str, title: str) -> Optional[SpotifyTrack]:
        """Buscar track en Spotify."""
        if not self.get_access_token():
            return None
        
        try:
            # Limpiar y preparar query
            query = f"artist:{artist} track:{title}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            params = {
                'q': query,
                'type': 'track',
                'limit': 1
            }
            
            response = requests.get(
                'https://api.spotify.com/v1/search',
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get('tracks', {}).get('items', [])
                
                if tracks:
                    track = tracks[0]
                    return SpotifyTrack(
                        id=track['id'],
                        name=track['name'],
                        artist=', '.join([artist['name'] for artist in track['artists']]),
                        album=track['album']['name'],
                        duration_ms=track['duration_ms'],
                        popularity=track['popularity'],
                        preview_url=track.get('preview_url'),
                        external_urls=track.get('external_urls', {})
                    )
                else:
                    print(f"🔍 No se encontró: {artist} - {title}")
                    return None
            else:
                print(f"❌ Error en búsqueda: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error buscando track: {e}")
            return None
    
    def get_audio_features(self, track_id: str) -> Optional[AudioFeatures]:
        """Obtener características de audio de un track."""
        if not self.get_access_token():
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(
                f'https://api.spotify.com/v1/audio-features/{track_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return AudioFeatures(
                    danceability=data.get('danceability', 0.0),
                    energy=data.get('energy', 0.0),
                    key=data.get('key', 0),
                    loudness=data.get('loudness', 0.0),
                    mode=data.get('mode', 0),
                    speechiness=data.get('speechiness', 0.0),
                    acousticness=data.get('acousticness', 0.0),
                    instrumentalness=data.get('instrumentalness', 0.0),
                    liveness=data.get('liveness', 0.0),
                    valence=data.get('valence', 0.0),
                    tempo=data.get('tempo', 0.0),
                    time_signature=data.get('time_signature', 4)
                )
            else:
                print(f"❌ Error obteniendo audio features: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error en audio features: {e}")
            return None
    
    def get_track_analysis(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Obtener análisis detallado de un track."""
        if not self.get_access_token():
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(
                f'https://api.spotify.com/v1/audio-analysis/{track_id}',
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error obteniendo análisis: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return None
    
    def suggest_cue_points_from_analysis(self, track_id: str) -> List[Dict[str, Any]]:
        """Sugerir cue points basado en análisis de Spotify."""
        analysis = self.get_track_analysis(track_id)
        if not analysis:
            return []
        
        suggested_cues = []
        
        try:
            # Obtener secciones del análisis
            sections = analysis.get('sections', [])
            beats = analysis.get('beats', [])
            
            # Sugerir cue points en cambios de sección
            for i, section in enumerate(sections):
                start_time = section.get('start', 0)
                confidence = section.get('confidence', 0)
                loudness = section.get('loudness', -60)
                
                # Solo sugerir si la confianza es alta
                if confidence > 0.7:
                    # Determinar tipo de sección basado en características
                    energy_level = min(10, max(1, int((loudness + 60) / 6) + 1))
                    
                    if i == 0:
                        name = "Intro"
                        color = "#FF6600"
                    elif i == len(sections) - 1:
                        name = "Outro"
                        color = "#9900FF"
                    elif energy_level >= 8:
                        name = f"Drop {i}"
                        color = "#FF0000"
                    elif energy_level <= 3:
                        name = f"Breakdown {i}"
                        color = "#0066FF"
                    else:
                        name = f"Section {i}"
                        color = "#00FF00"
                    
                    suggested_cues.append({
                        'position': start_time,
                        'name': name,
                        'color': color,
                        'energy_level': energy_level,
                        'confidence': confidence,
                        'source': 'spotify_analysis'
                    })
            
            # Limitar a máximo 8 sugerencias (para hot cues)
            suggested_cues = suggested_cues[:8]
            
            print(f"🎯 Sugeridos {len(suggested_cues)} cue points desde análisis de Spotify")
            return suggested_cues
            
        except Exception as e:
            print(f"❌ Error procesando análisis: {e}")
            return []
    
    def enhance_track_metadata(self, artist: str, title: str) -> Dict[str, Any]:
        """Mejorar metadatos de track con información de Spotify."""
        track = self.search_track(artist, title)
        if not track:
            return {}
        
        # Obtener características de audio
        audio_features = self.get_audio_features(track.id)
        
        enhanced_metadata = {
            'spotify_id': track.id,
            'spotify_name': track.name,
            'spotify_artist': track.artist,
            'spotify_album': track.album,
            'spotify_duration_ms': track.duration_ms,
            'spotify_popularity': track.popularity,
            'spotify_preview_url': track.preview_url,
            'spotify_external_urls': track.external_urls
        }
        
        if audio_features:
            enhanced_metadata.update({
                'spotify_bpm': round(audio_features.tempo),
                'spotify_key': self.get_key_name(audio_features.key, audio_features.mode),
                'spotify_energy': round(audio_features.energy * 10),
                'spotify_danceability': round(audio_features.danceability * 10),
                'spotify_valence': round(audio_features.valence * 10),
                'spotify_acousticness': round(audio_features.acousticness * 10),
                'spotify_instrumentalness': round(audio_features.instrumentalness * 10),
                'spotify_time_signature': audio_features.time_signature
            })
        
        return enhanced_metadata
    
    def get_key_name(self, key: int, mode: int) -> str:
        """Convertir key numérico a nombre musical."""
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        if 0 <= key <= 11:
            key_name = keys[key]
            mode_name = 'major' if mode == 1 else 'minor'
            return f"{key_name} {mode_name}"
        return "Unknown"
    
    def test_connection(self) -> bool:
        """Probar conexión con Spotify API."""
        print("🧪 Probando conexión con Spotify API...")
        
        if not self.get_access_token():
            print("❌ No se pudo obtener token de acceso")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(
                'https://api.spotify.com/v1/search?q=test&type=track&limit=1',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Conexión con Spotify API exitosa")
                return True
            else:
                print(f"❌ Error en conexión: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error probando conexión: {e}")
            return False

def demo_spotify_integration():
    """Demostración de la integración con Spotify."""
    print("🎵 Demo: Integración con Spotify")
    print("=" * 50)
    
    spotify = SpotifyIntegration()
    
    # Probar conexión
    if not spotify.test_connection():
        print("❌ No se pudo conectar con Spotify")
        return
    
    # Buscar un track de ejemplo
    print("\n🔍 Buscando track de ejemplo...")
    track = spotify.search_track("Deadmau5", "Strobe")
    
    if track:
        print(f"✅ Encontrado: {track.artist} - {track.name}")
        print(f"📀 Álbum: {track.album}")
        print(f"⏱️ Duración: {track.duration_ms / 1000:.1f}s")
        print(f"📊 Popularidad: {track.popularity}/100")
        
        # Obtener características de audio
        print("\n🎵 Obteniendo características de audio...")
        audio_features = spotify.get_audio_features(track.id)
        
        if audio_features:
            print(f"🥁 BPM: {audio_features.tempo:.1f}")
            print(f"🎹 Tonalidad: {spotify.get_key_name(audio_features.key, audio_features.mode)}")
            print(f"⚡ Energía: {audio_features.energy * 10:.1f}/10")
            print(f"💃 Danceability: {audio_features.danceability * 10:.1f}/10")
            print(f"😊 Valence: {audio_features.valence * 10:.1f}/10")
        
        # Sugerir cue points
        print("\n🎯 Sugiriendo cue points...")
        suggested_cues = spotify.suggest_cue_points_from_analysis(track.id)
        
        for i, cue in enumerate(suggested_cues, 1):
            minutes = int(cue['position'] // 60)
            seconds = int(cue['position'] % 60)
            print(f"  {i}. {cue['name']} @ {minutes}:{seconds:02d} (Energy: {cue['energy_level']}/10) {cue['color']}")
    
    print("\n✅ Demo completado")

if __name__ == "__main__":
    demo_spotify_integration()
