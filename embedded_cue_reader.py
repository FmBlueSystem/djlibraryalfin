#!/usr/bin/env python3
"""
🎯 DjAlfin - Lector de Cue Points Embebidos
Sistema para leer cue points que ya están embebidos en archivos de audio
por Serato DJ, MixInKey, Traktor Pro, Rekordbox, etc.
"""

import os
import struct
import json
import time
import base64
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple
from mutagen import File
from mutagen.id3 import ID3, GEOB, PRIV, TXXX, COMM, APIC
from mutagen.mp4 import MP4
from mutagen.flac import FLAC

@dataclass
class EmbeddedCuePoint:
    """Cue point leído desde archivo embebido."""
    position: float
    type: str
    color: str
    name: str
    hotcue_index: int
    created_at: float
    energy_level: int = 5
    source: str = "embedded"
    software: str = "unknown"  # serato, mixinkey, traktor, rekordbox

class SeratoParser:
    """Parser para metadatos de Serato DJ."""
    
    @staticmethod
    def read_serato_cues(file_path: str) -> List[EmbeddedCuePoint]:
        """Leer cue points de Serato desde archivo."""
        cue_points = []
        
        try:
            audio_file = File(file_path)
            if not audio_file or not hasattr(audio_file, 'tags') or not audio_file.tags:
                return cue_points
            
            # Buscar diferentes tipos de tags de Serato
            serato_tags = [
                'GEOB:Serato_Markers2',
                'GEOB:Serato_Markers_',
                'PRIV:Serato_Markers2',
                'TXXX:Serato_Markers2'
            ]
            
            for tag_name in serato_tags:
                if tag_name in audio_file.tags:
                    print(f"✅ Found Serato tag: {tag_name}")
                    tag_data = audio_file.tags[tag_name]
                    
                    if hasattr(tag_data, 'data'):
                        data = tag_data.data
                    elif hasattr(tag_data, 'text'):
                        # Decodificar si está en base64
                        try:
                            data = base64.b64decode(tag_data.text[0])
                        except:
                            continue
                    else:
                        continue
                    
                    parsed_cues = SeratoParser._parse_serato_markers(data)
                    cue_points.extend(parsed_cues)
                    break
            
            print(f"🎵 Serato: Found {len(cue_points)} cue points")
            
        except Exception as e:
            print(f"❌ Error reading Serato cues: {e}")
        
        return cue_points
    
    @staticmethod
    def _parse_serato_markers(data: bytes) -> List[EmbeddedCuePoint]:
        """Parsear datos binarios de Serato."""
        cue_points = []
        
        if not data or len(data) < 8:
            return cue_points
        
        try:
            offset = 0
            
            # Skip header si existe
            if data.startswith(b'Serato_Markers'):
                offset = 16
            
            while offset < len(data) - 8:
                # Buscar patrón de cue point
                if offset + 4 <= len(data):
                    # Leer tipo de marcador
                    marker_type = struct.unpack('>I', data[offset:offset+4])[0]
                    offset += 4
                    
                    if marker_type == 0x00 or marker_type == 0x01:  # Cue point
                        # Leer posición (4 bytes)
                        if offset + 4 <= len(data):
                            position_ms = struct.unpack('>I', data[offset:offset+4])[0]
                            position_sec = position_ms / 1000.0
                            offset += 4
                            
                            # Leer color (3 bytes RGB)
                            if offset + 3 <= len(data):
                                r, g, b = struct.unpack('BBB', data[offset:offset+3])
                                color = f"#{r:02X}{g:02X}{b:02X}"
                                offset += 3
                                
                                # Leer índice de hot cue (1 byte)
                                hotcue_index = 0
                                if offset < len(data):
                                    hotcue_index = data[offset]
                                    offset += 1
                                
                                # Crear cue point
                                cue_point = EmbeddedCuePoint(
                                    position=position_sec,
                                    type="cue",
                                    color=color,
                                    name=f"Serato Cue {len(cue_points) + 1}",
                                    hotcue_index=hotcue_index,
                                    created_at=time.time(),
                                    energy_level=5,
                                    source="embedded",
                                    software="serato"
                                )
                                cue_points.append(cue_point)
                            else:
                                break
                        else:
                            break
                    else:
                        offset += 1
                else:
                    break
                    
        except Exception as e:
            print(f"❌ Error parsing Serato markers: {e}")
        
        return cue_points

