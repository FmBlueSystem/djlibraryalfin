# core/multi_source_genre_aggregator.py

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .genre_confidence_scorer import GenreConfidenceScorer, SourceData, GenreScore
from .intelligent_cache import get_cache
from .adaptive_rate_limiter import get_rate_limiter, record_api_result
from .enrichment_logger import get_enrichment_logger, set_log_context
from .semantic_genre_scorer import get_semantic_scorer
# Evitar importación circular - importaremos dinámicamente cuando sea necesario

@dataclass
class AggregationResult:
    """Resultado de la agregación de géneros multi-fuente."""
    final_genres: List[str]
    confidence_score: float
    sources_used: List[str]
    processing_time: float
    detailed_scores: List[GenreScore] = field(default_factory=list)
    fallback_used: bool = False
    errors: List[str] = field(default_factory=list)

@dataclass
class SourceConfig:
    """Configuración para una fuente de datos."""
    enabled: bool = True
    timeout: float = 10.0
    max_retries: int = 2
    priority: int = 1  # 1=alta, 2=media, 3=baja
    fallback_only: bool = False

class MultiSourceGenreAggregator:
    """
    Sistema de agregación inteligente de géneros que combina múltiples fuentes API
    con scoring de confianza, encadenamiento contextual y fallback automático.
    """
    
    def __init__(self):
        self.confidence_scorer = GenreConfidenceScorer()
        
        # Integración con sistemas mejorados
        self.cache = get_cache()
        self.rate_limiter = get_rate_limiter()
        self.logger = get_enrichment_logger()
        self.semantic_scorer = get_semantic_scorer()
        
        self.sources_config = {
            'musicbrainz': SourceConfig(priority=1, timeout=8.0),
            'spotify': SourceConfig(priority=1, timeout=12.0),
            'discogs': SourceConfig(priority=2, timeout=15.0),
            'lastfm': SourceConfig(priority=3, timeout=10.0, fallback_only=True),
            'local': SourceConfig(priority=3, enabled=False)  # Solo si es necesario
        }
        
        # Estadísticas para optimización
        self.success_stats = {source: 0 for source in self.sources_config.keys()}
        self.failure_stats = {source: 0 for source in self.sources_config.keys()}
        
    def set_source_config(self, source: str, config: SourceConfig):
        """Actualiza configuración de una fuente específica."""
        self.sources_config[source] = config
        
    def _get_active_sources(self, include_fallback: bool = False) -> List[str]:
        """Obtiene lista de fuentes activas basándose en configuración y prioridad."""
        active = []
        
        for source, config in self.sources_config.items():
            if not config.enabled:
                continue
                
            if config.fallback_only and not include_fallback:
                continue
                
            active.append(source)
        
        # Ordenar por prioridad (1=alta prioridad primero)
        active.sort(key=lambda s: self.sources_config[s].priority)
        return active
    
    def _fetch_from_source(self, source: str, track_info: Dict, enrichment_function) -> Optional[SourceData]:
        """
        Obtiene datos de una fuente específica con manejo de errores y timeouts mejorado.
        """
        config = self.sources_config.get(source)
        if not config or not config.enabled:
            return None
        
        artist = track_info.get('artist', '')
        title = track_info.get('title', '')
        
        # Verificar cache primero
        cached_result = self.cache.get(artist, title, source)
        if cached_result:
            self.logger.cache_hit(source, track_info)
            
            # Crear SourceData desde cache
            genres = self._parse_genres_from_result(cached_result, source)
            if genres:
                return SourceData(
                    source=source,
                    genres=genres,
                    metadata=cached_result,
                    raw_confidence=0.9  # High confidence for cached results
                )
        else:
            self.logger.cache_miss(source, track_info)
            
        # Wait for rate limiting
        wait_time = self.rate_limiter.wait_for_rate_limit(source)
        
        # Get optimal timeout
        timeout = self.rate_limiter.get_optimal_timeout(source)
        
        # Log API request
        self.logger.api_request(source, track_info, {'timeout': timeout})
        
        try:
            start_time = time.time()
            
            # Llamar función de enriquecimiento específica
            result = enrichment_function(track_info, source)
            
            processing_time = time.time() - start_time
            
            # Log successful response
            self.logger.api_response(source, track_info, True, processing_time, result)
            
            # Record success in rate limiter
            record_api_result(source, True, processing_time)
            
            if not result or 'genre' not in result:
                return None
                
            # Parsear géneros según el formato de cada fuente
            genres = self._parse_genres_from_result(result, source)
            
            if not genres:
                return None
            
            # Calculate confidence
            confidence = self._calculate_raw_confidence(result, source, processing_time)
            
            # Store in cache
            self.cache.put(artist, title, source, result, confidence)
                
            # Crear SourceData
            source_data = SourceData(
                source=source,
                genres=genres,
                metadata=result,
                raw_confidence=confidence
            )
            
            self.success_stats[source] += 1
            print(f"✅ {source}: Encontrados {len(genres)} géneros en {processing_time:.2f}s")
            return source_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log error
            self.logger.error(source, f"Error fetching from {source}", e, track_info=track_info)
            
            # Determine error type
            was_timeout = "timeout" in str(e).lower()
            was_throttled = "429" in str(e) or "rate limit" in str(e).lower()
            
            # Record failure in rate limiter
            record_api_result(source, False, processing_time, 
                            error_type=type(e).__name__,
                            was_timeout=was_timeout, 
                            was_throttled=was_throttled)
            
            self.failure_stats[source] += 1
            print(f"❌ Error en {source}: {e}")
            return None
    
    def _parse_genres_from_result(self, result: Dict, source: str) -> List[str]:
        """Parsea géneros del resultado según el formato específico de cada fuente."""
        genre_text = result.get('genre', '')
        if not genre_text:
            return []
            
        # Diferentes formatos según la fuente
        if source == 'spotify':
            # Spotify devuelve lista o string separado por comas
            if isinstance(genre_text, list):
                return [g.strip() for g in genre_text if g.strip()]
            else:
                return [g.strip() for g in str(genre_text).split(',') if g.strip()]
                
        elif source == 'discogs':
            # Discogs combina genre y style
            genres = []
            if isinstance(genre_text, str):
                genres.extend(g.strip() for g in genre_text.split(',') if g.strip())
            elif isinstance(genre_text, list):
                genres.extend(g.strip() for g in genre_text if g.strip())
            return genres
            
        elif source == 'musicbrainz':
            # MusicBrainz tags separados por comas
            return [g.strip() for g in str(genre_text).split(',') if g.strip()]
            
        elif source == 'lastfm':
            # Last.fm top tags
            if isinstance(genre_text, list):
                return [g.strip() for g in genre_text if g.strip()]
            else:
                return [g.strip() for g in str(genre_text).split(',') if g.strip()]
        
        # Formato genérico
        return [g.strip() for g in str(genre_text).split(',') if g.strip()]
    
    def _calculate_raw_confidence(self, result: Dict, source: str, processing_time: float) -> float:
        """Calcula confianza bruta basándose en la respuesta de la fuente."""
        confidence = 0.5  # Base
        
        # Factor de velocidad de respuesta
        if processing_time < 2.0:
            confidence += 0.1
        elif processing_time > 10.0:
            confidence -= 0.1
            
        # Factor de completitud de datos
        metadata_fields = ['artist', 'album', 'title', 'year']
        completeness = sum(1 for field in metadata_fields if result.get(field)) / len(metadata_fields)
        confidence += completeness * 0.2
        
        # Factor específico por fuente
        if source == 'spotify' and result.get('spotify_track_id'):
            confidence += 0.15
        elif source == 'musicbrainz' and result.get('musicbrainz_recording_id'):
            confidence += 0.15
        elif source == 'discogs' and result.get('discogs_release_id'):
            confidence += 0.15
            
        return min(confidence, 1.0)
    
    def _apply_contextual_chaining(self, sources_data: List[SourceData], track_info: Dict) -> List[SourceData]:
        """
        Aplica encadenamiento contextual usando resultados de una fuente para mejorar otras.
        """
        enhanced_data = sources_data.copy()
        
        # Buscar fuentes con IDs específicos
        musicbrainz_data = next((sd for sd in sources_data if sd.source == 'musicbrainz'), None)
        spotify_data = next((sd for sd in sources_data if sd.source == 'spotify'), None)
        
        # Si tenemos ID de MusicBrainz, intentar obtener más info de Spotify
        if musicbrainz_data and musicbrainz_data.metadata.get('musicbrainz_artist_id'):
            mb_artist_id = musicbrainz_data.metadata['musicbrainz_artist_id']
            # Aquí se podría hacer una búsqueda mejorada en Spotify usando el ID de MB
            print(f"🔗 Encadenamiento: MusicBrainz Artist ID {mb_artist_id} disponible para cross-referencia")
        
        # Si tenemos datos de Spotify, usar para validar otros resultados
        if spotify_data and spotify_data.genres:
            spotify_genres = set(g.lower() for g in spotify_data.genres)
            
            # Validar géneros de otras fuentes contra Spotify
            for source_data in enhanced_data:
                if source_data.source != 'spotify':
                    validated_genres = []
                    for genre in source_data.genres:
                        # Si el género tiene alguna coincidencia semántica con Spotify, aumentar confianza
                        if any(sg in genre.lower() or genre.lower() in sg for sg in spotify_genres):
                            validated_genres.append(genre)
                    
                    if validated_genres != source_data.genres:
                        print(f"🔗 Validación cruzada: {source_data.source} géneros validados con Spotify")
                        source_data.genres = validated_genres
        
        return enhanced_data
    
    def _apply_final_curation(self, genres: List[str]) -> List[str]:
        """Aplica curación final usando sistemas mejorados."""
        if not genres:
            return []
        
        # 1. Aplicar scoring semántico
        scored_genres = self.semantic_scorer.score_genre_list(genres)
        
        # 2. Obtener mejores géneros basado en scores
        top_genres = [genre for genre, score in scored_genres if score > 0.3][:4]
        
        # 3. Registrar uso de géneros para aprendizaje
        for genre in top_genres:
            self.semantic_scorer.record_genre_usage(genre)
            
        try:
            # 4. Aplicar curación tradicional como paso final
            from .metadata_enricher import _curate_genres
            
            # Combinar géneros en string para curación
            combined_genres = "; ".join(top_genres)
            
            # Aplicar curación existente
            curated = _curate_genres(combined_genres, max_genres=4)
            
            if curated:
                final_genres = [g.strip() for g in curated.split(';') if g.strip()]
                
                # Log curated result
                self.logger.info(
                    "curator", 
                    f"Curación completada: {len(genres)} -> {len(final_genres)} géneros",
                    data={
                        'original_genres': genres,
                        'scored_genres': [(g, s) for g, s in scored_genres[:6]],
                        'final_genres': final_genres
                    }
                )
                
                return final_genres
            
        except ImportError:
            # Fallback mejorado con scoring semántico
            print("⚠️ No se pudo importar _curate_genres, usando scoring semántico")
            return top_genres
        
        return top_genres
    
    async def aggregate_genres_async(self, track_info: Dict, enrichment_functions: Dict) -> AggregationResult:
        """
        Versión asíncrona de agregación de géneros (para uso futuro).
        """
        start_time = time.time()
        sources_data = []
        errors = []
        
        # Por ahora, ejecutar de forma síncrona
        # En el futuro se puede implementar verdadero async
        result = self.aggregate_genres(track_info, enrichment_functions)
        
        return result
    
    def aggregate_genres(self, track_info: Dict, enrichment_functions: Dict) -> AggregationResult:
        """
        Agrega géneros de múltiples fuentes con scoring inteligente mejorado.
        
        Args:
            track_info: Información del track (título, artista, etc.)
            enrichment_functions: Dict con funciones de enriquecimiento por fuente
                                 {'spotify': func, 'musicbrainz': func, ...}
        """
        start_time = time.time()
        sources_data = []
        errors = []
        fallback_used = False
        
        # Set logging context
        set_log_context(
            task_type='aggregation',
            track_artist=track_info.get('artist', 'Unknown'),
            track_title=track_info.get('title', 'Unknown')
        )
        
        # Log aggregation start
        self.logger.aggregation_start(track_info, list(enrichment_functions.keys()))
        
        # Obtener fuentes activas
        active_sources = self._get_active_sources()
        
        print(f"🔄 Iniciando agregación para: {track_info.get('artist', 'Unknown')} - {track_info.get('title', 'Unknown')}")
        print(f"🎯 Fuentes activas: {', '.join(active_sources)}")
        
        # Recopilar datos de fuentes primarias
        for source in active_sources:
            if source in enrichment_functions:
                source_data = self._fetch_from_source(source, track_info, enrichment_functions[source])
                if source_data:
                    sources_data.append(source_data)
                else:
                    errors.append(f"No se pudieron obtener datos de {source}")
        
        # Si no tenemos suficientes datos, usar fuentes de fallback
        if len(sources_data) < 2:
            self.logger.warning("aggregator", "Pocos datos obtenidos, activando fallback")
            print("⚠️ Pocos datos obtenidos, activando fuentes de fallback...")
            fallback_sources = self._get_active_sources(include_fallback=True)
            
            for source in fallback_sources:
                if source not in active_sources and source in enrichment_functions:
                    source_data = self._fetch_from_source(source, track_info, enrichment_functions[source])
                    if source_data:
                        sources_data.append(source_data)
                        fallback_used = True
        
        # Aplicar encadenamiento contextual
        if len(sources_data) > 1:
            sources_data = self._apply_contextual_chaining(sources_data, track_info)
        
        # Scoring y agregación
        if sources_data:
            scored_genres = self.confidence_scorer.score_genres(sources_data)
            
            # Obtener mejores géneros
            top_genres = [g.genre for g in scored_genres[:4] if g.confidence > 0.3]
            
            # Aplicar curación final (ahora con scoring semántico)
            final_genres = self._apply_final_curation(top_genres)
            
            # Calcular score de confianza general
            if scored_genres:
                confidence_score = sum(g.confidence for g in scored_genres[:4]) / min(len(scored_genres), 4)
            else:
                confidence_score = 0.0
                
        else:
            final_genres = []
            scored_genres = []
            confidence_score = 0.0
            errors.append("No se obtuvieron datos de ninguna fuente")
        
        processing_time = time.time() - start_time
        sources_used = [sd.source for sd in sources_data]
        
        result = AggregationResult(
            final_genres=final_genres,
            confidence_score=confidence_score,
            sources_used=sources_used,
            processing_time=processing_time,
            detailed_scores=scored_genres,
            fallback_used=fallback_used,
            errors=errors
        )
        
        # Log aggregation completion
        self.logger.aggregation_complete(
            track_info, 
            {
                'final_genres': final_genres,
                'confidence_score': confidence_score,
                'sources_used': sources_used,
                'fallback_used': fallback_used
            },
            processing_time
        )
        
        print(f"✅ Agregación completada en {processing_time:.2f}s")
        print(f"🎵 Géneros finales: {'; '.join(final_genres) if final_genres else 'Ninguno'}")
        print(f"📊 Score de confianza: {confidence_score:.2f}")
        
        return result
    
    def get_performance_stats(self) -> Dict:
        """Retorna estadísticas de rendimiento de las fuentes."""
        stats = {}
        
        for source in self.sources_config.keys():
            total = self.success_stats[source] + self.failure_stats[source]
            success_rate = self.success_stats[source] / total if total > 0 else 0
            
            stats[source] = {
                'success_count': self.success_stats[source],
                'failure_count': self.failure_stats[source],
                'success_rate': success_rate,
                'total_requests': total,
                'enabled': self.sources_config[source].enabled,
                'priority': self.sources_config[source].priority
            }
        
        return stats
    
    def optimize_source_priorities(self):
        """Optimiza prioridades basándose en estadísticas de rendimiento."""
        stats = self.get_performance_stats()
        
        # Reordenar basándose en success_rate y número de requests
        reliable_sources = []
        for source, data in stats.items():
            if data['total_requests'] > 5:  # Mínimo de requests para considerar confiable
                reliability_score = data['success_rate'] * (1 + min(data['total_requests'] / 100, 0.5))
                reliable_sources.append((source, reliability_score))
        
        # Actualizar prioridades
        reliable_sources.sort(key=lambda x: x[1], reverse=True)
        
        for i, (source, score) in enumerate(reliable_sources[:3]):  # Top 3 como alta prioridad
            if source in self.sources_config:
                self.sources_config[source].priority = 1
                print(f"🔧 {source} promovido a prioridad alta (score: {score:.2f})")
        
        print("📊 Optimización de prioridades completada")