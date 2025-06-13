"""
Sistema de Clasificación Inteligente de Géneros Musicales para DjAlfin
Proporciona normalización, validación histórica y mejora de exactitud en metadatos
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import sqlite3
from datetime import datetime


class GenreConfidence(Enum):
    """Niveles de confianza para clasificación de géneros."""
    HIGH = 0.9      # Género confirmado por múltiples fuentes
    MEDIUM = 0.7    # Género probable con validación parcial
    LOW = 0.5       # Género sugerido, requiere revisión
    UNKNOWN = 0.0   # No se pudo determinar


@dataclass
class GenreClassification:
    """Resultado de clasificación de género."""
    primary_genre: str
    subgenres: List[str]
    confidence: GenreConfidence
    sources: List[str]
    historical_context: Optional[str] = None
    decade: Optional[str] = None


class GenreClassifier:
    """
    Clasificador inteligente de géneros musicales con validación histórica.
    """
    
    def __init__(self):
        self.genre_hierarchy = self._build_genre_hierarchy()
        self.historical_genres = self._build_historical_timeline()
        self.genre_aliases = self._build_genre_aliases()
        self.invalid_genres = self._build_invalid_genres()
        
    def _build_genre_hierarchy(self) -> Dict[str, Dict]:
        """Construye jerarquía de géneros principales y subgéneros."""
        return {
            "Electronic": {
                "subgenres": ["House", "Techno", "Trance", "Dubstep", "Drum & Bass", 
                             "Ambient", "IDM", "Breakbeat", "Garage", "Hardstyle"],
                "aliases": ["EDM", "Dance", "Electronic Dance Music"],
                "decades": ["1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "Rock": {
                "subgenres": ["Classic Rock", "Hard Rock", "Progressive Rock", "Punk Rock",
                             "Alternative Rock", "Indie Rock", "Metal", "Grunge"],
                "aliases": ["Rock & Roll", "Rock Music"],
                "decades": ["1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "Hip Hop": {
                "subgenres": ["Rap", "Trap", "Old School Hip Hop", "Conscious Hip Hop",
                             "Gangsta Rap", "Alternative Hip Hop"],
                "aliases": ["Hip-Hop", "Rap Music"],
                "decades": ["1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "Pop": {
                "subgenres": ["Dance Pop", "Electropop", "Synthpop", "Teen Pop", "K-Pop"],
                "aliases": ["Popular Music", "Pop Music"],
                "decades": ["1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "R&B": {
                "subgenres": ["Soul", "Funk", "Contemporary R&B", "Neo-Soul", "Motown"],
                "aliases": ["Rhythm and Blues", "RnB", "R and B"],
                "decades": ["1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "Jazz": {
                "subgenres": ["Bebop", "Swing", "Fusion", "Smooth Jazz", "Free Jazz", "Cool Jazz"],
                "aliases": ["Jazz Music"],
                "decades": ["1900s", "1910s", "1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "Country": {
                "subgenres": ["Country Rock", "Bluegrass", "Honky Tonk", "Country Pop"],
                "aliases": ["Country Music", "Country & Western"],
                "decades": ["1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "Reggae": {
                "subgenres": ["Dancehall", "Dub", "Ska", "Rocksteady"],
                "aliases": ["Reggae Music"],
                "decades": ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "Latin": {
                "subgenres": ["Salsa", "Bachata", "Merengue", "Reggaeton", "Bossa Nova", "Tango"],
                "aliases": ["Latin Music", "Latino"],
                "decades": ["1900s", "1910s", "1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
            },
            "Classical": {
                "subgenres": ["Baroque", "Romantic", "Contemporary Classical", "Opera"],
                "aliases": ["Classical Music", "Art Music"],
                "decades": ["1600s", "1700s", "1800s", "1900s", "2000s", "2010s", "2020s"]
            }
        }
    
    def _build_historical_timeline(self) -> Dict[str, List[str]]:
        """Construye línea temporal de géneros por década."""
        return {
            "1950s": ["Rock & Roll", "Country", "Jazz", "Blues", "Pop"],
            "1960s": ["Rock", "Soul", "Motown", "Folk", "Psychedelic Rock"],
            "1970s": ["Disco", "Funk", "Punk Rock", "Progressive Rock", "Reggae"],
            "1980s": ["New Wave", "Synthpop", "Hip Hop", "Heavy Metal", "Post-Punk"],
            "1990s": ["Grunge", "Alternative Rock", "Techno", "House", "Gangsta Rap"],
            "2000s": ["Nu Metal", "Emo", "Crunk", "Garage Rock Revival", "Dubstep"],
            "2010s": ["Trap", "EDM", "Indie Pop", "Mumblecore", "Future Bass"],
            "2020s": ["Hyperpop", "Drill", "Afrobeats", "Bedroom Pop", "Phonk"]
        }
    
    def _build_genre_aliases(self) -> Dict[str, str]:
        """Mapeo de aliases a géneros normalizados."""
        aliases = {}
        for main_genre, data in self.genre_hierarchy.items():
            # Agregar aliases del género principal
            for alias in data.get("aliases", []):
                aliases[alias.lower()] = main_genre
            
            # Agregar subgéneros
            for subgenre in data.get("subgenres", []):
                aliases[subgenre.lower()] = main_genre
        
        # Aliases adicionales comunes
        additional_aliases = {
            "edm": "Electronic",
            "dance": "Electronic",
            "electronic dance music": "Electronic",
            "hip-hop": "Hip Hop",
            "rap": "Hip Hop",
            "rnb": "R&B",
            "r and b": "R&B",
            "rhythm and blues": "R&B",
            "rock and roll": "Rock",
            "rock & roll": "Rock",
            "metal": "Rock",
            "heavy metal": "Rock",
            "hard rock": "Rock"
        }
        aliases.update(additional_aliases)
        
        return aliases
    
    def _build_invalid_genres(self) -> Set[str]:
        """Lista de géneros inválidos que deben ser corregidos."""
        return {
            "n/a", "na", "unknown", "none", "",
            "2008 universal fire victim",
            "easy listening pop soul contemporary r & b",
            "various", "misc", "other", "undefined"
        }
    
    def normalize_genre(self, raw_genre: str) -> Optional[str]:
        """Normaliza un género crudo a formato estándar."""
        if not raw_genre or not isinstance(raw_genre, str):
            return None
        
        # Limpiar y normalizar
        cleaned = raw_genre.strip().lower()
        
        # Verificar si es inválido
        if cleaned in self.invalid_genres:
            return None
        
        # Buscar en aliases
        if cleaned in self.genre_aliases:
            return self.genre_aliases[cleaned]
        
        # Buscar coincidencias parciales
        for alias, normalized in self.genre_aliases.items():
            if alias in cleaned or cleaned in alias:
                return normalized
        
        # Si no se encuentra, capitalizar apropiadamente
        return self._capitalize_genre(raw_genre)
    
    def _capitalize_genre(self, genre: str) -> str:
        """Capitaliza apropiadamente un género."""
        # Palabras que deben permanecer en minúsculas
        lowercase_words = {"and", "or", "of", "the", "in", "on", "at", "to", "for", "with", "&"}
        
        words = genre.split()
        capitalized = []
        
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in lowercase_words:
                capitalized.append(word.capitalize())
            else:
                capitalized.append(word.lower())
        
        return " ".join(capitalized)
    
    def validate_historical_context(self, genre: str, year: Optional[int]) -> bool:
        """Valida si un género es históricamente consistente con el año."""
        if not year or not genre:
            return True  # No podemos validar sin información
        
        decade = f"{(year // 10) * 10}s"
        
        # Verificar si el género existía en esa década
        for decade_key, genres in self.historical_genres.items():
            if decade_key == decade:
                return any(g.lower() in genre.lower() or genre.lower() in g.lower() 
                          for g in genres)
        
        # Si no encontramos la década exacta, ser más permisivo
        return True
    
    def classify_genre(self, 
                      raw_genres: List[str], 
                      artist: Optional[str] = None,
                      year: Optional[int] = None,
                      sources: Optional[List[str]] = None) -> GenreClassification:
        """
        Clasifica géneros usando múltiples fuentes y validación histórica.
        """
        if not raw_genres:
            return GenreClassification(
                primary_genre="Unknown",
                subgenres=[],
                confidence=GenreConfidence.UNKNOWN,
                sources=sources or []
            )
        
        # Normalizar todos los géneros
        normalized_genres = []
        for genre in raw_genres:
            normalized = self.normalize_genre(genre)
            if normalized:
                normalized_genres.append(normalized)
        
        if not normalized_genres:
            return GenreClassification(
                primary_genre="Unknown",
                subgenres=[],
                confidence=GenreConfidence.UNKNOWN,
                sources=sources or []
            )
        
        # Encontrar género principal más común
        genre_counts = {}
        for genre in normalized_genres:
            # Buscar género principal
            main_genre = self._find_main_genre(genre)
            genre_counts[main_genre] = genre_counts.get(main_genre, 0) + 1
        
        # Seleccionar género principal
        primary_genre = max(genre_counts.keys(), key=lambda x: genre_counts[x])
        
        # Encontrar subgéneros
        subgenres = [g for g in normalized_genres if g != primary_genre]
        
        # Calcular confianza
        confidence = self._calculate_confidence(
            primary_genre, normalized_genres, year, sources or []
        )
        
        # Contexto histórico
        historical_context = None
        decade = None
        if year:
            decade = f"{(year // 10) * 10}s"
            if not self.validate_historical_context(primary_genre, year):
                historical_context = f"⚠️ Género inusual para {decade}"
        
        return GenreClassification(
            primary_genre=primary_genre,
            subgenres=subgenres,
            confidence=confidence,
            sources=sources or [],
            historical_context=historical_context,
            decade=decade
        )
    
    def _find_main_genre(self, genre: str) -> str:
        """Encuentra el género principal para un subgénero."""
        for main_genre, data in self.genre_hierarchy.items():
            if genre == main_genre:
                return main_genre
            if genre in data.get("subgenres", []):
                return main_genre
        return genre
    
    def _calculate_confidence(self, 
                            primary_genre: str, 
                            all_genres: List[str],
                            year: Optional[int],
                            sources: List[str]) -> GenreConfidence:
        """Calcula nivel de confianza basado en múltiples factores."""
        score = 0.0
        
        # Factor 1: Número de fuentes
        if len(sources) >= 2:
            score += 0.3
        elif len(sources) == 1:
            score += 0.1
        
        # Factor 2: Consistencia entre géneros
        main_genre_count = sum(1 for g in all_genres if self._find_main_genre(g) == primary_genre)
        consistency = main_genre_count / len(all_genres)
        score += consistency * 0.4
        
        # Factor 3: Validación histórica
        if year and self.validate_historical_context(primary_genre, year):
            score += 0.2
        
        # Factor 4: Género reconocido vs desconocido
        if primary_genre in self.genre_hierarchy:
            score += 0.1
        
        # Convertir a enum
        if score >= 0.8:
            return GenreConfidence.HIGH
        elif score >= 0.6:
            return GenreConfidence.MEDIUM
        elif score >= 0.3:
            return GenreConfidence.LOW
        else:
            return GenreConfidence.UNKNOWN
    
    def suggest_corrections(self, db_path: str) -> List[Tuple[str, str, str, str]]:
        """
        Sugiere correcciones para géneros problemáticos en la base de datos.
        Retorna lista de (file_path, current_genre, suggested_genre, reason).
        """
        corrections = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Buscar pistas con géneros problemáticos
            cursor.execute("""
                SELECT file_path, title, artist, genre, year
                FROM tracks
                WHERE genre IS NOT NULL AND genre != ''
            """)
            
            for row in cursor.fetchall():
                file_path, title, artist, current_genre, year = row
                
                # Verificar si el género necesita corrección
                normalized = self.normalize_genre(current_genre)
                
                if not normalized or current_genre.lower() in self.invalid_genres:
                    # Intentar inferir género basado en contexto
                    suggested = self._infer_genre_from_context(title, artist, year)
                    if suggested:
                        corrections.append((
                            file_path, 
                            current_genre, 
                            suggested, 
                            "Género inválido corregido por contexto"
                        ))
                elif normalized != current_genre:
                    corrections.append((
                        file_path,
                        current_genre,
                        normalized,
                        "Normalización de formato"
                    ))
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"Error accediendo a la base de datos: {e}")
        
        return corrections
    
    def _infer_genre_from_context(self, 
                                title: Optional[str], 
                                artist: Optional[str], 
                                year: Optional[int]) -> Optional[str]:
        """Intenta inferir género basado en contexto de título, artista y año."""
        # Palabras clave en títulos que sugieren géneros
        title_keywords = {
            "Electronic": ["remix", "mix", "edit", "club", "dance", "beat"],
            "Hip Hop": ["rap", "hip hop", "freestyle", "cypher"],
            "Rock": ["rock", "metal", "punk", "grunge"],
            "Pop": ["pop", "hit", "chart", "radio"],
            "R&B": ["soul", "funk", "groove", "smooth"]
        }
        
        if title:
            title_lower = title.lower()
            for genre, keywords in title_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    return genre
        
        # Inferir por década si no hay otras pistas
        if year:
            decade = f"{(year // 10) * 10}s"
            if decade in self.historical_genres:
                # Retornar el género más común de esa década
                decade_genres = self.historical_genres[decade]
                if decade_genres:
                    return decade_genres[0]  # Primer género de la década
        
        return None
    
    def get_genre_statistics(self, db_path: str) -> Dict[str, any]:
        """Genera estadísticas de géneros en la base de datos."""
        stats = {
            "total_tracks": 0,
            "tracks_with_genre": 0,
            "unique_genres": 0,
            "invalid_genres": 0,
            "genre_distribution": {},
            "problematic_genres": [],
            "decade_distribution": {}
        }
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Estadísticas básicas
            cursor.execute("SELECT COUNT(*) FROM tracks")
            stats["total_tracks"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tracks WHERE genre IS NOT NULL AND genre != ''")
            stats["tracks_with_genre"] = cursor.fetchone()[0]
            
            # Distribución de géneros
            cursor.execute("""
                SELECT genre, COUNT(*) as count
                FROM tracks
                WHERE genre IS NOT NULL AND genre != ''
                GROUP BY genre
                ORDER BY count DESC
            """)
            
            for genre, count in cursor.fetchall():
                stats["genre_distribution"][genre] = count
                
                # Verificar si es problemático
                if genre.lower() in self.invalid_genres:
                    stats["problematic_genres"].append((genre, count))
                    stats["invalid_genres"] += count
            
            stats["unique_genres"] = len(stats["genre_distribution"])
            
            # Distribución por década
            cursor.execute("""
                SELECT year, genre, COUNT(*) as count
                FROM tracks
                WHERE year IS NOT NULL AND genre IS NOT NULL AND genre != ''
                GROUP BY year, genre
            """)
            
            for year, genre, count in cursor.fetchall():
                decade = f"{(year // 10) * 10}s"
                if decade not in stats["decade_distribution"]:
                    stats["decade_distribution"][decade] = {}
                
                normalized_genre = self.normalize_genre(genre) or genre
                main_genre = self._find_main_genre(normalized_genre)
                
                if main_genre not in stats["decade_distribution"][decade]:
                    stats["decade_distribution"][decade][main_genre] = 0
                stats["decade_distribution"][decade][main_genre] += count
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"Error generando estadísticas: {e}")
        
        return stats


# Funciones de utilidad para integración con el sistema existente

def enhance_metadata_with_genre_classification(metadata: Dict, 
                                             sources: List[str] = None) -> Dict:
    """
    Mejora metadatos existentes con clasificación inteligente de géneros.
    """
    classifier = GenreClassifier()
    
    # Extraer géneros de diferentes fuentes
    raw_genres = []
    if metadata.get("genre"):
        raw_genres.append(metadata["genre"])
    
    # Clasificar género
    classification = classifier.classify_genre(
        raw_genres=raw_genres,
        artist=metadata.get("artist"),
        year=metadata.get("year"),
        sources=sources or ["file_metadata"]
    )
    
    # Actualizar metadatos
    enhanced_metadata = metadata.copy()
    enhanced_metadata.update({
        "genre": classification.primary_genre,
        "subgenres": classification.subgenres,
        "genre_confidence": classification.confidence.value,
        "genre_sources": classification.sources,
        "historical_context": classification.historical_context,
        "decade": classification.decade
    })
    
    return enhanced_metadata


def validate_and_fix_genre_database(db_path: str, apply_fixes: bool = False) -> Dict:
    """
    Valida y opcionalmente corrige géneros en la base de datos.
    """
    classifier = GenreClassifier()
    
    # Generar estadísticas
    stats = classifier.get_genre_statistics(db_path)
    
    # Obtener sugerencias de corrección
    corrections = classifier.suggest_corrections(db_path)
    
    result = {
        "statistics": stats,
        "suggested_corrections": len(corrections),
        "corrections_applied": 0
    }
    
    if apply_fixes and corrections:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for file_path, old_genre, new_genre, reason in corrections:
                cursor.execute("""
                    UPDATE tracks 
                    SET genre = ?, 
                        last_modified = datetime('now')
                    WHERE file_path = ?
                """, (new_genre, file_path))
                
                if cursor.rowcount > 0:
                    result["corrections_applied"] += 1
                    print(f"✅ {file_path}: '{old_genre}' → '{new_genre}' ({reason})")
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            print(f"Error aplicando correcciones: {e}")
    
    return result