class MixInKeyParser:
    """Parser para metadatos de Mixed In Key."""
    
    @staticmethod
    def read_mixinkey_cues(file_path: str) -> List[EmbeddedCuePoint]:
        """Leer cue points de Mixed In Key desde archivo."""
        cue_points = []
        
        try:
            audio_file = File(file_path)
            if not audio_file or not hasattr(audio_file, 'tags') or not audio_file.tags:
                return cue_points
            
            # Mixed In Key usa diferentes tags
            mixinkey_tags = [
                'COMM::eng',  # Comentarios en inglés
                'COMM:MixedInKey',
                'TXXX:MixedInKey',
                'TXXX:MIXEDINKEY',
                'comment'  # Para FLAC/MP4
            ]
            
            for tag_name in mixinkey_tags:
                if tag_name in audio_file.tags:
                    print(f"✅ Found MixInKey tag: {tag_name}")
                    tag_data = audio_file.tags[tag_name]
                    
                    if hasattr(tag_data, 'text'):
                        text = tag_data.text[0] if tag_data.text else ""
                    else:
                        text = str(tag_data)
                    
                    parsed_cues = MixInKeyParser._parse_mixinkey_comments(text)
                    cue_points.extend(parsed_cues)
                    
                    if cue_points:
                        break
            
            print(f"🎹 MixInKey: Found {len(cue_points)} cue points")
            
        except Exception as e:
            print(f"❌ Error reading MixInKey cues: {e}")
        
        return cue_points
    
    @staticmethod
    def _parse_mixinkey_comments(text: str) -> List[EmbeddedCuePoint]:
        """Parsear comentarios de Mixed In Key."""
        cue_points = []
        
        try:
            # Buscar patrones de cue points
            # Formato típico: "CUE:120.5,240.2,360.8" o "CUES:120.5;240.2;360.8"
            text_upper = text.upper()
            
            if 'CUE' in text_upper:
                # Extraer datos de cue points
                for separator in ['CUE:', 'CUES:']:
                    if separator in text_upper:
                        cue_data = text_upper.split(separator)[1].split()[0]  # Tomar primera palabra
                        
                        # Separar por comas o punto y coma
                        positions = []
                        for sep in [',', ';', '|']:
                            if sep in cue_data:
                                positions = cue_data.split(sep)
                                break
                        
                        if not positions:
                            positions = [cue_data]
                        
                        # Crear cue points
                        colors = ['#FF0000', '#FF6600', '#FFFF00', '#00FF00', '#00FFFF', '#0066FF', '#9900FF', '#FF00CC']
                        
                        for i, pos_str in enumerate(positions):
                            try:
                                position = float(pos_str.strip())
                                if position > 0:  # Validar posición
                                    cue_point = EmbeddedCuePoint(
                                        position=position,
                                        type="cue",
                                        color=colors[i % len(colors)],
                                        name=f"MIK Cue {i+1}",
                                        hotcue_index=i+1 if i < 8 else 0,
                                        created_at=time.time(),
                                        energy_level=5,
                                        source="embedded",
                                        software="mixinkey"
                                    )
                                    cue_points.append(cue_point)
                            except ValueError:
                                continue
                        
                        break
            
        except Exception as e:
            print(f"❌ Error parsing MixInKey comments: {e}")
        
        return cue_points

class TraktorParser:
    """Parser para metadatos de Traktor Pro."""
    
    @staticmethod
    def read_traktor_cues(file_path: str) -> List[EmbeddedCuePoint]:
        """Leer cue points de Traktor desde archivo."""
        cue_points = []
        
        try:
            audio_file = File(file_path)
            if not audio_file or not hasattr(audio_file, 'tags') or not audio_file.tags:
                return cue_points
            
            # Traktor usa PRIV tags
            traktor_tags = [
                'PRIV:www.native-instruments.com',
                'PRIV:Native Instruments',
                'TXXX:TRAKTOR',
                'TXXX:NI_TRAKTOR'
            ]
            
            for tag_name in traktor_tags:
                if tag_name in audio_file.tags:
                    print(f"✅ Found Traktor tag: {tag_name}")
                    tag_data = audio_file.tags[tag_name]
                    
                    if hasattr(tag_data, 'data'):
                        data = tag_data.data
                    elif hasattr(tag_data, 'text'):
                        data = tag_data.text[0].encode() if tag_data.text else b''
                    else:
                        continue
                    
                    parsed_cues = TraktorParser._parse_traktor_data(data)
                    cue_points.extend(parsed_cues)
                    
                    if cue_points:
                        break
            
            print(f"🎛️ Traktor: Found {len(cue_points)} cue points")
            
        except Exception as e:
            print(f"❌ Error reading Traktor cues: {e}")
        
        return cue_points
    
    @staticmethod
    def _parse_traktor_data(data: bytes) -> List[EmbeddedCuePoint]:
        """Parsear datos de Traktor."""
        cue_points = []
        
        try:
            # Traktor usa formato XML o binario propietario
            # Intentar decodificar como texto primero
            try:
                text = data.decode('utf-8', errors='ignore')
                if 'CUE' in text.upper() or 'HOTCUE' in text.upper():
                    # Buscar patrones de posición
                    import re
                    positions = re.findall(r'(\d+\.\d+)', text)
                    
                    colors = ['#FF0000', '#FF6600', '#FFFF00', '#00FF00', '#00FFFF', '#0066FF', '#9900FF', '#FF00CC']
                    
                    for i, pos_str in enumerate(positions[:8]):  # Máximo 8 cue points
                        try:
                            position = float(pos_str)
                            if position > 0:
                                cue_point = EmbeddedCuePoint(
                                    position=position,
                                    type="cue",
                                    color=colors[i % len(colors)],
                                    name=f"Traktor Cue {i+1}",
                                    hotcue_index=i+1,
                                    created_at=time.time(),
                                    energy_level=5,
                                    source="embedded",
                                    software="traktor"
                                )
                                cue_points.append(cue_point)
                        except ValueError:
                            continue
            except:
                pass
            
        except Exception as e:
            print(f"❌ Error parsing Traktor data: {e}")
        
        return cue_points

