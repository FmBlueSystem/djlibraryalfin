#!/usr/bin/env python3
"""
DjAlfin - Cue Point Manager
Sistema de gestión de cue points compatible con Serato, Mixed In Key y Traktor
"""

import os
import struct
import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from mutagen import File
from mutagen.id3 import ID3, GEOB, PRIV, TXXX, COMM
import base64
import time

@dataclass
class CuePoint:
    """Estructura unificada de cue point."""
    position: float          # Posición en segundos
    type: str               # 'cue', 'loop_in', 'loop_out', 'hotcue'
    color: str              # Color en formato hex (#FF0000)
    name: str               # Nombre personalizable
    hotcue_index: int       # Índice 1-8 para hot cues (0 = no es hotcue)
    created_at: float       # Timestamp de creación
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CuePoint':
        """Crear desde diccionario."""
        return cls(**data)

@dataclass
class LoopPoint:
    """Estructura de loop point."""
    start_position: float   # Inicio del loop en segundos
    end_position: float     # Fin del loop en segundos
    color: str              # Color en formato hex
    name: str               # Nombre del loop
    enabled: bool           # Si el loop está activo
    created_at: float       # Timestamp de creación
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoopPoint':
        """Crear desde diccionario."""
        return cls(**data)

class CuePointManager:
    """Gestor principal de cue points con compatibilidad multi-formato."""
    
    # Colores predefinidos compatibles con Serato
    SERATO_COLORS = {
        'red': '#FF0000',
        'orange': '#FF8000', 
        'yellow': '#FFFF00',
        'green': '#00FF00',
        'cyan': '#00FFFF',
        'blue': '#0000FF',
        'purple': '#8000FF',
        'pink': '#FF00FF'
    }
    
    def __init__(self):
        self.cue_points: List[CuePoint] = []
        self.loop_points: List[LoopPoint] = []
        
    def add_cue_point(self, position: float, name: str = "", 
                     color: str = "#FF0000", hotcue_index: int = 0) -> CuePoint:
        """Agregar un nuevo cue point."""
        cue_type = "hotcue" if hotcue_index > 0 else "cue"
        
        cue_point = CuePoint(
            position=position,
            type=cue_type,
            color=color,
            name=name or f"Cue {len(self.cue_points) + 1}",
            hotcue_index=hotcue_index,
            created_at=time.time()
        )
        
        self.cue_points.append(cue_point)
        return cue_point
    
    def add_loop_point(self, start_pos: float, end_pos: float, 
                      name: str = "", color: str = "#00FF00") -> LoopPoint:
        """Agregar un nuevo loop point."""
        loop_point = LoopPoint(
            start_position=start_pos,
            end_position=end_pos,
            color=color,
            name=name or f"Loop {len(self.loop_points) + 1}",
            enabled=True,
            created_at=time.time()
        )
        
        self.loop_points.append(loop_point)
        return loop_point
    
    def get_hotcues(self) -> List[CuePoint]:
        """Obtener solo los hot cues (índice > 0)."""
        return [cue for cue in self.cue_points if cue.hotcue_index > 0]
    
    def get_cue_by_hotkey(self, index: int) -> Optional[CuePoint]:
        """Obtener cue point por índice de hotkey."""
        for cue in self.cue_points:
            if cue.hotcue_index == index:
                return cue
        return None
    
    def remove_cue_point(self, position: float, tolerance: float = 0.1) -> bool:
        """Remover cue point por posición."""
        for i, cue in enumerate(self.cue_points):
            if abs(cue.position - position) <= tolerance:
                del self.cue_points[i]
                return True
        return False
    
    def clear_all(self):
        """Limpiar todos los cue points y loops."""
        self.cue_points.clear()
        self.loop_points.clear()

