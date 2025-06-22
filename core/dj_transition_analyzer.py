# core/dj_transition_analyzer.py

import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from .audio_enrichment_service import get_audio_enrichment_service
from .fuzzy_key_analyzer import get_fuzzy_key_analyzer
from .pitch_shift_recommender import get_pitch_shift_recommender

class TransitionType(Enum):
    """Tipos de transición entre tracks."""
    QUICK_CUT = "quick_cut"           # Corte rápido
    CROSSFADE = "crossfade"           # Crossfade simple
    BEATMATCH = "beatmatch"           # Beatmatching
    HARMONIC_MIX = "harmonic_mix"     # Mezcla armónica
    FUZZY_HARMONIC_MIX = "fuzzy_harmonic_mix"  # Mezcla armónica fuzzy
    ENERGY_TRANSITION = "energy_transition"  # Transición de energía
    KEY_TRANSITION = "key_transition"  # Transición por tonalidad
    PITCH_SHIFT_MIX = "pitch_shift_mix"  # Mezcla con pitch shifting

class TransitionQuality(Enum):
    """Calidad de la transición."""
    EXCELLENT = "excellent"  # 0.9-1.0
    GOOD = "good"           # 0.7-0.9
    FAIR = "fair"           # 0.5-0.7
    POOR = "poor"           # 0.3-0.5
    BAD = "bad"             # 0.0-0.3

@dataclass
class TransitionPoint:
    """Punto óptimo de transición en un track."""
    time_position: float      # Posición en segundos
    transition_type: TransitionType
    quality_score: float      # 0.0-1.0
    characteristics: Dict[str, Any]

@dataclass
class TransitionAnalysis:
    """Análisis completo de transición entre dos tracks."""
    from_track: Dict
    to_track: Dict
    
    # Compatibility scores
    bpm_compatibility: float
    key_compatibility: float
    fuzzy_key_compatibility: float  # Fuzzy Keymixing compatibility
    energy_compatibility: float
    mood_compatibility: float
    
    # Transition recommendations
    recommended_type: TransitionType
    transition_quality: TransitionQuality
    overall_score: float
    
    # Timing recommendations
    mix_out_point: float      # Cuándo empezar a salir del track actual
    mix_in_point: float       # Cuándo empezar a entrar al siguiente track
    crossfade_duration: float # Duración recomendada de crossfade
    
    # Technical details
    bpm_ratio: float          # Ratio de BPMs
    key_relationship: str     # Relación entre tonalidades
    fuzzy_key_relationship: str  # Relación fuzzy entre tonalidades
    pitch_shift_recommendation: Optional[Dict]  # Recomendación de pitch shift
    energy_delta: float       # Diferencia de energía
    
    # Specific recommendations
    recommendations: List[str]
    warnings: List[str]

