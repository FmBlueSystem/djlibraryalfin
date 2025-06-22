# core/advanced_music_filters.py

from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import re
import json

from .audio_enrichment_service import get_audio_enrichment_service
from .semantic_genre_scorer import get_semantic_scorer
from .database import get_all_tracks

class FilterOperator(Enum):
    """Operadores para filtros."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"

class FilterType(Enum):
    """Tipos de filtros disponibles."""
    # Metadatos básicos
    ARTIST = "artist"
    TITLE = "title"
    ALBUM = "album"
    GENRE = "genre"
    YEAR = "year"
    DURATION = "duration"
    BPM = "bpm"
    KEY = "key"
    
    # Características de audio
    ENERGY = "energy"
    DANCEABILITY = "danceability"
    VALENCE = "valence"
    ACOUSTICNESS = "acousticness"
    INSTRUMENTALNESS = "instrumentalness"
    LIVENESS = "liveness"
    SPEECHINESS = "speechiness"
    LOUDNESS = "loudness"
    
    # Características espectrales
    SPECTRAL_CENTROID = "spectral_centroid"
    SPECTRAL_ROLLOFF = "spectral_rolloff"
    ZERO_CROSSING_RATE = "zero_crossing_rate"
    
    # Análisis de estructura
    BEAT_STRENGTH = "beat_strength"
    RHYTHM_CONSISTENCY = "rhythm_consistency"
    DYNAMIC_RANGE = "dynamic_range"
    
    # Características DJ
    INTRO_LENGTH = "intro_length"
    OUTRO_LENGTH = "outro_length"
    MIX_IN_POINT = "mix_in_point"
    MIX_OUT_POINT = "mix_out_point"
    
    # Filtros especiales
    AUDIO_QUALITY = "audio_quality"
    ANALYSIS_CONFIDENCE = "analysis_confidence"
    HARMONIC_COMPATIBILITY = "harmonic_compatibility"
    SIMILAR_TO_TRACK = "similar_to_track"

@dataclass
class FilterRule:
    """Regla de filtro individual."""
    filter_type: FilterType
    operator: FilterOperator
    value: Any
    weight: float = 1.0  # Peso del filtro (para scoring)
    enabled: bool = True

@dataclass
class FilterSet:
    """Conjunto de filtros con lógica de combinación."""
    rules: List[FilterRule]
    logic: str = "AND"  # "AND" o "OR"
    name: str = ""
    description: str = ""

@dataclass
class FilterResult:
    """Resultado de aplicar filtros."""
    tracks: List[Dict]
    total_filtered: int
    filter_stats: Dict[str, Any]
    processing_time: float

class AdvancedMusicFilters:
    """
    Sistema avanzado de filtros musicales basado en características de audio.
    
    Features:
    - Filtros por características musicales (energy, danceability, etc.)
    - Filtros semánticos inteligentes
    - Filtros de compatibilidad armónica
    - Filtros de similitud
    - Combinación lógica de múltiples filtros
    - Scoring y ranking de resultados
    - Presets de filtros para diferentes escenarios
    """
    
    def __init__(self):
        self.audio_service = get_audio_enrichment_service()
        self.semantic_scorer = get_semantic_scorer()
        
        # Presets de filtros predefinidos
        self.filter_presets = self._create_filter_presets()
        
        print("🔍 AdvancedMusicFilters inicializado")
    
    def apply_filters(self, filter_set: FilterSet, 
                     tracks: Optional[List[Dict]] = None) -> FilterResult:
        """
        Aplica un conjunto de filtros a una lista de tracks.
        
        Args:
            filter_set: Conjunto de filtros a aplicar
            tracks: Lista de tracks (si None, usa todos los tracks)
            
        Returns:
            FilterResult con tracks filtrados y estadísticas
        """
        import time
        start_time = time.time()
        
        # Obtener tracks si no se proporcionan
        if tracks is None:
            tracks = get_all_tracks()
        
        print(f"🔍 Aplicando filtros a {len(tracks)} tracks")
        
        filtered_tracks = []
        filter_stats = {
            "total_input": len(tracks),
            "rules_applied": len([r for r in filter_set.rules if r.enabled]),
            "logic": filter_set.logic,
            "rule_matches": {}
        }
        
        for track in tracks:
            if self._track_matches_filterset(track, filter_set, filter_stats):
                filtered_tracks.append(track)
        
        processing_time = time.time() - start_time
        filter_stats["processing_time"] = processing_time
        
        print(f"✅ Filtros aplicados: {len(filtered_tracks)}/{len(tracks)} tracks en {processing_time:.2f}s")
        
        return FilterResult(
            tracks=filtered_tracks,
            total_filtered=len(filtered_tracks),
            filter_stats=filter_stats,
            processing_time=processing_time
        )
    
    def _track_matches_filterset(self, track: Dict, filter_set: FilterSet, 
                                stats: Dict) -> bool:
        """Verifica si un track cumple con el conjunto de filtros."""
        enabled_rules = [r for r in filter_set.rules if r.enabled]
        if not enabled_rules:
            return True
        
        rule_results = []
        
        for rule in enabled_rules:
            matches = self._track_matches_rule(track, rule)
            rule_results.append(matches)
            
            # Actualizar estadísticas
            rule_key = f"{rule.filter_type.value}_{rule.operator.value}"
            if rule_key not in stats["rule_matches"]:
                stats["rule_matches"][rule_key] = {"matches": 0, "total": 0}
            stats["rule_matches"][rule_key]["total"] += 1
            if matches:
                stats["rule_matches"][rule_key]["matches"] += 1
        
        # Aplicar lógica de combinación
        if filter_set.logic == "OR":
            return any(rule_results)
        else:  # AND
            return all(rule_results)
    
    def _track_matches_rule(self, track: Dict, rule: FilterRule) -> bool:
        """Verifica si un track cumple con una regla específica."""
        try:
            # Obtener valor del track
            track_value = self._get_track_value(track, rule.filter_type)
            
            # Aplicar operador
            return self._apply_operator(track_value, rule.operator, rule.value, track, rule.filter_type)
            
        except Exception as e:
            print(f"⚠️ Error aplicando regla {rule.filter_type.value}: {e}")
            return False
    
    def _get_track_value(self, track: Dict, filter_type: FilterType) -> Any:
        """Obtiene el valor de un track para un tipo de filtro específico."""
        # Mapeo directo para campos de base de datos
        field_mapping = {
            FilterType.ARTIST: "artist",
            FilterType.TITLE: "title",
            FilterType.ALBUM: "album",
            FilterType.GENRE: "genre",
            FilterType.YEAR: "year",
            FilterType.DURATION: "duration",
            FilterType.BPM: "bpm",
            FilterType.KEY: "key",
            FilterType.ENERGY: "energy",
            FilterType.DANCEABILITY: "danceability",
            FilterType.VALENCE: "valence",
            FilterType.ACOUSTICNESS: "acousticness",
            FilterType.INSTRUMENTALNESS: "instrumentalness",
            FilterType.LIVENESS: "liveness",
            FilterType.SPEECHINESS: "speechiness",
            FilterType.LOUDNESS: "loudness",
            FilterType.SPECTRAL_CENTROID: "spectral_centroid",
            FilterType.SPECTRAL_ROLLOFF: "spectral_rolloff",
            FilterType.ZERO_CROSSING_RATE: "zero_crossing_rate",
            FilterType.BEAT_STRENGTH: "beat_strength",
            FilterType.RHYTHM_CONSISTENCY: "rhythm_consistency",
            FilterType.DYNAMIC_RANGE: "dynamic_range",
            FilterType.INTRO_LENGTH: "intro_length",
            FilterType.OUTRO_LENGTH: "outro_length",
            FilterType.MIX_IN_POINT: "mix_in_point",
            FilterType.MIX_OUT_POINT: "mix_out_point",
            FilterType.ANALYSIS_CONFIDENCE: "audio_analysis_confidence"
        }
        
        # Filtros especiales que requieren cálculo
        if filter_type == FilterType.AUDIO_QUALITY:
            return self._calculate_audio_quality(track)
        elif filter_type == FilterType.HARMONIC_COMPATIBILITY:
            # Esto requiere un track de referencia en rule.value
            return self._calculate_harmonic_compatibility(track, rule.value)
        elif filter_type == FilterType.SIMILAR_TO_TRACK:
            # Esto requiere un track de referencia en rule.value
            return self._calculate_track_similarity(track, rule.value)
        
        # Obtener valor directo
        field = field_mapping.get(filter_type)
        if field:
            return track.get(field)
        
        return None
    
    def _apply_operator(self, track_value: Any, operator: FilterOperator, 
                       filter_value: Any, track: Dict, filter_type: FilterType) -> bool:
        """Aplica un operador de comparación."""
        # Manejar valores nulos
        if operator == FilterOperator.IS_NULL:
            return track_value is None
        elif operator == FilterOperator.IS_NOT_NULL:
            return track_value is not None
        
        if track_value is None:
            return False
        
        # Operadores de igualdad
        if operator == FilterOperator.EQUALS:
            if isinstance(track_value, str) and isinstance(filter_value, str):
                return track_value.lower() == filter_value.lower()
            return track_value == filter_value
        
        elif operator == FilterOperator.NOT_EQUALS:
            if isinstance(track_value, str) and isinstance(filter_value, str):
                return track_value.lower() != filter_value.lower()
            return track_value != filter_value
        
        # Operadores numéricos
        elif operator == FilterOperator.GREATER_THAN:
            return float(track_value) > float(filter_value)
        
        elif operator == FilterOperator.LESS_THAN:
            return float(track_value) < float(filter_value)
        
        elif operator == FilterOperator.BETWEEN:
            if isinstance(filter_value, (list, tuple)) and len(filter_value) == 2:
                min_val, max_val = filter_value
                return min_val <= float(track_value) <= max_val
            return False
        
        # Operadores de texto
        elif operator == FilterOperator.CONTAINS:
            return str(filter_value).lower() in str(track_value).lower()
        
        elif operator == FilterOperator.NOT_CONTAINS:
            return str(filter_value).lower() not in str(track_value).lower()
        
        elif operator == FilterOperator.STARTS_WITH:
            return str(track_value).lower().startswith(str(filter_value).lower())
        
        elif operator == FilterOperator.ENDS_WITH:
            return str(track_value).lower().endswith(str(filter_value).lower())
        
        elif operator == FilterOperator.REGEX:
            try:
                pattern = re.compile(str(filter_value), re.IGNORECASE)
                return bool(pattern.search(str(track_value)))
            except re.error:
                return False
        
        # Operadores de lista
        elif operator == FilterOperator.IN_LIST:
            if isinstance(filter_value, (list, tuple)):
                return any(str(track_value).lower() == str(v).lower() for v in filter_value)
            return False
        
        elif operator == FilterOperator.NOT_IN_LIST:
            if isinstance(filter_value, (list, tuple)):
                return not any(str(track_value).lower() == str(v).lower() for v in filter_value)
            return True
        
        return False
    
    def _calculate_audio_quality(self, track: Dict) -> float:
        """Calcula un score de calidad de audio basado en múltiples factores."""
        quality_factors = []
        
        # Factor 1: Confianza del análisis
        confidence = track.get("audio_analysis_confidence")
        if confidence is not None:
            quality_factors.append(confidence)
        
        # Factor 2: Completitud de características
        audio_fields = ["energy", "danceability", "valence", "acousticness"]
        complete_fields = sum(1 for field in audio_fields if track.get(field) is not None)
        completeness = complete_fields / len(audio_fields)
        quality_factors.append(completeness)
        
        # Factor 3: Rango dinámico (si disponible)
        dynamic_range = track.get("dynamic_range")
        if dynamic_range is not None:
            # Normalizar rango dinámico (0.3-1.0 es bueno)
            normalized_dr = min(dynamic_range / 0.7, 1.0) if dynamic_range > 0 else 0
            quality_factors.append(normalized_dr)
        
        # Factor 4: Consistencia rítmica
        rhythm_consistency = track.get("rhythm_consistency")
        if rhythm_consistency is not None:
            quality_factors.append(rhythm_consistency)
        
        if quality_factors:
            return sum(quality_factors) / len(quality_factors)
        else:
            return 0.5  # Neutral si no hay datos
    
    def _calculate_harmonic_compatibility(self, track: Dict, reference_track: Dict) -> float:
        """Calcula compatibilidad armónica entre dos tracks."""
        track_key = track.get("key")
        ref_key = reference_track.get("key")
        
        if not track_key or not ref_key or track_key == "Unknown" or ref_key == "Unknown":
            return 0.5  # Neutral si no hay información de key
        
        # Usar el audio analyzer para calcular compatibilidad harmónica
        # (esto requeriría implementar el método en audio_analyzer)
        # Por ahora, una implementación simplificada
        
        if track_key == ref_key:
            return 1.0  # Misma tonalidad
        
        # Mapeo básico de compatibilidad
        compatibility_map = {
            ("C Major", "A Minor"): 0.9,
            ("G Major", "E Minor"): 0.9,
            ("D Major", "B Minor"): 0.9,
            ("A Major", "F# Minor"): 0.9,
            ("E Major", "C# Minor"): 0.9,
            ("B Major", "G# Minor"): 0.9,
            ("F# Major", "D# Minor"): 0.9,
            ("F Major", "D Minor"): 0.9,
            ("Bb Major", "G Minor"): 0.9,
            ("Eb Major", "C Minor"): 0.9,
            ("Ab Major", "F Minor"): 0.9,
            ("Db Major", "Bb Minor"): 0.9,
        }
        
        # Verificar ambas direcciones
        pair1 = (track_key, ref_key)
        pair2 = (ref_key, track_key)
        
        if pair1 in compatibility_map:
            return compatibility_map[pair1]
        elif pair2 in compatibility_map:
            return compatibility_map[pair2]
        else:
            return 0.3  # Baja compatibilidad por defecto
    
    def _calculate_track_similarity(self, track: Dict, reference_track: Dict) -> float:
        """Calcula similitud entre dos tracks."""
        track_path = track.get("file_path")
        ref_path = reference_track.get("file_path")
        
        if not track_path or not ref_path:
            return 0.0
        
        # Usar el servicio de audio para calcular similitud
        similarity = self.audio_service.calculate_tracks_similarity(track_path, ref_path)
        return similarity if similarity is not None else 0.0
    
    def create_smart_filter(self, criteria: Dict) -> FilterSet:
        """
        Crea un conjunto de filtros inteligente basado en criterios naturales.
        
        Args:
            criteria: Diccionario con criterios como {"mood": "energetic", "bpm_range": [120, 140]}
        """
        rules = []
        
        # Procesar mood
        if "mood" in criteria:
            mood_rules = self._create_mood_rules(criteria["mood"])
            rules.extend(mood_rules)
        
        # Procesar rangos
        for key, value in criteria.items():
            if key.endswith("_range") and isinstance(value, (list, tuple)) and len(value) == 2:
                field_name = key.replace("_range", "")
                if field_name == "bpm":
                    filter_type = FilterType.BPM
                elif field_name == "energy":
                    filter_type = FilterType.ENERGY
                elif field_name == "year":
                    filter_type = FilterType.YEAR
                else:
                    continue
                
                rule = FilterRule(
                    filter_type=filter_type,
                    operator=FilterOperator.BETWEEN,
                    value=value
                )
                rules.append(rule)
        
        # Procesar géneros
        if "genres" in criteria:
            genres = criteria["genres"]
            if isinstance(genres, str):
                genres = [genres]
            
            for genre in genres:
                rule = FilterRule(
                    filter_type=FilterType.GENRE,
                    operator=FilterOperator.CONTAINS,
                    value=genre
                )
                rules.append(rule)
        
        return FilterSet(
            rules=rules,
            logic="AND",
            name="Smart Filter",
            description="Filtro generado automáticamente"
        )
    
    def _create_mood_rules(self, mood: str) -> List[FilterRule]:
        """Crea reglas de filtro para un mood específico."""
        mood_rules = {
            "energetic": [
                FilterRule(FilterType.ENERGY, FilterOperator.GREATER_THAN, 0.7),
                FilterRule(FilterType.DANCEABILITY, FilterOperator.GREATER_THAN, 0.6),
                FilterRule(FilterType.BPM, FilterOperator.BETWEEN, [120, 160])
            ],
            "chill": [
                FilterRule(FilterType.ENERGY, FilterOperator.LESS_THAN, 0.4),
                FilterRule(FilterType.VALENCE, FilterOperator.BETWEEN, [0.3, 0.8]),
                FilterRule(FilterType.ACOUSTICNESS, FilterOperator.GREATER_THAN, 0.3),
                FilterRule(FilterType.BPM, FilterOperator.BETWEEN, [60, 110])
            ],
            "party": [
                FilterRule(FilterType.ENERGY, FilterOperator.GREATER_THAN, 0.8),
                FilterRule(FilterType.DANCEABILITY, FilterOperator.GREATER_THAN, 0.8),
                FilterRule(FilterType.VALENCE, FilterOperator.GREATER_THAN, 0.7),
                FilterRule(FilterType.BPM, FilterOperator.BETWEEN, [120, 140])
            ],
            "melancholic": [
                FilterRule(FilterType.VALENCE, FilterOperator.LESS_THAN, 0.3),
                FilterRule(FilterType.ENERGY, FilterOperator.LESS_THAN, 0.5),
                FilterRule(FilterType.ACOUSTICNESS, FilterOperator.GREATER_THAN, 0.4)
            ],
            "instrumental": [
                FilterRule(FilterType.INSTRUMENTALNESS, FilterOperator.GREATER_THAN, 0.7)
            ],
            "acoustic": [
                FilterRule(FilterType.ACOUSTICNESS, FilterOperator.GREATER_THAN, 0.7)
            ],
            "live": [
                FilterRule(FilterType.LIVENESS, FilterOperator.GREATER_THAN, 0.7)
            ]
        }
        
        return mood_rules.get(mood.lower(), [])
    
    def _create_filter_presets(self) -> Dict[str, FilterSet]:
        """Crea presets de filtros predefinidos."""
        presets = {}
        
        # Preset: Tracks de alta energía
        presets["high_energy"] = FilterSet(
            rules=[
                FilterRule(FilterType.ENERGY, FilterOperator.GREATER_THAN, 0.8),
                FilterRule(FilterType.DANCEABILITY, FilterOperator.GREATER_THAN, 0.7)
            ],
            name="Alta Energía",
            description="Tracks con alta energía y danceabilidad"
        )
        
        # Preset: Tracks perfectos para mezclar
        presets["mixable"] = FilterSet(
            rules=[
                FilterRule(FilterType.BEAT_STRENGTH, FilterOperator.GREATER_THAN, 0.7),
                FilterRule(FilterType.RHYTHM_CONSISTENCY, FilterOperator.GREATER_THAN, 0.8),
                FilterRule(FilterType.INTRO_LENGTH, FilterOperator.GREATER_THAN, 5.0),
                FilterRule(FilterType.OUTRO_LENGTH, FilterOperator.GREATER_THAN, 5.0)
            ],
            name="Ideal para Mezclas",
            description="Tracks con características ideales para DJ mixing"
        )
        
        # Preset: Alta calidad de audio
        presets["high_quality"] = FilterSet(
            rules=[
                FilterRule(FilterType.AUDIO_QUALITY, FilterOperator.GREATER_THAN, 0.8),
                FilterRule(FilterType.ANALYSIS_CONFIDENCE, FilterOperator.GREATER_THAN, 0.9),
                FilterRule(FilterType.DYNAMIC_RANGE, FilterOperator.GREATER_THAN, 0.5)
            ],
            name="Alta Calidad",
            description="Tracks con alta calidad de audio y análisis confiable"
        )
        
        # Preset: BPM compatible (house music)
        presets["house_compatible"] = FilterSet(
            rules=[
                FilterRule(FilterType.BPM, FilterOperator.BETWEEN, [120, 130]),
                FilterRule(FilterType.GENRE, FilterOperator.CONTAINS, "house"),
                FilterRule(FilterType.DANCEABILITY, FilterOperator.GREATER_THAN, 0.7)
            ],
            name="House Compatible",
            description="Tracks compatibles con house music"
        )
        
        return presets
    
    def get_preset(self, preset_name: str) -> Optional[FilterSet]:
        """Obtiene un preset de filtros."""
        return self.filter_presets.get(preset_name)
    
    def get_available_presets(self) -> List[str]:
        """Obtiene lista de presets disponibles."""
        return list(self.filter_presets.keys())
    
    def analyze_library_characteristics(self, tracks: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Analiza las características de la biblioteca musical.
        
        Returns:
            Estadísticas detalladas de la biblioteca
        """
        if tracks is None:
            tracks = get_all_tracks()
        
        analysis = {
            "total_tracks": len(tracks),
            "characteristics": {},
            "distributions": {},
            "recommendations": []
        }
        
        # Analizar características numéricas
        numeric_fields = ["energy", "danceability", "valence", "acousticness", 
                         "instrumentalness", "liveness", "speechiness", "loudness", "bpm"]
        
        for field in numeric_fields:
            values = [t.get(field) for t in tracks if t.get(field) is not None]
            if values:
                analysis["characteristics"][field] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "coverage": len(values) / len(tracks)
                }
        
        # Analizar distribución de géneros
        genre_counts = {}
        for track in tracks:
            genres = track.get("genre", "")
            if genres:
                for genre in genres.split(";"):
                    genre = genre.strip()
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        analysis["distributions"]["genres"] = dict(sorted(
            genre_counts.items(), key=lambda x: x[1], reverse=True
        )[:20])  # Top 20 géneros
        
        # Generar recomendaciones
        if analysis["characteristics"].get("energy", {}).get("coverage", 0) < 0.5:
            analysis["recommendations"].append(
                "Considera ejecutar análisis de audio para obtener más características de energía"
            )
        
        if len(analysis["distributions"]["genres"]) < 5:
            analysis["recommendations"].append(
                "La biblioteca tiene pocos géneros diversificados"
            )
        
        return analysis