class RekordboxParser:
    """Parser para metadatos de Pioneer Rekordbox."""
    
    @staticmethod
    def read_rekordbox_cues(file_path: str) -> List[EmbeddedCuePoint]:
        """Leer cue points de Rekordbox desde archivo."""
        cue_points = []
        
        try:
            audio_file = File(file_path)
            if not audio_file or not hasattr(audio_file, 'tags') or not audio_file.tags:
                return cue_points
            
            # Rekordbox usa diferentes tags según el formato
            rekordbox_tags = [
                'TXXX:PIONEER_REKORDBOX',
                'COMM:Pioneer',
                'PRIV:Pioneer',
                '----:com.pioneer.rekordbox'  # Para MP4
            ]
            
            for tag_name in rekordbox_tags:
                if tag_name in audio_file.tags:
                    print(f"✅ Found Rekordbox tag: {tag_name}")
                    tag_data = audio_file.tags[tag_name]
                    
                    if hasattr(tag_data, 'data'):
                        data = tag_data.data
                    elif hasattr(tag_data, 'text'):
                        data = tag_data.text[0] if tag_data.text else ""
                    else:
                        data = str(tag_data)
                    
                    parsed_cues = RekordboxParser._parse_rekordbox_data(data)
                    cue_points.extend(parsed_cues)
                    
                    if cue_points:
                        break
            
            print(f"🎧 Rekordbox: Found {len(cue_points)} cue points")
            
        except Exception as e:
            print(f"❌ Error reading Rekordbox cues: {e}")
        
        return cue_points
    
    @staticmethod
    def _parse_rekordbox_data(data) -> List[EmbeddedCuePoint]:
        """Parsear datos de Rekordbox."""
        cue_points = []
        
        try:
            # Convertir a string si es necesario
            if isinstance(data, bytes):
                text = data.decode('utf-8', errors='ignore')
            else:
                text = str(data)
            
            # Buscar patrones de cue points
            if 'CUE' in text.upper() or 'HOT' in text.upper():
                import re
                positions = re.findall(r'(\d+\.\d+)', text)
                
                colors = ['#FF0000', '#FF6600', '#FFFF00', '#00FF00', '#00FFFF', '#0066FF', '#9900FF', '#FF00CC']
                
                for i, pos_str in enumerate(positions[:8]):
                    try:
                        position = float(pos_str)
                        if position > 0:
                            cue_point = EmbeddedCuePoint(
                                position=position,
                                type="cue",
                                color=colors[i % len(colors)],
                                name=f"RB Cue {i+1}",
                                hotcue_index=i+1,
                                created_at=time.time(),
                                energy_level=5,
                                source="embedded",
                                software="rekordbox"
                            )
                            cue_points.append(cue_point)
                    except ValueError:
                        continue
            
        except Exception as e:
            print(f"❌ Error parsing Rekordbox data: {e}")
        
        return cue_points

