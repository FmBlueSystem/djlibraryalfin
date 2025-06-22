# core/pitch_shift_recommender.py

import math
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .fuzzy_key_analyzer import get_fuzzy_key_analyzer
from .camelot_key_mapper import get_camelot_key_mapper, KeyFormat

class PitchShiftDirection(Enum):
    """Dirección del pitch shift."""
    UP = "up"
    DOWN = "down"
    BOTH = "both"

class PitchShiftMethod(Enum):
    """Método de pitch shifting."""
    SEMITONES = "semitones"       # Ajuste por semitonos
    CENTS = "cents"               # Ajuste por cents (1/100 semitono)
    PERCENTAGE = "percentage"     # Ajuste por porcentaje de velocidad
    BPM_SYNC = "bpm_sync"        # Ajuste para sincronizar BPMs

@dataclass
class PitchShiftRecommendation:
    """Recomendación de pitch shift."""
    from_key: str
    to_key: str
    target_key: str
    shift_semitones: float        # Cambio en semitonos (puede ser decimal)
    shift_cents: int              # Cambio en cents (±1200 max)
    shift_percentage: float       # Cambio en porcentaje de velocidad
    direction: PitchShiftDirection
    compatibility_improvement: float  # Mejora en compatibilidad (0-1)
    original_compatibility: float
    new_compatibility: float
    confidence: float             # Confianza en la recomendación
    method: PitchShiftMethod
    explanation: str
    alternative_targets: List[Tuple[str, float, float]]  # (target_key, shift, compatibility)

@dataclass
class BPMSyncRecommendation:
    """Recomendación específica para sincronización de BPM."""
    from_bpm: float
    to_bpm: float
    target_bpm: float
    pitch_shift_semitones: float
    pitch_shift_percentage: float
    time_stretch_factor: float    # Factor de time stretching (mantiene pitch)
    sync_quality: float          # Calidad de la sincronización (0-1)
    method_recommended: str      # "pitch_shift", "time_stretch", "hybrid"
    explanation: str

