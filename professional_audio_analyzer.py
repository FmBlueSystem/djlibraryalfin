#!/usr/bin/env python3
"""
🎵 DjAlfin - Professional Audio Analyzer
Análisis real de audio con detección de beats, downbeats y validación de cue points
"""

import librosa
import numpy as np
import soundfile as sf
from dataclasses import dataclass
from typing import List, Tuple, Optional
import time

@dataclass
class BeatInfo:
    """Información de un beat detectado."""
    position: float  # Posición en segundos
    is_downbeat: bool  # Si es el primer beat del compás
    confidence: float  # Confianza de la detección (0-1)
    bpm: float  # BPM en esta posición
    energy: float  # Nivel de energía (0-1)

@dataclass
class CueAnalysis:
    """Análisis de un cue point."""
    original_position: float
    nearest_downbeat: float
    distance_to_downbeat: float
    is_on_downbeat: bool
    confidence: float
    suggested_position: Optional[float]
    energy_level: float
    bpm_at_position: float
    musical_context: str  # "intro", "verse", "chorus", "breakdown", "outro"

@dataclass
class AudioAnalysis:
    """Análisis completo de un archivo de audio."""
    duration: float
    sample_rate: int
    waveform: np.ndarray  # Waveform real
    beats: List[BeatInfo]
    downbeats: List[float]
    tempo: float
    tempo_changes: List[Tuple[float, float]]  # (time, bpm)
    energy_curve: np.ndarray
    spectral_centroid: np.ndarray
    cue_analyses: List[CueAnalysis]

