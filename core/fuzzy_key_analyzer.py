# core/fuzzy_key_analyzer.py

import math
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

class CamelotKey(Enum):
    """Enumeración de todas las claves Camelot."""
    # A = Minor, B = Major
    KEY_1A = "1A"    # A♭ Minor / G# Minor  
    KEY_1B = "1B"    # B Major / C♭ Major
    KEY_2A = "2A"    # E♭ Minor / D# Minor
    KEY_2B = "2B"    # F# Major / G♭ Major
    KEY_3A = "3A"    # B♭ Minor / A# Minor
    KEY_3B = "3B"    # D♭ Major / C# Major
    KEY_4A = "4A"    # F Minor
    KEY_4B = "4B"    # A♭ Major / G# Major
    KEY_5A = "5A"    # C Minor
    KEY_5B = "5B"    # E♭ Major / D# Major
    KEY_6A = "6A"    # G Minor
    KEY_6B = "6B"    # B♭ Major / A# Major
    KEY_7A = "7A"    # D Minor
    KEY_7B = "7B"    # F Major
    KEY_8A = "8A"    # A Minor
    KEY_8B = "8B"    # C Major
    KEY_9A = "9A"    # E Minor
    KEY_9B = "9B"    # G Major
    KEY_10A = "10A"  # B Minor
    KEY_10B = "10B"  # D Major
    KEY_11A = "11A"  # F# Minor / G♭ Minor
    KEY_11B = "11B"  # A Major
    KEY_12A = "12A"  # C# Minor / D♭ Minor
    KEY_12B = "12B"  # E Major

@dataclass
class FuzzyKeyCompatibility:
    """Resultado de análisis de compatibilidad fuzzy entre dos claves."""
    from_key: str
    to_key: str
    compatibility_score: float  # 0.0-1.0
    fuzzy_level: int          # 1-5, donde 1 = perfecto, 5 = muy fuzzy
    relationship_type: str    # "perfect", "adjacent", "relative", "diagonal", "pitch_shift"
    pitch_shift_semitones: int  # ±semitones necesarios para compatibilidad
    confidence: float         # Confianza en la recomendación
    explanation: str          # Explicación de la relación

@dataclass
class FuzzyKeyRecommendation:
    """Recomendación de mezcla con Fuzzy Keymixing."""
    original_compatibility: float
    fuzzy_compatibility: float
    improvement_factor: float
    recommended_pitch_shift: int
    alternative_keys: List[Tuple[str, float]]  # Claves alternativas con scores
    mixing_advice: List[str]

