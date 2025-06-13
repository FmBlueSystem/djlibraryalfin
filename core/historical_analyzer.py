"""
Analizador de Consistencia Histórica para Metadatos Musicales
Valida la coherencia temporal y contextual de géneros, artistas y tendencias
"""

import sqlite3
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
import json
from datetime import datetime


@dataclass
class HistoricalInconsistency:
    """Representa una inconsistencia histórica detectada."""
    file_path: str
    field: str
    current_value: str
    issue_type: str
    severity: str  # "high", "medium", "low"
    suggested_correction: Optional[str] = None
    explanation: str = ""
    confidence: float = 0.0


@dataclass
class HistoricalContext:
    """Contexto histórico de un período musical."""
    decade: str
    dominant_genres: List[str]
    emerging_genres: List[str]
    technology_context: List[str]
    cultural_movements: List[str]
    typical_bpm_ranges: Dict[str, Tuple[int, int]]


class HistoricalConsistencyAnalyzer:
    """
    Analizador de consistencia histórica para metadatos musicales.
    Detecta anomalías temporales y sugiere correcciones basadas en contexto histórico.
    """
    
    def __init__(self):
        self.historical_contexts = self._build_historical_contexts()
        self.genre_evolution = self._build_genre_evolution()
        self.technology_timeline = self._build_technology_timeline()
        self.artist_career_spans = {}  # Se llena dinámicamente
        
    def _build_historical_contexts(self) -> Dict[str, HistoricalContext]:
        """Construye contextos históricos por década."""
        return {
            "1950s": HistoricalContext(
                decade="1950s",
                dominant_genres=["Rock & Roll", "Country", "Jazz", "Blues", "Pop"],
                emerging_genres=["Rock & Roll", "Doo-wop"],
                technology_context=["Vinyl records", "Radio broadcasting", "Electric guitars"],
                cultural_movements=["Rock & Roll revolution", "Civil Rights Movement"],
                typical_bpm_ranges={
                    "Rock & Roll": (120, 160),
                    "Country": (90, 130),
                    "Jazz": (80, 180),
                    "Blues": (60, 120)
                }
            ),
            "1960s": HistoricalContext(
                decade="1960s",
                dominant_genres=["Rock", "Soul", "Motown", "Folk", "Pop"],
                emerging_genres=["Psychedelic Rock", "Folk Rock", "Soul"],
                technology_context=["Stereo recording", "Multi-track recording", "Electric bass"],
                cultural_movements=["British Invasion", "Counterculture", "Civil Rights"],
                typical_bpm_ranges={
                    "Rock": (110, 150),
                    "Soul": (90, 140),
                    "Folk": (80, 120),
                    "Pop": (100, 140)
                }
            ),
            "1970s": HistoricalContext(
                decade="1970s",
                dominant_genres=["Rock", "Disco", "Funk", "Punk Rock", "Progressive Rock"],
                emerging_genres=["Disco", "Punk Rock", "Reggae", "Heavy Metal"],
                technology_context=["Synthesizers", "Drum machines", "Multi-track studios"],
                cultural_movements=["Disco era", "Punk movement", "Reggae culture"],
                typical_bpm_ranges={
                    "Disco": (110, 130),
                    "Funk": (90, 120),
                    "Punk Rock": (140, 200),
                    "Progressive Rock": (60, 180)
                }
            ),
            "1980s": HistoricalContext(
                decade="1980s",
                dominant_genres=["New Wave", "Synthpop", "Hip Hop", "Heavy Metal", "Pop"],
                emerging_genres=["Hip Hop", "New Wave", "Synthpop", "Thrash Metal"],
                technology_context=["Digital recording", "MIDI", "Sampling", "MTV"],
                cultural_movements=["MTV culture", "Hip Hop culture", "New Wave movement"],
                typical_bpm_ranges={
                    "New Wave": (110, 140),
                    "Synthpop": (100, 130),
                    "Hip Hop": (80, 110),
                    "Heavy Metal": (120, 180)
                }
            ),
            "1990s": HistoricalContext(
                decade="1990s",
                dominant_genres=["Grunge", "Alternative Rock", "Hip Hop", "Techno", "Pop"],
                emerging_genres=["Grunge", "Techno", "House", "Gangsta Rap", "Britpop"],
                technology_context=["CD dominance", "Digital effects", "Internet emergence"],
                cultural_movements=["Grunge movement", "Rave culture", "Alternative culture"],
                typical_bpm_ranges={
                    "Grunge": (90, 130),
                    "Techno": (120, 150),
                    "House": (115, 130),
                    "Hip Hop": (80, 110)
                }
            ),
            "2000s": HistoricalContext(
                decade="2000s",
                dominant_genres=["Pop", "Hip Hop", "Rock", "Electronic", "R&B"],
                emerging_genres=["Dubstep", "Crunk", "Emo", "Nu Metal"],
                technology_context=["Digital downloads", "Auto-Tune", "Pro Tools", "iPod"],
                cultural_movements=["Digital music revolution", "Social media emergence"],
                typical_bpm_ranges={
                    "Pop": (100, 130),
                    "Hip Hop": (70, 110),
                    "Electronic": (120, 140),
                    "Dubstep": (140, 150)
                }
            ),
            "2010s": HistoricalContext(
                decade="2010s",
                dominant_genres=["Pop", "Hip Hop", "Electronic", "Indie", "Trap"],
                emerging_genres=["Trap", "Future Bass", "Tropical House", "Mumblecore"],
                technology_context=["Streaming services", "Social media", "Bedroom production"],
                cultural_movements=["Streaming revolution", "Social media culture"],
                typical_bpm_ranges={
                    "Trap": (130, 170),
                    "Pop": (90, 130),
                    "Electronic": (100, 150),
                    "Future Bass": (140, 160)
                }
            ),
            "2020s": HistoricalContext(
                decade="2020s",
                dominant_genres=["Pop", "Hip Hop", "Electronic", "Hyperpop", "Drill"],
                emerging_genres=["Hyperpop", "Drill", "Afrobeats", "Phonk"],
                technology_context=["AI music tools", "TikTok influence", "Home studios"],
                cultural_movements=["TikTok culture", "Pandemic isolation", "AI revolution"],
                typical_bpm_ranges={
                    "Hyperpop": (150, 200),
                    "Drill": (130, 150),
                    "Pop": (90, 130),
                    "Afrobeats": (100, 130)
                }
            )
        }
    
    def _build_genre_evolution(self) -> Dict[str, Dict[str, List[str]]]:
        """Mapea la evolución de géneros a través del tiempo."""
        return {
            "Electronic": {
                "origins": ["1970s"],
                "peak_decades": ["1990s", "2000s", "2010s"],
                "subgenre_emergence": {
                    "1970s": ["Kraftwerk-style electronic"],
                    "1980s": ["Synthpop", "New Wave"],
                    "1990s": ["Techno", "House", "Trance"],
                    "2000s": ["Dubstep", "Electro House"],
                    "2010s": ["Future Bass", "Tropical House", "Trap"],
                    "2020s": ["Hyperpop", "Phonk"]
                }
            },
            "Hip Hop": {
                "origins": ["1970s"],
                "peak_decades": ["1990s", "2000s", "2010s", "2020s"],
                "subgenre_emergence": {
                    "1970s": ["Old School Hip Hop"],
                    "1980s": ["Golden Age Hip Hop"],
                    "1990s": ["Gangsta Rap", "East Coast vs West Coast"],
                    "2000s": ["Crunk", "Snap music"],
                    "2010s": ["Trap", "Mumble rap"],
                    "2020s": ["Drill", "Melodic rap"]
                }
            },
            "Rock": {
                "origins": ["1950s"],
                "peak_decades": ["1960s", "1970s", "1980s", "1990s"],
                "subgenre_emergence": {
                    "1950s": ["Rock & Roll"],
                    "1960s": ["Psychedelic Rock", "Folk Rock"],
                    "1970s": ["Progressive Rock", "Punk Rock", "Heavy Metal"],
                    "1980s": ["New Wave", "Thrash Metal"],
                    "1990s": ["Grunge", "Alternative Rock"],
                    "2000s": ["Nu Metal", "Emo"],
                    "2010s": ["Indie Rock revival"]
                }
            }
        }
    
    def _build_technology_timeline(self) -> Dict[str, List[str]]:
        """Timeline de tecnologías musicales que afectan la producción."""
        return {
            "1950s": ["Electric guitars", "Magnetic tape", "Vinyl records"],
            "1960s": ["Multi-track recording", "Electric bass", "Stereo recording"],
            "1970s": ["Synthesizers", "Drum machines", "16-track recording"],
            "1980s": ["Digital recording", "MIDI", "Sampling", "CD technology"],
            "1990s": ["Digital Audio Workstations", "Internet", "CD dominance"],
            "2000s": ["Pro Tools", "Auto-Tune", "Digital downloads", "iPod"],
            "2010s": ["Streaming services", "Bedroom production", "Social media"],
            "2020s": ["AI music tools", "TikTok influence", "Home studio revolution"]
        }
    
    def analyze_database_consistency(self, db_path: str) -> List[HistoricalInconsistency]:
        """Analiza toda la base de datos en busca de inconsistencias históricas."""
        inconsistencies = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Obtener todos los tracks con metadatos
            cursor.execute("""
                SELECT file_path, title, artist, album, genre, year, bpm, key, duration
                FROM tracks
                WHERE year IS NOT NULL
                ORDER BY year
            """)
            
            tracks = cursor.fetchall()
            
            # Analizar cada track
            for track in tracks:
                file_path, title, artist, album, genre, year, bpm, key, duration = track
                
                if year:
                    decade = f"{(year // 10) * 10}s"
                    
                    # Verificar consistencia de género
                    genre_issues = self._check_genre_consistency(
                        file_path, genre, year, decade
                    )
                    inconsistencies.extend(genre_issues)
                    
                    # Verificar consistencia de BPM
                    bpm_issues = self._check_bpm_consistency(
                        file_path, genre, bpm, decade
                    )
                    inconsistencies.extend(bpm_issues)
                    
                    # Verificar consistencia de artista (si tenemos datos)
                    artist_issues = self._check_artist_consistency(
                        file_path, artist, year, decade
                    )
                    inconsistencies.extend(artist_issues)
            
            # Análisis de patrones globales
            pattern_issues = self._analyze_global_patterns(cursor)
            inconsistencies.extend(pattern_issues)
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"Error analizando base de datos: {e}")
        
        return inconsistencies
    
    def _check_genre_consistency(self, file_path: str, genre: str, year: int, decade: str) -> List[HistoricalInconsistency]:
        """Verifica consistencia histórica del género."""
        issues = []
        
        if not genre or genre == "N/A":
            return issues
        
        context = self.historical_contexts.get(decade)
        if not context:
            return issues
        
        # Verificar si el género existía en esa época
        all_period_genres = context.dominant_genres + context.emerging_genres
        
        # Buscar coincidencias exactas o parciales
        genre_exists = any(
            genre.lower() in period_genre.lower() or 
            period_genre.lower() in genre.lower()
            for period_genre in all_period_genres
        )
        
        if not genre_exists:
            # Verificar en evolución de géneros
            genre_valid = self._check_genre_evolution(genre, decade)
            
            if not genre_valid:
                severity = "high" if year < 1980 else "medium"
                
                # Sugerir género alternativo
                suggested = self._suggest_alternative_genre(genre, decade)
                
                issues.append(HistoricalInconsistency(
                    file_path=file_path,
                    field="genre",
                    current_value=genre,
                    issue_type="anachronistic_genre",
                    severity=severity,
                    suggested_correction=suggested,
                    explanation=f"El género '{genre}' es inusual para {decade}",
                    confidence=0.7 if suggested else 0.5
                ))
        
        return issues
    
    def _check_bpm_consistency(self, file_path: str, genre: str, bpm: Optional[float], decade: str) -> List[HistoricalInconsistency]:
        """Verifica consistencia del BPM con el género y época."""
        issues = []
        
        if not bpm or not genre:
            return issues
        
        context = self.historical_contexts.get(decade)
        if not context or genre not in context.typical_bpm_ranges:
            return issues
        
        min_bpm, max_bpm = context.typical_bpm_ranges[genre]
        
        if not (min_bpm <= bpm <= max_bpm):
            # BPM fuera del rango típico para el género en esa época
            severity = "low" if abs(bpm - (min_bpm + max_bpm) / 2) < 20 else "medium"
            
            issues.append(HistoricalInconsistency(
                file_path=file_path,
                field="bpm",
                current_value=str(bpm),
                issue_type="unusual_bpm_for_genre_period",
                severity=severity,
                suggested_correction=f"{min_bpm}-{max_bpm}",
                explanation=f"BPM {bpm} es inusual para {genre} en {decade} (típico: {min_bpm}-{max_bpm})",
                confidence=0.6
            ))
        
        return issues
    
    def _check_artist_consistency(self, file_path: str, artist: str, year: int, decade: str) -> List[HistoricalInconsistency]:
        """Verifica consistencia temporal del artista."""
        issues = []
        
        # Por ahora, implementación básica
        # En el futuro se podría integrar con bases de datos de artistas
        
        return issues
    
    def _check_genre_evolution(self, genre: str, decade: str) -> bool:
        """Verifica si un género es válido según su evolución histórica."""
        for main_genre, evolution in self.genre_evolution.items():
            if genre.lower() in main_genre.lower() or main_genre.lower() in genre.lower():
                # Verificar si el género había emergido en esa década
                for evo_decade, subgenres in evolution.get("subgenre_emergence", {}).items():
                    if decade >= evo_decade:
                        if any(genre.lower() in sub.lower() or sub.lower() in genre.lower() 
                               for sub in subgenres):
                            return True
                
                # Verificar décadas de origen y pico
                if decade in evolution.get("origins", []) or decade in evolution.get("peak_decades", []):
                    return True
        
        return False
    
    def _suggest_alternative_genre(self, current_genre: str, decade: str) -> Optional[str]:
        """Sugiere un género alternativo más apropiado para la época."""
        context = self.historical_contexts.get(decade)
        if not context:
            return None
        
        # Buscar géneros similares que fueran dominantes en esa época
        all_genres = context.dominant_genres + context.emerging_genres
        
        # Buscar coincidencias parciales
        for period_genre in all_genres:
            if any(word in period_genre.lower() for word in current_genre.lower().split()):
                return period_genre
        
        # Si no hay coincidencias, sugerir el género más común de la época
        if context.dominant_genres:
            return context.dominant_genres[0]
        
        return None
    
    def _analyze_global_patterns(self, cursor) -> List[HistoricalInconsistency]:
        """Analiza patrones globales en la base de datos."""
        issues = []
        
        # Análisis de distribución temporal de géneros
        cursor.execute("""
            SELECT genre, year, COUNT(*) as count
            FROM tracks
            WHERE genre IS NOT NULL AND year IS NOT NULL
            GROUP BY genre, year
            ORDER BY year
        """)
        
        genre_year_counts = defaultdict(lambda: defaultdict(int))
        for genre, year, count in cursor.fetchall():
            decade = f"{(year // 10) * 10}s"
            genre_year_counts[genre][decade] += count
        
        # Detectar géneros con distribuciones temporales sospechosas
        for genre, decade_counts in genre_year_counts.items():
            total_tracks = sum(decade_counts.values())
            
            # Si un género aparece solo en una década muy temprana o tardía
            decades = list(decade_counts.keys())
            if len(decades) == 1:
                decade = decades[0]
                if self._is_suspicious_single_decade(genre, decade):
                    # Esto requeriría más análisis específico
                    pass
        
        return issues
    
    def _is_suspicious_single_decade(self, genre: str, decade: str) -> bool:
        """Determina si es sospechoso que un género aparezca solo en una década."""
        # Implementación básica - se puede expandir
        modern_genres = ["Dubstep", "Trap", "Future Bass", "Hyperpop"]
        early_decades = ["1950s", "1960s", "1970s"]
        
        if any(modern in genre for modern in modern_genres) and decade in early_decades:
            return True
        
        return False
    
    def generate_consistency_report(self, db_path: str) -> Dict:
        """Genera un reporte completo de consistencia histórica."""
        inconsistencies = self.analyze_database_consistency(db_path)
        
        # Agrupar por tipo de problema
        by_type = defaultdict(list)
        by_severity = defaultdict(list)
        
        for issue in inconsistencies:
            by_type[issue.issue_type].append(issue)
            by_severity[issue.severity].append(issue)
        
        # Estadísticas generales
        total_issues = len(inconsistencies)
        
        report = {
            "summary": {
                "total_inconsistencies": total_issues,
                "high_severity": len(by_severity["high"]),
                "medium_severity": len(by_severity["medium"]),
                "low_severity": len(by_severity["low"])
            },
            "by_type": {
                issue_type: len(issues) 
                for issue_type, issues in by_type.items()
            },
            "detailed_issues": inconsistencies,
            "recommendations": self._generate_recommendations(inconsistencies)
        }
        
        return report
    
    def _generate_recommendations(self, inconsistencies: List[HistoricalInconsistency]) -> List[str]:
        """Genera recomendaciones basadas en las inconsistencias encontradas."""
        recommendations = []
        
        # Contar tipos de problemas
        issue_counts = Counter(issue.issue_type for issue in inconsistencies)
        
        if issue_counts.get("anachronistic_genre", 0) > 10:
            recommendations.append(
                "Se detectaron muchos géneros anacrónicos. "
                "Considere revisar la fuente de metadatos o implementar "
                "validación histórica automática."
            )
        
        if issue_counts.get("unusual_bpm_for_genre_period", 0) > 5:
            recommendations.append(
                "Varios tracks tienen BPM inusuales para su género y época. "
                "Verifique la precisión de la detección de BPM."
            )
        
        high_severity = sum(1 for issue in inconsistencies if issue.severity == "high")
        if high_severity > 0:
            recommendations.append(
                f"Se encontraron {high_severity} inconsistencias de alta severidad "
                "que requieren atención inmediata."
            )
        
        return recommendations