class PitchShiftRecommender:
    """
    Sistema de recomendaciones de pitch shifting para Fuzzy Keymixing.
    
    Features:
    - Análisis automático de pitch shift necesario
    - Recomendaciones para compatibilidad armónica
    - Sincronización de BPM con pitch shifting
    - Cálculo de múltiples alternativas
    - Optimización para diferentes rangos de DJ pitch
    - Consideración de calidad de audio vs compatibilidad
    """
    
    def __init__(self):
        self.fuzzy_analyzer = get_fuzzy_key_analyzer()
        self.key_mapper = get_camelot_key_mapper()
        
        # Configuración de pitch shifting
        self.max_pitch_shift = 12  # ±12 semitonos (1 octava)
        self.optimal_pitch_range = 2  # ±2 semitonos para calidad óptima
        self.dj_pitch_range = 8  # ±8% típico en CDJs/software DJ
        
        # Mapeo semitono -> porcentaje (aproximado)
        self.semitone_to_percentage = 5.946  # 2^(1/12) ≈ 1.05946
        
        print("🎛️ PitchShiftRecommender inicializado")
    
    def recommend_pitch_shift(self, from_key: str, to_key: str, 
                            max_shift: int = 4, 
                            prefer_minimal: bool = True) -> Optional[PitchShiftRecommendation]:
        """
        Recomienda pitch shift para mejorar compatibilidad entre dos claves.
        
        Args:
            from_key: Clave actual
            to_key: Clave objetivo
            max_shift: Máximo shift en semitonos a considerar
            prefer_minimal: Si preferir shifts menores
            
        Returns:
            PitchShiftRecommendation con la mejor opción
        """
        # Analizar compatibilidad original
        original_analysis = self.fuzzy_analyzer.analyze_fuzzy_compatibility(from_key, to_key)
        original_compatibility = original_analysis.compatibility_score
        
        # Si ya es muy compatible, no necesita pitch shift
        if original_compatibility >= 0.9:
            return PitchShiftRecommendation(
                from_key=from_key, to_key=to_key, target_key=to_key,
                shift_semitones=0, shift_cents=0, shift_percentage=0.0,
                direction=PitchShiftDirection.BOTH,
                compatibility_improvement=0.0,
                original_compatibility=original_compatibility,
                new_compatibility=original_compatibility,
                confidence=0.95, method=PitchShiftMethod.SEMITONES,
                explanation="Ya es altamente compatible, no necesita pitch shift",
                alternative_targets=[]
            )
        
        best_recommendation = None
        best_improvement = 0.0
        alternatives = []
        
        # Probar diferentes shifts
        for shift in range(-max_shift, max_shift + 1):
            if shift == 0:
                continue  # Ya probamos el original
            
            # Calcular clave objetivo con shift
            target_key = self._apply_pitch_shift_to_key(from_key, shift)
            if not target_key:
                continue
            
            # Analizar nueva compatibilidad
            new_analysis = self.fuzzy_analyzer.analyze_fuzzy_compatibility(target_key, to_key)
            new_compatibility = new_analysis.compatibility_score
            
            improvement = new_compatibility - original_compatibility
            
            # Añadir a alternativas
            alternatives.append((target_key, shift, new_compatibility))
            
            # Verificar si es la mejor opción
            if improvement > best_improvement:
                # Calcular métricas de pitch shift
                shift_percentage = shift * self.semitone_to_percentage
                shift_cents = shift * 100
                direction = PitchShiftDirection.UP if shift > 0 else PitchShiftDirection.DOWN
                
                # Calcular confianza basada en mejora y shift mínimo
                confidence = min(0.95, 0.5 + improvement * 0.5)
                if prefer_minimal and abs(shift) <= 2:
                    confidence += 0.1
                
                explanation = f"Shift de {shift:+d} semitonos mejora compatibilidad de {original_compatibility:.2f} a {new_compatibility:.2f}"
                
                best_recommendation = PitchShiftRecommendation(
                    from_key=from_key, to_key=to_key, target_key=target_key,
                    shift_semitones=float(shift), shift_cents=shift_cents, 
                    shift_percentage=shift_percentage, direction=direction,
                    compatibility_improvement=improvement,
                    original_compatibility=original_compatibility,
                    new_compatibility=new_compatibility,
                    confidence=confidence, method=PitchShiftMethod.SEMITONES,
                    explanation=explanation, alternative_targets=[]
                )
                best_improvement = improvement
        
        # Añadir alternativas a la mejor recomendación
        if best_recommendation:
            # Filtrar y ordenar alternativas
            good_alternatives = [
                alt for alt in alternatives 
                if alt[2] > original_compatibility and alt[1] != best_recommendation.shift_semitones
            ]
            good_alternatives.sort(key=lambda x: x[2], reverse=True)
            best_recommendation.alternative_targets = good_alternatives[:5]
        
        return best_recommendation
    
    def recommend_bpm_sync_pitch_shift(self, from_bpm: float, to_bpm: float,
                                     from_key: str = None, to_key: str = None) -> BPMSyncRecommendation:
        """
        Recomienda pitch shift para sincronizar BPMs manteniendo armonía.
        
        Args:
            from_bpm: BPM actual
            to_bpm: BPM objetivo  
            from_key: Clave actual (opcional, para verificar armonía)
            to_key: Clave objetivo (opcional)
            
        Returns:
            BPMSyncRecommendation con opciones de sincronización
        """
        if from_bpm <= 0 or to_bpm <= 0:
            return BPMSyncRecommendation(
                from_bpm=from_bpm, to_bpm=to_bpm, target_bpm=to_bpm,
                pitch_shift_semitones=0, pitch_shift_percentage=0,
                time_stretch_factor=1.0, sync_quality=0.0,
                method_recommended="none", explanation="BPMs inválidos"
            )
        
        # Calcular ratio de BPMs
        bpm_ratio = to_bpm / from_bpm
        
        # Calcular pitch shift necesario (en semitonos)
        # Formula: semitones = 12 * log2(ratio)
        pitch_shift_semitones = 12 * math.log2(bpm_ratio)
        pitch_shift_percentage = (bpm_ratio - 1) * 100
        
        # Calcular time stretch factor (inverso del pitch shift)
        time_stretch_factor = 1.0 / bpm_ratio
        
        # Determinar método recomendado
        abs_shift = abs(pitch_shift_semitones)
        
        if abs_shift <= 2:
            # Pitch shift puro - buena calidad
            method_recommended = "pitch_shift"
            sync_quality = 1.0 - (abs_shift / 8)  # Calidad basada en shift
            explanation = f"Pitch shift de {pitch_shift_semitones:+.1f} semitonos para sincronizar BPMs"
            
        elif abs_shift <= 6:
            # Híbrido - combinar pitch shift y time stretch
            method_recommended = "hybrid"
            sync_quality = 0.8 - (abs_shift / 12)
            explanation = f"Combinación de pitch shift y time stretch para {abs_shift:.1f} semitonos de diferencia"
            
        else:
            # Time stretch puro - mantiene pitch pero cambia tempo
            method_recommended = "time_stretch"
            sync_quality = 0.6
            explanation = f"Time stretch recomendado para diferencia grande de BPM ({abs_shift:.1f} semitonos)"
        
        # Verificar compatibilidad armónica si tenemos claves
        if from_key and to_key:
            # Calcular clave resultante con pitch shift
            shifted_key = self._apply_pitch_shift_to_key(from_key, pitch_shift_semitones)
            if shifted_key:
                harmonic_analysis = self.fuzzy_analyzer.analyze_fuzzy_compatibility(shifted_key, to_key)
                harmonic_quality = harmonic_analysis.compatibility_score
                
                # Ajustar sync_quality considerando armonía
                sync_quality = (sync_quality + harmonic_quality) / 2
                
                if harmonic_quality < 0.4:
                    explanation += f" (⚠️ Posible clash armónico: {harmonic_quality:.2f})"
                elif harmonic_quality > 0.8:
                    explanation += f" (✅ Excelente armonía: {harmonic_quality:.2f})"
        
        return BPMSyncRecommendation(
            from_bpm=from_bpm, to_bpm=to_bpm, target_bpm=to_bpm,
            pitch_shift_semitones=pitch_shift_semitones,
            pitch_shift_percentage=pitch_shift_percentage,
            time_stretch_factor=time_stretch_factor,
            sync_quality=max(0.0, min(1.0, sync_quality)),
            method_recommended=method_recommended,
            explanation=explanation
        )
    
    def find_optimal_targets(self, from_key: str, candidate_keys: List[str],
                           max_shift: int = 3) -> List[PitchShiftRecommendation]:
        """
        Encuentra los mejores targets considerando pitch shifting.
        
        Args:
            from_key: Clave actual
            candidate_keys: Lista de claves candidatas
            max_shift: Máximo shift a considerar
            
        Returns:
            Lista de recomendaciones ordenadas por calidad
        """
        recommendations = []
        
        for candidate_key in candidate_keys:
            # Analizar sin pitch shift
            recommendation = self.recommend_pitch_shift(from_key, candidate_key, max_shift)
            if recommendation and recommendation.new_compatibility > 0.4:
                recommendations.append(recommendation)
        
        # Ordenar por nueva compatibilidad y mejora
        recommendations.sort(
            key=lambda x: (x.new_compatibility, x.compatibility_improvement),
            reverse=True
        )
        
        return recommendations[:10]  # Top 10
    
    def calculate_pitch_shift_quality_impact(self, shift_semitones: float) -> Dict[str, float]:
        """
        Calcula el impacto en calidad de audio del pitch shifting.
        
        Args:
            shift_semitones: Cantidad de pitch shift
            
        Returns:
            Dict con métricas de impacto en calidad
        """
        abs_shift = abs(shift_semitones)
        
        # Calidad general (0-1, donde 1 = sin degradación)
        if abs_shift == 0:
            overall_quality = 1.0
        elif abs_shift <= 1:
            overall_quality = 0.95
        elif abs_shift <= 2:
            overall_quality = 0.9
        elif abs_shift <= 4:
            overall_quality = 0.8
        elif abs_shift <= 6:
            overall_quality = 0.65
        elif abs_shift <= 8:
            overall_quality = 0.5
        else:
            overall_quality = 0.3
        
        # Impacto específico en diferentes aspectos
        timbre_preservation = max(0.2, 1.0 - (abs_shift / 10))
        rhythm_preservation = max(0.5, 1.0 - (abs_shift / 15))
        bass_quality = max(0.1, 1.0 - (abs_shift / 8))  # Bass se degrada más rápido
        vocal_quality = max(0.3, 1.0 - (abs_shift / 6))  # Vocales son sensibles
        
        return {
            "overall_quality": overall_quality,
            "timbre_preservation": timbre_preservation,
            "rhythm_preservation": rhythm_preservation,
            "bass_quality": bass_quality,
            "vocal_quality": vocal_quality,
            "recommended_max_shift": 4 if overall_quality > 0.7 else 2,
            "quality_category": self._get_quality_category(overall_quality)
        }
    
    def _apply_pitch_shift_to_key(self, key: str, shift_semitones: float) -> Optional[str]:
        """
        Aplica pitch shift a una clave y retorna la nueva clave.
        
        Args:
            key: Clave original
            shift_semitones: Semitonos a shiftar (puede ser decimal)
            
        Returns:
            Nueva clave después del shift
        """
        # Convertir a Camelot para cálculo
        camelot_key = self.key_mapper.convert_key(key)
        if not camelot_key:
            return None
        
        # Extraer número y letra
        num = int(camelot_key[:-1])
        letter = camelot_key[-1]
        
        # Aplicar shift (redondear a semitonos enteros)
        shift_rounded = round(shift_semitones)
        new_num = ((num - 1 + shift_rounded) % 12) + 1
        
        new_camelot = f"{new_num}{letter}"
        
        # Convertir de vuelta al formato original si no era Camelot
        original_format = self._detect_original_format(key)
        if original_format == "camelot":
            return new_camelot
        else:
            # Convertir de vuelta al formato tradicional
            return self.key_mapper.convert_key(new_camelot, target_format=KeyFormat.TRADITIONAL)
    
    def _detect_original_format(self, key: str) -> str:
        """Detecta el formato original de la clave."""
        key_info = self.key_mapper.analyze_key(key)
        if not key_info:
            return "unknown"
        
        if key.strip() in self.key_mapper.camelot_master_map:
            return "camelot"
        elif "Major" in key or "Minor" in key:
            return "traditional"
        else:
            return "simplified"
    
    def _get_quality_category(self, quality_score: float) -> str:
        """Categoriza la calidad del pitch shift."""
        if quality_score >= 0.9:
            return "Excellent"
        elif quality_score >= 0.8:
            return "Good" 
        elif quality_score >= 0.6:
            return "Fair"
        elif quality_score >= 0.4:
            return "Poor"
        else:
            return "Unacceptable"
    
    def generate_pitch_shift_guide(self, from_key: str, target_keys: List[str] = None) -> Dict[str, any]:
        """
        Genera una guía completa de pitch shifting para una clave.
        
        Args:
            from_key: Clave de referencia
            target_keys: Claves objetivo específicas (opcional)
            
        Returns:
            Guía completa con todas las opciones
        """
        if not target_keys:
            # Usar todas las claves Camelot como targets
            target_keys = list(self.key_mapper.camelot_master_map.keys())
        
        guide = {
            "reference_key": from_key,
            "shift_options": {},
            "quality_impact": {},
            "recommendations": [],
            "summary": {}
        }
        
        # Analizar cada shift posible (-6 a +6 semitonos)
        for shift in range(-6, 7):
            if shift == 0:
                continue
            
            shifted_key = self._apply_pitch_shift_to_key(from_key, shift)
            if not shifted_key:
                continue
            
            # Analizar compatibilidades con targets
            compatibilities = []
            for target in target_keys[:12]:  # Limitar para performance
                analysis = self.fuzzy_analyzer.analyze_fuzzy_compatibility(shifted_key, target)
                if analysis.compatibility_score > 0.5:
                    compatibilities.append((target, analysis.compatibility_score))
            
            # Calcular impacto en calidad
            quality_impact = self.calculate_pitch_shift_quality_impact(shift)
            
            guide["shift_options"][f"{shift:+d}"] = {
                "shifted_key": shifted_key,
                "compatible_targets": sorted(compatibilities, key=lambda x: x[1], reverse=True)[:5],
                "quality_impact": quality_impact,
                "recommended": quality_impact["overall_quality"] > 0.7 and len(compatibilities) > 0
            }
        
        # Generar recomendaciones generales
        best_shifts = []
        for shift_str, data in guide["shift_options"].items():
            if data["recommended"] and data["compatible_targets"]:
                quality = data["quality_impact"]["overall_quality"]
                compatibility_count = len(data["compatible_targets"])
                score = quality * compatibility_count
                best_shifts.append((shift_str, score, data))
        
        best_shifts.sort(key=lambda x: x[1], reverse=True)
        guide["recommendations"] = best_shifts[:3]
        
        # Resumen
        total_options = sum(len(data["compatible_targets"]) for data in guide["shift_options"].values())
        recommended_shifts = [shift for shift, data in guide["shift_options"].items() if data["recommended"]]
        
        guide["summary"] = {
            "total_compatible_options": total_options,
            "recommended_shifts": recommended_shifts,
            "optimal_range": "±2 semitonos para mejor calidad",
            "creative_range": "±4 semitonos para más opciones"
        }
        
        return guide