class ProfessionalAudioAnalyzer:
    """Analizador profesional de audio para DJ."""
    
    def __init__(self):
        self.cache = {}  # Cache para análisis previos
        
    def analyze_audio_file(self, file_path: str, cue_points: List = None) -> AudioAnalysis:
        """Análisis completo de un archivo de audio."""
        
        print(f"🎵 Analyzing audio: {file_path}")
        start_time = time.time()
        
        try:
            # Cargar audio
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            print(f"📊 Loaded: {duration:.1f}s, {sr}Hz")
            
            # Análisis básico
            waveform = self._extract_waveform(y, sr)
            
            # Análisis de beats y tempo
            beats_info = self._analyze_beats_and_tempo(y, sr)
            
            # Análisis de energía y características espectrales
            energy_curve = self._analyze_energy(y, sr)
            spectral_centroid = self._analyze_spectral_features(y, sr)
            
            # Análisis de cue points si se proporcionan
            cue_analyses = []
            if cue_points:
                cue_analyses = self._analyze_cue_points(cue_points, beats_info['downbeats'], y, sr)
            
            analysis = AudioAnalysis(
                duration=duration,
                sample_rate=sr,
                waveform=waveform,
                beats=beats_info['beats'],
                downbeats=beats_info['downbeats'],
                tempo=beats_info['tempo'],
                tempo_changes=beats_info['tempo_changes'],
                energy_curve=energy_curve,
                spectral_centroid=spectral_centroid,
                cue_analyses=cue_analyses
            )
            
            elapsed = time.time() - start_time
            print(f"✅ Analysis complete in {elapsed:.1f}s")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing audio: {e}")
            raise
    
    def _extract_waveform(self, y: np.ndarray, sr: int, target_points: int = 2000) -> np.ndarray:
        """Extraer waveform real con resolución específica."""
        
        # Calcular RMS para obtener amplitud
        hop_length = len(y) // target_points
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # Normalizar
        rms = rms / np.max(rms)
        
        return rms
    
    def _analyze_beats_and_tempo(self, y: np.ndarray, sr: int) -> dict:
        """Análisis avanzado de beats y tempo."""
        
        print("🥁 Analyzing beats and tempo...")
        
        # Detección de tempo y beats
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
        
        # Detección de downbeats
        downbeats = self._detect_downbeats(y, sr, beats)
        
        # Análisis de cambios de tempo
        tempo_changes = self._analyze_tempo_changes(y, sr, beats)
        
        # Crear información detallada de beats
        beats_info = []
        for i, beat_time in enumerate(beats):
            is_downbeat = any(abs(beat_time - db) < 0.05 for db in downbeats)
            
            # Calcular energía en este beat
            beat_start = int(beat_time * sr)
            beat_end = int((beat_time + 0.1) * sr)  # 100ms window
            if beat_end < len(y):
                energy = np.mean(np.abs(y[beat_start:beat_end]))
            else:
                energy = 0.0
            
            # BPM local (promedio de los últimos 4 beats)
            if i >= 3:
                recent_beats = beats[i-3:i+1]
                intervals = np.diff(recent_beats)
                local_bpm = 60.0 / np.mean(intervals) if len(intervals) > 0 else tempo
            else:
                local_bpm = tempo
            
            beat_info = BeatInfo(
                position=beat_time,
                is_downbeat=is_downbeat,
                confidence=0.8,  # Placeholder - podría calcularse
                bpm=local_bpm,
                energy=energy
            )
            beats_info.append(beat_info)
        
        return {
            'beats': beats_info,
            'downbeats': downbeats,
            'tempo': tempo,
            'tempo_changes': tempo_changes
        }
    
    def _detect_downbeats(self, y: np.ndarray, sr: int, beats: np.ndarray) -> List[float]:
        """Detectar downbeats (primer beat del compás)."""
        
        try:
            # Usar análisis harmónico para detectar downbeats
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            
            # Simplificación: asumir compás de 4/4 y tomar cada 4to beat
            downbeats = []
            for i in range(0, len(beats), 4):
                if i < len(beats):
                    downbeats.append(beats[i])
            
            return downbeats
            
        except Exception as e:
            print(f"⚠️ Downbeat detection failed, using fallback: {e}")
            # Fallback: cada 4 beats
            return [beats[i] for i in range(0, len(beats), 4)]
    
    def _analyze_tempo_changes(self, y: np.ndarray, sr: int, beats: np.ndarray) -> List[Tuple[float, float]]:
        """Detectar cambios de tempo a lo largo de la canción."""
        
        tempo_changes = []
        window_size = 8  # Analizar cada 8 beats
        
        for i in range(0, len(beats) - window_size, window_size // 2):
            window_beats = beats[i:i + window_size]
            if len(window_beats) >= 2:
                intervals = np.diff(window_beats)
                local_tempo = 60.0 / np.mean(intervals)
                tempo_changes.append((window_beats[0], local_tempo))
        
        return tempo_changes
    
    def _analyze_energy(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Análisis de energía a lo largo del tiempo."""
        
        # RMS energy con ventana deslizante
        hop_length = 512
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # Suavizar
        from scipy import ndimage
        rms_smooth = ndimage.gaussian_filter1d(rms, sigma=2)
        
        return rms_smooth
    
    def _analyze_spectral_features(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Análisis de características espectrales."""
        
        # Centroide espectral (brillo del sonido)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        
        return spectral_centroid
    
    def _analyze_cue_points(self, cue_points: List, downbeats: List[float], y: np.ndarray, sr: int) -> List[CueAnalysis]:
        """Análisis detallado de cue points."""
        
        print(f"🎯 Analyzing {len(cue_points)} cue points...")
        
        analyses = []
        
        for cue in cue_points:
            position = cue.position
            
            # Encontrar el downbeat más cercano
            distances = [abs(position - db) for db in downbeats]
            nearest_idx = np.argmin(distances)
            nearest_downbeat = downbeats[nearest_idx]
            distance = distances[nearest_idx]
            
            # Determinar si está "en el downbeat" (tolerancia de 100ms)
            is_on_downbeat = distance < 0.1
            
            # Calcular energía en la posición del cue
            cue_start = int(position * sr)
            cue_end = int((position + 0.5) * sr)  # 500ms window
            if cue_end < len(y):
                energy = np.mean(np.abs(y[cue_start:cue_end]))
            else:
                energy = 0.0
            
            # Estimar BPM local
            # Encontrar beats cercanos
            beat_distances = [abs(position - db) for db in downbeats]
            nearby_beats = [db for db, dist in zip(downbeats, beat_distances) if dist < 8.0]  # 8 segundos
            
            if len(nearby_beats) >= 2:
                intervals = np.diff(sorted(nearby_beats))
                local_bpm = 60.0 / (np.mean(intervals) * 4)  # *4 porque son downbeats
            else:
                local_bpm = 120.0  # Default
            
            # Determinar contexto musical (simplificado)
            duration = librosa.get_duration(y=y, sr=sr)
            relative_position = position / duration
            
            if relative_position < 0.1:
                context = "intro"
            elif relative_position < 0.3:
                context = "verse"
            elif relative_position < 0.7:
                context = "chorus"
            elif relative_position < 0.9:
                context = "breakdown"
            else:
                context = "outro"
            
            # Sugerir corrección si es necesario
            suggested_position = None
            if not is_on_downbeat and distance < 2.0:  # Solo si está cerca
                suggested_position = nearest_downbeat
            
            analysis = CueAnalysis(
                original_position=position,
                nearest_downbeat=nearest_downbeat,
                distance_to_downbeat=distance,
                is_on_downbeat=is_on_downbeat,
                confidence=max(0.0, 1.0 - distance),  # Más cerca = más confianza
                suggested_position=suggested_position,
                energy_level=energy,
                bpm_at_position=local_bpm,
                musical_context=context
            )
            
            analyses.append(analysis)
        
        # Estadísticas
        on_downbeat = sum(1 for a in analyses if a.is_on_downbeat)
        print(f"📊 Cue analysis: {on_downbeat}/{len(analyses)} on downbeat")
        
        return analyses
    
    def get_zoom_waveform(self, analysis: AudioAnalysis, center_time: float, zoom_duration: float) -> dict:
        """Obtener waveform para una vista con zoom."""
        
        start_time = max(0, center_time - zoom_duration / 2)
        end_time = min(analysis.duration, center_time + zoom_duration / 2)
        
        # Calcular índices en el waveform
        total_points = len(analysis.waveform)
        start_idx = int((start_time / analysis.duration) * total_points)
        end_idx = int((end_time / analysis.duration) * total_points)
        
        zoom_waveform = analysis.waveform[start_idx:end_idx]
        
        # Beats en el rango de zoom
        zoom_beats = [b for b in analysis.beats if start_time <= b.position <= end_time]
        zoom_downbeats = [db for db in analysis.downbeats if start_time <= db <= end_time]
        
        return {
            'waveform': zoom_waveform,
            'start_time': start_time,
            'end_time': end_time,
            'beats': zoom_beats,
            'downbeats': zoom_downbeats,
            'time_per_point': (end_time - start_time) / len(zoom_waveform) if len(zoom_waveform) > 0 else 0
        }

def test_analyzer():
    """Test del analizador con un archivo real."""
    
    analyzer = ProfessionalAudioAnalyzer()
    
    # Buscar un archivo de prueba
    import os
    audio_folder = "/Volumes/KINGSTON/Audio"
    
    if os.path.exists(audio_folder):
        mp3_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3') and not f.startswith('._')]
        
        if mp3_files:
            test_file = os.path.join(audio_folder, mp3_files[0])
            print(f"🧪 Testing with: {mp3_files[0]}")
            
            try:
                analysis = analyzer.analyze_audio_file(test_file)
                
                print(f"📊 Analysis Results:")
                print(f"   Duration: {analysis.duration:.1f}s")
                print(f"   Tempo: {analysis.tempo:.1f} BPM")
                print(f"   Beats detected: {len(analysis.beats)}")
                print(f"   Downbeats: {len(analysis.downbeats)}")
                print(f"   Waveform points: {len(analysis.waveform)}")
                
                return analysis
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                return None
        else:
            print("❌ No MP3 files found for testing")
            return None
    else:
        print("❌ Audio folder not found")
        return None

if __name__ == "__main__":
    test_analyzer()