class FuzzyKeyAnalyzer:
    """
    Analizador de compatibilidad de claves usando técnica Fuzzy Keymixing.
    
    Implementa la técnica avanzada de Fuzzy Keymixing que permite mayor flexibilidad
    en las mezclas armónicas comparado con el círculo de quintas tradicional.
    
    Features:
    - Análisis de compatibilidad con "grados de verdad"
    - Sistema Camelot completo con 24 claves
    - Recomendaciones de pitch shifting (±1-2 semitonos)
    - Compatibilidad diagonal y adyacente
    - Scoring graduado vs binario tradicional
    - Múltiples niveles de "fuzziness"
    """
    
    def __init__(self):
        # Mapeo completo de claves musicales a Camelot
        self.key_to_camelot = self._build_key_mapping()
        self.camelot_to_key = {v: k for k, v in self.key_to_camelot.items()}
        
        # Matriz de compatibilidad tradicional (círculo de quintas)
        self.traditional_compatibility = self._build_traditional_compatibility()
        
        # Matriz de compatibilidad fuzzy expandida
        self.fuzzy_compatibility = self._build_fuzzy_compatibility()
        
        # Configuración de niveles fuzzy
        self.fuzzy_levels = {
            1: {"name": "Perfect", "threshold": 0.9, "description": "Compatibilidad perfecta"},
            2: {"name": "Excellent", "threshold": 0.8, "description": "Excelente compatibilidad"},
            3: {"name": "Good", "threshold": 0.6, "description": "Buena compatibilidad con ajustes menores"},
            4: {"name": "Fair", "threshold": 0.4, "description": "Compatibilidad moderada con pitch shift"},
            5: {"name": "Creative", "threshold": 0.2, "description": "Compatibilidad creativa experimental"}
        }
        
        print("🎵 FuzzyKeyAnalyzer inicializado con 24 claves Camelot")
    
    def analyze_fuzzy_compatibility(self, key1: str, key2: str, 
                                   max_fuzziness: int = 4) -> FuzzyKeyCompatibility:
        """
        Analiza la compatibilidad fuzzy entre dos claves.
        
        Args:
            key1: Primera clave (ej: "C Major", "8B")
            key2: Segunda clave
            max_fuzziness: Nivel máximo de fuzziness a considerar (1-5)
            
        Returns:
            FuzzyKeyCompatibility con análisis completo
        """
        # Convertir a claves Camelot si es necesario
        camelot1 = self._to_camelot_key(key1)
        camelot2 = self._to_camelot_key(key2)
        
        if not camelot1 or not camelot2:
            return FuzzyKeyCompatibility(
                from_key=key1, to_key=key2, compatibility_score=0.5,
                fuzzy_level=5, relationship_type="unknown",
                pitch_shift_semitones=0, confidence=0.3,
                explanation="No se pudo determinar la clave Camelot"
            )
        
        # Análisis tradicional primero
        traditional_score = self._get_traditional_compatibility(camelot1, camelot2)
        
        # Si la compatibilidad tradicional es alta, usar esa
        if traditional_score >= 0.8:
            relationship = self._get_relationship_type(camelot1, camelot2)
            return FuzzyKeyCompatibility(
                from_key=key1, to_key=key2, compatibility_score=traditional_score,
                fuzzy_level=1, relationship_type=relationship,
                pitch_shift_semitones=0, confidence=0.95,
                explanation=f"Compatibilidad perfecta tradicional: {relationship}"
            )
        
        # Análisis fuzzy expandido
        best_compatibility = traditional_score
        best_level = 5
        best_relationship = "traditional"
        best_pitch_shift = 0
        best_explanation = "Compatibilidad tradicional limitada"
        
        # Probar diferentes niveles de fuzziness
        for level in range(2, max_fuzziness + 1):
            fuzzy_result = self._analyze_fuzzy_level(camelot1, camelot2, level)
            
            if fuzzy_result["score"] > best_compatibility:
                best_compatibility = fuzzy_result["score"]
                best_level = level
                best_relationship = fuzzy_result["relationship"]
                best_pitch_shift = fuzzy_result["pitch_shift"]
                best_explanation = fuzzy_result["explanation"]
        
        # Calcular confianza basada en mejora sobre método tradicional
        improvement = best_compatibility - traditional_score
        confidence = min(0.9, 0.6 + improvement)
        
        return FuzzyKeyCompatibility(
            from_key=key1, to_key=key2, compatibility_score=best_compatibility,
            fuzzy_level=best_level, relationship_type=best_relationship,
            pitch_shift_semitones=best_pitch_shift, confidence=confidence,
            explanation=best_explanation
        )
    
    def get_fuzzy_recommendations(self, current_key: str, 
                                candidate_keys: List[str],
                                max_fuzziness: int = 4) -> FuzzyKeyRecommendation:
        """
        Obtiene recomendaciones fuzzy para una clave dada.
        
        Args:
            current_key: Clave actual
            candidate_keys: Lista de claves candidatas
            max_fuzziness: Nivel máximo de fuzziness
            
        Returns:
            FuzzyKeyRecommendation con mejores opciones
        """
        traditional_compatibilities = []
        fuzzy_compatibilities = []
        alternatives = []
        
        for candidate in candidate_keys:
            # Análisis tradicional
            trad_analysis = self.analyze_fuzzy_compatibility(current_key, candidate, max_fuzziness=1)
            traditional_compatibilities.append(trad_analysis.compatibility_score)
            
            # Análisis fuzzy
            fuzzy_analysis = self.analyze_fuzzy_compatibility(current_key, candidate, max_fuzziness)
            fuzzy_compatibilities.append(fuzzy_analysis.compatibility_score)
            
            # Añadir a alternativas si es buena opción
            if fuzzy_analysis.compatibility_score > 0.4:
                alternatives.append((candidate, fuzzy_analysis.compatibility_score))
        
        # Calcular métricas
        avg_traditional = sum(traditional_compatibilities) / len(traditional_compatibilities) if traditional_compatibilities else 0
        avg_fuzzy = sum(fuzzy_compatibilities) / len(fuzzy_compatibilities) if fuzzy_compatibilities else 0
        improvement_factor = (avg_fuzzy / avg_traditional) if avg_traditional > 0 else 1.0
        
        # Generar recomendación de pitch shift más común
        pitch_shifts = []
        for candidate in candidate_keys[:10]:  # Analizar primeros 10
            analysis = self.analyze_fuzzy_compatibility(current_key, candidate, max_fuzziness)
            if analysis.pitch_shift_semitones != 0:
                pitch_shifts.append(analysis.pitch_shift_semitones)
        
        recommended_pitch = max(set(pitch_shifts), key=pitch_shifts.count) if pitch_shifts else 0
        
        # Ordenar alternativas por score
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        # Generar consejos de mezcla
        mixing_advice = self._generate_mixing_advice(current_key, alternatives[:5], improvement_factor)
        
        return FuzzyKeyRecommendation(
            original_compatibility=avg_traditional,
            fuzzy_compatibility=avg_fuzzy,
            improvement_factor=improvement_factor,
            recommended_pitch_shift=recommended_pitch,
            alternative_keys=alternatives[:10],
            mixing_advice=mixing_advice
        )
    
    def _build_key_mapping(self) -> Dict[str, str]:
        """Construye mapeo completo de claves musicales a Camelot."""
        mapping = {}
        
        # Claves mayores
        major_keys = {
            "C Major": "8B", "G Major": "9B", "D Major": "10B", "A Major": "11B",
            "E Major": "12B", "B Major": "1B", "F# Major": "2B", "Gb Major": "2B",
            "C# Major": "3B", "Db Major": "3B", "Ab Major": "4B", "G# Major": "4B",
            "Eb Major": "5B", "D# Major": "5B", "Bb Major": "6B", "A# Major": "6B",
            "F Major": "7B"
        }
        
        # Claves menores
        minor_keys = {
            "A Minor": "8A", "E Minor": "9A", "B Minor": "10A", "F# Minor": "11A",
            "Gb Minor": "11A", "C# Minor": "12A", "Db Minor": "12A", "G# Minor": "1A",
            "Ab Minor": "1A", "D# Minor": "2A", "Eb Minor": "2A", "A# Minor": "3A",
            "Bb Minor": "3A", "F Minor": "4A", "C Minor": "5A", "G Minor": "6A",
            "D Minor": "7A"
        }
        
        # Combinar todos los mapeos
        mapping.update(major_keys)
        mapping.update(minor_keys)
        
        # Añadir variaciones con diferentes notaciones
        variations = {
            "C": "8B", "Cm": "5A", "C major": "8B", "C minor": "5A",
            "G": "9B", "Gm": "6A", "G major": "9B", "G minor": "6A",
            "D": "10B", "Dm": "7A", "D major": "10B", "D minor": "7A",
            "A": "11B", "Am": "8A", "A major": "11B", "A minor": "8A",
            "E": "12B", "Em": "9A", "E major": "12B", "E minor": "9A",
            "B": "1B", "Bm": "10A", "B major": "1B", "B minor": "10A",
            "F": "7B", "Fm": "4A", "F major": "7B", "F minor": "4A"
        }
        
        mapping.update(variations)
        
        # Claves Camelot directas (ya en formato correcto)
        for camelot_key in CamelotKey:
            mapping[camelot_key.value] = camelot_key.value
        
        return mapping
    
    def _build_traditional_compatibility(self) -> Dict[Tuple[str, str], float]:
        """Construye matriz de compatibilidad tradicional del círculo de quintas."""
        compatibility = {}
        
        # Compatibilidades perfectas (1.0)
        perfect_matches = [
            # Misma clave
            ("1A", "1A"), ("1B", "1B"), ("2A", "2A"), ("2B", "2B"),
            ("3A", "3A"), ("3B", "3B"), ("4A", "4A"), ("4B", "4B"),
            ("5A", "5A"), ("5B", "5B"), ("6A", "6A"), ("6B", "6B"),
            ("7A", "7A"), ("7B", "7B"), ("8A", "8A"), ("8B", "8B"),
            ("9A", "9A"), ("9B", "9B"), ("10A", "10A"), ("10B", "10B"),
            ("11A", "11A"), ("11B", "11B"), ("12A", "12A"), ("12B", "12B"),
            
            # Relativas mayor-menor (mismo número)
            ("1A", "1B"), ("1B", "1A"), ("2A", "2B"), ("2B", "2A"),
            ("3A", "3B"), ("3B", "3A"), ("4A", "4B"), ("4B", "4A"),
            ("5A", "5B"), ("5B", "5A"), ("6A", "6B"), ("6B", "6A"),
            ("7A", "7B"), ("7B", "7A"), ("8A", "8B"), ("8B", "8A"),
            ("9A", "9B"), ("9B", "9A"), ("10A", "10B"), ("10B", "10A"),
            ("11A", "11B"), ("11B", "11A"), ("12A", "12B"), ("12B", "12A")
        ]
        
        for match in perfect_matches:
            compatibility[match] = 1.0
        
        # Compatibilidades excelentes (0.9) - números adyacentes
        excellent_matches = []
        for i in range(1, 13):
            current = i
            next_num = (i % 12) + 1
            prev_num = ((i - 2) % 12) + 1
            
            # Adyacentes en la rueda
            excellent_matches.extend([
                (f"{current}A", f"{next_num}A"), (f"{current}A", f"{prev_num}A"),
                (f"{current}B", f"{next_num}B"), (f"{current}B", f"{prev_num}B"),
                (f"{next_num}A", f"{current}A"), (f"{prev_num}A", f"{current}A"),
                (f"{next_num}B", f"{current}B"), (f"{prev_num}B", f"{current}B")
            ])
        
        for match in excellent_matches:
            if match not in compatibility:  # No sobrescribir perfectos
                compatibility[match] = 0.9
        
        return compatibility
    
    def _build_fuzzy_compatibility(self) -> Dict[Tuple[str, str], Dict[str, float]]:
        """Construye matriz de compatibilidad fuzzy expandida."""
        fuzzy_matrix = {}
        
        # Para cada par de claves, calcular múltiples niveles de compatibilidad
        for from_key in CamelotKey:
            for to_key in CamelotKey:
                from_camelot = from_key.value
                to_camelot = to_key.value
                
                # Extraer números y letras
                from_num = int(from_camelot[:-1])
                from_letter = from_camelot[-1]
                to_num = int(to_camelot[:-1])
                to_letter = to_camelot[-1]
                
                # Calcular diferentes tipos de compatibilidad fuzzy
                compatibilities = {}
                
                # 1. Compatibilidad numérica (independiente de letra)
                num_distance = min(abs(from_num - to_num), 12 - abs(from_num - to_num))
                if num_distance == 0:
                    compatibilities["numeric"] = 1.0
                elif num_distance == 1:
                    compatibilities["numeric"] = 0.8
                elif num_distance == 2:
                    compatibilities["numeric"] = 0.6
                elif num_distance == 3:
                    compatibilities["numeric"] = 0.4
                else:
                    compatibilities["numeric"] = 0.2
                
                # 2. Compatibilidad modal (mayor/menor)
                if from_letter == to_letter:
                    compatibilities["modal"] = 1.0
                else:
                    compatibilities["modal"] = 0.7  # Cambio mayor-menor
                
                # 3. Compatibilidad diagonal (números diferentes, letras diferentes)
                if num_distance <= 2 and from_letter != to_letter:
                    compatibilities["diagonal"] = 0.6
                else:
                    compatibilities["diagonal"] = 0.0
                
                # 4. Compatibilidad con pitch shift (+/-1 semitono)
                pitch_shift_scores = []
                for shift in [-2, -1, 1, 2]:
                    shifted_num = ((from_num + shift - 1) % 12) + 1
                    if shifted_num == to_num:
                        if shift in [-1, 1]:
                            pitch_shift_scores.append(0.7)  # ±1 semitono
                        else:
                            pitch_shift_scores.append(0.5)  # ±2 semitonos
                
                compatibilities["pitch_shift"] = max(pitch_shift_scores) if pitch_shift_scores else 0.0
                
                fuzzy_matrix[(from_camelot, to_camelot)] = compatibilities
        
        return fuzzy_matrix
    
    def _analyze_fuzzy_level(self, camelot1: str, camelot2: str, level: int) -> Dict:
        """Analiza compatibilidad en un nivel específico de fuzziness."""
        if (camelot1, camelot2) not in self.fuzzy_compatibility:
            return {"score": 0.0, "relationship": "unknown", "pitch_shift": 0, "explanation": "Claves no reconocidas"}
        
        fuzzy_data = self.fuzzy_compatibility[(camelot1, camelot2)]
        
        if level == 2:  # Excellent - compatibilidad numérica
            score = fuzzy_data["numeric"] * 0.9
            return {
                "score": score,
                "relationship": "numeric_adjacent",
                "pitch_shift": 0,
                "explanation": f"Compatibilidad numérica excelente (mismo/adyacente en rueda Camelot)"
            }
        
        elif level == 3:  # Good - compatibilidad modal o diagonal
            modal_score = fuzzy_data["modal"] * fuzzy_data["numeric"]
            diagonal_score = fuzzy_data["diagonal"]
            score = max(modal_score, diagonal_score)
            
            if modal_score > diagonal_score:
                relationship = "modal_compatible"
                explanation = "Buena compatibilidad modal (mayor/menor relacionado)"
            else:
                relationship = "diagonal"
                explanation = "Compatibilidad diagonal en rueda Camelot"
            
            return {
                "score": score,
                "relationship": relationship,
                "pitch_shift": 0,
                "explanation": explanation
            }
        
        elif level == 4:  # Fair - con pitch shifting
            pitch_score = fuzzy_data["pitch_shift"]
            num1 = int(camelot1[:-1])
            num2 = int(camelot2[:-1])
            
            # Calcular pitch shift necesario
            shift = self._calculate_pitch_shift(num1, num2)
            
            return {
                "score": pitch_score,
                "relationship": "pitch_shift",
                "pitch_shift": shift,
                "explanation": f"Compatibilidad con pitch shift de {shift:+d} semitonos"
            }
        
        elif level == 5:  # Creative - cualquier combinación creativa
            # Combinar todos los factores con pesos menores
            combined_score = (
                fuzzy_data["numeric"] * 0.3 +
                fuzzy_data["modal"] * 0.2 +
                fuzzy_data["diagonal"] * 0.3 +
                fuzzy_data["pitch_shift"] * 0.4
            )
            
            return {
                "score": min(combined_score, 0.6),  # Cap en 0.6 para nivel creativo
                "relationship": "creative",
                "pitch_shift": self._calculate_pitch_shift(int(camelot1[:-1]), int(camelot2[:-1])),
                "explanation": "Compatibilidad creativa experimental con ajustes múltiples"
            }
        
        return {"score": 0.0, "relationship": "unknown", "pitch_shift": 0, "explanation": "Nivel de fuzziness no válido"}
    
    def _calculate_pitch_shift(self, num1: int, num2: int) -> int:
        """Calcula el pitch shift necesario en semitonos."""
        # Diferencia en la rueda Camelot
        diff = num2 - num1
        
        # Normalizar a rango -6 a +6 (mitad de la rueda)
        if diff > 6:
            diff -= 12
        elif diff < -6:
            diff += 12
        
        return diff
    
    def _to_camelot_key(self, key: str) -> Optional[str]:
        """Convierte cualquier formato de clave a Camelot."""
        if not key:
            return None
        
        # Limpiar y normalizar la clave
        key_clean = key.strip()
        
        # Si ya es formato Camelot, validar y retornar
        if key_clean in [ck.value for ck in CamelotKey]:
            return key_clean
        
        # Buscar en el mapeo
        return self.key_to_camelot.get(key_clean)
    
    def _get_traditional_compatibility(self, camelot1: str, camelot2: str) -> float:
        """Obtiene compatibilidad tradicional entre dos claves Camelot."""
        pair = (camelot1, camelot2)
        return self.traditional_compatibility.get(pair, 0.3)  # 0.3 default para incompatibles
    
    def _get_relationship_type(self, camelot1: str, camelot2: str) -> str:
        """Determina el tipo de relación entre dos claves."""
        if camelot1 == camelot2:
            return "identical"
        
        num1 = int(camelot1[:-1])
        num2 = int(camelot2[:-1])
        letter1 = camelot1[-1]
        letter2 = camelot2[-1]
        
        if num1 == num2:
            return "relative" if letter1 != letter2 else "identical"
        
        num_distance = min(abs(num1 - num2), 12 - abs(num1 - num2))
        if num_distance == 1:
            return "adjacent"
        elif num_distance == 5 or num_distance == 7:
            return "fifth"
        else:
            return "distant"
    
    def _generate_mixing_advice(self, current_key: str, alternatives: List[Tuple[str, float]], 
                              improvement_factor: float) -> List[str]:
        """Genera consejos de mezcla basados en análisis fuzzy."""
        advice = []
        
        if improvement_factor > 2.0:
            advice.append("🎯 Fuzzy Keymixing aumenta tus opciones de mezcla significativamente")
        elif improvement_factor > 1.5:
            advice.append("✅ Fuzzy logic te da más flexibilidad que el método tradicional")
        
        if alternatives:
            top_alt = alternatives[0]
            advice.append(f"🔥 Mejor opción fuzzy: {top_alt[0]} (score: {top_alt[1]:.2f})")
        
        # Análizar tipos de relaciones en las mejores alternativas
        relationship_types = []
        for alt_key, score in alternatives[:3]:
            analysis = self.analyze_fuzzy_compatibility(current_key, alt_key)
            if analysis.pitch_shift_semitones != 0:
                advice.append(f"🎛️ {alt_key}: Ajustar pitch {analysis.pitch_shift_semitones:+d} semitonos")
            relationship_types.append(analysis.relationship_type)
        
        # Consejo general basado en tipos de relación
        if "pitch_shift" in relationship_types:
            advice.append("💡 Usa controles de pitch para optimizar las mezclas")
        if "diagonal" in relationship_types:
            advice.append("🎪 Experimenta con mezclas diagonales en la rueda Camelot")
        
        return advice
    
    def get_fuzzy_compatible_keys(self, key: str, max_fuzziness: int = 4) -> Dict[int, List[str]]:
        """
        Obtiene todas las claves compatibles organizadas por nivel de fuzziness.
        
        Args:
            key: Clave de referencia
            max_fuzziness: Nivel máximo a considerar
            
        Returns:
            Dict con claves organizadas por nivel {level: [keys]}
        """
        camelot_key = self._to_camelot_key(key)
        if not camelot_key:
            return {}
        
        compatible_by_level = {level: [] for level in range(1, max_fuzziness + 1)}
        
        # Probar todas las claves
        for target_camelot in [ck.value for ck in CamelotKey]:
            if target_camelot == camelot_key:
                compatible_by_level[1].append(target_camelot)
                continue
            
            # Analizar en cada nivel
            for level in range(1, max_fuzziness + 1):
                analysis = self.analyze_fuzzy_compatibility(key, target_camelot, max_fuzziness=level)
                
                threshold = self.fuzzy_levels[level]["threshold"]
                if analysis.compatibility_score >= threshold:
                    # Añadir al nivel más bajo donde es compatible
                    compatible_by_level[level].append(target_camelot)
                    break
        
        return compatible_by_level
    
    def compare_traditional_vs_fuzzy(self, key: str) -> Dict[str, any]:
        """
        Compara opciones tradicionales vs fuzzy para una clave.
        
        Returns:
            Análisis comparativo completo
        """
        camelot_key = self._to_camelot_key(key)
        if not camelot_key:
            return {"error": "Clave no válida"}
        
        all_keys = [ck.value for ck in CamelotKey]
        
        # Análisis tradicional
        traditional_compatible = []
        for target in all_keys:
            score = self._get_traditional_compatibility(camelot_key, target)
            if score >= 0.7:  # Threshold tradicional
                traditional_compatible.append((target, score))
        
        # Análisis fuzzy
        fuzzy_compatible = []
        for target in all_keys:
            analysis = self.analyze_fuzzy_compatibility(key, target, max_fuzziness=4)
            if analysis.compatibility_score >= 0.4:  # Threshold fuzzy más bajo
                fuzzy_compatible.append((target, analysis.compatibility_score))
        
        # Calcular mejora
        traditional_count = len(traditional_compatible)
        fuzzy_count = len(fuzzy_compatible)
        improvement_ratio = fuzzy_count / traditional_count if traditional_count > 0 else float('inf')
        
        return {
            "original_key": key,
            "camelot_key": camelot_key,
            "traditional_options": len(traditional_compatible),
            "fuzzy_options": len(fuzzy_compatible),
            "improvement_ratio": improvement_ratio,
            "traditional_compatible": sorted(traditional_compatible, key=lambda x: x[1], reverse=True),
            "fuzzy_compatible": sorted(fuzzy_compatible, key=lambda x: x[1], reverse=True),
            "additional_options": fuzzy_count - traditional_count,
            "summary": f"Fuzzy Keymixing añade {fuzzy_count - traditional_count} opciones adicionales ({improvement_ratio:.1f}x mejora)"
        }