def main():
    """Función principal para ejecutar análisis de consistencia."""
    import os
    
    # Determinar ruta de la base de datos
    project_root = os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(project_root, "config")
    db_path = os.path.join(config_path, "library.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        return
    
    print("🕰️  Analizando consistencia histórica de metadatos...")
    
    analyzer = HistoricalConsistencyAnalyzer()
    report = analyzer.generate_consistency_report(db_path)
    
    # Mostrar resumen
    print(f"\n📊 Resumen del Análisis:")
    print(f"  • Total de inconsistencias: {report['summary']['total_inconsistencies']}")
    print(f"  • Alta severidad: {report['summary']['high_severity']}")
    print(f"  • Media severidad: {report['summary']['medium_severity']}")
    print(f"  • Baja severidad: {report['summary']['low_severity']}")
    
    # Mostrar por tipo
    if report['by_type']:
        print(f"\n📋 Por Tipo de Problema:")
        for issue_type, count in report['by_type'].items():
            print(f"  • {issue_type.replace('_', ' ').title()}: {count}")
    
    # Mostrar recomendaciones
    if report['recommendations']:
        print(f"\n💡 Recomendaciones:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Mostrar algunos ejemplos de inconsistencias
    if report['detailed_issues']:
        print(f"\n🔍 Ejemplos de Inconsistencias:")
        for issue in report['detailed_issues'][:5]:
            filename = os.path.basename(issue.file_path)
            print(f"  • {filename}")
            print(f"    {issue.explanation}")
            if issue.suggested_correction:
                print(f"    Sugerencia: {issue.suggested_correction}")
            print()


if __name__ == "__main__":
    main()