class SeratoMetadataParser:
    """Parser para metadatos de Serato DJ."""
    
    @staticmethod
    def parse_serato_markers(data: bytes) -> List[CuePoint]:
        """Parsear datos binarios de Serato_Markers2."""
        cue_points = []
        
        if not data or len(data) < 4:
            return cue_points
        
        try:
            # Skip header y version
            offset = 0
            
            # Buscar marcadores de cue points
            while offset < len(data) - 8:
                # Buscar patrón de cue point
                if data[offset:offset+4] == b'\x00\x00\x00\x05':  # Marker type
                    offset += 4
                    
                    # Leer posición (4 bytes, big endian)
                    if offset + 4 <= len(data):
                        position_ms = struct.unpack('>I', data[offset:offset+4])[0]
                        position_sec = position_ms / 1000.0
                        offset += 4
                        
                        # Leer color (3 bytes RGB)
                        if offset + 3 <= len(data):
                            r, g, b = struct.unpack('BBB', data[offset:offset+3])
                            color = f"#{r:02X}{g:02X}{b:02X}"
                            offset += 3
                            
                            # Crear cue point
                            cue_point = CuePoint(
                                position=position_sec,
                                type="cue",
                                color=color,
                                name=f"Serato Cue {len(cue_points) + 1}",
                                hotcue_index=0,
                                created_at=time.time()
                            )
                            cue_points.append(cue_point)
                        else:
                            break
                    else:
                        break
                else:
                    offset += 1
                    
        except Exception as e:
            print(f"Error parsing Serato markers: {e}")
        
        return cue_points
    
    @staticmethod
    def create_serato_markers(cue_points: List[CuePoint]) -> bytes:
        """Crear datos binarios para Serato_Markers2."""
        data = bytearray()
        
        # Header
        data.extend(b'Serato_Markers2')
        data.extend(b'\x00\x00\x00\x01')  # Version
        
        for cue in cue_points:
            # Marker type
            data.extend(b'\x00\x00\x00\x05')
            
            # Position in milliseconds
            position_ms = int(cue.position * 1000)
            data.extend(struct.pack('>I', position_ms))
            
            # Color RGB
            color_hex = cue.color.lstrip('#')
            if len(color_hex) == 6:
                r = int(color_hex[0:2], 16)
                g = int(color_hex[2:4], 16) 
                b = int(color_hex[4:6], 16)
                data.extend(struct.pack('BBB', r, g, b))
            else:
                data.extend(b'\xFF\x00\x00')  # Default red
        
        return bytes(data)