# Instancia global
_pitch_shift_recommender = None

def get_pitch_shift_recommender() -> PitchShiftRecommender:
    """Obtiene la instancia global del recomendador de pitch shift."""
    global _pitch_shift_recommender
    if _pitch_shift_recommender is None:
        _pitch_shift_recommender = PitchShiftRecommender()
    return _pitch_shift_recommender

# Funciones de conveniencia
def recommend_key_pitch_shift(from_key: str, to_key: str, max_shift: int = 4) -> Optional[PitchShiftRecommendation]:
    """Recomienda pitch shift entre dos claves."""
    return get_pitch_shift_recommender().recommend_pitch_shift(from_key, to_key, max_shift)

def recommend_bpm_pitch_sync(from_bpm: float, to_bpm: float, from_key: str = None, to_key: str = None) -> BPMSyncRecommendation:
    """Recomienda pitch shift para sincronizar BPMs."""
    return get_pitch_shift_recommender().recommend_bpm_sync_pitch_shift(from_bpm, to_bpm, from_key, to_key)

def calculate_pitch_quality_impact(shift_semitones: float) -> Dict[str, float]:
    """Calcula impacto de calidad del pitch shift."""
    return get_pitch_shift_recommender().calculate_pitch_shift_quality_impact(shift_semitones)