# Instancia global
_advanced_filters = None

def get_advanced_filters() -> AdvancedMusicFilters:
    """Obtiene la instancia global de filtros avanzados."""
    global _advanced_filters
    if _advanced_filters is None:
        _advanced_filters = AdvancedMusicFilters()
    return _advanced_filters

# Funciones de conveniencia
def filter_tracks_by_characteristics(energy_range: Tuple[float, float] = None,
                                   danceability_range: Tuple[float, float] = None,
                                   bpm_range: Tuple[int, int] = None,
                                   tracks: List[Dict] = None) -> List[Dict]:
    """Filtra tracks por características específicas."""
    filters = get_advanced_filters()
    rules = []
    
    if energy_range:
        rules.append(FilterRule(FilterType.ENERGY, FilterOperator.BETWEEN, energy_range))
    if danceability_range:
        rules.append(FilterRule(FilterType.DANCEABILITY, FilterOperator.BETWEEN, danceability_range))
    if bpm_range:
        rules.append(FilterRule(FilterType.BPM, FilterOperator.BETWEEN, bpm_range))
    
    if not rules:
        return tracks or get_all_tracks()
    
    filter_set = FilterSet(rules=rules, logic="AND")
    result = filters.apply_filters(filter_set, tracks)
    return result.tracks

def filter_tracks_by_mood(mood: str, tracks: List[Dict] = None) -> List[Dict]:
    """Filtra tracks por mood."""
    filters = get_advanced_filters()
    criteria = {"mood": mood}
    filter_set = filters.create_smart_filter(criteria)
    result = filters.apply_filters(filter_set, tracks)
    return result.tracks

def get_mixable_tracks(min_intro: float = 5.0, min_outro: float = 5.0, 
                      tracks: List[Dict] = None) -> List[Dict]:
    """Obtiene tracks ideales para mezclar."""
    filters = get_advanced_filters()
    preset = filters.get_preset("mixable")
    if preset:
        result = filters.apply_filters(preset, tracks)
        return result.tracks
    return tracks or []