class DjAlfinMetadataManager:
    """Gestor de metadatos nativo de DjAlfin con compatibilidad multi-formato."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.cue_manager = CuePointManager()
        
    def load_metadata(self) -> bool:
        """Cargar metadatos desde el archivo."""
        try:
            audio_file = File(self.file_path)
            if not audio_file:
                return False
            
            # Intentar cargar desde diferentes formatos
            loaded = False
            
            # 1. Formato nativo DjAlfin
            if self._load_djalfin_metadata(audio_file):
                loaded = True
            
            # 2. Formato Serato
            elif self._load_serato_metadata(audio_file):
                loaded = True
            
            # 3. Formato Mixed In Key
            elif self._load_mixedinkey_metadata(audio_file):
                loaded = True
            
            return loaded
            
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return False
    
    def save_metadata(self, format_type: str = "all") -> bool:
        """Guardar metadatos en el archivo."""
        try:
            audio_file = File(self.file_path)
            if not audio_file:
                return False
            
            # Asegurar que tiene tags ID3
            if not hasattr(audio_file, 'tags') or audio_file.tags is None:
                audio_file.add_tags()
            
            success = True
            
            if format_type in ["all", "djalfin"]:
                success &= self._save_djalfin_metadata(audio_file)
            
            if format_type in ["all", "serato"]:
                success &= self._save_serato_metadata(audio_file)
            
            # Guardar cambios
            audio_file.save()
            return success
            
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
    
    def _load_djalfin_metadata(self, audio_file) -> bool:
        """Cargar metadatos nativos de DjAlfin."""
        try:
            if hasattr(audio_file.tags, 'get'):
                # Buscar tag personalizado DjAlfin
                djalfin_tag = audio_file.tags.get('TXXX:DJALFIN_CUES')
                if djalfin_tag:
                    data = json.loads(djalfin_tag.text[0])
                    
                    # Cargar cue points
                    for cue_data in data.get('cue_points', []):
                        cue = CuePoint.from_dict(cue_data)
                        self.cue_manager.cue_points.append(cue)
                    
                    # Cargar loop points
                    for loop_data in data.get('loop_points', []):
                        loop = LoopPoint.from_dict(loop_data)
                        self.cue_manager.loop_points.append(loop)
                    
                    return True
        except Exception as e:
            print(f"Error loading DjAlfin metadata: {e}")
        
        return False
    
    def _load_serato_metadata(self, audio_file) -> bool:
        """Cargar metadatos de Serato."""
        try:
            if hasattr(audio_file.tags, 'get'):
                # Buscar tag Serato_Markers2
                serato_tag = audio_file.tags.get('GEOB:Serato_Markers2')
                if serato_tag:
                    cue_points = SeratoMetadataParser.parse_serato_markers(serato_tag.data)
                    self.cue_manager.cue_points.extend(cue_points)
                    return len(cue_points) > 0
        except Exception as e:
            print(f"Error loading Serato metadata: {e}")
        
        return False
    
    def _load_mixedinkey_metadata(self, audio_file) -> bool:
        """Cargar metadatos de Mixed In Key."""
        try:
            if hasattr(audio_file.tags, 'get'):
                # Mixed In Key usa comentarios para cue points
                comment_tag = audio_file.tags.get('COMM::eng')
                if comment_tag and 'CUE' in comment_tag.text[0].upper():
                    # Parsear comentarios de Mixed In Key
                    # Formato típico: "CUE:120.5,240.2,360.8"
                    comment_text = comment_tag.text[0]
                    if 'CUE:' in comment_text:
                        cue_data = comment_text.split('CUE:')[1].split(',')
                        for i, pos_str in enumerate(cue_data):
                            try:
                                position = float(pos_str.strip())
                                cue = CuePoint(
                                    position=position,
                                    type="cue",
                                    color=list(self.cue_manager.SERATO_COLORS.values())[i % 8],
                                    name=f"MIK Cue {i+1}",
                                    hotcue_index=0,
                                    created_at=time.time()
                                )
                                self.cue_manager.cue_points.append(cue)
                            except ValueError:
                                continue
                        return len(self.cue_manager.cue_points) > 0
        except Exception as e:
            print(f"Error loading Mixed In Key metadata: {e}")
        
        return False
    
    def _save_djalfin_metadata(self, audio_file) -> bool:
        """Guardar metadatos nativos de DjAlfin."""
        try:
            # Crear estructura de datos
            data = {
                'version': '1.0',
                'created_at': time.time(),
                'cue_points': [cue.to_dict() for cue in self.cue_manager.cue_points],
                'loop_points': [loop.to_dict() for loop in self.cue_manager.loop_points]
            }
            
            # Guardar como tag personalizado
            json_data = json.dumps(data, indent=None, separators=(',', ':'))
            audio_file.tags.add(TXXX(encoding=3, desc='DJALFIN_CUES', text=[json_data]))
            
            return True
            
        except Exception as e:
            print(f"Error saving DjAlfin metadata: {e}")
            return False
    
    def _save_serato_metadata(self, audio_file) -> bool:
        """Guardar metadatos compatibles con Serato."""
        try:
            # Crear datos binarios de Serato
            serato_data = SeratoMetadataParser.create_serato_markers(self.cue_manager.cue_points)
            
            # Guardar como GEOB tag
            audio_file.tags.add(GEOB(
                encoding=3,
                mime='application/octet-stream',
                desc='Serato_Markers2',
                data=serato_data
            ))
            
            return True
            
        except Exception as e:
            print(f"Error saving Serato metadata: {e}")
            return False

# Funciones de utilidad
def auto_detect_cue_points(file_path: str, sensitivity: float = 0.7) -> List[float]:
    """Detectar automáticamente cue points basado en cambios de energía."""
    try:
        import librosa
        import numpy as np
        
        # Cargar audio
        y, sr = librosa.load(file_path)
        
        # Calcular energía RMS
        hop_length = 512
        frame_length = 2048
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Detectar picos de energía
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(rms, height=sensitivity * np.max(rms), distance=sr//hop_length)
        
        # Convertir a tiempo en segundos
        times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
        
        return times.tolist()
        
    except ImportError:
        print("Librosa no disponible para auto-detección")
        return []
    except Exception as e:
        print(f"Error en auto-detección: {e}")
        return []

def demo_cue_points():
    """Demostración del sistema de cue points."""
    print("🎯 Demo: Sistema de Cue Points DjAlfin")
    print("=" * 50)
    
    # Crear gestor
    manager = CuePointManager()
    
    # Agregar algunos cue points
    manager.add_cue_point(30.5, "Intro", "#FF0000", 1)
    manager.add_cue_point(65.2, "Verse", "#00FF00", 2) 
    manager.add_cue_point(120.8, "Chorus", "#0000FF", 3)
    manager.add_cue_point(180.3, "Bridge", "#FFFF00", 4)
    
    # Agregar loop
    manager.add_loop_point(90.0, 120.0, "Main Loop", "#FF00FF")
    
    # Mostrar información
    print(f"📍 Cue Points: {len(manager.cue_points)}")
    for cue in manager.cue_points:
        print(f"  • {cue.name} @ {cue.position:.1f}s (Hot: {cue.hotcue_index}) {cue.color}")
    
    print(f"\n🔁 Loop Points: {len(manager.loop_points)}")
    for loop in manager.loop_points:
        print(f"  • {loop.name}: {loop.start_position:.1f}s - {loop.end_position:.1f}s {loop.color}")
    
    print("\n✅ Demo completado!")

if __name__ == "__main__":
    demo_cue_points()
