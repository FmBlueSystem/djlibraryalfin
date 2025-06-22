# core/semantic_genre_scorer.py

import re
import math
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import difflib

@dataclass
class GenreRelation:
    """Relación semántica entre géneros."""
    genre_a: str
    genre_b: str
    similarity: float
    relation_type: str  # parent, child, sibling, variant
    confidence: float

@dataclass 
class GenreSemantics:
    """Semántica de un género específico."""
    name: str
    normalized_name: str
    category: str  # electronic, rock, jazz, etc.
    subcategory: str  # house, metal, bebop, etc.
    characteristics: List[str]  # dance, aggressive, melodic, etc.
    tempo_range: Tuple[int, int]  # BPM range
    parent_genres: List[str]
    child_genres: List[str]
    related_genres: List[str]
    aliases: List[str]
    weight: float  # Peso general del género

class SemanticGenreScorer:
    """
    Sistema de scoring semántico que entiende relaciones entre géneros musicales.
    
    Features:
    - Base de conocimiento de géneros musicales
    - Análisis de similitud semántica
    - Detección de jerarquías (house -> deep house)
    - Resolución de aliases (drum n bass = dnb)
    - Scoring basado en contexto musical
    - Machine learning básico para preferencias
    """
    
    def __init__(self):
        self.genre_knowledge = self._build_genre_knowledge_base()
        self.similarity_cache: Dict[Tuple[str, str], float] = {}
        self.user_preferences: Dict[str, float] = {}  # Aprendizaje de preferencias
        self.genre_frequency: Dict[str, int] = defaultdict(int)  # Tracking de uso
        
        # Weights para diferentes factores de scoring
        self.scoring_weights = {
            'exact_match': 1.0,
            'semantic_similarity': 0.8,
            'parent_child': 0.6,
            'sibling_relation': 0.4,
            'category_match': 0.3,
            'user_preference': 0.5,
            'frequency_bonus': 0.2
        }
    
    def _build_genre_knowledge_base(self) -> Dict[str, GenreSemantics]:
        """Construye base de conocimiento de géneros musicales."""
        knowledge = {}
        
        # Electronic genres
        electronic_genres = {
            'house': GenreSemantics(
                name='House',
                normalized_name='house',
                category='electronic',
                subcategory='house',
                characteristics=['dance', 'four-on-floor', 'repetitive'],
                tempo_range=(120, 130),
                parent_genres=['electronic'],
                child_genres=['deep house', 'tech house', 'progressive house', 'funky house'],
                related_genres=['techno', 'disco'],
                aliases=['house music'],
                weight=0.9
            ),
            'deep house': GenreSemantics(
                name='Deep House',
                normalized_name='deep house',
                category='electronic',
                subcategory='house',
                characteristics=['deep', 'soulful', 'atmospheric', 'warm'],
                tempo_range=(120, 125),
                parent_genres=['house', 'electronic'],
                child_genres=[],
                related_genres=['tech house', 'progressive house'],
                aliases=['deep'],
                weight=0.95
            ),
            'tech house': GenreSemantics(
                name='Tech House',
                normalized_name='tech house',
                category='electronic',
                subcategory='house',
                characteristics=['techno', 'minimal', 'driving', 'underground'],
                tempo_range=(123, 130),
                parent_genres=['house', 'techno'],
                child_genres=[],
                related_genres=['deep house', 'minimal techno'],
                aliases=['tech-house'],
                weight=0.9
            ),
            'progressive house': GenreSemantics(
                name='Progressive House',
                normalized_name='progressive house',
                category='electronic',
                subcategory='house',
                characteristics=['progressive', 'emotional', 'build-up', 'epic'],
                tempo_range=(125, 132),
                parent_genres=['house', 'progressive'],
                child_genres=[],
                related_genres=['trance', 'deep house'],
                aliases=['prog house'],
                weight=0.85
            ),
            'techno': GenreSemantics(
                name='Techno',
                normalized_name='techno',
                category='electronic',
                subcategory='techno',
                characteristics=['repetitive', 'industrial', 'minimalist', 'driving'],
                tempo_range=(120, 150),
                parent_genres=['electronic'],
                child_genres=['minimal techno', 'detroit techno', 'acid techno'],
                related_genres=['house', 'electro'],
                aliases=['techno music'],
                weight=0.9
            ),
            'trance': GenreSemantics(
                name='Trance',
                normalized_name='trance',
                category='electronic',
                subcategory='trance',
                characteristics=['emotional', 'melodic', 'uplifting', 'hypnotic'],
                tempo_range=(128, 140),
                parent_genres=['electronic'],
                child_genres=['uplifting trance', 'progressive trance', 'psytrance'],
                related_genres=['progressive house', 'eurodance'],
                aliases=['trance music'],
                weight=0.85
            ),
            'drum and bass': GenreSemantics(
                name='Drum & Bass',
                normalized_name='drum and bass',
                category='electronic',
                subcategory='breakbeat',
                characteristics=['fast', 'breakbeat', 'bass-heavy', 'syncopated'],
                tempo_range=(160, 180),
                parent_genres=['electronic', 'jungle'],
                child_genres=['liquid dnb', 'neurofunk', 'jump up'],
                related_genres=['dubstep', 'breakbeat'],
                aliases=['dnb', 'drum n bass', 'drum & bass'],
                weight=0.9
            ),
            'dubstep': GenreSemantics(
                name='Dubstep',
                normalized_name='dubstep',
                category='electronic',
                subcategory='bass',
                characteristics=['wobble', 'bass-heavy', 'syncopated', 'aggressive'],
                tempo_range=(140, 150),
                parent_genres=['electronic', 'garage'],
                child_genres=['melodic dubstep', 'riddim', 'brostep'],
                related_genres=['drum and bass', 'garage'],
                aliases=['dub step'],
                weight=0.8
            )
        }
        
        # Rock genres
        rock_genres = {
            'rock': GenreSemantics(
                name='Rock',
                normalized_name='rock',
                category='rock',
                subcategory='rock',
                characteristics=['guitar-driven', 'rhythmic', 'energetic'],
                tempo_range=(80, 200),
                parent_genres=[],
                child_genres=['hard rock', 'alternative rock', 'progressive rock', 'indie rock'],
                related_genres=['pop', 'metal'],
                aliases=['rock music'],
                weight=0.8
            ),
            'alternative rock': GenreSemantics(
                name='Alternative Rock',
                normalized_name='alternative rock',
                category='rock',
                subcategory='alternative',
                characteristics=['alternative', 'indie', 'non-mainstream'],
                tempo_range=(90, 160),
                parent_genres=['rock'],
                child_genres=['grunge', 'britpop'],
                related_genres=['indie rock', 'punk'],
                aliases=['alt rock', 'alternative'],
                weight=0.85
            ),
            'progressive rock': GenreSemantics(
                name='Progressive Rock',
                normalized_name='progressive rock',
                category='rock',
                subcategory='progressive',
                characteristics=['complex', 'experimental', 'long compositions'],
                tempo_range=(60, 180),
                parent_genres=['rock'],
                child_genres=['art rock', 'post rock'],
                related_genres=['progressive metal', 'jazz fusion'],
                aliases=['prog rock', 'prog'],
                weight=0.8
            )
        }
        
        # Jazz genres
        jazz_genres = {
            'jazz': GenreSemantics(
                name='Jazz',
                normalized_name='jazz',
                category='jazz',
                subcategory='jazz',
                characteristics=['improvisation', 'complex harmony', 'swing'],
                tempo_range=(60, 300),
                parent_genres=[],
                child_genres=['bebop', 'smooth jazz', 'fusion', 'free jazz'],
                related_genres=['blues', 'classical'],
                aliases=['jazz music'],
                weight=0.9
            ),
            'bebop': GenreSemantics(
                name='Bebop',
                normalized_name='bebop',
                category='jazz',
                subcategory='bebop',
                characteristics=['fast', 'complex', 'improvisation', 'virtuosic'],
                tempo_range=(120, 300),
                parent_genres=['jazz'],
                child_genres=['hard bop'],
                related_genres=['cool jazz', 'swing'],
                aliases=['bop'],
                weight=0.95
            )
        }
        
        # Pop genres
        pop_genres = {
            'pop': GenreSemantics(
                name='Pop',
                normalized_name='pop',
                category='pop',
                subcategory='pop',
                characteristics=['catchy', 'mainstream', 'accessible'],
                tempo_range=(60, 140),
                parent_genres=[],
                child_genres=['pop rock', 'dance pop', 'electropop'],
                related_genres=['rock', 'electronic'],
                aliases=['pop music'],
                weight=0.7
            ),
            'art pop': GenreSemantics(
                name='Art Pop',
                normalized_name='art pop',
                category='pop',
                subcategory='art',
                characteristics=['artistic', 'experimental', 'avant-garde'],
                tempo_range=(70, 130),
                parent_genres=['pop'],
                child_genres=[],
                related_genres=['alternative rock', 'progressive rock'],
                aliases=['artpop'],
                weight=0.85
            )
        }
        
        # Combinar todas las categorías
        all_genres = {}
        all_genres.update(electronic_genres)
        all_genres.update(rock_genres)
        all_genres.update(jazz_genres)
        all_genres.update(pop_genres)
        
        # Añadir géneros adicionales por normalización
        for genre_key, genre_data in list(all_genres.items()):
            # Añadir aliases como entradas separadas
            for alias in genre_data.aliases:
                alias_normalized = self._normalize_genre_name(alias)
                if alias_normalized not in all_genres:
                    all_genres[alias_normalized] = genre_data
        
        return all_genres
    
    def _normalize_genre_name(self, genre: str) -> str:
        """Normaliza nombre de género para comparación."""
        if not genre:
            return ""
        
        # Convertir a minúsculas y limpiar
        normalized = genre.lower().strip()
        
        # Remover caracteres especiales comunes
        normalized = re.sub(r'[^\w\s&-]', '', normalized)
        
        # Normalizar espacios y guiones
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.replace(' and ', ' & ')
        normalized = normalized.replace(' n ', ' & ')
        
        # Mapeos específicos comunes
        mappings = {
            'drum n bass': 'drum and bass',
            'drum & bass': 'drum and bass',
            'dnb': 'drum and bass',
            'edm': 'electronic dance music',
            'idm': 'intelligent dance music',
            'r&b': 'rhythm and blues',
            'rnb': 'rhythm and blues',
            'hip hop': 'hip-hop',
            'hiphop': 'hip-hop'
        }
        
        return mappings.get(normalized, normalized)
    
    def calculate_semantic_similarity(self, genre1: str, genre2: str) -> float:
        """
        Calcula similitud semántica entre dos géneros.
        
        Args:
            genre1: Primer género
            genre2: Segundo género
            
        Returns:
            Similitud entre 0.0 y 1.0
        """
        if not genre1 or not genre2:
            return 0.0
        
        # Usar cache si disponible
        cache_key = tuple(sorted([genre1.lower(), genre2.lower()]))
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Normalizar géneros
        norm1 = self._normalize_genre_name(genre1)
        norm2 = self._normalize_genre_name(genre2)
        
        # Exact match
        if norm1 == norm2:
            similarity = 1.0
        else:
            similarity = self._calculate_advanced_similarity(norm1, norm2)
        
        # Guardar en cache
        self.similarity_cache[cache_key] = similarity
        return similarity
    
    def _calculate_advanced_similarity(self, genre1: str, genre2: str) -> float:
        """Calcula similitud avanzada entre géneros."""
        # Obtener semántica de géneros
        sem1 = self.genre_knowledge.get(genre1)
        sem2 = self.genre_knowledge.get(genre2)
        
        similarity_factors = []
        
        # 1. Similitud léxica básica
        lexical_sim = difflib.SequenceMatcher(None, genre1, genre2).ratio()
        similarity_factors.append(('lexical', lexical_sim, 0.3))
        
        if sem1 and sem2:
            # 2. Relación jerárquica
            hierarchy_sim = self._calculate_hierarchy_similarity(sem1, sem2)
            similarity_factors.append(('hierarchy', hierarchy_sim, 0.4))
            
            # 3. Categoría/subcategoría
            category_sim = self._calculate_category_similarity(sem1, sem2)
            similarity_factors.append(('category', category_sim, 0.2))
            
            # 4. Características compartidas
            char_sim = self._calculate_characteristics_similarity(sem1, sem2)
            similarity_factors.append(('characteristics', char_sim, 0.1))
        
        # Calcular promedio ponderado
        total_weight = sum(weight for _, _, weight in similarity_factors)
        if total_weight > 0:
            weighted_sum = sum(sim * weight for _, sim, weight in similarity_factors)
            return weighted_sum / total_weight
        
        return lexical_sim
    
    def _calculate_hierarchy_similarity(self, sem1: GenreSemantics, sem2: GenreSemantics) -> float:
        """Calcula similitud basada en jerarquía de géneros."""
        # Parent-child relation
        if sem1.normalized_name in sem2.parent_genres or sem2.normalized_name in sem1.parent_genres:
            return 0.8
        if sem1.normalized_name in sem2.child_genres or sem2.normalized_name in sem1.child_genres:
            return 0.8
        
        # Sibling relation (mismos padres)
        shared_parents = set(sem1.parent_genres) & set(sem2.parent_genres)
        if shared_parents:
            return 0.6
        
        # Related genres
        if sem1.normalized_name in sem2.related_genres or sem2.normalized_name in sem1.related_genres:
            return 0.4
        
        return 0.0
    
    def _calculate_category_similarity(self, sem1: GenreSemantics, sem2: GenreSemantics) -> float:
        """Calcula similitud basada en categorías."""
        if sem1.category == sem2.category:
            if sem1.subcategory == sem2.subcategory:
                return 1.0
            else:
                return 0.6
        return 0.0
    
    def _calculate_characteristics_similarity(self, sem1: GenreSemantics, sem2: GenreSemantics) -> float:
        """Calcula similitud basada en características musicales."""
        chars1 = set(sem1.characteristics)
        chars2 = set(sem2.characteristics)
        
        if not chars1 or not chars2:
            return 0.0
        
        intersection = len(chars1 & chars2)
        union = len(chars1 | chars2)
        
        return intersection / union if union > 0 else 0.0
    
    def score_genre_list(self, genres: List[str], context: Dict = None) -> List[Tuple[str, float]]:
        """
        Puntúa una lista de géneros considerando contexto y semántica.
        
        Args:
            genres: Lista de géneros a puntuar
            context: Contexto adicional (artista, album, etc.)
            
        Returns:
            Lista de tuplas (género, score) ordenada por score
        """
        if not genres:
            return []
        
        scored_genres = []
        
        for genre in genres:
            score = self._calculate_genre_score(genre, genres, context)
            scored_genres.append((genre, score))
        
        # Ordenar por score descendente
        scored_genres.sort(key=lambda x: x[1], reverse=True)
        
        return scored_genres
    
    def _calculate_genre_score(self, genre: str, all_genres: List[str], context: Dict = None) -> float:
        """Calcula score de un género individual."""
        norm_genre = self._normalize_genre_name(genre)
        
        score_components = []
        
        # 1. Score base del género
        sem = self.genre_knowledge.get(norm_genre)
        base_score = sem.weight if sem else 0.5
        score_components.append(('base', base_score, 0.3))
        
        # 2. Consistencia con otros géneros (clustering)
        consistency_score = self._calculate_consistency_score(genre, all_genres)
        score_components.append(('consistency', consistency_score, 0.25))
        
        # 3. Especificidad (géneros más específicos son mejores)
        specificity_score = self._calculate_specificity_score(genre)
        score_components.append(('specificity', specificity_score, 0.2))
        
        # 4. Preferencia del usuario (si disponible)
        user_score = self.user_preferences.get(norm_genre, 0.5)
        score_components.append(('user_preference', user_score, 0.15))
        
        # 5. Frecuencia de uso (géneros más comunes en biblioteca)
        frequency_score = self._calculate_frequency_score(genre)
        score_components.append(('frequency', frequency_score, 0.1))
        
        # Calcular score final
        total_weight = sum(weight for _, _, weight in score_components)
        weighted_sum = sum(score * weight for _, score, weight in score_components)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _calculate_consistency_score(self, genre: str, all_genres: List[str]) -> float:
        """Calcula qué tan consistente es un género con otros en la lista."""
        if len(all_genres) <= 1:
            return 1.0
        
        similarities = []
        for other_genre in all_genres:
            if other_genre != genre:
                sim = self.calculate_semantic_similarity(genre, other_genre)
                similarities.append(sim)
        
        if not similarities:
            return 0.5
        
        # Promedio de similitudes con otros géneros
        avg_similarity = sum(similarities) / len(similarities)
        
        # Bonus si hay alta cohesión
        if avg_similarity > 0.6:
            return min(1.0, avg_similarity * 1.2)
        
        return avg_similarity
    
    def _calculate_specificity_score(self, genre: str) -> float:
        """Calcula score de especificidad del género."""
        norm_genre = self._normalize_genre_name(genre)
        sem = self.genre_knowledge.get(norm_genre)
        
        if not sem:
            # Si no conocemos el género, usar heurísticas
            if len(genre.split()) > 1:
                return 0.8  # Géneros compuestos suelen ser más específicos
            elif len(genre) > 8:
                return 0.7  # Géneros largos suelen ser más específicos
            else:
                return 0.4  # Géneros cortos suelen ser genéricos
        
        # Basado en jerarquía
        if sem.child_genres:
            return 0.6  # Es padre de otros géneros
        elif sem.parent_genres:
            return 0.9  # Es hijo específico de géneros más amplios
        else:
            return 0.7  # Género independiente
    
    def _calculate_frequency_score(self, genre: str) -> float:
        """Calcula score basado en frecuencia de uso."""
        norm_genre = self._normalize_genre_name(genre)
        frequency = self.genre_frequency.get(norm_genre, 0)
        
        if frequency == 0:
            return 0.5  # Neutral para géneros nuevos
        
        # Normalizar frecuencia a score (log scale para evitar dominancia)
        max_frequency = max(self.genre_frequency.values()) if self.genre_frequency else 1
        normalized_freq = frequency / max_frequency
        
        # Aplicar log suave para reducir impacto de outliers
        freq_score = 0.5 + 0.5 * math.log10(1 + normalized_freq * 9)
        
        return min(1.0, freq_score)
    
    def update_user_preference(self, genre: str, preference: float):
        """Actualiza preferencia del usuario para un género."""
        norm_genre = self._normalize_genre_name(genre)
        
        # Aprendizaje gradual
        current_pref = self.user_preferences.get(norm_genre, 0.5)
        learning_rate = 0.1
        new_pref = current_pref + learning_rate * (preference - current_pref)
        
        self.user_preferences[norm_genre] = max(0.0, min(1.0, new_pref))
    
    def record_genre_usage(self, genre: str):
        """Registra uso de un género para estadísticas."""
        norm_genre = self._normalize_genre_name(genre)
        self.genre_frequency[norm_genre] += 1
    
    def find_related_genres(self, genre: str, max_results: int = 5) -> List[Tuple[str, float]]:
        """
        Encuentra géneros relacionados con uno dado.
        
        Args:
            genre: Género de referencia
            max_results: Máximo número de resultados
            
        Returns:
            Lista de (género, similitud) ordenada por similitud
        """
        norm_genre = self._normalize_genre_name(genre)
        related = []
        
        for other_genre in self.genre_knowledge.keys():
            if other_genre != norm_genre:
                similarity = self.calculate_semantic_similarity(genre, other_genre)
                if similarity > 0.3:  # Threshold mínimo
                    # Usar nombre original si disponible
                    original_name = self.genre_knowledge[other_genre].name
                    related.append((original_name, similarity))
        
        # Ordenar por similitud y limitar resultados
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:max_results]
    
    def suggest_genre_corrections(self, genre: str) -> List[Tuple[str, float]]:
        """
        Sugiere correcciones para géneros mal escritos o ambiguos.
        
        Args:
            genre: Género a corregir
            
        Returns:
            Lista de (corrección, confianza) ordenada por confianza
        """
        suggestions = []
        
        for known_genre, sem in self.genre_knowledge.items():
            # Verificar similitud léxica
            lexical_sim = difflib.SequenceMatcher(None, genre.lower(), known_genre).ratio()
            
            # Verificar aliases
            alias_matches = [
                difflib.SequenceMatcher(None, genre.lower(), alias.lower()).ratio()
                for alias in sem.aliases
            ]
            best_alias_match = max(alias_matches) if alias_matches else 0
            
            # Usar la mejor similitud
            best_sim = max(lexical_sim, best_alias_match)
            
            if best_sim > 0.6:  # Threshold para sugerencias
                suggestions.append((sem.name, best_sim))
        
        # Ordenar por confianza
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:3]  # Top 3 sugerencias
    
    def get_genre_info(self, genre: str) -> Optional[Dict]:
        """Obtiene información completa sobre un género."""
        norm_genre = self._normalize_genre_name(genre)
        sem = self.genre_knowledge.get(norm_genre)
        
        if not sem:
            return None
        
        return {
            'name': sem.name,
            'category': sem.category,
            'subcategory': sem.subcategory,
            'characteristics': sem.characteristics,
            'tempo_range': sem.tempo_range,
            'parent_genres': sem.parent_genres,
            'child_genres': sem.child_genres,
            'related_genres': sem.related_genres,
            'aliases': sem.aliases,
            'weight': sem.weight,
            'user_preference': self.user_preferences.get(norm_genre, 0.5),
            'usage_frequency': self.genre_frequency.get(norm_genre, 0)
        }
    
    def export_knowledge_base(self) -> Dict:
        """Exporta la base de conocimiento completa."""
        return {
            'genres': {
                name: {
                    'semantics': {
                        'name': sem.name,
                        'category': sem.category,
                        'subcategory': sem.subcategory,
                        'characteristics': sem.characteristics,
                        'tempo_range': sem.tempo_range,
                        'parent_genres': sem.parent_genres,
                        'child_genres': sem.child_genres,
                        'related_genres': sem.related_genres,
                        'aliases': sem.aliases,
                        'weight': sem.weight
                    },
                    'user_preference': self.user_preferences.get(name, 0.5),
                    'frequency': self.genre_frequency.get(name, 0)
                }
                for name, sem in self.genre_knowledge.items()
            },
            'statistics': {
                'total_genres': len(self.genre_knowledge),
                'categories': list(set(sem.category for sem in self.genre_knowledge.values())),
                'total_relations': len(self.similarity_cache),
                'user_preferences_count': len(self.user_preferences),
                'total_genre_usage': sum(self.genre_frequency.values())
            }
        }

# Instancia global del scorer semántico
_semantic_scorer_instance = None

def get_semantic_scorer() -> SemanticGenreScorer:
    """Obtiene la instancia global del scorer semántico."""
    global _semantic_scorer_instance
    if _semantic_scorer_instance is None:
        _semantic_scorer_instance = SemanticGenreScorer()
    return _semantic_scorer_instance

# Funciones de conveniencia
def calculate_genre_similarity(genre1: str, genre2: str) -> float:
    """Calcula similitud entre dos géneros."""
    return get_semantic_scorer().calculate_semantic_similarity(genre1, genre2)

def score_genres(genres: List[str], context: Dict = None) -> List[Tuple[str, float]]:
    """Puntúa lista de géneros."""
    return get_semantic_scorer().score_genre_list(genres, context)

def find_similar_genres(genre: str, max_results: int = 5) -> List[Tuple[str, float]]:
    """Encuentra géneros similares."""
    return get_semantic_scorer().find_related_genres(genre, max_results)

def get_genre_details(genre: str) -> Optional[Dict]:
    """Obtiene detalles de un género."""
    return get_semantic_scorer().get_genre_info(genre)