"""
Analizador profesional de BPM para DjAlfin.
Utiliza librosa para detección precisa de tempo y beat tracking.
"""

import librosa
import numpy as np
from pathlib import Path
import warnings
from typing import Optional, Tuple, Dict, Any

# Suprimir warnings de librosa para logs más limpios
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")

class BPMAnalyzer:
    """
    Analizador profesional de BPM con algoritmos avanzados.
    
    Características:
    - Detección de BPM con múltiples algoritmos
    - Confidence scoring
    - Detección de half/double tempo
    - Beat grid analysis
    - Manejo de BPM variable
    """
    
    def __init__(self):
        """Inicializa el analizador con configuración optimizada."""
        self.sr = 22050  # Sample rate optimizado para análisis
        self.hop_length = 512  # Resolución temporal
        self.min_bpm = 60    # BPM mínimo válido
        self.max_bpm = 200   # BPM máximo válido
        
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analiza un archivo de audio completo para extraer BPM y características.
        
        Args:
            file_path (str): Ruta al archivo de audio
            
        Returns:
            dict: Diccionario con BPM, confidence, y otras características
        """
        try:
            print(f"🔬 Analizando BPM: {Path(file_path).name}")
            
            # Cargar audio con librosa
            y, sr = librosa.load(file_path, sr=self.sr, duration=60.0)  # Primeros 60s
            
            if len(y) < self.sr:  # Archivo muy corto
                return self._create_result(error="Archivo demasiado corto para análisis")
            
            # Análisis de tempo con múltiples métodos
            bpm_primary = self._analyze_tempo_primary(y, sr)
            bpm_secondary = self._analyze_tempo_secondary(y, sr)
            
            # Validar y elegir mejor BPM
            final_bpm, confidence = self._validate_and_choose_bpm(
                bpm_primary, bpm_secondary, y, sr
            )
            
            # Análisis adicional
            beat_track = self._analyze_beat_track(y, sr, final_bpm)
            rhythm_features = self._analyze_rhythm_features(y, sr)
            
            return self._create_result(
                bpm=final_bpm,
                confidence=confidence,
                beat_track=beat_track,
                rhythm_features=rhythm_features
            )
            
        except Exception as e:
            print(f"❌ Error en análisis BPM: {e}")
            return self._create_result(error=str(e))
    
    def _analyze_tempo_primary(self, y: np.ndarray, sr: int) -> float:
        """Método primario de detección de tempo usando onset detection."""
        # Detección de onsets (inicio de notas/beats)
        onset_envelope = librosa.onset.onset_strength(
            y=y, sr=sr, hop_length=self.hop_length
        )
        
        # Análisis de tempo basado en onsets
        tempo, _ = librosa.beat.beat_track(
            onset_envelope=onset_envelope, 
            sr=sr,
            hop_length=self.hop_length,
            start_bpm=120.0,  # BPM inicial estimado
            tightness=100     # Qué tan estricto es el tracking
        )
        
        return tempo.item() if hasattr(tempo, 'item') else float(tempo)
    
    def _analyze_tempo_secondary(self, y: np.ndarray, sr: int) -> float:
        """Método secundario usando autocorrelación para verificación."""
        # Análisis espectral para patrones rítmicos
        stft = librosa.stft(y, hop_length=self.hop_length)
        magnitude = np.abs(stft)
        
        # Detectar periodicidad en las frecuencias bajas (donde está el beat)
        low_freq_mag = magnitude[:40, :]  # Primeras 40 bins (frecuencias bajas)
        
        # Onset strength en frecuencias bajas
        onset_envelope = librosa.onset.onset_strength(
            S=low_freq_mag, 
            sr=sr, 
            hop_length=self.hop_length
        )
        
        # Tempo alternativo
        tempo, _ = librosa.beat.beat_track(
            onset_envelope=onset_envelope,
            sr=sr,
            hop_length=self.hop_length,
            units='time'
        )
        
        return tempo.item() if hasattr(tempo, 'item') else float(tempo)
    
    def _validate_and_choose_bpm(self, bpm1: float, bpm2: float, 
                                y: np.ndarray, sr: int) -> Tuple[float, float]:
        """
        Valida los BPMs detectados y elige el más confiable.
        Maneja casos de half/double tempo.
        """
        # Limpiar BPMs fuera del rango válido
        valid_bpms = []
        
        for bpm in [bpm1, bpm2]:
            if self.min_bpm <= bpm <= self.max_bpm:
                valid_bpms.append(bpm)
            elif self.min_bpm <= bpm/2 <= self.max_bpm:  # Half tempo
                valid_bpms.append(bpm/2)
            elif self.min_bpm <= bpm*2 <= self.max_bpm:  # Double tempo
                valid_bpms.append(bpm*2)
        
        if not valid_bpms:
            # Fallback: análisis básico
            return self._fallback_bpm_analysis(y, sr)
        
        # Si tenemos múltiples BPMs, elegir por consistencia
        if len(valid_bpms) > 1:
            # Calcular confidence basado en qué tan cerca están los valores
            diff = abs(valid_bpms[0] - valid_bpms[1])
            if diff < 5:  # Muy similares, alta confianza
                confidence = 0.9
                final_bpm = np.mean(valid_bpms)
            elif diff < 10:  # Moderadamente similares
                confidence = 0.7
                final_bpm = valid_bpms[0]  # Tomar el primero
            else:  # Muy diferentes, baja confianza
                confidence = 0.5
                final_bpm = valid_bpms[0]
        else:
            final_bpm = valid_bpms[0]
            confidence = 0.8  # Confianza base
        
        # Redondear a 1 decimal
        final_bpm = round(final_bpm, 1)
        
        return final_bpm, confidence
    
    def _fallback_bpm_analysis(self, y: np.ndarray, sr: int) -> Tuple[float, float]:
        """Análisis de fallback cuando otros métodos fallan."""
        try:
            # Método simple pero robusto
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr, trim=False)
            bpm = tempo.item() if hasattr(tempo, 'item') else float(tempo)
            
            # Ajustar si está fuera del rango
            while bpm < self.min_bpm:
                bpm *= 2
            while bpm > self.max_bpm:
                bpm /= 2
                
            return round(bpm, 1), 0.6  # Confianza moderada
            
        except Exception:
            return 120.0, 0.3  # BPM por defecto con baja confianza
    
    def _analyze_beat_track(self, y: np.ndarray, sr: int, bpm: float) -> Dict[str, Any]:
        """Analiza el beat tracking para grid de beats."""
        try:
            # Detectar beats específicos
            tempo, beats = librosa.beat.beat_track(
                y=y, sr=sr, hop_length=self.hop_length, trim=False
            )
            
            # Convertir beats a timestamps
            beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=self.hop_length)
            
            # Calcular intervalos entre beats
            if len(beat_times) > 1:
                intervals = np.diff(beat_times)
                avg_interval = np.mean(intervals)
                interval_stability = 1.0 - (np.std(intervals) / avg_interval)
            else:
                avg_interval = 60.0 / bpm  # Calcular basado en BPM
                interval_stability = 0.5
            
            return {
                'beat_times': beat_times.tolist()[:20],  # Primeros 20 beats
                'beat_count': len(beat_times),
                'avg_interval': float(avg_interval),
                'stability': float(interval_stability)
            }
            
        except Exception as e:
            print(f"⚠️ Error en beat tracking: {e}")
            return {
                'beat_times': [],
                'beat_count': 0,
                'avg_interval': 60.0 / bpm,
                'stability': 0.5
            }
    
    def _analyze_rhythm_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analiza características rítmicas adicionales."""
        try:
            # Características espectrales relacionadas con ritmo
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
            
            # RMS energy para detectar intensidad rítmica
            rms = librosa.feature.rms(y=y)
            
            return {
                'spectral_centroid_mean': float(np.mean(spectral_centroid)),
                'zero_crossing_rate_mean': float(np.mean(zero_crossing_rate)),
                'rms_mean': float(np.mean(rms)),
                'energy_variance': float(np.var(rms))
            }
            
        except Exception:
            return {
                'spectral_centroid_mean': 0.0,
                'zero_crossing_rate_mean': 0.0,
                'rms_mean': 0.0,
                'energy_variance': 0.0
            }
    
    def _create_result(self, bpm: float = None, confidence: float = None,
                      beat_track: Dict = None, rhythm_features: Dict = None,
                      error: str = None) -> Dict[str, Any]:
        """Crea el diccionario de resultado estandarizado."""
        if error:
            return {
                'bpm': None,
                'confidence': 0.0,
                'error': error,
                'beat_track': None,
                'rhythm_features': None,
                'analysis_time': None
            }
        
        return {
            'bpm': bpm,
            'confidence': confidence,
            'error': None,
            'beat_track': beat_track or {},
            'rhythm_features': rhythm_features or {},
            'analysis_time': f"BPM: {bpm:.1f} (Confidence: {confidence:.1%})"
        }
    
    def quick_bpm_estimate(self, file_path: str, duration: float = 30.0) -> float:
        """
        Estimación rápida de BPM para preview (usa menos recursos).
        
        Args:
            file_path (str): Ruta al archivo
            duration (float): Duración en segundos para analizar
            
        Returns:
            float: BPM estimado
        """
        try:
            # Cargar solo una porción pequeña del archivo
            y, sr = librosa.load(file_path, sr=11025, duration=duration, offset=30.0)
            
            # Análisis rápido
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr, trim=False)
            bpm = tempo.item() if hasattr(tempo, 'item') else float(tempo)
            
            # Validar rango
            while bpm < self.min_bpm:
                bpm *= 2
            while bpm > self.max_bpm:
                bpm /= 2
                
            return round(bpm, 1)
            
        except Exception as e:
            print(f"⚠️ Error en estimación rápida BPM: {e}")
            return 120.0  # BPM por defecto


# Funciones de utilidad para integración fácil
def analyze_track_bpm(file_path: str) -> Dict[str, Any]:
    """Función de conveniencia para analizar BPM de un track."""
    analyzer = BPMAnalyzer()
    return analyzer.analyze_file(file_path)

def get_quick_bpm(file_path: str) -> float:
    """Función de conveniencia para BPM rápido."""
    analyzer = BPMAnalyzer()
    return analyzer.quick_bpm_estimate(file_path)


# Testing y debugging
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"🎵 Analizando: {file_path}")
        
        result = analyze_track_bpm(file_path)
        
        print(f"📊 Resultados:")
        print(f"   BPM: {result['bpm']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        if result['beat_track']:
            print(f"   Beats detectados: {result['beat_track']['beat_count']}")
            print(f"   Estabilidad: {result['beat_track']['stability']:.1%}")
        
        if result['error']:
            print(f"❌ Error: {result['error']}")
    else:
        print("Uso: python bpm_analyzer.py <archivo_audio>") 