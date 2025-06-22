# core/audio_analyzer.py

import librosa
import numpy as np
import math
import tempfile
import subprocess
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

@dataclass
class AudioFeatures:
    """Características musicales extraídas del audio."""
    # Características básicas
    duration: float
    tempo: float
    key: str
    energy: float
    
    # Características de Spotify-style
    danceability: float
    valence: float  # Positividad musical
    acousticness: float
    instrumentalness: float
    liveness: float
    speechiness: float
    loudness: float
    
    # Características técnicas
    spectral_centroid: float
    spectral_rolloff: float
    zero_crossing_rate: float
    mfcc_features: List[float]
    
    # Análisis de estructura
    beat_strength: float
    rhythm_consistency: float
    dynamic_range: float
    
    # Compatibilidad DJ
    intro_length: float
    outro_length: float
    mix_in_point: float
    mix_out_point: float
    
    # Metadatos de confianza
    analysis_confidence: float
    features_version: str = "1.0"

class AudioAnalyzer:
    """
    Analizador de audio avanzado para extraer características musicales.
    
    Features:
    - Análisis completo de características musicales
    - Compatibilidad con múltiples formatos
    - Análisis optimizado para DJs
    - Extracción de puntos de mezcla
    - Cálculo de compatibilidad entre tracks
    """
    
    def __init__(self):
        self.sample_rate = 22050  # Optimizado para análisis musical
        self.hop_length = 512
        self.frame_length = 2048
        
        # Configuración de análisis
        self.analysis_duration = 120.0  # Analizar primeros 2 minutos
        self.confidence_threshold = 0.7
        
        print("🎵 AudioAnalyzer inicializado")
    
    def analyze_file(self, file_path: str) -> Optional[AudioFeatures]:
        """
        Analiza un archivo de audio y extrae todas las características.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            AudioFeatures con todas las características extraídas
        """
        try:
            print(f"🔍 Analizando audio: {Path(file_path).name}")
            
            # Cargar audio
            y, sr = self._load_audio(file_path)
            if y is None:
                return None
            
            # Extraer características básicas
            duration = len(y) / sr
            tempo, beats = self._analyze_tempo_beats(y, sr)
            key = self._analyze_key(y, sr)
            energy = self._calculate_energy(y)
            
            # Características de mood/feeling
            danceability = self._calculate_danceability(y, sr, tempo, beats)
            valence = self._calculate_valence(y, sr)
            acousticness = self._calculate_acousticness(y, sr)
            instrumentalness = self._calculate_instrumentalness(y, sr)
            liveness = self._calculate_liveness(y, sr)
            speechiness = self._calculate_speechiness(y, sr)
            loudness = self._calculate_loudness(y)
            
            # Características espectrales
            spectral_centroid = self._calculate_spectral_centroid(y, sr)
            spectral_rolloff = self._calculate_spectral_rolloff(y, sr)
            zero_crossing_rate = self._calculate_zcr(y)
            mfcc_features = self._extract_mfcc_features(y, sr)
            
            # Análisis de estructura
            beat_strength = self._calculate_beat_strength(y, sr, beats)
            rhythm_consistency = self._calculate_rhythm_consistency(beats)
            dynamic_range = self._calculate_dynamic_range(y)
            
            # Análisis DJ-específico
            intro_length, outro_length = self._analyze_intro_outro(y, sr)
            mix_in_point, mix_out_point = self._calculate_mix_points(y, sr, duration)
            
            # Calcular confianza general
            analysis_confidence = self._calculate_analysis_confidence(
                tempo, energy, danceability, acousticness
            )
            
            features = AudioFeatures(
                duration=duration,
                tempo=tempo,
                key=key,
                energy=energy,
                danceability=danceability,
                valence=valence,
                acousticness=acousticness,
                instrumentalness=instrumentalness,
                liveness=liveness,
                speechiness=speechiness,
                loudness=loudness,
                spectral_centroid=spectral_centroid,
                spectral_rolloff=spectral_rolloff,
                zero_crossing_rate=zero_crossing_rate,
                mfcc_features=mfcc_features,
                beat_strength=beat_strength,
                rhythm_consistency=rhythm_consistency,
                dynamic_range=dynamic_range,
                intro_length=intro_length,
                outro_length=outro_length,
                mix_in_point=mix_in_point,
                mix_out_point=mix_out_point,
                analysis_confidence=analysis_confidence
            )
            
            print(f"✅ Análisis completado - Tempo: {tempo:.1f} BPM, Key: {key}, Energy: {energy:.2f}")
            return features
            
        except Exception as e:
            print(f"❌ Error analizando audio {file_path}: {e}")
            return None
    
    def _load_audio(self, file_path: str) -> Tuple[Optional[np.ndarray], int]:
        """Carga archivo de audio con manejo de errores."""
        try:
            # Intentar cargar directamente con librosa
            y, sr = librosa.load(
                file_path, 
                sr=self.sample_rate, 
                duration=self.analysis_duration
            )
            
            if len(y) == 0:
                raise ValueError("Audio vacío")
                
            return y, sr
            
        except Exception as e:
            print(f"⚠️ Error cargando audio con librosa: {e}")
            
            # Fallback: convertir con ffmpeg si está disponible
            try:
                return self._load_audio_with_ffmpeg(file_path)
            except Exception as e2:
                print(f"❌ Error cargando audio con ffmpeg: {e2}")
                return None, 0
    
    def _load_audio_with_ffmpeg(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Carga audio usando ffmpeg como fallback."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Convertir a WAV temporal
        cmd = [
            'ffmpeg', '-i', file_path, 
            '-ar', str(self.sample_rate),
            '-ac', '1',  # Mono
            '-t', str(self.analysis_duration),
            '-y', temp_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Cargar WAV temporal
        y, sr = librosa.load(temp_path, sr=self.sample_rate)
        
        # Limpiar archivo temporal
        Path(temp_path).unlink(missing_ok=True)
        
        return y, sr
    
    def _analyze_tempo_beats(self, y: np.ndarray, sr: int) -> Tuple[float, np.ndarray]:
        """Analiza tempo y detecta beats."""
        try:
            # Detectar beats
            tempo, beats = librosa.beat.beat_track(
                y=y, sr=sr, 
                hop_length=self.hop_length,
                units='time'
            )
            
            # Validar tempo
            if tempo < 60 or tempo > 200:
                # Intentar con diferentes parámetros
                onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
                onset_times = librosa.frames_to_time(onset_frames, sr=sr)
                
                if len(onset_times) > 1:
                    # Estimar tempo de onsets
                    intervals = np.diff(onset_times)
                    median_interval = np.median(intervals)
                    tempo = 60.0 / median_interval if median_interval > 0 else 120.0
                else:
                    tempo = 120.0  # Default
            
            return float(tempo), beats
            
        except Exception as e:
            print(f"⚠️ Error analizando tempo: {e}")
            return 120.0, np.array([])
    
    def _analyze_key(self, y: np.ndarray, sr: int) -> str:
        """Analiza la tonalidad musical."""
        try:
            # Usar chromagram para detectar tonalidad
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Mapeo de notas
            notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            # Encontrar nota dominante
            key_idx = np.argmax(chroma_mean)
            key_note = notes[key_idx]
            
            # Detectar modo (mayor/menor) basado en patrones de chroma
            major_profile = [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
            minor_profile = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]
            
            # Rotar perfiles para la nota detectada
            major_rotated = np.roll(major_profile, key_idx)
            minor_rotated = np.roll(minor_profile, key_idx)
            
            major_correlation = np.corrcoef(chroma_mean, major_rotated)[0, 1]
            minor_correlation = np.corrcoef(chroma_mean, minor_rotated)[0, 1]
            
            if major_correlation > minor_correlation:
                return f"{key_note} Major"
            else:
                return f"{key_note} Minor"
                
        except Exception as e:
            print(f"⚠️ Error analizando tonalidad: {e}")
            return "Unknown"
    
    def _calculate_energy(self, y: np.ndarray) -> float:
        """Calcula energía del audio."""
        try:
            # RMS energy
            rms = librosa.feature.rms(y=y)[0]
            energy = np.mean(rms)
            
            # Normalizar a 0-1
            return min(float(energy * 10), 1.0)
            
        except Exception:
            return 0.5
    
    def _calculate_danceability(self, y: np.ndarray, sr: int, tempo: float, beats: np.ndarray) -> float:
        """Calcula danceability (qué tan bailable es el track)."""
        try:
            factors = []
            
            # Factor 1: Consistencia de tempo
            if 100 <= tempo <= 140:
                tempo_factor = 1.0
            elif 80 <= tempo < 100 or 140 < tempo <= 160:
                tempo_factor = 0.8
            else:
                tempo_factor = 0.4
            factors.append(tempo_factor)
            
            # Factor 2: Fuerza del beat
            if len(beats) > 1:
                beat_intervals = np.diff(beats)
                beat_consistency = 1.0 - np.std(beat_intervals) / np.mean(beat_intervals)
                factors.append(max(0, beat_consistency))
            
            # Factor 3: Energía rítmica
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
            rhythm_energy = np.mean(onset_strength)
            factors.append(min(rhythm_energy * 2, 1.0))
            
            # Factor 4: Regularidad espectral
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            contrast_variation = np.std(spectral_contrast)
            regularity = max(0, 1.0 - contrast_variation / 10)
            factors.append(regularity)
            
            return float(np.mean(factors))
            
        except Exception:
            return 0.5
    
    def _calculate_valence(self, y: np.ndarray, sr: int) -> float:
        """Calcula valencia (positividad musical)."""
        try:
            # Basado en características espectrales que correlacionan con mood
            
            # Factor 1: Centroide espectral (brightness)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            brightness = np.mean(spectral_centroid) / sr * 2  # Normalizado
            
            # Factor 2: Chroma deviation (armonía)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_std = np.std(chroma)
            harmony = max(0, 1 - chroma_std)
            
            # Factor 3: Tempo influence
            tempo_factor = 0.7 if self._last_tempo > 120 else 0.3
            
            # Factor 4: Zero crossing rate (indica suavidad)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            smoothness = 1 - np.mean(zcr)
            
            valence = np.mean([brightness, harmony, tempo_factor, smoothness])
            return float(np.clip(valence, 0, 1))
            
        except Exception:
            return 0.5
    
    def _calculate_acousticness(self, y: np.ndarray, sr: int) -> float:
        """Calcula nivel de acústico vs electrónico."""
        try:
            # Factor 1: Análisis espectral de frecuencias típicamente acústicas
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            
            # Frecuencias acústicas típicas (200-4000 Hz)
            acoustic_freqs = magnitude[20:400, :]  # Aprox 200-4000Hz
            total_energy = np.sum(magnitude)
            acoustic_energy = np.sum(acoustic_freqs)
            
            acoustic_ratio = acoustic_energy / total_energy if total_energy > 0 else 0
            
            # Factor 2: Presencia de armónicos naturales
            harmonic = librosa.effects.harmonic(y)
            percussive = librosa.effects.percussive(y)
            
            harmonic_ratio = np.sum(harmonic**2) / (np.sum(harmonic**2) + np.sum(percussive**2))
            
            # Factor 3: Ausencia de frecuencias sintéticas altas
            high_freqs = magnitude[800:, :]  # Frecuencias muy altas
            synthetic_indicator = 1 - min(np.sum(high_freqs) / total_energy, 1)
            
            acousticness = np.mean([acoustic_ratio * 2, harmonic_ratio, synthetic_indicator])
            return float(np.clip(acousticness, 0, 1))
            
        except Exception:
            return 0.5
    
    def _calculate_instrumentalness(self, y: np.ndarray, sr: int) -> float:
        """Calcula nivel instrumental vs vocal."""
        try:
            # Detectar presencia vocal usando análisis espectral
            
            # Factor 1: Frecuencias vocales típicas (80-255 Hz fundamental)
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            
            vocal_freqs = magnitude[8:25, :]  # Aprox 80-255Hz fundamentales
            vocal_harmonics = magnitude[25:100, :]  # Armónicos vocales
            
            vocal_energy = np.sum(vocal_freqs) + np.sum(vocal_harmonics) * 0.5
            total_energy = np.sum(magnitude)
            
            vocal_presence = vocal_energy / total_energy if total_energy > 0 else 0
            
            # Factor 2: Variabilidad espectral (voces varían más)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            spectral_variation = np.std(spectral_rolloff) / np.mean(spectral_rolloff)
            
            # Voces tienen más variación espectral
            vocal_variation = min(spectral_variation * 2, 1)
            
            # Factor 3: Onset patterns (instrumentos vs voces)
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
            onset_regularity = 1 - np.std(onset_strength) / np.mean(onset_strength)
            
            # Invertir: más instrumental = menos vocal
            instrumentalness = 1 - np.mean([vocal_presence * 3, vocal_variation, 1 - onset_regularity])
            
            return float(np.clip(instrumentalness, 0, 1))
            
        except Exception:
            return 0.5
    
    def _calculate_liveness(self, y: np.ndarray, sr: int) -> float:
        """Calcula si suena como grabación en vivo."""
        try:
            # Factor 1: Ruido de fondo / ambiente
            # Analizar frecuencias muy bajas y muy altas
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            
            background_noise = magnitude[:5, :] + magnitude[-20:, :]  # Muy bajo + muy alto
            signal_energy = magnitude[5:-20, :]
            
            noise_ratio = np.sum(background_noise) / np.sum(signal_energy)
            
            # Factor 2: Reverberación natural
            # Detectar decay natural de reverb
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
            if len(onset_frames) > 1:
                # Analizar decay después de onsets
                decay_analysis = []
                for onset in onset_frames[:10]:  # Primeros 10 onsets
                    start_frame = onset
                    end_frame = min(onset + sr // 4, len(y))  # 0.25s después
                    
                    if end_frame > start_frame:
                        segment = y[start_frame:end_frame]
                        # Calcular decay rate
                        rms_envelope = librosa.feature.rms(y=segment, frame_length=256, hop_length=128)[0]
                        if len(rms_envelope) > 1:
                            decay_rate = np.polyfit(range(len(rms_envelope)), rms_envelope, 1)[0]
                            decay_analysis.append(abs(decay_rate))
                
                natural_decay = np.mean(decay_analysis) if decay_analysis else 0
            else:
                natural_decay = 0
            
            # Factor 3: Inconsistencias de grabación
            # Variaciones en loudness que indican ambiente en vivo
            rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            loudness_variation = np.std(rms) / np.mean(rms) if np.mean(rms) > 0 else 0
            
            liveness = np.mean([
                min(noise_ratio * 10, 1),
                min(natural_decay * 50, 1),
                min(loudness_variation * 5, 1)
            ])
            
            return float(np.clip(liveness, 0, 1))
            
        except Exception:
            return 0.1  # Default bajo para grabaciones de estudio
    
    def _calculate_speechiness(self, y: np.ndarray, sr: int) -> float:
        """Calcula presencia de speech/rap vs canto melódico."""
        try:
            # Factor 1: Periodicidad vs aperiodicidad
            # Speech es menos periódico que canto
            
            # Usar autocorrelación para detectar periodicidad
            autocorr = librosa.autocorrelate(y)
            periodicity = np.max(autocorr[sr//4:sr//2]) / np.max(autocorr)  # Peak relative strength
            
            # Factor 2: Rango dinámico rápido
            # Speech tiene cambios rápidos de amplitud
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr, hop_length=128)
            rapid_changes = np.sum(np.diff(onset_strength) > np.std(onset_strength))
            change_rate = rapid_changes / len(onset_strength)
            
            # Factor 3: Distribución espectral típica de speech
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            # Los primeros MFCCs indican formantes del speech
            speech_formants = np.mean(np.abs(mfccs[1:4, :]))  # MFCCs 1-3
            
            # Factor 4: Zero crossing rate alto (consonantes)
            zcr = librosa.feature.zero_crossing_rate(y, frame_length=1024, hop_length=512)[0]
            zcr_variation = np.std(zcr)  # Speech tiene más variación en ZCR
            
            speechiness = np.mean([
                1 - periodicity,  # Menos periódico = más speech
                min(change_rate * 20, 1),
                min(speech_formants / 10, 1),
                min(zcr_variation * 100, 1)
            ])
            
            return float(np.clip(speechiness, 0, 1))
            
        except Exception:
            return 0.1  # Default bajo
    
    def _calculate_loudness(self, y: np.ndarray) -> float:
        """Calcula loudness percibido."""
        try:
            # Usar RMS como proxy de loudness
            rms = np.sqrt(np.mean(y**2))
            
            # Convertir a dBFS
            if rms > 0:
                loudness_db = 20 * np.log10(rms)
                # Normalizar de -60dB a 0dB -> 0 a 1
                normalized = (loudness_db + 60) / 60
                return float(np.clip(normalized, 0, 1))
            else:
                return 0.0
                
        except Exception:
            return 0.5
    
    def _calculate_spectral_centroid(self, y: np.ndarray, sr: int) -> float:
        """Calcula centroide espectral promedio."""
        try:
            centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            return float(np.mean(centroid))
        except Exception:
            return 2000.0  # Default
    
    def _calculate_spectral_rolloff(self, y: np.ndarray, sr: int) -> float:
        """Calcula rolloff espectral promedio."""
        try:
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            return float(np.mean(rolloff))
        except Exception:
            return 4000.0  # Default
    
    def _calculate_zcr(self, y: np.ndarray) -> float:
        """Calcula zero crossing rate promedio."""
        try:
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            return float(np.mean(zcr))
        except Exception:
            return 0.1
    
    def _extract_mfcc_features(self, y: np.ndarray, sr: int) -> List[float]:
        """Extrae características MFCC."""
        try:
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            # Promedio de cada coeficiente
            mfcc_means = np.mean(mfccs, axis=1)
            return mfcc_means.tolist()
        except Exception:
            return [0.0] * 13
    
    def _calculate_beat_strength(self, y: np.ndarray, sr: int, beats: np.ndarray) -> float:
        """Calcula fuerza promedio del beat."""
        try:
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
            if len(beats) > 0 and len(onset_strength) > 0:
                # Convertir beats a frames
                beat_frames = librosa.time_to_frames(beats, sr=sr)
                # Filtrar frames válidos
                valid_frames = beat_frames[beat_frames < len(onset_strength)]
                if len(valid_frames) > 0:
                    beat_strengths = onset_strength[valid_frames]
                    return float(np.mean(beat_strengths))
            return 0.5
        except Exception:
            return 0.5
    
    def _calculate_rhythm_consistency(self, beats: np.ndarray) -> float:
        """Calcula consistencia rítmica."""
        try:
            if len(beats) < 3:
                return 0.5
            
            intervals = np.diff(beats)
            if len(intervals) == 0:
                return 0.5
                
            consistency = 1.0 - (np.std(intervals) / np.mean(intervals))
            return float(max(0, min(consistency, 1)))
            
        except Exception:
            return 0.5
    
    def _calculate_dynamic_range(self, y: np.ndarray) -> float:
        """Calcula rango dinámico."""
        try:
            # Usar percentiles para evitar outliers
            rms = librosa.feature.rms(y=y)[0]
            p95 = np.percentile(rms, 95)
            p5 = np.percentile(rms, 5)
            
            if p5 > 0:
                dynamic_range = 20 * np.log10(p95 / p5)
                # Normalizar: 0-40dB -> 0-1
                normalized = dynamic_range / 40
                return float(np.clip(normalized, 0, 1))
            else:
                return 0.5
                
        except Exception:
            return 0.5
    
    def _analyze_intro_outro(self, y: np.ndarray, sr: int) -> Tuple[float, float]:
        """Analiza duración de intro y outro."""
        try:
            # Detectar cuando la música "realmente" empieza y termina
            # basado en energía
            
            rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            
            # Threshold basado en percentil
            energy_threshold = np.percentile(rms, 25)
            
            # Encontrar primer punto donde energía supera threshold consistentemente
            intro_frames = 0
            for i in range(len(rms) - 10):
                if np.mean(rms[i:i+10]) > energy_threshold:
                    intro_frames = i
                    break
            
            # Encontrar último punto donde energía está sobre threshold
            outro_frames = len(rms)
            for i in range(len(rms) - 10, 10, -1):
                if np.mean(rms[i-10:i]) > energy_threshold:
                    outro_frames = i
                    break
            
            # Convertir a tiempo
            intro_time = librosa.frames_to_time(intro_frames * 512, sr=sr)
            outro_time = len(y) / sr - librosa.frames_to_time(outro_frames * 512, sr=sr)
            
            return float(intro_time), float(outro_time)
            
        except Exception:
            return 0.0, 0.0
    
    def _calculate_mix_points(self, y: np.ndarray, sr: int, duration: float) -> Tuple[float, float]:
        """Calcula puntos óptimos de mezcla para DJs."""
        try:
            # Mix in: después del intro pero antes del primer breakdown
            # Mix out: antes del outro pero después del último breakdown
            
            # Análisis de estructura basado en energía
            rms = librosa.feature.rms(y=y, frame_length=4096, hop_length=1024)[0]
            
            # Suavizar para encontrar tendencias
            from scipy.ndimage import uniform_filter1d
            smoothed_rms = uniform_filter1d(rms, size=20)
            
            # Encontrar puntos de alta energía estable
            energy_threshold = np.percentile(smoothed_rms, 70)
            
            # Mix in point: primer momento de alta energía estable (después de 10% del track)
            start_search = int(len(smoothed_rms) * 0.1)
            mix_in_frame = start_search
            
            for i in range(start_search, len(smoothed_rms) - 50):
                if np.mean(smoothed_rms[i:i+50]) > energy_threshold:
                    mix_in_frame = i
                    break
            
            # Mix out point: último momento de alta energía estable (antes del 90%)
            end_search = int(len(smoothed_rms) * 0.9)
            mix_out_frame = end_search
            
            for i in range(end_search, 50, -1):
                if np.mean(smoothed_rms[i-50:i]) > energy_threshold:
                    mix_out_frame = i
                    break
            
            # Convertir a tiempo
            mix_in_time = librosa.frames_to_time(mix_in_frame * 1024, sr=sr)
            mix_out_time = librosa.frames_to_time(mix_out_frame * 1024, sr=sr)
            
            return float(mix_in_time), float(mix_out_time)
            
        except Exception:
            # Default a 25% y 75% del track
            return duration * 0.25, duration * 0.75
    
    def _calculate_analysis_confidence(self, tempo: float, energy: float, 
                                     danceability: float, acousticness: float) -> float:
        """Calcula confianza general del análisis."""
        try:
            confidence_factors = []
            
            # Factor tempo: más confianza si está en rango normal
            if 80 <= tempo <= 180:
                tempo_confidence = 1.0
            elif 60 <= tempo < 80 or 180 < tempo <= 200:
                tempo_confidence = 0.8
            else:
                tempo_confidence = 0.5
            confidence_factors.append(tempo_confidence)
            
            # Factor energía: más confianza si no está en extremos
            energy_confidence = 1.0 - abs(energy - 0.5) * 0.5
            confidence_factors.append(energy_confidence)
            
            # Factor danceability: valores razonables
            dance_confidence = 1.0 if 0.2 <= danceability <= 0.9 else 0.7
            confidence_factors.append(dance_confidence)
            
            # Factor acoustic: valores no extremos
            acoustic_confidence = 1.0 if 0.1 <= acousticness <= 0.9 else 0.8
            confidence_factors.append(acoustic_confidence)
            
            return float(np.mean(confidence_factors))
            
        except Exception:
            return 0.7
    
    # Almacenar tempo para uso en otros cálculos
    @property
    def _last_tempo(self) -> float:
        return getattr(self, '_temp_tempo', 120.0)
    
    def calculate_track_similarity(self, features1: AudioFeatures, features2: AudioFeatures) -> float:
        """
        Calcula similitud entre dos tracks basándose en sus características.
        
        Args:
            features1: Características del primer track
            features2: Características del segundo track
            
        Returns:
            Similitud entre 0.0 y 1.0
        """
        try:
            similarities = []
            
            # Similitud de tempo (importante para DJs)
            tempo_diff = abs(features1.tempo - features2.tempo)
            tempo_sim = max(0, 1 - tempo_diff / 60)  # Penalizar diferencias > 60 BPM
            similarities.append(('tempo', tempo_sim, 0.25))
            
            # Similitud de energía
            energy_diff = abs(features1.energy - features2.energy)
            energy_sim = 1 - energy_diff
            similarities.append(('energy', energy_sim, 0.2))
            
            # Similitud de danceability
            dance_diff = abs(features1.danceability - features2.danceability)
            dance_sim = 1 - dance_diff
            similarities.append(('danceability', dance_sim, 0.15))
            
            # Similitud de valence (mood)
            valence_diff = abs(features1.valence - features2.valence)
            valence_sim = 1 - valence_diff
            similarities.append(('valence', valence_sim, 0.15))
            
            # Similitud de acousticness
            acoustic_diff = abs(features1.acousticness - features2.acousticness)
            acoustic_sim = 1 - acoustic_diff
            similarities.append(('acousticness', acoustic_sim, 0.1))
            
            # Similitud de loudness
            loudness_diff = abs(features1.loudness - features2.loudness)
            loudness_sim = 1 - loudness_diff
            similarities.append(('loudness', loudness_sim, 0.1))
            
            # Similitud MFCC (timbre)
            if len(features1.mfcc_features) == len(features2.mfcc_features):
                mfcc_diff = np.mean([abs(a - b) for a, b in zip(features1.mfcc_features, features2.mfcc_features)])
                mfcc_sim = max(0, 1 - mfcc_diff / 50)  # Normalizar
                similarities.append(('mfcc', mfcc_sim, 0.05))
            
            # Calcular similitud ponderada
            total_weight = sum(weight for _, _, weight in similarities)
            weighted_sum = sum(sim * weight for _, sim, weight in similarities)
            
            return weighted_sum / total_weight if total_weight > 0 else 0.5
            
        except Exception as e:
            print(f"❌ Error calculando similitud: {e}")
            return 0.5
    
    def get_track_compatibility_score(self, features1: AudioFeatures, features2: AudioFeatures) -> Dict[str, float]:
        """
        Calcula scores de compatibilidad específicos para DJs.
        
        Returns:
            Dict con scores de diferentes aspectos de compatibilidad
        """
        try:
            compatibility = {}
            
            # Compatibilidad de tempo para beatmatching
            tempo_diff = abs(features1.tempo - features2.tempo)
            if tempo_diff <= 5:
                tempo_compat = 1.0
            elif tempo_diff <= 15:
                tempo_compat = 0.8
            elif tempo_diff <= 30:
                tempo_compat = 0.5
            else:
                tempo_compat = 0.2
            
            compatibility['tempo_matching'] = tempo_compat
            
            # Compatibilidad de energía para flow del set
            energy_diff = abs(features1.energy - features2.energy)
            energy_compat = max(0, 1 - energy_diff * 1.5)  # Penalizar cambios bruscos
            compatibility['energy_flow'] = energy_compat
            
            # Compatibilidad harmónica (si ambos tienen key detectada)
            if features1.key != "Unknown" and features2.key != "Unknown":
                key_compat = self._calculate_harmonic_compatibility(features1.key, features2.key)
            else:
                key_compat = 0.5
            compatibility['harmonic_mixing'] = key_compat
            
            # Compatibilidad de mood
            mood_factors = [
                abs(features1.valence - features2.valence),
                abs(features1.danceability - features2.danceability),
                abs(features1.acousticness - features2.acousticness)
            ]
            mood_compat = 1 - np.mean(mood_factors)
            compatibility['mood_consistency'] = max(0, mood_compat)
            
            # Score general
            compatibility['overall'] = np.mean(list(compatibility.values()))
            
            return compatibility
            
        except Exception as e:
            print(f"❌ Error calculando compatibilidad: {e}")
            return {'overall': 0.5}
    
    def _calculate_harmonic_compatibility(self, key1: str, key2: str) -> float:
        """Calcula compatibilidad harmónica entre dos tonalidades."""
        try:
            # Mapeo básico de compatibilidad harmónica
            # Basado en círculo de quintas y relaciones modales
            
            # Extraer nota y modo
            def parse_key(key_str):
                parts = key_str.split()
                if len(parts) >= 2:
                    return parts[0], parts[1].lower()
                return key_str, 'major'
            
            note1, mode1 = parse_key(key1)
            note2, mode2 = parse_key(key2)
            
            # Círculo de quintas
            circle_of_fifths = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
            
            try:
                pos1 = circle_of_fifths.index(note1)
                pos2 = circle_of_fifths.index(note2)
                
                # Distancia en círculo de quintas
                distance = min(abs(pos1 - pos2), 12 - abs(pos1 - pos2))
                
                # Compatibilidad basada en distancia
                if distance == 0:  # Misma tonalidad
                    base_compat = 1.0
                elif distance == 1:  # Quinta perfecta
                    base_compat = 0.9
                elif distance == 2:  # Segunda mayor
                    base_compat = 0.7
                elif distance == 5:  # Tritono
                    base_compat = 0.3
                else:
                    base_compat = 0.6
                
                # Ajustar por modo
                if mode1 == mode2:
                    mode_bonus = 0.1
                elif (mode1 == 'major' and mode2 == 'minor') or (mode1 == 'minor' and mode2 == 'major'):
                    mode_bonus = 0.0  # Neutral
                else:
                    mode_bonus = 0.05
                
                return min(1.0, base_compat + mode_bonus)
                
            except ValueError:
                # Nota no encontrada en círculo
                return 0.5
                
        except Exception:
            return 0.5

# Instancia global
_audio_analyzer_instance = None

def get_audio_analyzer() -> AudioAnalyzer:
    """Obtiene la instancia global del analizador de audio."""
    global _audio_analyzer_instance
    if _audio_analyzer_instance is None:
        _audio_analyzer_instance = AudioAnalyzer()
    return _audio_analyzer_instance

# Funciones de conveniencia
def analyze_audio_file(file_path: str) -> Optional[AudioFeatures]:
    """Analiza un archivo de audio."""
    return get_audio_analyzer().analyze_file(file_path)

def calculate_similarity(features1: AudioFeatures, features2: AudioFeatures) -> float:
    """Calcula similitud entre dos tracks."""
    return get_audio_analyzer().calculate_track_similarity(features1, features2)

def get_mix_compatibility(features1: AudioFeatures, features2: AudioFeatures) -> Dict[str, float]:
    """Obtiene compatibilidad de mezcla entre tracks."""
    return get_audio_analyzer().get_track_compatibility_score(features1, features2)