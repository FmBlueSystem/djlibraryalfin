#!/usr/bin/env python3
"""
🎯 DjAlfin - Lector Básico de Metadatos Embebidos
Versión que funciona sin dependencias externas, usando solo librerías estándar
"""

import os
import struct
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

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
    software: str = "unknown"

class BasicMetadataReader:
    """Lector básico de metadatos usando solo librerías estándar."""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.m4a', '.flac', '.wav']
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Escanear archivo de audio para metadatos básicos."""
        result = {
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'size_mb': 0,
            'format': '',
            'cue_points': [],
            'metadata_found': [],
            'raw_data': {}
        }
        
        try:
            # Información básica del archivo
            file_stats = os.stat(file_path)
            result['size_mb'] = file_stats.st_size / (1024 * 1024)
            
            _, ext = os.path.splitext(file_path)
            result['format'] = ext.upper().replace('.', '')
            
            # Leer metadatos según formato
            if ext.lower() == '.mp3':
                result.update(self._read_mp3_metadata(file_path))
            elif ext.lower() == '.m4a':
                result.update(self._read_m4a_metadata(file_path))
            elif ext.lower() == '.flac':
                result.update(self._read_flac_metadata(file_path))
            elif ext.lower() == '.wav':
                result.update(self._read_wav_metadata(file_path))
            
        except Exception as e:
            print(f"❌ Error scanning {file_path}: {e}")
        
        return result
    
    def _read_mp3_metadata(self, file_path: str) -> Dict[str, Any]:
        """Leer metadatos de archivo MP3."""
        metadata = {'metadata_found': [], 'cue_points': []}
        
        try:
            with open(file_path, 'rb') as f:
                # Buscar header ID3v2
                header = f.read(10)
                if header[:3] != b'ID3':
                    return metadata
                
                # Leer tamaño del tag ID3v2
                size_bytes = header[6:10]
                tag_size = self._decode_synchsafe_int(size_bytes)
                
                # Leer datos del tag
                tag_data = f.read(tag_size)
                
                # Buscar frames específicos
                offset = 0
                while offset < len(tag_data) - 10:
                    frame_id = tag_data[offset:offset+4]
                    if len(frame_id) != 4:
                        break
                    
                    frame_size_bytes = tag_data[offset+4:offset+8]
                    frame_size = struct.unpack('>I', frame_size_bytes)[0]
                    
                    if frame_size == 0 or offset + 10 + frame_size > len(tag_data):
                        break
                    
                    frame_data = tag_data[offset+10:offset+10+frame_size]
                    
                    # Buscar frames de interés
                    frame_id_str = frame_id.decode('ascii', errors='ignore')
                    metadata['metadata_found'].append(frame_id_str)
                    
                    if b'serato' in frame_data.lower() or b'Serato' in frame_data:
                        print(f"✅ Found Serato data in {frame_id_str}")
                        cues = self._parse_serato_data(frame_data)
                        metadata['cue_points'].extend(cues)
                    
                    elif b'mixedinkey' in frame_data.lower() or b'MixedInKey' in frame_data:
                        print(f"✅ Found MixInKey data in {frame_id_str}")
                        cues = self._parse_mixinkey_data(frame_data)
                        metadata['cue_points'].extend(cues)
                    
                    elif b'traktor' in frame_data.lower() or b'native' in frame_data.lower():
                        print(f"✅ Found Traktor data in {frame_id_str}")
                        cues = self._parse_traktor_data(frame_data)
                        metadata['cue_points'].extend(cues)
                    
                    offset += 10 + frame_size
                
        except Exception as e:
            print(f"❌ Error reading MP3 metadata: {e}")
        
        return metadata
    
    def _read_m4a_metadata(self, file_path: str) -> Dict[str, Any]:
        """Leer metadatos de archivo M4A/MP4."""
        metadata = {'metadata_found': [], 'cue_points': []}
        
        try:
            with open(file_path, 'rb') as f:
                # Buscar atoms de metadatos
                while True:
                    atom_header = f.read(8)
                    if len(atom_header) < 8:
                        break
                    
                    atom_size = struct.unpack('>I', atom_header[:4])[0]
                    atom_type = atom_header[4:8]
                    
                    if atom_size == 0:
                        break
                    
                    if atom_type == b'meta':
                        # Leer datos del atom meta
                        meta_data = f.read(atom_size - 8)
                        
                        # Buscar datos de DJ software
                        if b'serato' in meta_data.lower():
                            print("✅ Found Serato data in M4A")
                            cues = self._parse_serato_data(meta_data)
                            metadata['cue_points'].extend(cues)
                        
                        metadata['metadata_found'].append('meta')
                        break
                    else:
                        # Saltar este atom
                        f.seek(f.tell() + atom_size - 8)
                
        except Exception as e:
            print(f"❌ Error reading M4A metadata: {e}")
        
        return metadata
    
    def _read_flac_metadata(self, file_path: str) -> Dict[str, Any]:
        """Leer metadatos de archivo FLAC."""
        metadata = {'metadata_found': [], 'cue_points': []}
        
        try:
            with open(file_path, 'rb') as f:
                # Verificar header FLAC
                if f.read(4) != b'fLaC':
                    return metadata
                
                # Leer bloques de metadatos
                while True:
                    block_header = f.read(4)
                    if len(block_header) < 4:
                        break
                    
                    is_last = (block_header[0] & 0x80) != 0
                    block_type = block_header[0] & 0x7F
                    block_size = struct.unpack('>I', b'\x00' + block_header[1:4])[0]
                    
                    block_data = f.read(block_size)
                    
                    if block_type == 4:  # VORBIS_COMMENT
                        # Buscar comentarios de DJ software
                        if b'serato' in block_data.lower():
                            print("✅ Found Serato data in FLAC")
                            cues = self._parse_serato_data(block_data)
                            metadata['cue_points'].extend(cues)
                        
                        metadata['metadata_found'].append('VORBIS_COMMENT')
                    
                    if is_last:
                        break
                
        except Exception as e:
            print(f"❌ Error reading FLAC metadata: {e}")
        
        return metadata
    
    def _read_wav_metadata(self, file_path: str) -> Dict[str, Any]:
        """Leer metadatos de archivo WAV."""
        metadata = {'metadata_found': [], 'cue_points': []}
        
        try:
            with open(file_path, 'rb') as f:
                # Verificar header WAV
                if f.read(4) != b'RIFF':
                    return metadata
                
                file_size = struct.unpack('<I', f.read(4))[0]
                if f.read(4) != b'WAVE':
                    return metadata
                
                # Leer chunks
                while f.tell() < file_size:
                    chunk_header = f.read(8)
                    if len(chunk_header) < 8:
                        break
                    
                    chunk_id = chunk_header[:4]
                    chunk_size = struct.unpack('<I', chunk_header[4:8])[0]
                    
                    if chunk_id == b'cue ':
                        # Chunk de cue points nativo de WAV
                        print("✅ Found native WAV cue points")
                        cue_data = f.read(chunk_size)
                        cues = self._parse_wav_cue_chunk(cue_data)
                        metadata['cue_points'].extend(cues)
                        metadata['metadata_found'].append('cue')
                    else:
                        # Saltar chunk
                        f.seek(f.tell() + chunk_size)
                        if chunk_size % 2:  # Padding
                            f.seek(f.tell() + 1)
                
        except Exception as e:
            print(f"❌ Error reading WAV metadata: {e}")
        
        return metadata
    
    def _parse_serato_data(self, data: bytes) -> List[EmbeddedCuePoint]:
        """Parsear datos de Serato (versión simplificada)."""
        cue_points = []
        
        try:
            # Buscar patrones de posición en los datos
            # Serato almacena posiciones como enteros de 4 bytes
            for i in range(0, len(data) - 4, 4):
                try:
                    # Intentar leer como posición en milisegundos
                    pos_ms = struct.unpack('>I', data[i:i+4])[0]
                    
                    # Validar que sea una posición razonable (entre 1s y 30min)
                    if 1000 <= pos_ms <= 1800000:
                        position_sec = pos_ms / 1000.0
                        
                        # Buscar color cerca de esta posición
                        color = "#FF0000"  # Default rojo
                        if i + 7 < len(data):
                            try:
                                r, g, b = data[i+4], data[i+5], data[i+6]
                                if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                                    color = f"#{r:02X}{g:02X}{b:02X}"
                            except:
                                pass
                        
                        cue_point = EmbeddedCuePoint(
                            position=position_sec,
                            type="cue",
                            color=color,
                            name=f"Serato Cue {len(cue_points) + 1}",
                            hotcue_index=len(cue_points) + 1 if len(cue_points) < 8 else 0,
                            created_at=time.time(),
                            energy_level=5,
                            source="embedded",
                            software="serato"
                        )
                        cue_points.append(cue_point)
                        
                        # Limitar a 8 cue points
                        if len(cue_points) >= 8:
                            break
                            
                except:
                    continue
            
        except Exception as e:
            print(f"❌ Error parsing Serato data: {e}")
        
        return cue_points
    
    def _parse_mixinkey_data(self, data: bytes) -> List[EmbeddedCuePoint]:
        """Parsear datos de MixInKey."""
        cue_points = []
        
        try:
            # Convertir a texto
            text = data.decode('utf-8', errors='ignore')
            
            # Buscar patrones de tiempo
            import re
            time_patterns = re.findall(r'(\d+\.\d+)', text)
            
            colors = ['#FF0000', '#FF6600', '#FFFF00', '#00FF00', '#00FFFF', '#0066FF', '#9900FF', '#FF00CC']
            
            for i, time_str in enumerate(time_patterns[:8]):
                try:
                    position = float(time_str)
                    if 1.0 <= position <= 1800.0:  # Entre 1s y 30min
                        cue_point = EmbeddedCuePoint(
                            position=position,
                            type="cue",
                            color=colors[i % len(colors)],
                            name=f"MIK Cue {i + 1}",
                            hotcue_index=i + 1,
                            created_at=time.time(),
                            energy_level=5,
                            source="embedded",
                            software="mixinkey"
                        )
                        cue_points.append(cue_point)
                except ValueError:
                    continue
            
        except Exception as e:
            print(f"❌ Error parsing MixInKey data: {e}")
        
        return cue_points
    
    def _parse_traktor_data(self, data: bytes) -> List[EmbeddedCuePoint]:
        """Parsear datos de Traktor."""
        cue_points = []
        
        try:
            # Similar a MixInKey pero con patrones diferentes
            text = data.decode('utf-8', errors='ignore')
            
            import re
            time_patterns = re.findall(r'(\d+\.\d+)', text)
            
            colors = ['#FF0000', '#FF6600', '#FFFF00', '#00FF00', '#00FFFF', '#0066FF', '#9900FF', '#FF00CC']
            
            for i, time_str in enumerate(time_patterns[:8]):
                try:
                    position = float(time_str)
                    if 1.0 <= position <= 1800.0:
                        cue_point = EmbeddedCuePoint(
                            position=position,
                            type="cue",
                            color=colors[i % len(colors)],
                            name=f"Traktor Cue {i + 1}",
                            hotcue_index=i + 1,
                            created_at=time.time(),
                            energy_level=5,
                            source="embedded",
                            software="traktor"
                        )
                        cue_points.append(cue_point)
                except ValueError:
                    continue
            
        except Exception as e:
            print(f"❌ Error parsing Traktor data: {e}")
        
        return cue_points
    
    def _parse_wav_cue_chunk(self, data: bytes) -> List[EmbeddedCuePoint]:
        """Parsear chunk de cue points nativo de WAV."""
        cue_points = []
        
        try:
            if len(data) < 4:
                return cue_points
            
            # Leer número de cue points
            num_cues = struct.unpack('<I', data[:4])[0]
            offset = 4
            
            colors = ['#FF0000', '#FF6600', '#FFFF00', '#00FF00', '#00FFFF', '#0066FF', '#9900FF', '#FF00CC']
            
            for i in range(min(num_cues, 8)):  # Máximo 8
                if offset + 24 <= len(data):
                    # Leer entrada de cue point (24 bytes)
                    cue_id = struct.unpack('<I', data[offset:offset+4])[0]
                    position = struct.unpack('<I', data[offset+4:offset+8])[0]
                    
                    # Convertir posición de samples a segundos (asumiendo 44.1kHz)
                    position_sec = position / 44100.0
                    
                    cue_point = EmbeddedCuePoint(
                        position=position_sec,
                        type="cue",
                        color=colors[i % len(colors)],
                        name=f"WAV Cue {i + 1}",
                        hotcue_index=i + 1,
                        created_at=time.time(),
                        energy_level=5,
                        source="embedded",
                        software="wav_native"
                    )
                    cue_points.append(cue_point)
                    
                    offset += 24
                else:
                    break
            
        except Exception as e:
            print(f"❌ Error parsing WAV cue chunk: {e}")
        
        return cue_points
    
    def _decode_synchsafe_int(self, data: bytes) -> int:
        """Decodificar entero synchsafe de ID3v2."""
        result = 0
        for byte in data:
            result = (result << 7) | (byte & 0x7F)
        return result

def scan_audio_folder(folder_path: str):
    """Escanear carpeta de audio buscando metadatos embebidos."""
    print(f"🔍 Scanning audio folder: {folder_path}")
    print("=" * 60)
    
    reader = BasicMetadataReader()
    
    # Buscar archivos de audio
    audio_files = []
    for ext in reader.supported_formats:
        import glob
        pattern = os.path.join(folder_path, f"*{ext}")
        files = glob.glob(pattern)
        audio_files.extend(files)
    
    if not audio_files:
        print("❌ No audio files found")
        return
    
    print(f"📁 Found {len(audio_files)} audio files")
    
    total_cues = 0
    files_with_cues = 0
    software_detected = set()
    
    # Analizar primeros 10 archivos
    for audio_file in audio_files[:10]:
        print(f"\n📀 Analyzing: {os.path.basename(audio_file)}")
        print("-" * 40)
        
        metadata = reader.scan_file(audio_file)
        
        print(f"📊 Size: {metadata['size_mb']:.1f} MB")
        print(f"🎵 Format: {metadata['format']}")
        print(f"🏷️ Metadata frames: {len(metadata['metadata_found'])}")
        
        cue_points = metadata['cue_points']
        if cue_points:
            files_with_cues += 1
            total_cues += len(cue_points)
            
            print(f"🎯 Embedded cue points: {len(cue_points)}")
            
            for cue in cue_points:
                software_detected.add(cue.software)
                minutes = int(cue.position // 60)
                seconds = int(cue.position % 60)
                print(f"   🎵 {cue.name} @ {minutes}:{seconds:02d} ({cue.software}) {cue.color}")
        else:
            print("❌ No embedded cue points found")
    
    print("\n" + "=" * 60)
    print(f"📊 Scan Results:")
    print(f"   📁 Files analyzed: {min(len(audio_files), 10)}")
    print(f"   ✅ Files with embedded cues: {files_with_cues}")
    print(f"   🎯 Total cue points found: {total_cues}")
    print(f"   🎛️ Software detected: {', '.join(software_detected) if software_detected else 'None'}")
    
    if total_cues > 0:
        print("\n🎉 Embedded cue points found! Ready for integration.")
    else:
        print("\n💡 No embedded cue points found.")
        print("   Try files that have been processed by:")
        print("   - Serato DJ")
        print("   - Mixed In Key")
        print("   - Traktor Pro")
        print("   - Other DJ software")

def main():
    """Función principal."""
    print("🎯 DjAlfin - Basic Embedded Metadata Reader")
    print("Reading cue points from DJ software without external dependencies")
    
    # Escanear carpeta de audio
    audio_folder = "/Volumes/KINGSTON/Audio"
    scan_audio_folder(audio_folder)

if __name__ == "__main__":
    main()
