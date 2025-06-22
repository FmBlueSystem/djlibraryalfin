# core/smart_playlist_generator.py

import random
import math
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import json

from .audio_enrichment_service import get_audio_enrichment_service
from .database import get_all_tracks, create_connection
from .semantic_genre_scorer import get_semantic_scorer

class GenerationMode(Enum):
    """Modos de generación de playlists."""
    SEED_ARTIST = "seed_artist"
    SEED_GENRE = "seed_genre"
    SEED_TRACK = "seed_track"
    MOOD_BASED = "mood_based"
    SIMILARITY_CHAIN = "similarity_chain"
    BPM_PROGRESSION = "bpm_progression"
    ENERGY_CURVE = "energy_curve"

@dataclass
class GenerationCriteria:
    """Criterios para generación de playlists."""
    # Criterios básicos
    mode: GenerationMode
    target_length: int = 20
    allow_duplicates: bool = False
    
    # Seeds (según el modo)
    seed_artist: Optional[str] = None
    seed_genre: Optional[str] = None
    seed_track_path: Optional[str] = None
    
    # Filtros de características musicales
    tempo_range: Optional[Tuple[float, float]] = None
    energy_range: Optional[Tuple[float, float]] = None
    danceability_range: Optional[Tuple[float, float]] = None
    valence_range: Optional[Tuple[float, float]] = None
    acousticness_range: Optional[Tuple[float, float]] = None
    
    # Filtros tradicionales
    year_range: Optional[Tuple[int, int]] = None
    genres_include: Optional[List[str]] = None
    genres_exclude: Optional[List[str]] = None
    artists_exclude: Optional[List[str]] = None
    
    # Configuración avanzada
    similarity_threshold: float = 0.5
    diversity_factor: float = 0.3  # 0=máxima similitud, 1=máxima diversidad
    
    # Curvas de progresión (para modos avanzados)
    energy_curve_type: str = "flat"  # "flat", "ascending", "descending", "bell", "valley"
    bpm_progression_type: str = "stable"  # "stable", "ascending", "descending", "mixed"

@dataclass
class GeneratedPlaylist:
    """Resultado de generación de playlist."""
    tracks: List[Dict]
    generation_info: Dict
    similarity_scores: List[float]
    total_duration: float
    average_characteristics: Dict[str, float]