class DJTransitionAnalyzer:
    """
    Analizador de transiciones para DJs con optimizaciones avanzadas.
    
    Features:
    - Análisis de compatibilidad BPM
    - Análisis de compatibilidad armónica  
    - Detección de puntos óptimos de mezcla
    - Recomendaciones de tipo de transición
    - Análisis de flujo de energía
    - Detección de clash harmónico
    - Optimización para diferentes estilos de DJ
    """
    
    def __init__(self):
        self.audio_service = get_audio_enrichment_service()
        self.fuzzy_analyzer = get_fuzzy_key_analyzer()
        self.pitch_recommender = get_pitch_shift_recommender()
        
        # Configuración de compatibilidad
        self.bpm_tolerance = {
            'perfect': 2,    # ±2 BPM
            'good': 5,       # ±5 BPM  
            'fair': 10,      # ±10 BPM
            'poor': 20       # ±20 BPM
        }
        
        # Círculo de quintas para análisis armónico
        self.circle_of_fifths = [
            'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F'
        ]
        
        # Relaciones armónicas compatibles
        self.harmonic_relations = self._build_harmonic_relations()
        
        print("🎛️ DJTransitionAnalyzer inicializado")
    
    def analyze_transition(self, from_track: Dict, to_track: Dict) -> TransitionAnalysis:
        """
        Analiza la transición entre dos tracks.
        
        Args:
            from_track: Track actual
            to_track: Siguiente track
            
        Returns:
            TransitionAnalysis con recomendaciones completas
        """
        print(f"🔍 Analizando transición: {from_track.get('title', 'Unknown')} -> {to_track.get('title', 'Unknown')}")
        
        # Analizar compatibilidades individuales
        bpm_compat = self._analyze_bpm_compatibility(from_track, to_track)
        key_compat = self._analyze_key_compatibility(from_track, to_track)
        fuzzy_key_compat = self._analyze_fuzzy_key_compatibility(from_track, to_track)
        energy_compat = self._analyze_energy_compatibility(from_track, to_track)
        mood_compat = self._analyze_mood_compatibility(from_track, to_track)
        
        # Determinar tipo de transición recomendado
        recommended_type = self._determine_transition_type(
            bpm_compat, key_compat, fuzzy_key_compat, energy_compat, mood_compat, from_track, to_track
        )
        
        # Calcular puntos de mezcla óptimos
        mix_out, mix_in, crossfade_duration = self._calculate_mix_points(
            from_track, to_track, recommended_type
        )
        
        # Analizar pitch shifting si es necesario
        pitch_shift_rec = self._analyze_pitch_shift_potential(from_track, to_track, fuzzy_key_compat)
        
        # Calcular score general
        overall_score = self._calculate_overall_score(
            bpm_compat, key_compat, fuzzy_key_compat, energy_compat, mood_compat
        )
        
        # Determinar calidad de transición
        quality = self._determine_transition_quality(overall_score)
        
        # Generar recomendaciones y warnings
        recommendations = self._generate_recommendations(
            from_track, to_track, bpm_compat, key_compat, fuzzy_key_compat, energy_compat, recommended_type, pitch_shift_rec
        )
        warnings = self._generate_warnings(
            from_track, to_track, bpm_compat, key_compat, fuzzy_key_compat, energy_compat
        )
        
        # Calcular métricas técnicas adicionales
        bpm_ratio = self._calculate_bpm_ratio(from_track, to_track)
        key_relationship = self._get_key_relationship(from_track, to_track)
        fuzzy_key_relationship = self._get_fuzzy_key_relationship(from_track, to_track, fuzzy_key_compat)
        energy_delta = self._calculate_energy_delta(from_track, to_track)
        
        return TransitionAnalysis(
            from_track=from_track,
            to_track=to_track,
            bpm_compatibility=bpm_compat,
            key_compatibility=key_compat,
            fuzzy_key_compatibility=fuzzy_key_compat,
            energy_compatibility=energy_compat,
            mood_compatibility=mood_compat,
            recommended_type=recommended_type,
            transition_quality=quality,
            overall_score=overall_score,
            mix_out_point=mix_out,
            mix_in_point=mix_in,
            crossfade_duration=crossfade_duration,
            bpm_ratio=bpm_ratio,
            key_relationship=key_relationship,
            fuzzy_key_relationship=fuzzy_key_relationship,
            pitch_shift_recommendation=pitch_shift_rec,
            energy_delta=energy_delta,
            recommendations=recommendations,
            warnings=warnings
        )
    
    def _analyze_bpm_compatibility(self, track1: Dict, track2: Dict) -> float:
        """Analiza compatibilidad de BPM entre dos tracks."""
        bpm1 = track1.get('bpm')
        bpm2 = track2.get('bpm')
        
        if not bpm1 or not bpm2:
            return 0.5  # Neutral si no hay datos de BPM
        
        # Calcular diferencia absoluta
        bpm_diff = abs(bpm1 - bpm2)
        
        # También considerar ratios comunes (2:1, 3:2, etc.)
        ratios_to_check = [
            (1, 1),    # Mismo BPM
            (2, 1),    # Doble tiempo
            (1, 2),    # Medio tiempo
            (3, 2),    # Sesquiáltera
            (2, 3),    # Sesquiáltera inversa
            (4, 3),    # 4:3
            (3, 4)     # 3:4
        ]
        
        best_compatibility = 0.0
        
        for ratio1, ratio2 in ratios_to_check:
            # Calcular BPM ajustado según ratio
            adjusted_bpm2 = bpm2 * (ratio1 / ratio2)
            adjusted_diff = abs(bpm1 - adjusted_bpm2)
            
            # Calcular score de compatibilidad
            if adjusted_diff <= self.bpm_tolerance['perfect']:
                compatibility = 1.0
            elif adjusted_diff <= self.bpm_tolerance['good']:
                compatibility = 0.9 - (adjusted_diff - self.bpm_tolerance['perfect']) * 0.1 / (self.bpm_tolerance['good'] - self.bpm_tolerance['perfect'])
            elif adjusted_diff <= self.bpm_tolerance['fair']:
                compatibility = 0.7 - (adjusted_diff - self.bpm_tolerance['good']) * 0.2 / (self.bpm_tolerance['fair'] - self.bpm_tolerance['good'])
            elif adjusted_diff <= self.bpm_tolerance['poor']:
                compatibility = 0.5 - (adjusted_diff - self.bpm_tolerance['fair']) * 0.2 / (self.bpm_tolerance['poor'] - self.bpm_tolerance['fair'])
            else:
                compatibility = max(0.0, 0.3 - (adjusted_diff - self.bpm_tolerance['poor']) * 0.3 / 50)
            
            # Penalizar ratios complejos
            ratio_complexity = abs(ratio1 - ratio2) / max(ratio1, ratio2)
            compatibility *= (1.0 - ratio_complexity * 0.2)
            
            best_compatibility = max(best_compatibility, compatibility)
        
        return best_compatibility
    
    def _analyze_key_compatibility(self, track1: Dict, track2: Dict) -> float:
        """Analiza compatibilidad harmónica entre dos tracks."""
        key1 = track1.get('key')
        key2 = track2.get('key')
        
        if not key1 or not key2 or key1 == "Unknown" or key2 == "Unknown":
            return 0.5  # Neutral si no hay información de tonalidad
        
        # Parsear tonalidades
        note1, mode1 = self._parse_key(key1)
        note2, mode2 = self._parse_key(key2)
        
        if not note1 or not note2:
            return 0.5
        
        # Verificar en relaciones harmónicas predefinidas
        key_pair = (f"{note1} {mode1}", f"{note2} {mode2}")
        reverse_pair = (f"{note2} {mode2}", f"{note1} {mode1}")
        
        if key_pair in self.harmonic_relations:
            return self.harmonic_relations[key_pair]
        elif reverse_pair in self.harmonic_relations:
            return self.harmonic_relations[reverse_pair]
        
        # Análisis basado en círculo de quintas si no hay relación directa
        return self._calculate_circle_of_fifths_compatibility(note1, note2, mode1, mode2)
    
    def _analyze_fuzzy_key_compatibility(self, track1: Dict, track2: Dict) -> float:
        """Analiza compatibilidad fuzzy entre dos tracks."""
        key1 = track1.get('key')
        key2 = track2.get('key')
        
        if not key1 or not key2 or key1 == "Unknown" or key2 == "Unknown":
            return 0.5  # Neutral si no hay información de tonalidad
        
        # Usar el analizador fuzzy
        fuzzy_analysis = self.fuzzy_analyzer.analyze_fuzzy_compatibility(key1, key2, max_fuzziness=4)
        return fuzzy_analysis.compatibility_score
    
    def _analyze_energy_compatibility(self, track1: Dict, track2: Dict) -> float:
        """Analiza compatibilidad de energía entre tracks."""
        energy1 = track1.get('energy')
        energy2 = track2.get('energy')
        
        if energy1 is None or energy2 is None:
            return 0.5  # Neutral si no hay datos
        
        energy_diff = abs(energy1 - energy2)
        
        # Calcular compatibilidad basada en diferencia
        if energy_diff <= 0.1:
            return 1.0  # Energías muy similares
        elif energy_diff <= 0.2:
            return 0.9  # Energías similares
        elif energy_diff <= 0.3:
            return 0.7  # Diferencia moderada
        elif energy_diff <= 0.5:
            return 0.5  # Diferencia notable
        else:
            return 0.3  # Energías muy diferentes
    
    def _analyze_mood_compatibility(self, track1: Dict, track2: Dict) -> float:
        """Analiza compatibilidad de mood entre tracks."""
        # Características de mood
        mood_characteristics = ['valence', 'danceability', 'acousticness']
        
        compatibilities = []
        
        for char in mood_characteristics:
            val1 = track1.get(char)
            val2 = track2.get(char)
            
            if val1 is not None and val2 is not None:
                diff = abs(val1 - val2)
                compatibility = max(0, 1 - diff * 1.5)  # Penalizar diferencias
                compatibilities.append(compatibility)
        
        if compatibilities:
            return sum(compatibilities) / len(compatibilities)
        else:
            return 0.5  # Neutral si no hay datos
    
    def _analyze_pitch_shift_potential(self, track1: Dict, track2: Dict, fuzzy_compat: float) -> Optional[Dict]:
        """Analiza el potencial de pitch shifting para mejorar la transición."""
        key1 = track1.get('key')
        key2 = track2.get('key')
        
        if not key1 or not key2 or key1 == "Unknown" or key2 == "Unknown":
            return None
        
        # Si la compatibilidad fuzzy ya es alta, no necesitamos pitch shift
        if fuzzy_compat >= 0.8:
            return None
        
        # Analizar recomendación de pitch shift
        pitch_recommendation = self.pitch_recommender.recommend_pitch_shift(key1, key2, max_shift=4)
        
        if pitch_recommendation and pitch_recommendation.compatibility_improvement > 0.2:
            return {
                "original_compatibility": pitch_recommendation.original_compatibility,
                "new_compatibility": pitch_recommendation.new_compatibility,
                "improvement": pitch_recommendation.compatibility_improvement,
                "shift_semitones": pitch_recommendation.shift_semitones,
                "shift_percentage": pitch_recommendation.shift_percentage,
                "direction": pitch_recommendation.direction.value,
                "confidence": pitch_recommendation.confidence,
                "explanation": pitch_recommendation.explanation
            }
        
        return None
    
    def _determine_transition_type(self, bpm_compat: float, key_compat: float, fuzzy_key_compat: float,
                                 energy_compat: float, mood_compat: float,
                                 from_track: Dict, to_track: Dict) -> TransitionType:
        """Determina el tipo de transición recomendado."""
        
        # Si BPM es muy compatible, beatmatching es posible
        if bpm_compat >= 0.8:
            # Si hay compatibilidad harmónica tradicional perfecta
            if key_compat >= 0.8:
                return TransitionType.HARMONIC_MIX
            # Si hay compatibilidad fuzzy alta
            elif fuzzy_key_compat >= 0.7:
                return TransitionType.FUZZY_HARMONIC_MIX
            else:
                return TransitionType.BEATMATCH
        
        # Si energías son muy diferentes, transición de energía
        energy1 = from_track.get('energy') or 0.5
        energy2 = to_track.get('energy') or 0.5
        if abs(energy1 - energy2) > 0.4:
            return TransitionType.ENERGY_TRANSITION
        
        # Pitch shift mixing - cuando fuzzy es significativamente mejor que tradicional
        if fuzzy_key_compat > key_compat + 0.3 and fuzzy_key_compat >= 0.6:
            return TransitionType.PITCH_SHIFT_MIX
        
        # Si hay compatibilidad de key tradicional pero no de BPM
        if key_compat >= 0.7 and bpm_compat < 0.6:
            return TransitionType.KEY_TRANSITION
        
        # Si hay compatibilidad fuzzy pero no tradicional
        if fuzzy_key_compat >= 0.6 and key_compat < 0.5:
            return TransitionType.FUZZY_HARMONIC_MIX
        
        # Si hay compatibilidad general moderada (incluir fuzzy en el cálculo)
        avg_compat = (bpm_compat + max(key_compat, fuzzy_key_compat) + energy_compat + mood_compat) / 4
        if avg_compat >= 0.6:
            return TransitionType.CROSSFADE
        
        # Fallback a corte rápido
        return TransitionType.QUICK_CUT
    
    def _calculate_mix_points(self, from_track: Dict, to_track: Dict, 
                            transition_type: TransitionType) -> Tuple[float, float, float]:
        """Calcula puntos óptimos de mezcla."""
        
        # Obtener puntos de mezcla pre-analizados si existen
        from_mix_out = from_track.get('mix_out_point')
        to_mix_in = to_track.get('mix_in_point')
        
        # Duración de tracks
        from_duration = from_track.get('duration', 240)  # Default 4 min
        to_duration = to_track.get('duration', 240)
        
        # Ajustar según tipo de transición
        if transition_type == TransitionType.QUICK_CUT:
            # Corte al final del primer track
            mix_out = from_duration - 1.0
            mix_in = 0.0
            crossfade = 0.1
            
        elif transition_type == TransitionType.CROSSFADE:
            # Crossfade moderado
            mix_out = from_mix_out or (from_duration * 0.85)
            mix_in = to_mix_in or 8.0
            crossfade = 8.0
            
        elif transition_type in [TransitionType.BEATMATCH, TransitionType.HARMONIC_MIX, TransitionType.FUZZY_HARMONIC_MIX]:
            # Mezcla larga para beatmatching
            mix_out = from_mix_out or (from_duration * 0.75)
            mix_in = to_mix_in or 16.0
            crossfade = 16.0
            
        elif transition_type == TransitionType.ENERGY_TRANSITION:
            # Transición más rápida para cambio de energía
            mix_out = from_mix_out or (from_duration * 0.90)
            mix_in = to_mix_in or 4.0
            crossfade = 4.0
            
        elif transition_type == TransitionType.KEY_TRANSITION:
            # Transición media para cambio de tonalidad
            mix_out = from_mix_out or (from_duration * 0.80)
            mix_in = to_mix_in or 12.0
            crossfade = 12.0
            
        elif transition_type == TransitionType.PITCH_SHIFT_MIX:
            # Transición con tiempo para ajustar pitch
            mix_out = from_mix_out or (from_duration * 0.70)
            mix_in = to_mix_in or 20.0
            crossfade = 20.0
            
        else:
            # Default
            mix_out = from_duration * 0.85
            mix_in = 8.0
            crossfade = 8.0
        
        return mix_out, mix_in, crossfade
    
    def _calculate_overall_score(self, bpm_compat: float, key_compat: float, fuzzy_key_compat: float,
                               energy_compat: float, mood_compat: float) -> float:
        """Calcula score general de la transición."""
        # Pesos para diferentes aspectos (ajustables según preferencias DJ)
        weights = {
            'bpm': 0.35,      # BPM es muy importante para DJs
            'key': 0.25,      # Harmonía es importante
            'energy': 0.25,   # Flujo de energía
            'mood': 0.15      # Consistencia de mood
        }
        
        # Usar el mejor score entre key tradicional y fuzzy
        best_key_compat = max(key_compat, fuzzy_key_compat)
        
        weighted_score = (
            bpm_compat * weights['bpm'] +
            best_key_compat * weights['key'] +
            energy_compat * weights['energy'] +
            mood_compat * weights['mood']
        )
        
        return weighted_score
    
    def _determine_transition_quality(self, overall_score: float) -> TransitionQuality:
        """Determina la calidad de la transición basándose en el score."""
        if overall_score >= 0.9:
            return TransitionQuality.EXCELLENT
        elif overall_score >= 0.7:
            return TransitionQuality.GOOD
        elif overall_score >= 0.5:
            return TransitionQuality.FAIR
        elif overall_score >= 0.3:
            return TransitionQuality.POOR
        else:
            return TransitionQuality.BAD
    
    def _generate_recommendations(self, from_track: Dict, to_track: Dict,
                                bpm_compat: float, key_compat: float, fuzzy_key_compat: float,
                                energy_compat: float, transition_type: TransitionType, 
                                pitch_shift_rec: Optional[Dict]) -> List[str]:
        """Genera recomendaciones específicas para la transición."""
        recommendations = []
        
        # Recomendaciones basadas en BPM
        if bpm_compat >= 0.8:
            recommendations.append("✅ BPMs muy compatibles - ideal para beatmatching")
        elif bpm_compat >= 0.6:
            recommendations.append("🎛️ BPMs moderadamente compatibles - ajusta pitch gradualmente")
        else:
            bpm1 = from_track.get('bpm', 0)
            bpm2 = to_track.get('bpm', 0)
            if bpm1 and bpm2:
                if bpm2 > bpm1:
                    recommendations.append(f"⬆️ Acelera desde {bpm1:.0f} a {bpm2:.0f} BPM")
                else:
                    recommendations.append(f"⬇️ Desacelera desde {bpm1:.0f} a {bpm2:.0f} BPM")
        
        # Recomendaciones basadas en tonalidad (tradicional vs fuzzy)
        if key_compat >= 0.8:
            recommendations.append("🎵 Tonalidades perfectamente compatibles - mezcla armónica tradicional")
        elif fuzzy_key_compat >= 0.8:
            recommendations.append("🌟 Excelente compatibilidad Fuzzy Keymixing - más flexible que método tradicional")
        elif key_compat >= 0.6:
            recommendations.append("🎼 Tonalidades moderadamente compatibles (tradicional)")
        elif fuzzy_key_compat >= 0.6:
            recommendations.append("🎯 Buena compatibilidad Fuzzy - experimenta con grados de verdad")
        elif fuzzy_key_compat > key_compat + 0.2:
            recommendations.append("💡 Fuzzy Keymixing mejora significativamente la compatibilidad")
        else:
            recommendations.append("⚠️ Tonalidades incompatibles - considera EQ, filtros o pitch shifting")
        
        # Recomendaciones específicas de pitch shift
        if pitch_shift_rec:
            shift = pitch_shift_rec.get('shift_semitones', 0)
            improvement = pitch_shift_rec.get('improvement', 0)
            if improvement > 0.3:
                recommendations.append(f"🎛️ PITCH SHIFT: Ajusta {shift:+.1f} semitonos para mejorar {improvement:.1%}")
            elif improvement > 0.1:
                recommendations.append(f"🔧 Considera pitch shift de {shift:+.1f} semitonos (mejora moderada)")
        
        # Recomendaciones basadas en energía
        energy1 = from_track.get('energy') or 0.5
        energy2 = to_track.get('energy') or 0.5
        if energy2 > energy1 + 0.2:
            recommendations.append("📈 Incremento de energía - ideal para build-up")
        elif energy2 < energy1 - 0.2:
            recommendations.append("📉 Reducción de energía - perfecto para cooldown")
        else:
            recommendations.append("➡️ Energía estable - mantiene el flow")
        
        # Recomendaciones específicas por tipo de transición
        if transition_type == TransitionType.BEATMATCH:
            recommendations.append("🎯 Usa beatmatching - alinea los beats perfectamente")
        elif transition_type == TransitionType.HARMONIC_MIX:
            recommendations.append("🎶 Mezcla armónica tradicional recomendada - compatibilidad perfecta")
        elif transition_type == TransitionType.FUZZY_HARMONIC_MIX:
            recommendations.append("🌈 Fuzzy Harmonic Mix - usa grados de verdad para mezcla flexible")
        elif transition_type == TransitionType.PITCH_SHIFT_MIX:
            recommendations.append("🎛️ Pitch Shift Mix - ajusta tonalidad para compatibilidad óptima")
        elif transition_type == TransitionType.QUICK_CUT:
            recommendations.append("✂️ Corte rápido recomendado - cambio dramático")
        
        return recommendations
    
    def _generate_warnings(self, from_track: Dict, to_track: Dict,
                         bpm_compat: float, key_compat: float, fuzzy_key_compat: float,
                         energy_compat: float) -> List[str]:
        """Genera warnings sobre problemas potenciales."""
        warnings = []
        
        # Warnings de BPM
        if bpm_compat < 0.3:
            warnings.append("⚠️ BPMs muy incompatibles - transición será difícil")
        
        # Warnings de tonalidad (considerar tanto tradicional como fuzzy)
        if key_compat < 0.3 and fuzzy_key_compat < 0.4:
            key1 = from_track.get('key')
            key2 = to_track.get('key')
            if key1 and key2 and key1 != "Unknown" and key2 != "Unknown":
                warnings.append(f"🚫 Clash armónico severo: {key1} -> {key2}")
        elif key_compat < 0.3 and fuzzy_key_compat >= 0.4:
            warnings.append("💡 Clash tradicional pero Fuzzy Keymixing puede ayudar")
        
        # Warnings de energía
        energy1 = from_track.get('energy') or 0.5
        energy2 = to_track.get('energy') or 0.5
        if abs(energy1 - energy2) > 0.6:
            warnings.append("⚡ Cambio de energía muy drástico - puede romper el flow")
        
        # Warnings técnicos
        if not from_track.get('mix_out_point'):
            warnings.append("📍 Track actual sin punto de salida analizado")
        if not to_track.get('mix_in_point'):
            warnings.append("📍 Siguiente track sin punto de entrada analizado")
        
        return warnings
    
    def _parse_key(self, key_str: str) -> Tuple[Optional[str], Optional[str]]:
        """Parsea string de tonalidad en nota y modo."""
        if not key_str or key_str == "Unknown":
            return None, None
        
        # Formatos comunes: "C Major", "Am", "C#m", "Db", etc.
        key_str = key_str.strip()
        
        # Detectar modo
        if "major" in key_str.lower():
            mode = "major"
            note = key_str.replace("Major", "").replace("major", "").strip()
        elif "minor" in key_str.lower() or key_str.endswith('m'):
            mode = "minor"
            note = key_str.replace("Minor", "").replace("minor", "").replace('m', '').strip()
        else:
            # Asumir mayor si no se especifica
            mode = "major"
            note = key_str
        
        # Limpiar nota
        note = note.strip()
        if len(note) == 0:
            return None, None
        
        return note, mode
    
    def _build_harmonic_relations(self) -> Dict[Tuple[str, str], float]:
        """Construye diccionario de relaciones harmónicas compatibles."""
        relations = {}
        
        # Relaciones perfectas (1.0)
        perfect_relations = [
            # Relativas mayor-menor
            ("C Major", "A Minor"), ("G Major", "E Minor"), ("D Major", "B Minor"),
            ("A Major", "F# Minor"), ("E Major", "C# Minor"), ("B Major", "G# Minor"),
            ("F# Major", "D# Minor"), ("F Major", "D Minor"), ("Bb Major", "G Minor"),
            ("Eb Major", "C Minor"), ("Ab Major", "F Minor"), ("Db Major", "Bb Minor"),
            
            # Misma tonalidad
            ("C Major", "C Major"), ("A Minor", "A Minor"), ("G Major", "G Major"),
            ("E Minor", "E Minor"), ("D Major", "D Major"), ("B Minor", "B Minor"),
        ]
        
        for rel in perfect_relations:
            relations[rel] = 1.0
        
        # Relaciones excelentes (0.9)
        excellent_relations = [
            # Quinta perfecta
            ("C Major", "G Major"), ("G Major", "D Major"), ("D Major", "A Major"),
            ("A Major", "E Major"), ("E Major", "B Major"), ("F Major", "C Major"),
            ("Bb Major", "F Major"), ("Eb Major", "Bb Major"), ("Ab Major", "Eb Major"),
            ("Db Major", "Ab Major"), ("F# Major", "C# Major"), ("B Major", "F# Major"),
        ]
        
        for rel in excellent_relations:
            relations[rel] = 0.9
        
        # Relaciones buenas (0.8)
        good_relations = [
            # Cuarta perfecta
            ("C Major", "F Major"), ("G Major", "C Major"), ("D Major", "G Major"),
            ("A Major", "D Major"), ("E Major", "A Major"), ("B Major", "E Major"),
        ]
        
        for rel in good_relations:
            relations[rel] = 0.8
        
        return relations
    
    def _calculate_circle_of_fifths_compatibility(self, note1: str, note2: str, 
                                                mode1: str, mode2: str) -> float:
        """Calcula compatibilidad basada en círculo de quintas."""
        try:
            # Normalizar notas
            note1 = note1.replace('b', '#').replace('#', '#')  # Simplificar sostenidos/bemoles
            note2 = note2.replace('b', '#').replace('#', '#')
            
            if note1 in self.circle_of_fifths and note2 in self.circle_of_fifths:
                pos1 = self.circle_of_fifths.index(note1)
                pos2 = self.circle_of_fifths.index(note2)
                
                # Calcular distancia mínima en el círculo
                distance = min(abs(pos1 - pos2), 12 - abs(pos1 - pos2))
                
                # Convertir distancia a compatibilidad
                if distance == 0:  # Misma nota
                    base_compat = 1.0 if mode1 == mode2 else 0.9
                elif distance == 1:  # Quinta perfecta
                    base_compat = 0.9
                elif distance == 2:  # Segunda mayor
                    base_compat = 0.7
                elif distance == 3:
                    base_compat = 0.5
                elif distance == 4:
                    base_compat = 0.4
                elif distance == 5:
                    base_compat = 0.3
                else:
                    base_compat = 0.2
                
                # Ajustar por diferencia de modo
                if mode1 != mode2:
                    base_compat *= 0.85
                
                return base_compat
            
        except (ValueError, IndexError):
            pass
        
        return 0.5  # Compatibilidad neutral si no se puede determinar
    
    def _calculate_bpm_ratio(self, track1: Dict, track2: Dict) -> float:
        """Calcula ratio de BPMs."""
        bpm1 = track1.get('bpm')
        bpm2 = track2.get('bpm')
        
        if bpm1 and bpm2 and bpm1 > 0:
            return bpm2 / bpm1
        return 1.0
    
    def _get_key_relationship(self, track1: Dict, track2: Dict) -> str:
        """Obtiene descripción de la relación entre tonalidades."""
        key1 = track1.get('key')
        key2 = track2.get('key')
        
        if not key1 or not key2 or key1 == "Unknown" or key2 == "Unknown":
            return "Unknown"
        
        if key1 == key2:
            return "Same Key"
        
        note1, mode1 = self._parse_key(key1)
        note2, mode2 = self._parse_key(key2)
        
        if note1 and note2:
            if note1 == note2 and mode1 != mode2:
                return "Parallel Major/Minor"
            elif mode1 == mode2:
                return f"Same Mode ({mode1})"
            else:
                return "Different Keys"
        
        return "Unknown Relationship"
    
    def _get_fuzzy_key_relationship(self, track1: Dict, track2: Dict, fuzzy_compat: float) -> str:
        """Obtiene descripción de la relación fuzzy entre tonalidades."""
        key1 = track1.get('key')
        key2 = track2.get('key')
        
        if not key1 or not key2 or key1 == "Unknown" or key2 == "Unknown":
            return "Unknown"
        
        if key1 == key2:
            return "Same Key"
        
        # Analizar con fuzzy system
        fuzzy_analysis = self.fuzzy_analyzer.analyze_fuzzy_compatibility(key1, key2, max_fuzziness=4)
        
        if fuzzy_compat >= 0.9:
            return f"Perfect Fuzzy Match (Level {fuzzy_analysis.fuzzy_level})"
        elif fuzzy_compat >= 0.8:
            return f"Excellent Fuzzy ({fuzzy_analysis.relationship_type})"
        elif fuzzy_compat >= 0.6:
            return f"Good Fuzzy ({fuzzy_analysis.relationship_type})"
        elif fuzzy_compat >= 0.4:
            return f"Fair Fuzzy ({fuzzy_analysis.relationship_type})"
        else:
            return f"Creative Fuzzy ({fuzzy_analysis.relationship_type})"
    
    def _calculate_energy_delta(self, track1: Dict, track2: Dict) -> float:
        """Calcula diferencia de energía."""
        energy1 = track1.get('energy') or 0.5
        energy2 = track2.get('energy') or 0.5
        return energy2 - energy1
    
    def find_best_next_tracks(self, current_track: Dict, candidate_tracks: List[Dict], 
                            limit: int = 10) -> List[Tuple[Dict, TransitionAnalysis]]:
        """
        Encuentra los mejores tracks para seguir al actual.
        
        Args:
            current_track: Track actual
            candidate_tracks: Lista de tracks candidatos
            limit: Número máximo de resultados
            
        Returns:
            Lista de tuplas (track, analysis) ordenada por calidad de transición
        """
        analyses = []
        
        for candidate in candidate_tracks:
            # No incluir el mismo track
            if candidate.get('id') == current_track.get('id'):
                continue
            
            analysis = self.analyze_transition(current_track, candidate)
            analyses.append((candidate, analysis))
        
        # Ordenar por score general
        analyses.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        return analyses[:limit]
    
    def analyze_set_flow(self, track_sequence: List[Dict]) -> Dict[str, Any]:
        """
        Analiza el flujo de un set completo.
        
        Args:
            track_sequence: Secuencia de tracks en orden
            
        Returns:
            Análisis completo del flujo del set
        """
        if len(track_sequence) < 2:
            return {"error": "Need at least 2 tracks for flow analysis"}
        
        transitions = []
        overall_scores = []
        energy_curve = []
        bpm_curve = []
        
        for i in range(len(track_sequence) - 1):
            current = track_sequence[i]
            next_track = track_sequence[i + 1]
            
            # Analizar transición
            analysis = self.analyze_transition(current, next_track)
            transitions.append(analysis)
            overall_scores.append(analysis.overall_score)
            
            # Construir curvas
            energy_curve.append(current.get('energy') or 0.5)
            bpm_curve.append(current.get('bpm', 120))
        
        # Añadir último track a las curvas
        last_track = track_sequence[-1]
        energy_curve.append(last_track.get('energy') or 0.5)
        bpm_curve.append(last_track.get('bpm', 120))
        
        # Calcular métricas del set
        avg_transition_quality = sum(overall_scores) / len(overall_scores)
        energy_variance = self._calculate_variance(energy_curve)
        bpm_variance = self._calculate_variance(bpm_curve)
        
        # Detectar problemas en el flujo
        flow_issues = []
        for i, analysis in enumerate(transitions):
            if analysis.transition_quality == TransitionQuality.BAD:
                track_name = analysis.to_track.get('title', f'Track {i+2}')
                flow_issues.append(f"Transición problemática en posición {i+1} -> {track_name}")
        
        return {
            "total_tracks": len(track_sequence),
            "transitions": transitions,
            "average_transition_quality": avg_transition_quality,
            "energy_curve": energy_curve,
            "bpm_curve": bpm_curve,
            "energy_variance": energy_variance,
            "bpm_variance": bpm_variance,
            "flow_issues": flow_issues,
            "set_duration": sum(t.get('duration', 0) for t in track_sequence),
            "recommendations": self._generate_set_recommendations(transitions, energy_curve, bpm_curve)
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calcula varianza de una lista de valores."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def _generate_set_recommendations(self, transitions: List[TransitionAnalysis], 
                                    energy_curve: List[float], bpm_curve: List[float]) -> List[str]:
        """Genera recomendaciones para el set completo."""
        recommendations = []
        
        # Análisis de energy curve
        energy_trend = energy_curve[-1] - energy_curve[0]
        if energy_trend > 0.3:
            recommendations.append("📈 Set con build-up energético - excelente para peak time")
        elif energy_trend < -0.3:
            recommendations.append("📉 Set con cooldown - perfecto para closing")
        else:
            recommendations.append("➡️ Energía estable - mantiene consistencia")
        
        # Análisis de calidad de transiciones
        poor_transitions = sum(1 for t in transitions if t.overall_score < 0.5)
        if poor_transitions == 0:
            recommendations.append("✅ Todas las transiciones son de calidad")
        elif poor_transitions <= len(transitions) * 0.2:
            recommendations.append("🎯 Mayoría de transiciones son buenas")
        else:
            recommendations.append("⚠️ Múltiples transiciones necesitan mejora")
        
        # Análisis de BPM
        bpm_variance = self._calculate_variance(bpm_curve)
        if bpm_variance < 100:
            recommendations.append("🎛️ BPM consistente - ideal para dancefloor")
        else:
            recommendations.append("🔀 BPM variable - asegurar transiciones suaves")
        
        return recommendations

# Instancia global
_dj_transition_analyzer = None

def get_dj_transition_analyzer() -> DJTransitionAnalyzer:
    """Obtiene la instancia global del analizador de transiciones."""
    global _dj_transition_analyzer
    if _dj_transition_analyzer is None:
        _dj_transition_analyzer = DJTransitionAnalyzer()
    return _dj_transition_analyzer

# Funciones de conveniencia
def analyze_track_transition(from_track: Dict, to_track: Dict) -> TransitionAnalysis:
    """Analiza transición entre dos tracks."""
    return get_dj_transition_analyzer().analyze_transition(from_track, to_track)

def find_compatible_tracks(current_track: Dict, candidates: List[Dict], limit: int = 10) -> List[Tuple[Dict, TransitionAnalysis]]:
    """Encuentra tracks compatibles para transición."""
    return get_dj_transition_analyzer().find_best_next_tracks(current_track, candidates, limit)

def analyze_set_transitions(track_list: List[Dict]) -> Dict[str, Any]:
    """Analiza flujo completo de un set."""
    return get_dj_transition_analyzer().analyze_set_flow(track_list)