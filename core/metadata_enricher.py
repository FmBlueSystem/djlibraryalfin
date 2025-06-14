"""
Sistema de enriquecimiento de metadatos para DjAlfin
Coordina múltiples APIs para completar metadatos faltantes
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
import os

from .spotify_client import SpotifyClient
from .musicbrainz_client import MusicBrainzClient
from .metadata_reader import read_metadata
from .metadata_writer import write_all_metadata
from .genre_classifier import GenreClassifier, enhance_metadata_with_genre_classification


class MetadataSource(Enum):
    """Fuentes de metadatos disponibles."""
    SPOTIFY = "spotify"
    MUSICBRAINZ = "musicbrainz"
    LASTFM = "lastfm"
    DISCOGS = "discogs"


@dataclass
class MetadataSearchResult:
    """Resultado de búsqueda de metadatos."""
    source: MetadataSource
    confidence: float  # 0.0 - 1.0
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


@dataclass
class TrackMetadata:
    """Metadatos de una pista."""
    file_path: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    energy: Optional[float] = None
    
    def is_complete(self) -> bool:
        """Verifica si los metadatos están completos."""
        # Lista de valores considerados problemáticos/inválidos
        invalid_values = {'N/A', 'N A', 'NA', 'Unknown', 'unknown', 'UNKNOWN', '', None}
        
        essential_fields = [self.title, self.artist, self.album, self.genre]
        return all(
            field is not None and
            field.strip() not in invalid_values and
            field.strip() != ""
            for field in essential_fields
        )
    
    def missing_fields(self) -> List[str]:
        """Retorna lista de campos faltantes o problemáticos."""
        # Lista de valores considerados problemáticos/inválidos
        invalid_values = {'N/A', 'N A', 'NA', 'Unknown', 'unknown', 'UNKNOWN', '', None}
        
        missing = []
        if not self.title or self.title.strip() in invalid_values:
            missing.append("title")
        if not self.artist or self.artist.strip() in invalid_values:
            missing.append("artist")
        if not self.album or self.album.strip() in invalid_values:
            missing.append("album")
        if not self.genre or self.genre.strip() in invalid_values:
            missing.append("genre")
        if not self.year:
            missing.append("year")
        if not self.bpm:
            missing.append("bpm")
        if not self.key:
            missing.append("key")
        return missing


class MetadataEnricher:
    """
    Sistema principal de enriquecimiento de metadatos.
    Coordina múltiples APIs para completar metadatos faltantes.
    """
    
    def __init__(self, db_path: str = None):
        # Si no se proporciona db_path, usar el DatabaseManager para obtener la ruta correcta
        if db_path is None:
            from .database import DatabaseManager
            db_manager = DatabaseManager()
            self.db_path = db_manager.db_path
        else:
            self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # Inicializar clientes de API
        self.clients = {}
        self._init_api_clients()

        # Inicializar clasificador de géneros
        self.genre_classifier = GenreClassifier()

        # Configuración de búsqueda
        self.search_priority = [
            MetadataSource.SPOTIFY,
            MetadataSource.MUSICBRAINZ,
            # MetadataSource.LASTFM,  # Implementar después
            # MetadataSource.DISCOGS  # Implementar después
        ]

        # Rate limiting
        self.last_api_call = {}
        self.rate_limits = {
            MetadataSource.SPOTIFY: 1.0,      # 1 segundo entre llamadas
            MetadataSource.MUSICBRAINZ: 2.0,  # 2 segundos entre llamadas
            MetadataSource.LASTFM: 1.0,
            MetadataSource.DISCOGS: 1.0
        }
    
    def _init_api_clients(self):
        """Inicializa los clientes de API disponibles."""
        try:
            self.clients[MetadataSource.SPOTIFY] = SpotifyClient()
            self.logger.info("✅ Spotify client initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Spotify client failed to initialize: {e}")
        
        try:
            self.clients[MetadataSource.MUSICBRAINZ] = MusicBrainzClient()
            self.logger.info("✅ MusicBrainz client initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ MusicBrainz client failed to initialize: {e}")
    
    def _respect_rate_limit(self, source: MetadataSource):
        """Respeta los límites de velocidad de las APIs."""
        if source in self.last_api_call:
            elapsed = time.time() - self.last_api_call[source]
            required_wait = self.rate_limits.get(source, 1.0)
            if elapsed < required_wait:
                time.sleep(required_wait - elapsed)
        
        self.last_api_call[source] = time.time()
    
    def get_tracks_with_missing_metadata(self) -> List[TrackMetadata]:
        """Obtiene todas las pistas con metadatos faltantes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path, title, artist, album, genre, year, bpm, key, energy
            FROM tracks
        """)
        
        tracks_with_missing = []
        for row in cursor.fetchall():
            track = TrackMetadata(
                file_path=row[0],
                title=row[1],
                artist=row[2],
                album=row[3],
                genre=row[4],
                year=row[5],
                bpm=row[6],
                key=row[7],
                energy=row[8]
            )
            
            if not track.is_complete():
                tracks_with_missing.append(track)
        
        conn.close()
        return tracks_with_missing
    
    def get_all_tracks(self) -> List[TrackMetadata]:
        """Obtiene todas las pistas de la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path, title, artist, album, genre, year, bpm, key, energy
            FROM tracks
        """)
        
        all_tracks = []
        for row in cursor.fetchall():
            track = TrackMetadata(
                file_path=row[0],
                title=row[1],
                artist=row[2],
                album=row[3],
                genre=row[4],
                year=row[5],
                bpm=row[6],
                key=row[7],
                energy=row[8]
            )
            all_tracks.append(track)
            
        conn.close()
        return all_tracks

    def search_metadata_spotify(self, track: TrackMetadata) -> MetadataSearchResult:
        """Busca metadatos en Spotify con clasificación inteligente de géneros."""
        if MetadataSource.SPOTIFY not in self.clients:
            return MetadataSearchResult(
                source=MetadataSource.SPOTIFY,
                confidence=0.0,
                metadata={},
                success=False,
                error_message="Spotify client not available"
            )

        try:
            self._respect_rate_limit(MetadataSource.SPOTIFY)

            client = self.clients[MetadataSource.SPOTIFY]
            result = client.search_track(track.title or "", track.artist or "")

            if result:
                # Mejorar clasificación de géneros
                if result.get("genre"):
                    # Obtener géneros adicionales del artista si es posible
                    raw_genres = [result["genre"]]

                    # Clasificar género inteligentemente
                    classification = self.genre_classifier.classify_genre(
                        raw_genres=raw_genres,
                        artist=track.artist,
                        year=track.year,
                        sources=["spotify"]
                    )

                    # Actualizar resultado con clasificación mejorada
                    result.update({
                        "genre": classification.primary_genre,
                        "subgenres": classification.subgenres,
                        "genre_confidence": classification.confidence.value,
                        "historical_context": classification.historical_context
                    })

                # Calcular confianza basada en coincidencias
                confidence = self._calculate_confidence(track, result)

                return MetadataSearchResult(
                    source=MetadataSource.SPOTIFY,
                    confidence=confidence,
                    metadata=result,
                    success=True
                )
            else:
                return MetadataSearchResult(
                    source=MetadataSource.SPOTIFY,
                    confidence=0.0,
                    metadata={},
                    success=False,
                    error_message="No results found"
                )

        except Exception as e:
            self.logger.error(f"Spotify search error: {e}")
            return MetadataSearchResult(
                source=MetadataSource.SPOTIFY,
                confidence=0.0,
                metadata={},
                success=False,
                error_message=str(e)
            )
    
    def search_metadata_musicbrainz(self, track: TrackMetadata) -> MetadataSearchResult:
        """Busca metadatos en MusicBrainz con clasificación inteligente de géneros."""
        if MetadataSource.MUSICBRAINZ not in self.clients:
            return MetadataSearchResult(
                source=MetadataSource.MUSICBRAINZ,
                confidence=0.0,
                metadata={},
                success=False,
                error_message="MusicBrainz client not available"
            )

        try:
            self._respect_rate_limit(MetadataSource.MUSICBRAINZ)

            client = self.clients[MetadataSource.MUSICBRAINZ]
            result = client.search_track(track.title or "", track.artist or "")

            if result:
                # Mejorar clasificación de géneros
                if result.get("genre"):
                    # Clasificar género inteligentemente
                    classification = self.genre_classifier.classify_genre(
                        raw_genres=[result["genre"]],
                        artist=track.artist,
                        year=track.year or result.get("year"),
                        sources=["musicbrainz"]
                    )

                    # Actualizar resultado con clasificación mejorada
                    result.update({
                        "genre": classification.primary_genre,
                        "subgenres": classification.subgenres,
                        "genre_confidence": classification.confidence.value,
                        "historical_context": classification.historical_context
                    })

                # Calcular confianza basada en coincidencias
                confidence = self._calculate_confidence(track, result)

                return MetadataSearchResult(
                    source=MetadataSource.MUSICBRAINZ,
                    confidence=confidence,
                    metadata=result,
                    success=True
                )
            else:
                return MetadataSearchResult(
                    source=MetadataSource.MUSICBRAINZ,
                    confidence=0.0,
                    metadata={},
                    success=False,
                    error_message="No results found"
                )

        except Exception as e:
            self.logger.error(f"MusicBrainz search error: {e}")
            return MetadataSearchResult(
                source=MetadataSource.MUSICBRAINZ,
                confidence=0.0,
                metadata={},
                success=False,
                error_message=str(e)
            )
    
    def _calculate_confidence(self, original: TrackMetadata, found: Dict[str, Any]) -> float:
        """Calcula la confianza de un resultado basado en similitudes."""
        confidence = 0.0
        checks = 0

        # Comparar título
        if original.title and found.get('title'):
            if original.title.lower() in found['title'].lower() or found['title'].lower() in original.title.lower():
                confidence += 0.4
            checks += 1

        # Comparar artista
        if original.artist and found.get('artist'):
            if original.artist.lower() in found['artist'].lower() or found['artist'].lower() in original.artist.lower():
                confidence += 0.4
            checks += 1

        # Comparar álbum
        if original.album and found.get('album'):
            if original.album.lower() in found['album'].lower() or found['album'].lower() in original.album.lower():
                confidence += 0.2
            checks += 1

        # Si no pudimos hacer comparaciones directas pero tenemos metadatos útiles,
        # asignar una confianza base
        if checks == 0 and found:
            useful_fields = ['genre', 'year', 'bpm', 'key', 'energy', 'spotify_id']
            if any(field in found for field in useful_fields):
                confidence = 0.5  # Confianza media para metadatos útiles sin verificación

        return confidence / max(checks, 1) if checks > 0 else confidence

    def enrich_track(
        self, track: TrackMetadata, write_to_file: bool = False
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Enriquece los metadatos de una sola pista y opcionalmente los escribe en el archivo.

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (éxito, mensaje, metadatos_enriquecidos)
        """
        self.logger.info(f"Enriqueciendo pista: {track.file_path}")
        search_results: List[MetadataSearchResult] = []

        for source in self.search_priority:
            search_func = getattr(self, f"search_metadata_{source.value}", None)
            if search_func:
                result = search_func(track)
                if result.success:
                    search_results.append(result)

        if not search_results:
            return False, "No se encontraron resultados en ninguna API.", None

        # Lógica para elegir el mejor resultado (mayor confianza)
        best_result = max(search_results, key=lambda r: r.confidence)
        self.logger.info(
            f"Mejor resultado de '{best_result.source.name}' con confianza {best_result.confidence:.2f}"
        )
        
        enriched_metadata = best_result.metadata
        
        # Mejorar con el clasificador de género (si no se hizo ya)
        enriched_metadata = enhance_metadata_with_genre_classification(
            metadata=enriched_metadata,
            sources=[best_result.source.value]
        )

        # Actualizar la base de datos
        self._update_track_metadata(track.file_path, enriched_metadata)
        
        # Opcionalmente, escribir en el archivo de audio
        if write_to_file:
            self.logger.info(f"Escribiendo metadatos en el archivo: {track.file_path}")
            if not write_all_metadata(track.file_path, enriched_metadata):
                msg = f"Metadatos actualizados en la BD, pero falló la escritura en el archivo: {track.file_path}"
                self.logger.warning(msg)
                return True, msg, enriched_metadata

        return True, "Metadatos enriquecidos y actualizados.", enriched_metadata

    def enrich_library(
        self, 
        enrich_all: bool = False, 
        write_to_file: bool = False,
        update_callback: Optional[callable] = None
    ) -> List[Tuple[str, bool, str]]:
        """
        Busca y completa metadatos para la biblioteca.

        Args:
            enrich_all (bool): Si es True, enriquece todas las pistas, no solo las que tienen datos faltantes.
            write_to_file (bool): Si es True, guarda los metadatos directamente en los archivos de audio.
            update_callback (callable): Función para reportar el progreso.
        """
        self.logger.info(f"Iniciando enriquecimiento de biblioteca. enrich_all={enrich_all}, write_to_file={write_to_file}")
        
        if enrich_all:
            tracks_to_process = self.get_all_tracks()
        else:
            tracks_to_process = self.get_tracks_with_missing_metadata()

        if not tracks_to_process:
            self.logger.info("No hay pistas que necesiten enriquecimiento.")
            if update_callback:
                update_callback(100, "Análisis completado. No se encontraron pistas para mejorar.", [])
            return []

        total_tracks = len(tracks_to_process)
        results = []
        
        for i, track in enumerate(tracks_to_process):
            success, message, _ = self.enrich_track(track, write_to_file=write_to_file)
            results.append((track.file_path, success, message))

            if update_callback:
                progress = (i + 1) / total_tracks * 100
                status_message = f"Procesando {i+1}/{total_tracks}: {os.path.basename(track.file_path)}"
                update_callback(progress, status_message, results)
        
        self.logger.info("Enriquecimiento de la biblioteca completado.")
        return results

    def _update_track_metadata(self, file_path: str, metadata: Dict[str, Any]):
        """Actualiza los metadatos de una pista en la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Preparar campos para actualizar
        updates = []
        values = []
        
        # Campos básicos
        if metadata.get('title'):
            updates.append("title = ?")
            values.append(metadata['title'])
            
        if metadata.get('artist'):
            updates.append("artist = ?")
            values.append(metadata['artist'])
            
        if metadata.get('album'):
            updates.append("album = ?")
            values.append(metadata['album'])
        
        if metadata.get('genre'):
            updates.append("genre = ?")
            values.append(metadata['genre'])
        
        if metadata.get('year'):
            updates.append("year = ?")
            values.append(metadata['year'])
        
        if metadata.get('bpm'):
            updates.append("bpm = ?")
            values.append(metadata['bpm'])
        
        if metadata.get('key'):
            updates.append("key = ?")
            values.append(metadata['key'])
        
        if metadata.get('energy'):
            updates.append("energy = ?")
            values.append(metadata['energy'])
        
        if updates:
            values.append(file_path)
            query = f"UPDATE tracks SET {', '.join(updates)} WHERE file_path = ?"
            cursor.execute(query, values)
            conn.commit()
            
            # Log los campos que se actualizaron
            updated_fields = [update.split(" = ")[0] for update in updates]
            for field, value in zip(updated_fields, values[:-1]):
                print(f"Metadato '{field}' actualizado a '{value}' en {os.path.basename(file_path)}")
            
            self.logger.info(f"Base de datos actualizada para: {os.path.basename(file_path)}")
        
        conn.close()
    
    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas sobre el estado de los metadatos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de pistas
        cursor.execute("SELECT COUNT(*) FROM tracks")
        total_tracks = cursor.fetchone()[0]
        
        # Pistas con metadatos completos
        cursor.execute("""
            SELECT COUNT(*) FROM tracks 
            WHERE title IS NOT NULL AND title != ''
            AND artist IS NOT NULL AND artist != ''
            AND album IS NOT NULL AND album != ''
            AND genre IS NOT NULL AND genre != ''
        """)
        complete_tracks = cursor.fetchone()[0]
        
        # Pistas sin género
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE genre IS NULL OR genre = ''")
        missing_genre = cursor.fetchone()[0]
        
        # Pistas sin BPM
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE bpm IS NULL")
        missing_bpm = cursor.fetchone()[0]
        
        # Pistas sin key
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE key IS NULL OR key = ''")
        missing_key = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_tracks': total_tracks,
            'complete_tracks': complete_tracks,
            'incomplete_tracks': total_tracks - complete_tracks,
            'completion_percentage': (complete_tracks / total_tracks * 100) if total_tracks > 0 else 0,
            'missing_genre': missing_genre,
            'missing_bpm': missing_bpm,
            'missing_key': missing_key
        }