class EmbeddedCueReader:
    """Lector principal de cue points embebidos."""
    
    def __init__(self):
        self.parsers = {
            'serato': SeratoParser(),
            'mixinkey': MixInKeyParser(),
            'traktor': TraktorParser(),
            'rekordbox': RekordboxParser()
        }
    
    def read_all_embedded_cues(self, file_path: str) -> List[EmbeddedCuePoint]:
        """Leer cue points de todos los formatos soportados."""
        all_cues = []
        
        print(f"🔍 Scanning embedded cues in: {os.path.basename(file_path)}")
        
        # Intentar leer desde cada formato
        for software, parser in self.parsers.items():
            try:
                if software == 'serato':
                    cues = parser.read_serato_cues(file_path)
                elif software == 'mixinkey':
                    cues = parser.read_mixinkey_cues(file_path)
                elif software == 'traktor':
                    cues = parser.read_traktor_cues(file_path)
                elif software == 'rekordbox':
                    cues = parser.read_rekordbox_cues(file_path)
                else:
                    continue
                
                if cues:
                    print(f"✅ {software.title()}: {len(cues)} cue points")
                    all_cues.extend(cues)
                
            except Exception as e:
                print(f"❌ Error reading {software} cues: {e}")
        
        # Eliminar duplicados basados en posición
        unique_cues = []
        seen_positions = set()
        
        for cue in all_cues:
            pos_key = round(cue.position, 1)  # Redondear a 0.1s para comparación
            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                unique_cues.append(cue)
        
        print(f"📊 Total unique cue points found: {len(unique_cues)}")
        return unique_cues
    
    def scan_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Escanear todos los metadatos del archivo."""
        metadata = {
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'cue_points': [],
            'software_detected': [],
            'tags_found': []
        }
        
        try:
            audio_file = File(file_path)
            if audio_file and hasattr(audio_file, 'tags') and audio_file.tags:
                # Listar todos los tags encontrados
                for tag_name in audio_file.tags.keys():
                    metadata['tags_found'].append(tag_name)
                    
                    # Detectar software por tags
                    tag_lower = tag_name.lower()
                    if 'serato' in tag_lower:
                        metadata['software_detected'].append('serato')
                    elif 'mixedinkey' in tag_lower or 'mixed' in tag_lower:
                        metadata['software_detected'].append('mixinkey')
                    elif 'traktor' in tag_lower or 'native' in tag_lower:
                        metadata['software_detected'].append('traktor')
                    elif 'pioneer' in tag_lower or 'rekordbox' in tag_lower:
                        metadata['software_detected'].append('rekordbox')
                
                # Leer cue points
                metadata['cue_points'] = self.read_all_embedded_cues(file_path)
                
        except Exception as e:
            print(f"❌ Error scanning metadata: {e}")
        
        return metadata

def demo_embedded_reader():
    """Demostración del lector de cue points embebidos."""
    print("🎯 DjAlfin - Embedded Cue Points Reader Demo")
    print("=" * 60)
    
    reader = EmbeddedCueReader()
    
    # Buscar archivos de audio en la carpeta actual
    audio_extensions = ['.mp3', '.m4a', '.flac', '.wav']
    audio_files = []
    
    for ext in audio_extensions:
        import glob
        files = glob.glob(f"*{ext}")
        audio_files.extend(files)
    
    if not audio_files:
        print("❌ No audio files found in current directory")
        print("💡 Copy some audio files with embedded cue points to test")
        return
    
    print(f"📁 Found {len(audio_files)} audio files")
    
    total_cues = 0
    files_with_cues = 0
    
    for audio_file in audio_files[:5]:  # Limitar a 5 archivos para demo
        print(f"\n📀 Analyzing: {audio_file}")
        print("-" * 40)
        
        metadata = reader.scan_file_metadata(audio_file)
        
        print(f"🏷️ Tags found: {len(metadata['tags_found'])}")
        if metadata['software_detected']:
            print(f"🎛️ Software detected: {', '.join(set(metadata['software_detected']))}")
        
        cue_points = metadata['cue_points']
        if cue_points:
            files_with_cues += 1
            total_cues += len(cue_points)
            
            print(f"🎯 Cue points: {len(cue_points)}")
            for cue in cue_points[:3]:  # Mostrar primeros 3
                minutes = int(cue.position // 60)
                seconds = int(cue.position % 60)
                print(f"   🎵 {cue.name} @ {minutes}:{seconds:02d} ({cue.software}) {cue.color}")
            
            if len(cue_points) > 3:
                print(f"   ... and {len(cue_points) - 3} more")
        else:
            print("❌ No embedded cue points found")
    
    print("\n" + "=" * 60)
    print(f"📊 Summary:")
    print(f"   📁 Files analyzed: {min(len(audio_files), 5)}")
    print(f"   ✅ Files with cues: {files_with_cues}")
    print(f"   🎯 Total cue points: {total_cues}")
    
    if total_cues > 0:
        print("\n🎉 Embedded cue points found! Ready for integration.")
    else:
        print("\n💡 No embedded cue points found. Try files from Serato, MixInKey, etc.")

if __name__ == "__main__":
    demo_embedded_reader()
