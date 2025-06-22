# core/genre_confidence_scorer.py

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import math

@dataclass
class GenreScore:
    """Representa un género con su puntuación de confianza."""
    genre: str
    confidence: float
    sources: List[str]
    consensus_score: float
    quality_score: float

@dataclass 
class SourceData:
    """Datos de género de una fuente específica."""
    source: str
    genres: List[str]
    metadata: Dict
    raw_confidence: float = 0.0

class GenreConfidenceScorer:
    """
    Sistema de scoring de confianza para géneros musicales basado en múltiples fuentes API.
    Calcula confianza basándose en consenso entre fuentes, calidad de datos y características específicas de cada API.
    """
    
    # Pesos base por fuente (pueden ajustarse dinámicamente)
    SOURCE_BASE_WEIGHTS = {
        'musicbrainz': 0.90,  # Muy confiable, datos técnicos precisos
        'spotify': 0.85,      # Alta confianza, géneros modernos/comerciales  
        'discogs': 0.80,      # Buena para géneros específicos/underground
        'lastfm': 0.70,       # Folksonómico, puede ser inconsistente
        'local': 0.60         # Tags locales, calidad variable
    }
    
    # Géneros que indican alta confianza por su especificidad
    HIGH_CONFIDENCE_GENRES = {
        'progressive house', 'deep house', 'tech house', 'minimal techno',
        'drum and bass', 'liquid dnb', 'neurofunk', 'jump up',
        'trance', 'uplifting trance', 'progressive trance', 'psytrance',
        'dubstep', 'melodic dubstep', 'riddim', 'future bass',
        'hardcore', 'gabber', 'speedcore', 'breakcore',
        'ambient', 'dark ambient', 'drone', 'field recording',
        'jazz fusion', 'bebop', 'hard bop', 'free jazz',
        'black metal', 'death metal', 'thrash metal', 'doom metal',
        'post rock', 'post punk', 'shoegaze', 'dream pop',
        'acid house', 'chicago house', 'detroit techno', 'uk garage'
    }
    
    # Géneros genéricos que reducen confianza
    LOW_CONFIDENCE_GENRES = {
        'electronic', 'rock', 'pop', 'dance', 'alternative', 'indie',
        'experimental', 'various', 'other', 'music', 'sound', 'audio'
    }
    
    def __init__(self):
        self.genre_frequency = defaultdict(int)
        self.source_reliability = dict(self.SOURCE_BASE_WEIGHTS)
        
    def calculate_source_confidence(self, source_data: SourceData) -> float:
        """
        Calcula la confianza de una fuente específica basándose en la calidad de sus datos.
        """
        if not source_data.genres:
            return 0.0
            
        base_weight = self.SOURCE_BASE_WEIGHTS.get(source_data.source, 0.5)
        
        # Factor de cantidad: más géneros específicos = mayor confianza
        quantity_factor = min(len(source_data.genres) / 5.0, 1.0)
        
        # Factor de calidad: géneros específicos vs genéricos
        quality_score = 0.0
        for genre in source_data.genres:
            genre_lower = genre.lower().strip()
            
            if genre_lower in self.HIGH_CONFIDENCE_GENRES:
                quality_score += 1.5
            elif genre_lower in self.LOW_CONFIDENCE_GENRES:
                quality_score += 0.3
            elif len(genre_lower) > 8 and ' ' in genre_lower:  # Géneros compuestos
                quality_score += 1.2
            elif len(genre_lower) > 4:  # Géneros específicos
                quality_score += 1.0
            else:  # Géneros cortos/genéricos
                quality_score += 0.5
                
        quality_factor = min(quality_score / len(source_data.genres), 1.5)
        
        # Factor de metadatos: más información = mayor confianza
        metadata_factor = 1.0
        if source_data.metadata:
            # Bonificación por tener IDs específicos de la fuente
            if any(f"{source_data.source}_" in key for key in source_data.metadata.keys()):
                metadata_factor += 0.1
            # Bonificación por tener información de álbum/artista
            if source_data.metadata.get('album') and source_data.metadata.get('artist'):
                metadata_factor += 0.1
                
        final_confidence = base_weight * quantity_factor * quality_factor * metadata_factor
        return min(final_confidence, 1.0)
    
    def calculate_consensus_score(self, genre: str, sources: List[str]) -> float:
        """
        Calcula puntuación de consenso basándose en cuántas fuentes mencionan el género.
        """
        if not sources:
            return 0.0
            
        # Consenso básico: más fuentes = mayor confianza
        consensus_base = len(sources) / len(self.SOURCE_BASE_WEIGHTS)
        
        # Bonificación por diversidad de fuentes
        source_diversity = len(set(sources)) / len(sources) if sources else 0
        
        # Bonificación por fuentes de alta confianza
        high_confidence_sources = sum(1 for src in sources 
                                    if self.SOURCE_BASE_WEIGHTS.get(src, 0) > 0.8)
        confidence_bonus = high_confidence_sources / len(sources) if sources else 0
        
        consensus_score = (consensus_base * 0.6 + 
                          source_diversity * 0.2 + 
                          confidence_bonus * 0.2)
        
        return min(consensus_score, 1.0)
    
    def calculate_genre_quality(self, genre: str) -> float:
        """
        Evalúa la calidad intrínseca de un género musical.
        """
        genre_lower = genre.lower().strip()
        
        # Géneros altamente específicos
        if genre_lower in self.HIGH_CONFIDENCE_GENRES:
            return 1.0
            
        # Géneros genéricos
        if genre_lower in self.LOW_CONFIDENCE_GENRES:
            return 0.3
            
        # Evaluación heurística
        quality_score = 0.5  # Base
        
        # Bonificación por longitud y complejidad
        if len(genre_lower) > 10:
            quality_score += 0.2
        elif len(genre_lower) > 6:
            quality_score += 0.1
            
        # Bonificación por géneros compuestos
        if ' ' in genre_lower or '-' in genre_lower:
            quality_score += 0.2
            
        # Penalización por números/años
        if re.search(r'\d{4}s?|\d{2}s', genre_lower):
            quality_score -= 0.1
            
        # Bonificación por términos técnicos musicales
        technical_terms = ['progressive', 'deep', 'minimal', 'ambient', 'fusion', 'experimental']
        if any(term in genre_lower for term in technical_terms):
            quality_score += 0.15
            
        return min(max(quality_score, 0.0), 1.0)
    
    def score_genres(self, sources_data: List[SourceData]) -> List[GenreScore]:
        """
        Procesa datos de múltiples fuentes y genera scores de confianza para géneros.
        """
        if not sources_data:
            return []
            
        # Recopilar todos los géneros y sus fuentes
        genre_sources = defaultdict(list)
        genre_confidences = defaultdict(list)
        
        for source_data in sources_data:
            source_confidence = self.calculate_source_confidence(source_data)
            
            for genre in source_data.genres:
                genre_clean = genre.strip()
                if genre_clean:
                    genre_sources[genre_clean].append(source_data.source)
                    genre_confidences[genre_clean].append(source_confidence)
        
        # Calcular scores finales
        scored_genres = []
        
        for genre, sources in genre_sources.items():
            # Scores individuales
            consensus_score = self.calculate_consensus_score(genre, sources)
            quality_score = self.calculate_genre_quality(genre)
            
            # Confianza promedio ponderada de las fuentes
            source_confidence_avg = sum(genre_confidences[genre]) / len(genre_confidences[genre])
            
            # Score final combinado
            final_confidence = (consensus_score * 0.4 + 
                              quality_score * 0.35 + 
                              source_confidence_avg * 0.25)
            
            scored_genres.append(GenreScore(
                genre=genre,
                confidence=final_confidence,
                sources=list(set(sources)),  # Remover duplicados
                consensus_score=consensus_score,
                quality_score=quality_score
            ))
        
        # Ordenar por confianza descendente
        scored_genres.sort(key=lambda x: x.confidence, reverse=True)
        
        return scored_genres
    
    def get_top_genres(self, sources_data: List[SourceData], max_genres: int = 4) -> List[str]:
        """
        Retorna los mejores géneros basándose en scoring de confianza.
        """
        scored_genres = self.score_genres(sources_data)
        
        # Filtrar por confianza mínima
        MIN_CONFIDENCE = 0.3
        high_confidence_genres = [g for g in scored_genres if g.confidence >= MIN_CONFIDENCE]
        
        # Tomar los mejores hasta max_genres
        top_genres = high_confidence_genres[:max_genres]
        
        return [genre.genre for genre in top_genres]
    
    def update_source_reliability(self, source: str, performance_score: float):
        """
        Actualiza la confiabilidad de una fuente basándose en su rendimiento histórico.
        """
        if source in self.source_reliability:
            # Ajuste gradual basado en rendimiento
            current = self.source_reliability[source]
            adjustment = (performance_score - current) * 0.1  # Factor de aprendizaje conservador
            self.source_reliability[source] = max(0.1, min(1.0, current + adjustment))
    
    def get_scoring_report(self, sources_data: List[SourceData]) -> Dict:
        """
        Genera un reporte detallado del proceso de scoring.
        """
        scored_genres = self.score_genres(sources_data)
        
        return {
            'total_genres_found': len(scored_genres),
            'high_confidence_count': len([g for g in scored_genres if g.confidence > 0.7]),
            'medium_confidence_count': len([g for g in scored_genres if 0.4 <= g.confidence <= 0.7]),
            'low_confidence_count': len([g for g in scored_genres if g.confidence < 0.4]),
            'sources_used': list(set(sd.source for sd in sources_data)),
            'top_genres': [(g.genre, f"{g.confidence:.2f}") for g in scored_genres[:10]],
            'consensus_genres': [g.genre for g in scored_genres if len(g.sources) > 1][:5]
        }