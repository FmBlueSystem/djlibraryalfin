# core/audio_enrichment_service.py

import json
import time
from typing import Dict, Optional, List, Tuple
from pathlib import Path

from .audio_analyzer import get_audio_analyzer, AudioFeatures
from .database import add_track, get_track_by_path
from .enrichment_logger import get_enrichment_logger

class AudioEnrichmentService:
    """
    Servicio para integrar análisis de audio con el sistema de enriquecimiento existente.
    
    Features:
    - Análisis automático de características musicales
    - Integración con metadata enricher
    - Cache de resultados en base de datos
    - Actualización inteligente basada en versiones
    - Logging completo del proceso
    """
    
    def __init__(self):
        self.audio_analyzer = get_audio_analyzer()
        self.logger = get_enrichment_logger()
        self.current_version = "1.0"
        
        print("🎵 AudioEnrichmentService inicializado")
    
    def enrich_track_audio_features(self, track_info: Dict) -> Dict:
        """
        Enriquece un track con características de audio.
        
        Args:
            track_info: Información básica del track (debe incluir file_path)
            
        Returns:
            track_info actualizado con características de audio
        """
        file_path = track_info.get('file_path')
        if not file_path:
            self.logger.warning("audio_enricher", "No file_path provided for audio analysis")
            return track_info
        
        if not Path(file_path).exists():
            self.logger.warning("audio_enricher", f"File not found: {file_path}")
            return track_info
        
        # Verificar si ya existe análisis actualizado
        existing_track = get_track_by_path(file_path)
        if self._is_analysis_current(existing_track):
            self.logger.debug("audio_enricher", f"Audio analysis up to date for {Path(file_path).name}")
            return self._merge_audio_features_from_db(track_info, existing_track)
        
        # Realizar análisis de audio
        self.logger.info("audio_enricher", f"Starting audio analysis for {Path(file_path).name}")
        
        start_time = time.time()
        audio_features = self.audio_analyzer.analyze_file(file_path)
        analysis_time = time.time() - start_time
        
        if audio_features:
            # Integrar características con track_info
            enriched_track = self._integrate_audio_features(track_info, audio_features)
            
            # Guardar en base de datos
            self._save_audio_features_to_db(enriched_track)
            
            self.logger.success(
                "audio_enricher", 
                f"Audio analysis completed for {Path(file_path).name}",
                performance_metrics={
                    'analysis_time': analysis_time,
                    'confidence': audio_features.analysis_confidence
                },
                data={
                    'tempo': audio_features.tempo,
                    'key': audio_features.key,
                    'energy': audio_features.energy,
                    'danceability': audio_features.danceability
                }
            )
            
            return enriched_track
        else:
            self.logger.error("audio_enricher", f"Failed to analyze audio for {Path(file_path).name}")
            return track_info
    
    def _is_analysis_current(self, track_data: Optional[Dict]) -> bool:
        """Verifica si el análisis de audio está actualizado."""
        if not track_data:
            return False
        
        # Verificar versión
        stored_version = track_data.get('audio_features_version')
        if stored_version != self.current_version:
            return False
        
        # Verificar que tenga características básicas
        required_fields = ['energy', 'danceability', 'valence', 'audio_analysis_confidence']
        for field in required_fields:
            if track_data.get(field) is None:
                return False
        
        # Verificar fecha de análisis (opcional: re-analizar después de X tiempo)
        analysis_date = track_data.get('audio_analyzed_date')
        if not analysis_date:
            return False
        
        return True
    
    def _merge_audio_features_from_db(self, track_info: Dict, db_track: Dict) -> Dict:
        """Combina track_info con características de audio de la base de datos."""
        # Copiar características de audio desde DB
        audio_fields = [
            'energy', 'danceability', 'valence', 'acousticness', 'instrumentalness',
            'liveness', 'speechiness', 'loudness',
            'spectral_centroid', 'spectral_rolloff', 'zero_crossing_rate', 'mfcc_features',
            'beat_strength', 'rhythm_consistency', 'dynamic_range',
            'intro_length', 'outro_length', 'mix_in_point', 'mix_out_point',
            'audio_analysis_confidence', 'audio_features_version', 'audio_analyzed_date'
        ]
        
        enriched = track_info.copy()
        for field in audio_fields:
            if field in db_track and db_track[field] is not None:
                enriched[field] = db_track[field]
        
        return enriched
    
    def _integrate_audio_features(self, track_info: Dict, audio_features: AudioFeatures) -> Dict:
        """Integra AudioFeatures con track_info."""
        enriched = track_info.copy()
        
        # Características básicas de mood/feeling
        enriched['energy'] = audio_features.energy
        enriched['danceability'] = audio_features.danceability
        enriched['valence'] = audio_features.valence
        enriched['acousticness'] = audio_features.acousticness
        enriched['instrumentalness'] = audio_features.instrumentalness
        enriched['liveness'] = audio_features.liveness
        enriched['speechiness'] = audio_features.speechiness
        enriched['loudness'] = audio_features.loudness
        
        # Características espectrales
        enriched['spectral_centroid'] = audio_features.spectral_centroid
        enriched['spectral_rolloff'] = audio_features.spectral_rolloff
        enriched['zero_crossing_rate'] = audio_features.zero_crossing_rate
        
        # MFCC como JSON string
        if audio_features.mfcc_features:
            enriched['mfcc_features'] = json.dumps(audio_features.mfcc_features)
        
        # Análisis de estructura
        enriched['beat_strength'] = audio_features.beat_strength
        enriched['rhythm_consistency'] = audio_features.rhythm_consistency
        enriched['dynamic_range'] = audio_features.dynamic_range
        
        # Análisis DJ-específico
        enriched['intro_length'] = audio_features.intro_length
        enriched['outro_length'] = audio_features.outro_length
        enriched['mix_in_point'] = audio_features.mix_in_point
        enriched['mix_out_point'] = audio_features.mix_out_point
        
        # Metadatos de análisis
        enriched['audio_analysis_confidence'] = audio_features.analysis_confidence
        enriched['audio_features_version'] = audio_features.features_version
        enriched['audio_analyzed_date'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Actualizar tempo y key si el análisis es más confiable
        if audio_features.analysis_confidence > 0.7:
            if audio_features.tempo and (not enriched.get('bpm') or enriched.get('bpm_confidence', 0) < 0.8):
                enriched['bpm'] = audio_features.tempo
                enriched['bpm_confidence'] = audio_features.analysis_confidence
            
            if audio_features.key and audio_features.key != "Unknown":
                enriched['key'] = audio_features.key
        
        return enriched
    
    def _save_audio_features_to_db(self, track_info: Dict):
        """Guarda las características de audio en la base de datos."""
        try:
            add_track(track_info)
            self.logger.debug("audio_enricher", f"Audio features saved to DB for {Path(track_info['file_path']).name}")
        except Exception as e:
            self.logger.error("audio_enricher", f"Failed to save audio features to DB: {e}")
    
    def batch_analyze_tracks(self, track_list: List[Dict], 
                           force_reanalysis: bool = False,
                           callback=None) -> List[Dict]:
        """
        Analiza múltiples tracks en lote.
        
        Args:
            track_list: Lista de tracks a analizar
            force_reanalysis: Forzar re-análisis incluso si ya existe
            callback: Función opcional para reportar progreso
            
        Returns:
            Lista de tracks enriquecidos
        """
        enriched_tracks = []
        total = len(track_list)
        
        self.logger.info("audio_enricher", f"Starting batch audio analysis for {total} tracks")
        
        for i, track in enumerate(track_list):
            try:
                # Verificar si necesita análisis
                if not force_reanalysis:
                    existing_track = get_track_by_path(track.get('file_path'))
                    if self._is_analysis_current(existing_track):
                        enriched_tracks.append(self._merge_audio_features_from_db(track, existing_track))
                        if callback:
                            callback(i + 1, total, f"Skipped (up to date): {Path(track['file_path']).name}")
                        continue
                
                # Analizar track
                enriched_track = self.enrich_track_audio_features(track)
                enriched_tracks.append(enriched_track)
                
                if callback:
                    callback(i + 1, total, f"Analyzed: {Path(track['file_path']).name}")
                
            except Exception as e:
                self.logger.error("audio_enricher", f"Error analyzing track {track.get('file_path')}: {e}")
                enriched_tracks.append(track)  # Añadir sin modificar
                
                if callback:
                    callback(i + 1, total, f"Error: {Path(track['file_path']).name}")
        
        self.logger.info("audio_enricher", f"Batch analysis completed: {len(enriched_tracks)} tracks processed")
        return enriched_tracks
    
    def get_track_audio_features(self, file_path: str) -> Optional[Dict]:
        """
        Obtiene las características de audio de un track específico.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Dict con características de audio o None si no existen
        """
        track_data = get_track_by_path(file_path)
        if not track_data:
            return None
        
        if not self._is_analysis_current(track_data):
            return None
        
        # Extraer solo campos de audio
        audio_fields = [
            'energy', 'danceability', 'valence', 'acousticness', 'instrumentalness',
            'liveness', 'speechiness', 'loudness',
            'spectral_centroid', 'spectral_rolloff', 'zero_crossing_rate', 'mfcc_features',
            'beat_strength', 'rhythm_consistency', 'dynamic_range',
            'intro_length', 'outro_length', 'mix_in_point', 'mix_out_point',
            'audio_analysis_confidence', 'audio_features_version'
        ]
        
        audio_features = {}
        for field in audio_fields:
            if field in track_data and track_data[field] is not None:
                audio_features[field] = track_data[field]
        
        return audio_features if audio_features else None
    
    def calculate_tracks_similarity(self, file_path1: str, file_path2: str) -> Optional[float]:
        """
        Calcula similitud entre dos tracks basándose en características de audio.
        
        Args:
            file_path1: Ruta del primer track
            file_path2: Ruta del segundo track
            
        Returns:
            Similitud entre 0.0 y 1.0, o None si no se puede calcular
        """
        # Obtener características de ambos tracks
        features1_dict = self.get_track_audio_features(file_path1)
        features2_dict = self.get_track_audio_features(file_path2)
        
        if not features1_dict or not features2_dict:
            return None
        
        try:
            # Convertir dicts a AudioFeatures (simplificado)
            # Para una implementación completa, se necesitaría un método de conversión
            
            # Por ahora, calcular similitud básica usando campos principales
            similarity_factors = []
            
            # Similitud de características principales
            main_features = ['energy', 'danceability', 'valence', 'acousticness']
            for feature in main_features:
                if feature in features1_dict and feature in features2_dict:
                    val1 = features1_dict[feature]
                    val2 = features2_dict[feature]
                    if val1 is not None and val2 is not None:
                        similarity = 1.0 - abs(val1 - val2)
                        similarity_factors.append(similarity)
            
            if similarity_factors:
                return sum(similarity_factors) / len(similarity_factors)
            else:
                return None
                
        except Exception as e:
            self.logger.error("audio_enricher", f"Error calculating similarity: {e}")
            return None
    
    def get_similar_tracks(self, reference_file_path: str, 
                          candidate_tracks: List[Dict], 
                          max_results: int = 10,
                          min_similarity: float = 0.5) -> List[Tuple[Dict, float]]:
        """
        Encuentra tracks similares al de referencia.
        
        Args:
            reference_file_path: Track de referencia
            candidate_tracks: Lista de tracks candidatos
            max_results: Máximo número de resultados
            min_similarity: Similitud mínima requerida
            
        Returns:
            Lista de tuplas (track, similitud) ordenada por similitud
        """
        similar_tracks = []
        
        for track in candidate_tracks:
            candidate_path = track.get('file_path')
            if candidate_path == reference_file_path:
                continue  # Saltar el mismo track
            
            similarity = self.calculate_tracks_similarity(reference_file_path, candidate_path)
            if similarity is not None and similarity >= min_similarity:
                similar_tracks.append((track, similarity))
        
        # Ordenar por similitud descendente
        similar_tracks.sort(key=lambda x: x[1], reverse=True)
        
        return similar_tracks[:max_results]
    
    def get_tracks_by_mood(self, mood: str, track_list: List[Dict]) -> List[Dict]:
        """
        Filtra tracks por mood/estado de ánimo.
        
        Args:
            mood: Tipo de mood ('energetic', 'chill', 'happy', 'danceable', etc.)
            track_list: Lista de tracks a filtrar
            
        Returns:
            Lista de tracks que coinciden con el mood
        """
        filtered_tracks = []
        
        # Definir criterios para diferentes moods
        mood_criteria = {
            'energetic': {'energy': (0.7, 1.0), 'danceability': (0.6, 1.0)},
            'chill': {'energy': (0.0, 0.4), 'valence': (0.3, 0.8), 'acousticness': (0.3, 1.0)},
            'happy': {'valence': (0.7, 1.0), 'energy': (0.5, 1.0)},
            'danceable': {'danceability': (0.7, 1.0), 'energy': (0.6, 1.0)},
            'melancholic': {'valence': (0.0, 0.3), 'energy': (0.0, 0.5)},
            'instrumental': {'instrumentalness': (0.7, 1.0)},
            'acoustic': {'acousticness': (0.7, 1.0)},
            'live': {'liveness': (0.7, 1.0)}
        }
        
        criteria = mood_criteria.get(mood.lower())
        if not criteria:
            self.logger.warning("audio_enricher", f"Unknown mood: {mood}")
            return track_list
        
        for track in track_list:
            audio_features = self.get_track_audio_features(track.get('file_path'))
            if not audio_features:
                continue
            
            # Verificar si el track cumple con los criterios del mood
            matches_mood = True
            for feature, (min_val, max_val) in criteria.items():
                feature_value = audio_features.get(feature)
                if feature_value is None or not (min_val <= feature_value <= max_val):
                    matches_mood = False
                    break
            
            if matches_mood:
                filtered_tracks.append(track)
        
        return filtered_tracks

# Instancia global
_audio_enrichment_service = None

def get_audio_enrichment_service() -> AudioEnrichmentService:
    """Obtiene la instancia global del servicio de enriquecimiento de audio."""
    global _audio_enrichment_service
    if _audio_enrichment_service is None:
        _audio_enrichment_service = AudioEnrichmentService()
    return _audio_enrichment_service

# Funciones de conveniencia
def enrich_track_with_audio(track_info: Dict) -> Dict:
    """Enriquece un track con análisis de audio."""
    return get_audio_enrichment_service().enrich_track_audio_features(track_info)

def get_similar_tracks_to(reference_path: str, candidates: List[Dict], limit: int = 10) -> List[Tuple[Dict, float]]:
    """Encuentra tracks similares."""
    return get_audio_enrichment_service().get_similar_tracks(reference_path, candidates, limit)

def filter_tracks_by_mood(mood: str, tracks: List[Dict]) -> List[Dict]:
    """Filtra tracks por mood."""
    return get_audio_enrichment_service().get_tracks_by_mood(mood, tracks)