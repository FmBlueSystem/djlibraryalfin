"""Service for track recommendations based on DJ transition analysis."""

from typing import List, Dict, Optional, Tuple, Any
from core.dj_transition_analyzer import get_dj_transition_analyzer, TransitionAnalysis
from core.database import create_connection
import sqlite3
import time


class RecommendationService:
    """
    Service for generating track recommendations based on DJ compatibility analysis.
    """
    
    def __init__(self):
        self.analyzer = get_dj_transition_analyzer()
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes TTL
        print("🎯 RecommendationService inicializado")
    
    def get_compatible_tracks(self, current_track: Dict, limit: int = 10, 
                            min_score: float = 0.4, filters: Optional[Dict] = None) -> List[Tuple[Dict, TransitionAnalysis]]:
        """
        Get tracks compatible with the current track.
        
        Args:
            current_track: Current track to find matches for
            limit: Maximum number of recommendations
            min_score: Minimum compatibility score (0.0-1.0)
            filters: Optional filters (genre, bpm_range, energy_range)
            
        Returns:
            List of (track, analysis) tuples sorted by compatibility
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(current_track, limit, min_score, filters)
            
            # Check cache
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                print(f"🎯 Cache hit para recomendaciones de '{current_track.get('title', 'Unknown')}'")
                return cached_result
            
            print(f"🔍 Generando recomendaciones para: {current_track.get('title', 'Unknown')} - {current_track.get('artist', 'Unknown')}")
            
            # Get candidate tracks from database
            candidates = self._get_candidate_tracks(current_track, filters)
            
            if not candidates:
                print("⚠️ No hay candidatos disponibles")
                return []
            
            print(f"📊 Analizando {len(candidates)} candidatos...")
            
            # Analyze transitions with all candidates
            compatible_tracks = self.analyzer.find_best_next_tracks(
                current_track, candidates, limit=len(candidates)
            )
            
            # Filter by minimum score
            filtered_tracks = [
                (track, analysis) for track, analysis in compatible_tracks
                if analysis.overall_score >= min_score
            ]
            
            # Limit results
            result = filtered_tracks[:limit]
            
            # Cache the result
            self._store_in_cache(cache_key, result)
            
            print(f"✅ {len(result)} recomendaciones generadas (score >= {min_score})")
            return result
            
        except Exception as e:
            print(f"❌ Error generando recomendaciones: {e}")
            return []
    
    def get_recommendations_summary(self, current_track: Dict) -> Dict[str, Any]:
        """
        Get a summary of recommendations with statistics.
        
        Args:
            current_track: Current track
            
        Returns:
            Summary with counts by compatibility level and transition types
        """
        try:
            # Get all recommendations (no score filter)
            all_recommendations = self.get_compatible_tracks(
                current_track, limit=50, min_score=0.0
            )
            
            if not all_recommendations:
                return {
                    "total_candidates": 0,
                    "by_quality": {},
                    "by_transition_type": {},
                    "avg_score": 0.0,
                    "best_matches": []
                }
            
            # Analyze statistics
            scores = [analysis.overall_score for _, analysis in all_recommendations]
            avg_score = sum(scores) / len(scores)
            
            # Count by quality
            quality_counts = {}
            transition_type_counts = {}
            
            for _, analysis in all_recommendations:
                quality = analysis.transition_quality.value
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
                
                transition_type = analysis.recommended_type.value
                transition_type_counts[transition_type] = transition_type_counts.get(transition_type, 0) + 1
            
            # Get best matches (score >= 0.7)
            best_matches = [
                {
                    "track": {
                        "id": track["id"],
                        "title": track.get("title", "Unknown"),
                        "artist": track.get("artist", "Unknown"),
                        "bpm": track.get("bpm"),
                        "key": track.get("key")
                    },
                    "score": analysis.overall_score,
                    "transition_type": analysis.recommended_type.value,
                    "quality": analysis.transition_quality.value
                }
                for track, analysis in all_recommendations[:10]
                if analysis.overall_score >= 0.7
            ]
            
            return {
                "total_candidates": len(all_recommendations),
                "by_quality": quality_counts,
                "by_transition_type": transition_type_counts,
                "avg_score": avg_score,
                "best_matches": best_matches
            }
            
        except Exception as e:
            print(f"❌ Error generando resumen: {e}")
            return {}
    
    def get_detailed_analysis(self, current_track: Dict, target_track: Dict) -> Optional[Dict]:
        """
        Get detailed transition analysis between two specific tracks.
        
        Args:
            current_track: Current track
            target_track: Target track to analyze
            
        Returns:
            Detailed analysis dictionary
        """
        try:
            analysis = self.analyzer.analyze_transition(current_track, target_track)
            
            return {
                "overall_score": analysis.overall_score,
                "transition_quality": analysis.transition_quality.value,
                "recommended_type": analysis.recommended_type.value,
                "compatibility": {
                    "bpm": analysis.bpm_compatibility,
                    "key": analysis.key_compatibility,
                    "fuzzy_key": analysis.fuzzy_key_compatibility,
                    "energy": analysis.energy_compatibility,
                    "mood": analysis.mood_compatibility
                },
                "technical_details": {
                    "bpm_ratio": analysis.bpm_ratio,
                    "key_relationship": analysis.key_relationship,
                    "fuzzy_key_relationship": analysis.fuzzy_key_relationship,
                    "energy_delta": analysis.energy_delta,
                    "mix_out_point": analysis.mix_out_point,
                    "mix_in_point": analysis.mix_in_point,
                    "crossfade_duration": analysis.crossfade_duration
                },
                "pitch_shift": analysis.pitch_shift_recommendation,
                "recommendations": analysis.recommendations,
                "warnings": analysis.warnings
            }
            
        except Exception as e:
            print(f"❌ Error en análisis detallado: {e}")
            return None
    
    def _get_candidate_tracks(self, current_track: Dict, filters: Optional[Dict] = None) -> List[Dict]:
        """Get candidate tracks from database with optional filters."""
        try:
            conn = create_connection()
            if not conn:
                return []
            
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Base query
            base_query = """
                SELECT id, title, artist, album, genre, bpm, key, energy, valence, 
                       danceability, acousticness, duration, file_path
                FROM tracks
                WHERE id != ?
            """
            params = [current_track.get('id')]
            
            # Apply filters
            if filters:
                # Genre filter
                if filters.get('genre'):
                    base_query += " AND genre = ?"
                    params.append(filters['genre'])
                
                # BPM range filter
                if filters.get('bpm_range'):
                    bpm_min, bpm_max = filters['bpm_range']
                    base_query += " AND bpm BETWEEN ? AND ?"
                    params.extend([bpm_min, bpm_max])
                
                # Energy range filter
                if filters.get('energy_range'):
                    energy_min, energy_max = filters['energy_range']
                    base_query += " AND energy BETWEEN ? AND ?"
                    params.extend([energy_min, energy_max])
            
            # Limit candidates for performance
            base_query += " LIMIT 100"
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            candidates = [dict(row) for row in rows]
            conn.close()
            
            return candidates
            
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo candidatos: {e}")
            return []
    
    def _generate_cache_key(self, current_track: Dict, limit: int, min_score: float, filters: Optional[Dict]) -> str:
        """Generate cache key for request."""
        track_id = current_track.get('id', 'unknown')
        filters_key = str(sorted(filters.items())) if filters else 'no_filters'
        return f"rec_{track_id}_{limit}_{min_score}_{filters_key}"
    
    def _get_from_cache(self, key: str) -> Optional[List]:
        """Get result from cache if not expired."""
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    def _store_in_cache(self, key: str, result: List):
        """Store result in cache with timestamp."""
        self.cache[key] = (result, time.time())
        
        # Simple cache cleanup - remove old entries if cache gets too big
        if len(self.cache) > 50:
            current_time = time.time()
            expired_keys = [
                k for k, (_, timestamp) in self.cache.items()
                if current_time - timestamp > self.cache_ttl
            ]
            for k in expired_keys:
                del self.cache[k]
    
    def clear_cache(self):
        """Clear the recommendation cache."""
        self.cache.clear()
        print("🧹 Cache de recomendaciones limpiado")


# Global instance
_recommendation_service = None


def get_recommendation_service() -> RecommendationService:
    """Get global recommendation service instance."""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service


# Convenience functions
def get_track_recommendations(current_track: Dict, limit: int = 10, min_score: float = 0.4) -> List[Tuple[Dict, TransitionAnalysis]]:
    """Get track recommendations for current track."""
    return get_recommendation_service().get_compatible_tracks(current_track, limit, min_score)


def get_recommendation_summary(current_track: Dict) -> Dict[str, Any]:
    """Get recommendation summary for current track."""
    return get_recommendation_service().get_recommendations_summary(current_track)


def analyze_track_compatibility(current_track: Dict, target_track: Dict) -> Optional[Dict]:
    """Analyze compatibility between two tracks."""
    return get_recommendation_service().get_detailed_analysis(current_track, target_track)