# Instancia global
_fuzzy_key_analyzer = None

def get_fuzzy_key_analyzer() -> FuzzyKeyAnalyzer:
    """Obtiene la instancia global del analizador fuzzy de claves."""
    global _fuzzy_key_analyzer
    if _fuzzy_key_analyzer is None:
        _fuzzy_key_analyzer = FuzzyKeyAnalyzer()
    return _fuzzy_key_analyzer

# Funciones de conveniencia
def analyze_fuzzy_key_compatibility(key1: str, key2: str, max_fuzziness: int = 4) -> FuzzyKeyCompatibility:
    """Analiza compatibilidad fuzzy entre dos claves."""
    return get_fuzzy_key_analyzer().analyze_fuzzy_compatibility(key1, key2, max_fuzziness)

def get_fuzzy_key_recommendations(current_key: str, candidate_keys: List[str]) -> FuzzyKeyRecommendation:
    """Obtiene recomendaciones fuzzy para una clave."""
    return get_fuzzy_key_analyzer().get_fuzzy_recommendations(current_key, candidate_keys)

def compare_traditional_vs_fuzzy_keymixing(key: str) -> Dict[str, any]:
    """Compara opciones tradicionales vs fuzzy."""
    return get_fuzzy_key_analyzer().compare_traditional_vs_fuzzy(key)