class SmartPlaylistGenerator:
    """
    Generador inteligente de playlists basado en características musicales.
    
    Features:
    - Múltiples modos de generación (seed, mood, progression)
    - Algoritmos de similitud avanzados
    - Filtros basados en características de audio
    - Progresiones de energía y BPM
    - Diversidad controlable
    - Templates de mood predefinidos
    """
    
    def __init__(self):
        self.audio_service = get_audio_enrichment_service()
        self.semantic_scorer = get_semantic_scorer()
        
        # Templates de mood predefinidos
        self.mood_templates = self._create_mood_templates()
        
        print("🎵 SmartPlaylistGenerator inicializado")
    
    def generate_playlist(self, criteria: GenerationCriteria) -> GeneratedPlaylist:
        """
        Genera una playlist basándose en los criterios especificados.
        
        Args:
            criteria: Criterios de generación
            
        Returns:
            GeneratedPlaylist con tracks seleccionados y metadata
        """
        print(f"🎯 Generando playlist: {criteria.mode.value} ({criteria.target_length} tracks)")
        
        # Obtener todos los tracks disponibles
        all_tracks = self._get_available_tracks()
        if not all_tracks:
            return GeneratedPlaylist([], {"error": "No tracks available"}, [], 0.0, {})
        
        # Filtrar tracks según criterios básicos
        candidate_tracks = self._filter_tracks_by_criteria(all_tracks, criteria)
        if not candidate_tracks:
            return GeneratedPlaylist([], {"error": "No tracks match criteria"}, [], 0.0, {})
        
        print(f"📊 {len(candidate_tracks)} tracks candidatos después de filtros")
        
        # Generar playlist según el modo
        if criteria.mode == GenerationMode.SEED_ARTIST:
            selected_tracks = self._generate_by_artist(candidate_tracks, criteria)
        elif criteria.mode == GenerationMode.SEED_GENRE:
            selected_tracks = self._generate_by_genre(candidate_tracks, criteria)
        elif criteria.mode == GenerationMode.SEED_TRACK:
            selected_tracks = self._generate_by_similarity(candidate_tracks, criteria)
        elif criteria.mode == GenerationMode.MOOD_BASED:
            selected_tracks = self._generate_by_mood(candidate_tracks, criteria)
        elif criteria.mode == GenerationMode.SIMILARITY_CHAIN:
            selected_tracks = self._generate_similarity_chain(candidate_tracks, criteria)
        elif criteria.mode == GenerationMode.BPM_PROGRESSION:
            selected_tracks = self._generate_bpm_progression(candidate_tracks, criteria)
        elif criteria.mode == GenerationMode.ENERGY_CURVE:
            selected_tracks = self._generate_energy_curve(candidate_tracks, criteria)
        else:
            selected_tracks = self._generate_random_selection(candidate_tracks, criteria)
        
        # Calcular información de la playlist generada
        generation_info = self._calculate_generation_info(selected_tracks, criteria)
        similarity_scores = self._calculate_similarity_scores(selected_tracks)
        total_duration = sum(track.get('duration', 0) for track in selected_tracks)
        avg_characteristics = self._calculate_average_characteristics(selected_tracks)
        
        print(f"✅ Playlist generada: {len(selected_tracks)} tracks, {total_duration/60:.1f} min")
        
        return GeneratedPlaylist(
            tracks=selected_tracks,
            generation_info=generation_info,
            similarity_scores=similarity_scores,
            total_duration=total_duration,
            average_characteristics=avg_characteristics
        )
    
    def _get_available_tracks(self) -> List[Dict]:
        """Obtiene todos los tracks disponibles de la base de datos."""
        try:
            return get_all_tracks()
        except Exception as e:
            print(f"❌ Error obteniendo tracks: {e}")
            return []
    
    def _filter_tracks_by_criteria(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Filtra tracks según criterios básicos."""
        filtered = []
        
        for track in tracks:
            # Filtros de rango de tempo
            if criteria.tempo_range:
                bpm = track.get('bpm')
                if not bpm or not (criteria.tempo_range[0] <= bpm <= criteria.tempo_range[1]):
                    continue
            
            # Filtros de características de audio
            if criteria.energy_range:
                energy = track.get('energy')
                if energy is None or not (criteria.energy_range[0] <= energy <= criteria.energy_range[1]):
                    continue
            
            if criteria.danceability_range:
                danceability = track.get('danceability')
                if danceability is None or not (criteria.danceability_range[0] <= danceability <= criteria.danceability_range[1]):
                    continue
            
            if criteria.valence_range:
                valence = track.get('valence')
                if valence is None or not (criteria.valence_range[0] <= valence <= criteria.valence_range[1]):
                    continue
            
            if criteria.acousticness_range:
                acousticness = track.get('acousticness')
                if acousticness is None or not (criteria.acousticness_range[0] <= acousticness <= criteria.acousticness_range[1]):
                    continue
            
            # Filtros de año
            if criteria.year_range:
                year = track.get('year')
                if not year or not (criteria.year_range[0] <= year <= criteria.year_range[1]):
                    continue
            
            # Filtros de género
            if criteria.genres_include:
                track_genres = track.get('genre', '').lower()
                if not any(genre.lower() in track_genres for genre in criteria.genres_include):
                    continue
            
            if criteria.genres_exclude:
                track_genres = track.get('genre', '').lower()
                if any(genre.lower() in track_genres for genre in criteria.genres_exclude):
                    continue
            
            # Filtros de artista
            if criteria.artists_exclude:
                track_artist = track.get('artist', '').lower()
                if any(artist.lower() in track_artist for artist in criteria.artists_exclude):
                    continue
            
            filtered.append(track)
        
        return filtered
    
    def _generate_by_artist(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Genera playlist basada en un artista semilla."""
        if not criteria.seed_artist:
            return self._generate_random_selection(tracks, criteria)
        
        # Encontrar tracks del artista semilla
        artist_tracks = [t for t in tracks if criteria.seed_artist.lower() in t.get('artist', '').lower()]
        
        if not artist_tracks:
            return self._generate_random_selection(tracks, criteria)
        
        # Seleccionar tracks del artista principal
        selected = []
        max_artist_tracks = min(criteria.target_length // 3, len(artist_tracks))
        selected.extend(random.sample(artist_tracks, max_artist_tracks))
        
        # Completar con artistas similares
        remaining = criteria.target_length - len(selected)
        if remaining > 0:
            # Usar género del artista para encontrar similares
            artist_genres = set()
            for track in artist_tracks:
                genres = track.get('genre', '').split(';')
                artist_genres.update(g.strip().lower() for g in genres if g.strip())
            
            similar_tracks = []
            for track in tracks:
                if track in selected:
                    continue
                track_genres = set(g.strip().lower() for g in track.get('genre', '').split(';') if g.strip())
                if artist_genres & track_genres:  # Intersección de géneros
                    similar_tracks.append(track)
            
            if similar_tracks:
                additional = min(remaining, len(similar_tracks))
                selected.extend(random.sample(similar_tracks, additional))
        
        return selected[:criteria.target_length]
    
    def _generate_by_genre(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Genera playlist basada en un género semilla."""
        if not criteria.seed_genre:
            return self._generate_random_selection(tracks, criteria)
        
        # Encontrar tracks del género específico
        genre_tracks = []
        for track in tracks:
            track_genres = track.get('genre', '').lower()
            if criteria.seed_genre.lower() in track_genres:
                genre_tracks.append(track)
        
        # Si hay pocos tracks exactos, buscar géneros relacionados
        if len(genre_tracks) < criteria.target_length:
            related_genres = self.semantic_scorer.find_related_genres(criteria.seed_genre, max_results=5)
            
            for genre_name, similarity in related_genres:
                if similarity > 0.5:  # Solo géneros muy relacionados
                    for track in tracks:
                        if track in genre_tracks:
                            continue
                        track_genres = track.get('genre', '').lower()
                        if genre_name.lower() in track_genres:
                            genre_tracks.append(track)
        
        if not genre_tracks:
            return self._generate_random_selection(tracks, criteria)
        
        # Seleccionar con diversidad controlada
        return self._select_with_diversity(genre_tracks, criteria)
    
    def _generate_by_similarity(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Genera playlist basada en similitud a un track semilla."""
        if not criteria.seed_track_path:
            return self._generate_random_selection(tracks, criteria)
        
        # Encontrar el track semilla
        seed_track = None
        for track in tracks:
            if track.get('file_path') == criteria.seed_track_path:
                seed_track = track
                break
        
        if not seed_track:
            return self._generate_random_selection(tracks, criteria)
        
        # Calcular similitudes con todos los tracks
        similarities = []
        for track in tracks:
            if track == seed_track:
                continue
            
            similarity = self.audio_service.calculate_tracks_similarity(
                criteria.seed_track_path, track.get('file_path')
            )
            
            if similarity is not None and similarity >= criteria.similarity_threshold:
                similarities.append((track, similarity))
        
        # Ordenar por similitud
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Seleccionar con diversidad
        selected = [seed_track]
        for track, sim in similarities:
            if len(selected) >= criteria.target_length:
                break
            
            # Verificar diversidad si está activada
            if criteria.diversity_factor > 0:
                if self._is_diverse_enough(track, selected, criteria.diversity_factor):
                    selected.append(track)
            else:
                selected.append(track)
        
        return selected[:criteria.target_length]
    
    def _generate_by_mood(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Genera playlist basada en un mood específico."""
        # Esta función se puede expandir para usar mood templates predefinidos
        # Por ahora, usar filtros de características existentes
        return self._select_with_diversity(tracks, criteria)
    
    def _generate_similarity_chain(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Genera playlist como cadena de similitud (cada track similar al anterior)."""
        if not tracks:
            return []
        
        # Empezar con track aleatorio o semilla
        if criteria.seed_track_path:
            current_track = None
            for track in tracks:
                if track.get('file_path') == criteria.seed_track_path:
                    current_track = track
                    break
            if not current_track:
                current_track = random.choice(tracks)
        else:
            current_track = random.choice(tracks)
        
        selected = [current_track]
        available = [t for t in tracks if t != current_track]
        
        while len(selected) < criteria.target_length and available:
            # Encontrar el más similar al último añadido
            similarities = []
            current_path = selected[-1].get('file_path')
            
            for track in available:
                similarity = self.audio_service.calculate_tracks_similarity(
                    current_path, track.get('file_path')
                )
                if similarity is not None:
                    similarities.append((track, similarity))
            
            if not similarities:
                break
            
            # Seleccionar entre los más similares con algo de randomness
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_candidates = similarities[:min(5, len(similarities))]
            
            # Aplicar factor de diversidad
            if criteria.diversity_factor > 0:
                # Mezclar similitud con diversidad
                weights = []
                for track, sim in top_candidates:
                    diversity_bonus = criteria.diversity_factor * (1 - sim)
                    final_score = sim + diversity_bonus
                    weights.append(final_score)
                
                # Selección ponderada
                total_weight = sum(weights)
                if total_weight > 0:
                    r = random.uniform(0, total_weight)
                    cumulative = 0
                    for i, weight in enumerate(weights):
                        cumulative += weight
                        if r <= cumulative:
                            next_track = top_candidates[i][0]
                            break
                    else:
                        next_track = top_candidates[0][0]
                else:
                    next_track = top_candidates[0][0]
            else:
                next_track = top_candidates[0][0]
            
            selected.append(next_track)
            available.remove(next_track)
        
        return selected
    
    def _generate_bpm_progression(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Genera playlist con progresión de BPM."""
        # Filtrar tracks que tienen BPM
        bpm_tracks = [t for t in tracks if t.get('bpm')]
        if not bpm_tracks:
            return self._generate_random_selection(tracks, criteria)
        
        # Ordenar por BPM
        bpm_tracks.sort(key=lambda x: x.get('bpm', 0))
        
        if criteria.bpm_progression_type == "ascending":
            # BPM ascendente
            selected = bpm_tracks[:criteria.target_length]
        elif criteria.bpm_progression_type == "descending":
            # BPM descendente
            selected = bpm_tracks[::-1][:criteria.target_length]
        else:
            # BPM estable (rango estrecho)
            # Encontrar BPM promedio y seleccionar alrededor de ese valor
            avg_bpm = sum(t.get('bpm', 0) for t in bpm_tracks) / len(bpm_tracks)
            tolerance = 10  # ±10 BPM
            
            stable_tracks = [
                t for t in bpm_tracks 
                if abs(t.get('bpm', 0) - avg_bpm) <= tolerance
            ]
            
            if len(stable_tracks) >= criteria.target_length:
                selected = random.sample(stable_tracks, criteria.target_length)
            else:
                selected = stable_tracks + random.sample(
                    [t for t in bpm_tracks if t not in stable_tracks],
                    criteria.target_length - len(stable_tracks)
                )
        
        return selected[:criteria.target_length]
    
    def _generate_energy_curve(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Genera playlist con curva de energía específica."""
        # Filtrar tracks que tienen energía analizada
        energy_tracks = [t for t in tracks if t.get('energy') is not None]
        if not energy_tracks:
            return self._generate_random_selection(tracks, criteria)
        
        # Crear curva de energía objetivo
        target_energies = self._create_energy_curve(criteria.target_length, criteria.energy_curve_type)
        
        # Asignar tracks a cada punto de la curva
        selected = []
        used_tracks = set()
        
        for target_energy in target_energies:
            # Encontrar track con energía más cercana
            best_track = None
            best_diff = float('inf')
            
            for track in energy_tracks:
                if track.get('file_path') in used_tracks:
                    continue
                
                energy = track.get('energy', 0)
                diff = abs(energy - target_energy)
                
                if diff < best_diff:
                    best_diff = diff
                    best_track = track
            
            if best_track:
                selected.append(best_track)
                used_tracks.add(best_track.get('file_path'))
        
        return selected
    
    def _generate_random_selection(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Genera selección aleatoria como fallback."""
        if len(tracks) <= criteria.target_length:
            return tracks
        
        return random.sample(tracks, criteria.target_length)
    
    def _select_with_diversity(self, tracks: List[Dict], criteria: GenerationCriteria) -> List[Dict]:
        """Selecciona tracks aplicando factor de diversidad."""
        if len(tracks) <= criteria.target_length:
            return tracks
        
        if criteria.diversity_factor == 0:
            return random.sample(tracks, criteria.target_length)
        
        # Algoritmo de selección diversa
        selected = [random.choice(tracks)]
        available = [t for t in tracks if t != selected[0]]
        
        while len(selected) < criteria.target_length and available:
            # Calcular score de diversidad para cada candidato
            diversity_scores = []
            
            for candidate in available:
                # Calcular similitud promedio con tracks ya seleccionados
                similarities = []
                candidate_path = candidate.get('file_path')
                
                for selected_track in selected:
                    selected_path = selected_track.get('file_path')
                    sim = self.audio_service.calculate_tracks_similarity(candidate_path, selected_path)
                    if sim is not None:
                        similarities.append(sim)
                
                if similarities:
                    avg_similarity = sum(similarities) / len(similarities)
                    # Diversidad = 1 - similitud promedio
                    diversity_score = 1 - avg_similarity
                else:
                    diversity_score = 1.0  # Máxima diversidad si no hay datos
                
                diversity_scores.append((candidate, diversity_score))
            
            # Seleccionar basándose en diversidad ponderada
            diversity_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Selección con algo de randomness
            top_diverse = diversity_scores[:min(5, len(diversity_scores))]
            next_track = random.choice(top_diverse)[0]
            
            selected.append(next_track)
            available.remove(next_track)
        
        return selected
    
    def _is_diverse_enough(self, candidate: Dict, selected: List[Dict], diversity_factor: float) -> bool:
        """Verifica si un candidato es suficientemente diverso."""
        if not selected:
            return True
        
        # Calcular similitud promedio con tracks seleccionados
        similarities = []
        candidate_path = candidate.get('file_path')
        
        for track in selected:
            sim = self.audio_service.calculate_tracks_similarity(candidate_path, track.get('file_path'))
            if sim is not None:
                similarities.append(sim)
        
        if not similarities:
            return True
        
        avg_similarity = sum(similarities) / len(similarities)
        diversity_threshold = 1 - diversity_factor
        
        return avg_similarity < diversity_threshold
    
    def _create_energy_curve(self, length: int, curve_type: str) -> List[float]:
        """Crea una curva de energía objetivo."""
        if curve_type == "ascending":
            return [i / (length - 1) for i in range(length)]
        elif curve_type == "descending":
            return [(length - 1 - i) / (length - 1) for i in range(length)]
        elif curve_type == "bell":
            # Curva de campana
            curve = []
            for i in range(length):
                x = (i / (length - 1)) * 2 - 1  # -1 a 1
                y = math.exp(-(x**2))  # Gaussiana
                curve.append(y)
            return curve
        elif curve_type == "valley":
            # Curva de valle (inverso de campana)
            bell = self._create_energy_curve(length, "bell")
            return [1 - y for y in bell]
        else:  # "flat"
            return [0.5] * length
    
    def _calculate_generation_info(self, tracks: List[Dict], criteria: GenerationCriteria) -> Dict:
        """Calcula información sobre la generación."""
        return {
            "mode": criteria.mode.value,
            "criteria_used": {
                "target_length": criteria.target_length,
                "similarity_threshold": criteria.similarity_threshold,
                "diversity_factor": criteria.diversity_factor,
                "seed_artist": criteria.seed_artist,
                "seed_genre": criteria.seed_genre,
                "tempo_range": criteria.tempo_range,
                "energy_range": criteria.energy_range
            },
            "tracks_generated": len(tracks),
            "generation_timestamp": __import__('time').time()
        }
    
    def _calculate_similarity_scores(self, tracks: List[Dict]) -> List[float]:
        """Calcula scores de similitud entre tracks consecutivos."""
        if len(tracks) < 2:
            return []
        
        similarities = []
        for i in range(len(tracks) - 1):
            sim = self.audio_service.calculate_tracks_similarity(
                tracks[i].get('file_path'),
                tracks[i + 1].get('file_path')
            )
            similarities.append(sim if sim is not None else 0.0)
        
        return similarities
    
    def _calculate_average_characteristics(self, tracks: List[Dict]) -> Dict[str, float]:
        """Calcula características promedio de la playlist."""
        characteristics = ['energy', 'danceability', 'valence', 'acousticness', 'bpm']
        averages = {}
        
        for char in characteristics:
            values = [t.get(char) for t in tracks if t.get(char) is not None]
            if values:
                averages[char] = sum(values) / len(values)
            else:
                averages[char] = None
        
        return averages
    
    def _create_mood_templates(self) -> Dict[str, GenerationCriteria]:
        """Crea templates predefinidos para diferentes moods."""
        return {
            "workout": GenerationCriteria(
                mode=GenerationMode.MOOD_BASED,
                energy_range=(0.7, 1.0),
                danceability_range=(0.6, 1.0),
                tempo_range=(120, 160)
            ),
            "chill": GenerationCriteria(
                mode=GenerationMode.MOOD_BASED,
                energy_range=(0.0, 0.4),
                valence_range=(0.3, 0.8),
                acousticness_range=(0.3, 1.0),
                tempo_range=(60, 110)
            ),
            "party": GenerationCriteria(
                mode=GenerationMode.MOOD_BASED,
                energy_range=(0.8, 1.0),
                danceability_range=(0.8, 1.0),
                valence_range=(0.7, 1.0),
                tempo_range=(120, 140)
            ),
            "focus": GenerationCriteria(
                mode=GenerationMode.MOOD_BASED,
                instrumentalness_range=(0.7, 1.0),
                energy_range=(0.3, 0.7),
                valence_range=(0.4, 0.8)
            ),
            "melancholic": GenerationCriteria(
                mode=GenerationMode.MOOD_BASED,
                valence_range=(0.0, 0.3),
                energy_range=(0.0, 0.5),
                acousticness_range=(0.4, 1.0)
            )
        }
    
    def get_mood_template(self, mood: str) -> Optional[GenerationCriteria]:
        """Obtiene un template de mood predefinido."""
        return self.mood_templates.get(mood.lower())
    
    def get_available_moods(self) -> List[str]:
        """Obtiene lista de moods disponibles."""
        return list(self.mood_templates.keys())

# Instancia global
_smart_playlist_generator = None

def get_smart_playlist_generator() -> SmartPlaylistGenerator:
    """Obtiene la instancia global del generador de playlists."""
    global _smart_playlist_generator
    if _smart_playlist_generator is None:
        _smart_playlist_generator = SmartPlaylistGenerator()
    return _smart_playlist_generator

# Funciones de conveniencia
def generate_smart_playlist(criteria: GenerationCriteria) -> GeneratedPlaylist:
    """Genera una playlist inteligente."""
    return get_smart_playlist_generator().generate_playlist(criteria)

def get_mood_playlist(mood: str, length: int = 20) -> GeneratedPlaylist:
    """Genera playlist basada en mood predefinido."""
    generator = get_smart_playlist_generator()
    template = generator.get_mood_template(mood)
    if template:
        template.target_length = length
        return generator.generate_playlist(template)
    else:
        # Fallback a criterios básicos
        criteria = GenerationCriteria(mode=GenerationMode.MOOD_BASED, target_length=length)
        return generator.generate_playlist(criteria)

def get_similar_playlist(seed_track_path: str, length: int = 20, similarity: float = 0.5) -> GeneratedPlaylist:
    """Genera playlist similar a un track específico."""
    criteria = GenerationCriteria(
        mode=GenerationMode.SEED_TRACK,
        seed_track_path=seed_track_path,
        target_length=length,
        similarity_threshold=similarity
    )
    return get_smart_playlist_generator().generate_playlist(criteria)