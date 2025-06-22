# core/camelot_key_mapper.py

import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

class KeyFormat(Enum):
    """Formatos de clave soportados."""
    CAMELOT = "camelot"           # 8A, 12B
    OPEN_KEY = "open_key"         # 8m, 12d  
    TRADITIONAL = "traditional"   # C Major, A Minor
    SIMPLIFIED = "simplified"     # C, Am, F#m
    MUSICAL = "musical"           # Do Mayor, La menor
    NUMERIC = "numeric"           # 1, 6m, 11

@dataclass
class KeyInfo:
    """Información completa de una clave musical."""
    original_input: str
    camelot: str
    open_key: str
    traditional: str
    simplified: str
    note: str
    mode: str
    sharps_flats: int
    enharmonic_equivalent: Optional[str]
    circle_of_fifths_position: int

class CamelotKeyMapper:
    """
    Convertidor universal entre diferentes sistemas de notación de claves.
    
    Soporta conversión entre:
    - Sistema Camelot (1A-12A, 1B-12B)
    - Sistema OpenKey (1m-12m, 1d-12d)
    - Notación tradicional (C Major, A Minor)
    - Notación simplificada (C, Am)
    - Detección automática de formato
    - Manejo de enarmónicos (C#/Db)
    """
    
    def __init__(self):
        # Mapeo maestro: Camelot -> toda la información
        self.camelot_master_map = self._build_master_mapping()
        
        # Mapeos reversos para búsqueda rápida
        self.reverse_maps = self._build_reverse_mappings()
        
        # Patrones regex para detección automática
        self.key_patterns = self._build_key_patterns()
        
        print("🗝️ CamelotKeyMapper inicializado con soporte universal de claves")
    
    def convert_key(self, input_key: str, target_format: KeyFormat = KeyFormat.CAMELOT) -> Optional[str]:
        """
        Convierte una clave a cualquier formato.
        
        Args:
            input_key: Clave en cualquier formato soportado
            target_format: Formato de salida deseado
            
        Returns:
            Clave convertida o None si no se puede convertir
        """
        key_info = self.analyze_key(input_key)
        if not key_info:
            return None
        
        if target_format == KeyFormat.CAMELOT:
            return key_info.camelot
        elif target_format == KeyFormat.OPEN_KEY:
            return key_info.open_key
        elif target_format == KeyFormat.TRADITIONAL:
            return key_info.traditional
        elif target_format == KeyFormat.SIMPLIFIED:
            return key_info.simplified
        else:
            return key_info.camelot  # Default
    
    def analyze_key(self, input_key: str) -> Optional[KeyInfo]:
        """
        Analiza una clave y retorna información completa.
        
        Args:
            input_key: Clave en cualquier formato
            
        Returns:
            KeyInfo con toda la información de la clave
        """
        if not input_key or not input_key.strip():
            return None
        
        input_clean = input_key.strip()
        
        # Detectar formato automáticamente
        detected_format = self._detect_key_format(input_clean)
        if not detected_format:
            return None
        
        # Normalizar a formato estándar
        normalized_key = self._normalize_key(input_clean, detected_format)
        if not normalized_key:
            return None
        
        # Convertir a Camelot (formato maestro)
        camelot_key = self._to_camelot(normalized_key, detected_format)
        if not camelot_key or camelot_key not in self.camelot_master_map:
            return None
        
        # Obtener información completa
        master_info = self.camelot_master_map[camelot_key]
        
        return KeyInfo(
            original_input=input_key,
            camelot=camelot_key,
            open_key=master_info["open_key"],
            traditional=master_info["traditional"],
            simplified=master_info["simplified"],
            note=master_info["note"],
            mode=master_info["mode"],
            sharps_flats=master_info["sharps_flats"],
            enharmonic_equivalent=master_info["enharmonic"],
            circle_of_fifths_position=master_info["circle_position"]
        )
    
    def batch_convert(self, keys: List[str], target_format: KeyFormat = KeyFormat.CAMELOT) -> Dict[str, Optional[str]]:
        """
        Convierte múltiples claves en lote.
        
        Args:
            keys: Lista de claves a convertir
            target_format: Formato de salida
            
        Returns:
            Dict con clave original -> clave convertida
        """
        results = {}
        for key in keys:
            results[key] = self.convert_key(key, target_format)
        return results
    
    def get_compatible_keys(self, input_key: str, include_enharmonics: bool = True) -> List[str]:
        """
        Obtiene claves tradicionalmente compatibles (círculo de quintas).
        
        Args:
            input_key: Clave de referencia
            include_enharmonics: Si incluir equivalentes enarmónicos
            
        Returns:
            Lista de claves compatibles en formato Camelot
        """
        key_info = self.analyze_key(input_key)
        if not key_info:
            return []
        
        camelot = key_info.camelot
        compatible = []
        
        # Extraer número y letra
        num = int(camelot[:-1])
        letter = camelot[-1]
        
        # Misma clave
        compatible.append(camelot)
        
        # Relativa mayor/menor (mismo número, diferente letra)
        relative_letter = "B" if letter == "A" else "A"
        compatible.append(f"{num}{relative_letter}")
        
        # Claves adyacentes (±1 en la rueda)
        prev_num = ((num - 2) % 12) + 1
        next_num = (num % 12) + 1
        
        compatible.extend([
            f"{prev_num}{letter}",
            f"{next_num}{letter}",
            f"{prev_num}{relative_letter}",
            f"{next_num}{relative_letter}"
        ])
        
        # Remover duplicados
        compatible = list(set(compatible))
        
        # Incluir enarmónicos si se solicita
        if include_enharmonics:
            with_enharmonics = []
            for compat_key in compatible:
                with_enharmonics.append(compat_key)
                master_info = self.camelot_master_map.get(compat_key, {})
                enharmonic = master_info.get("enharmonic")
                if enharmonic:
                    enharmonic_camelot = self.convert_key(enharmonic, KeyFormat.CAMELOT)
                    if enharmonic_camelot:
                        with_enharmonics.append(enharmonic_camelot)
            
            compatible = list(set(with_enharmonics))
        
        return sorted(compatible)
    
    def _build_master_mapping(self) -> Dict[str, Dict]:
        """Construye el mapeo maestro completo."""
        # Datos maestros: cada entrada Camelot con toda su información
        master = {
            "1A": {
                "open_key": "1m", "traditional": "G# Minor", "simplified": "G#m",
                "note": "G#", "mode": "minor", "sharps_flats": 5, 
                "enharmonic": "Ab Minor", "circle_position": 1
            },
            "1B": {
                "open_key": "1d", "traditional": "B Major", "simplified": "B",
                "note": "B", "mode": "major", "sharps_flats": 5,
                "enharmonic": None, "circle_position": 1
            },
            "2A": {
                "open_key": "2m", "traditional": "D# Minor", "simplified": "D#m",
                "note": "D#", "mode": "minor", "sharps_flats": 6,
                "enharmonic": "Eb Minor", "circle_position": 2
            },
            "2B": {
                "open_key": "2d", "traditional": "F# Major", "simplified": "F#",
                "note": "F#", "mode": "major", "sharps_flats": 6,
                "enharmonic": "Gb Major", "circle_position": 2
            },
            "3A": {
                "open_key": "3m", "traditional": "A# Minor", "simplified": "A#m",
                "note": "A#", "mode": "minor", "sharps_flats": 7,
                "enharmonic": "Bb Minor", "circle_position": 3
            },
            "3B": {
                "open_key": "3d", "traditional": "C# Major", "simplified": "C#",
                "note": "C#", "mode": "major", "sharps_flats": 7,
                "enharmonic": "Db Major", "circle_position": 3
            },
            "4A": {
                "open_key": "4m", "traditional": "F Minor", "simplified": "Fm",
                "note": "F", "mode": "minor", "sharps_flats": 4,
                "enharmonic": None, "circle_position": 4
            },
            "4B": {
                "open_key": "4d", "traditional": "Ab Major", "simplified": "Ab",
                "note": "Ab", "mode": "major", "sharps_flats": 4,
                "enharmonic": "G# Major", "circle_position": 4
            },
            "5A": {
                "open_key": "5m", "traditional": "C Minor", "simplified": "Cm",
                "note": "C", "mode": "minor", "sharps_flats": 3,
                "enharmonic": None, "circle_position": 5
            },
            "5B": {
                "open_key": "5d", "traditional": "Eb Major", "simplified": "Eb",
                "note": "Eb", "mode": "major", "sharps_flats": 3,
                "enharmonic": "D# Major", "circle_position": 5
            },
            "6A": {
                "open_key": "6m", "traditional": "G Minor", "simplified": "Gm",
                "note": "G", "mode": "minor", "sharps_flats": 2,
                "enharmonic": None, "circle_position": 6
            },
            "6B": {
                "open_key": "6d", "traditional": "Bb Major", "simplified": "Bb",
                "note": "Bb", "mode": "major", "sharps_flats": 2,
                "enharmonic": "A# Major", "circle_position": 6
            },
            "7A": {
                "open_key": "7m", "traditional": "D Minor", "simplified": "Dm",
                "note": "D", "mode": "minor", "sharps_flats": 1,
                "enharmonic": None, "circle_position": 7
            },
            "7B": {
                "open_key": "7d", "traditional": "F Major", "simplified": "F",
                "note": "F", "mode": "major", "sharps_flats": 1,
                "enharmonic": None, "circle_position": 7
            },
            "8A": {
                "open_key": "8m", "traditional": "A Minor", "simplified": "Am",
                "note": "A", "mode": "minor", "sharps_flats": 0,
                "enharmonic": None, "circle_position": 8
            },
            "8B": {
                "open_key": "8d", "traditional": "C Major", "simplified": "C",
                "note": "C", "mode": "major", "sharps_flats": 0,
                "enharmonic": None, "circle_position": 8
            },
            "9A": {
                "open_key": "9m", "traditional": "E Minor", "simplified": "Em",
                "note": "E", "mode": "minor", "sharps_flats": -1,
                "enharmonic": None, "circle_position": 9
            },
            "9B": {
                "open_key": "9d", "traditional": "G Major", "simplified": "G",
                "note": "G", "mode": "major", "sharps_flats": -1,
                "enharmonic": None, "circle_position": 9
            },
            "10A": {
                "open_key": "10m", "traditional": "B Minor", "simplified": "Bm",
                "note": "B", "mode": "minor", "sharps_flats": -2,
                "enharmonic": None, "circle_position": 10
            },
            "10B": {
                "open_key": "10d", "traditional": "D Major", "simplified": "D",
                "note": "D", "mode": "major", "sharps_flats": -2,
                "enharmonic": None, "circle_position": 10
            },
            "11A": {
                "open_key": "11m", "traditional": "F# Minor", "simplified": "F#m",
                "note": "F#", "mode": "minor", "sharps_flats": -3,
                "enharmonic": "Gb Minor", "circle_position": 11
            },
            "11B": {
                "open_key": "11d", "traditional": "A Major", "simplified": "A",
                "note": "A", "mode": "major", "sharps_flats": -3,
                "enharmonic": None, "circle_position": 11
            },
            "12A": {
                "open_key": "12m", "traditional": "C# Minor", "simplified": "C#m",
                "note": "C#", "mode": "minor", "sharps_flats": -4,
                "enharmonic": "Db Minor", "circle_position": 12
            },
            "12B": {
                "open_key": "12d", "traditional": "E Major", "simplified": "E",
                "note": "E", "mode": "major", "sharps_flats": -4,
                "enharmonic": None, "circle_position": 12
            }
        }
        
        return master
    
    def _build_reverse_mappings(self) -> Dict[str, Dict[str, str]]:
        """Construye mapeos reversos para búsqueda rápida."""
        reverse_maps = {
            "open_key": {},
            "traditional": {},
            "simplified": {},
            "note_mode": {}
        }
        
        for camelot, info in self.camelot_master_map.items():
            # OpenKey mapping
            reverse_maps["open_key"][info["open_key"]] = camelot
            
            # Traditional mapping (incluir variaciones)
            traditional_variations = [
                info["traditional"],
                info["traditional"].lower(),
                info["traditional"].replace(" ", ""),
                info["traditional"].replace("Major", "major").replace("Minor", "minor")
            ]
            
            for variation in traditional_variations:
                reverse_maps["traditional"][variation] = camelot
            
            # Simplified mapping
            simplified_variations = [
                info["simplified"],
                info["simplified"].lower(),
                info["note"] + ("m" if info["mode"] == "minor" else ""),
                info["note"] + (" minor" if info["mode"] == "minor" else " major")
            ]
            
            for variation in simplified_variations:
                reverse_maps["simplified"][variation] = camelot
            
            # Note + mode mapping
            note_mode_key = f"{info['note']}_{info['mode']}"
            reverse_maps["note_mode"][note_mode_key] = camelot
            
            # Enharmonic equivalents
            if info["enharmonic"]:
                enharmonic_variations = [
                    info["enharmonic"],
                    info["enharmonic"].lower(),
                    info["enharmonic"].replace(" ", "")
                ]
                
                for variation in enharmonic_variations:
                    reverse_maps["traditional"][variation] = camelot
        
        return reverse_maps
    
    def _build_key_patterns(self) -> Dict[KeyFormat, str]:
        """Construye patrones regex para detección automática."""
        return {
            KeyFormat.CAMELOT: r'^(1[0-2]|[1-9])[AB]$',
            KeyFormat.OPEN_KEY: r'^(1[0-2]|[1-9])[md]$',
            KeyFormat.TRADITIONAL: r'^[A-G][#b]?\s+(Major|Minor|major|minor)$',
            KeyFormat.SIMPLIFIED: r'^[A-G][#b]?m?$',
        }
    
    def _detect_key_format(self, key: str) -> Optional[KeyFormat]:
        """Detecta automáticamente el formato de una clave."""
        key_clean = key.strip()
        
        # Probar cada patrón
        for format_type, pattern in self.key_patterns.items():
            if re.match(pattern, key_clean):
                return format_type
        
        # Intentos adicionales más flexibles
        
        # Camelot: números seguidos de A o B
        if re.match(r'^\d{1,2}[AB]$', key_clean):
            return KeyFormat.CAMELOT
        
        # OpenKey: números seguidos de m o d
        if re.match(r'^\d{1,2}[md]$', key_clean):
            return KeyFormat.OPEN_KEY
        
        # Traditional con variaciones
        if any(word in key_clean.lower() for word in ['major', 'minor', 'mayor', 'menor']):
            return KeyFormat.TRADITIONAL
        
        # Simplified: nota seguida opcionalmente de 'm'
        if re.match(r'^[A-G][#b]?m?$', key_clean):
            return KeyFormat.SIMPLIFIED
        
        return None
    
    def _normalize_key(self, key: str, format_type: KeyFormat) -> Optional[str]:
        """Normaliza una clave a formato estándar para su tipo."""
        key_clean = key.strip()
        
        if format_type == KeyFormat.CAMELOT:
            # Asegurar formato correcto
            match = re.match(r'^(\d{1,2})([AB])$', key_clean)
            if match:
                num, letter = match.groups()
                # Validar rango
                if 1 <= int(num) <= 12:
                    return f"{num}{letter}"
        
        elif format_type == KeyFormat.OPEN_KEY:
            # Convertir d/m a formato estándar
            match = re.match(r'^(\d{1,2})([md])$', key_clean)
            if match:
                num, letter = match.groups()
                if 1 <= int(num) <= 12:
                    return f"{num}{letter}"
        
        elif format_type == KeyFormat.TRADITIONAL:
            # Normalizar tradicional a formato estándar
            # Convertir variaciones comunes
            normalized = key_clean
            normalized = re.sub(r'\s+', ' ', normalized)  # Espacios múltiples a uno
            normalized = normalized.title()  # Capitalizar correctamente
            
            # Asegurar formato "Note Mode"
            parts = normalized.split()
            if len(parts) == 2:
                note_part, mode_part = parts
                mode_part = mode_part.capitalize()
                return f"{note_part} {mode_part}"
        
        elif format_type == KeyFormat.SIMPLIFIED:
            # Normalizar simplified
            # Convertir a formato consistente
            if key_clean.lower().endswith('minor'):
                note = key_clean.lower().replace('minor', '').strip()
                return f"{note.capitalize()}m"
            elif key_clean.lower().endswith('major'):
                note = key_clean.lower().replace('major', '').strip()
                return note.capitalize()
            else:
                return key_clean.capitalize()
        
        return None
    
    def _to_camelot(self, normalized_key: str, format_type: KeyFormat) -> Optional[str]:
        """Convierte una clave normalizada a formato Camelot."""
        
        if format_type == KeyFormat.CAMELOT:
            return normalized_key  # Ya está en Camelot
        
        elif format_type == KeyFormat.OPEN_KEY:
            # Convertir OpenKey a Camelot
            return self.reverse_maps["open_key"].get(normalized_key)
        
        elif format_type == KeyFormat.TRADITIONAL:
            # Buscar en mapeo tradicional
            return self.reverse_maps["traditional"].get(normalized_key)
        
        elif format_type == KeyFormat.SIMPLIFIED:
            # Buscar en mapeo simplificado
            return self.reverse_maps["simplified"].get(normalized_key)
        
        return None
    
    def get_key_relationships(self, input_key: str) -> Dict[str, List[str]]:
        """
        Obtiene todas las relaciones de una clave.
        
        Returns:
            Dict con diferentes tipos de relaciones
        """
        key_info = self.analyze_key(input_key)
        if not key_info:
            return {}
        
        camelot = key_info.camelot
        num = int(camelot[:-1])
        letter = camelot[-1]
        
        relationships = {
            "same_key": [camelot],
            "relative": [f"{num}{'B' if letter == 'A' else 'A'}"],
            "adjacent": [],
            "fifth_circle": [],
            "enharmonic": []
        }
        
        # Adyacentes
        prev_num = ((num - 2) % 12) + 1
        next_num = (num % 12) + 1
        relationships["adjacent"] = [f"{prev_num}{letter}", f"{next_num}{letter}"]
        
        # Círculo de quintas (5 pasos = quinta perfecta)
        fifth_up = ((num + 4) % 12) + 1
        fifth_down = ((num - 6) % 12) + 1
        relationships["fifth_circle"] = [f"{fifth_up}{letter}", f"{fifth_down}{letter}"]
        
        # Enarmónicos
        if key_info.enharmonic_equivalent:
            enharmonic_camelot = self.convert_key(key_info.enharmonic_equivalent, KeyFormat.CAMELOT)
            if enharmonic_camelot:
                relationships["enharmonic"] = [enharmonic_camelot]
        
        return relationships
    
    def validate_key(self, input_key: str) -> Dict[str, any]:
        """
        Valida una clave y proporciona información de corrección.
        
        Returns:
            Dict con información de validación
        """
        if not input_key or not input_key.strip():
            return {"valid": False, "error": "Clave vacía"}
        
        key_info = self.analyze_key(input_key)
        
        if key_info:
            return {
                "valid": True,
                "detected_format": self._detect_key_format(input_key),
                "camelot": key_info.camelot,
                "standardized": key_info.traditional,
                "confidence": "high"
            }
        else:
            # Intentar sugerir correcciones
            suggestions = self._suggest_corrections(input_key)
            return {
                "valid": False,
                "error": "Formato de clave no reconocido",
                "suggestions": suggestions,
                "confidence": "none"
            }
    
    def _suggest_corrections(self, input_key: str) -> List[str]:
        """Sugiere correcciones para claves mal formateadas."""
        suggestions = []
        key_lower = input_key.lower().strip()
        
        # Buscar coincidencias parciales en todos los mapeos
        for camelot, info in self.camelot_master_map.items():
            # Buscar coincidencias de nota
            if info["note"].lower() in key_lower:
                suggestions.append(info["traditional"])
                suggestions.append(info["simplified"])
            
            # Buscar coincidencias de modo
            if info["mode"] in key_lower:
                suggestions.append(info["traditional"])
        
        # Remover duplicados y limitar
        suggestions = list(set(suggestions))[:5]
        
        return suggestions
    
    def get_supported_formats(self) -> Dict[str, str]:
        """Retorna información sobre formatos soportados."""
        return {
            "camelot": "1A-12A (minor), 1B-12B (major)",
            "open_key": "1m-12m (minor), 1d-12d (major)", 
            "traditional": "C Major, A Minor, F# Major, etc.",
            "simplified": "C, Am, F#m, Bb, etc.",
            "examples": [
                "8B (Camelot) = 8d (OpenKey) = C Major (Traditional) = C (Simplified)",
                "5A (Camelot) = 5m (OpenKey) = C Minor (Traditional) = Cm (Simplified)"
            ]
        }

# Instancia global
_camelot_key_mapper = None

def get_camelot_key_mapper() -> CamelotKeyMapper:
    """Obtiene la instancia global del mapeador de claves."""
    global _camelot_key_mapper
    if _camelot_key_mapper is None:
        _camelot_key_mapper = CamelotKeyMapper()
    return _camelot_key_mapper

# Funciones de conveniencia
def convert_to_camelot(key: str) -> Optional[str]:
    """Convierte cualquier clave a formato Camelot."""
    return get_camelot_key_mapper().convert_key(key, KeyFormat.CAMELOT)

def convert_to_traditional(key: str) -> Optional[str]:
    """Convierte cualquier clave a formato tradicional."""
    return get_camelot_key_mapper().convert_key(key, KeyFormat.TRADITIONAL)

def analyze_key_complete(key: str) -> Optional[KeyInfo]:
    """Analiza una clave completamente."""
    return get_camelot_key_mapper().analyze_key(key)

def get_traditional_compatible_keys(key: str) -> List[str]:
    """Obtiene claves tradicionalmente compatibles."""
    return get_camelot_key_mapper().get_compatible_keys(key)