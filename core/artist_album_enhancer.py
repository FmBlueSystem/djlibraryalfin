"""
Mejorador de Metadatos de Artistas y Álbumes
Extiende el sistema de clasificación para incluir corrección de artistas y álbumes
"""

import sqlite3
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
import difflib


@dataclass
class ArtistAlbumCorrection:
    """Representa una corrección sugerida para artista o álbum."""
    file_path: str
    field: str  # "artist" o "album"
    current_value: str
    suggested_value: str
    confidence: float
    reason: str
    source: str


class ArtistAlbumEnhancer:
    """
    Mejorador de metadatos de artistas y álbumes.
    Detecta y corrige problemas comunes en estos campos.
    """
    
    def __init__(self):
        self.common_invalid_values = {
            "N/A", "n/a", "NA", "na", "Unknown", "unknown", "UNKNOWN",
            "Various Artists", "Various", "VA", "V.A.", "V/A",
            "Compilation", "COMPILATION", "compilation",
            "Soundtrack", "SOUNDTRACK", "soundtrack",
            "Mixed", "MIXED", "mixed", "Mix", "MIX",
            "", " ", "  ", "   ",  # Espacios vacíos
            "Track", "TRACK", "track",
            "Untitled", "UNTITLED", "untitled",
            "No Artist", "No Album", "NO ARTIST", "NO ALBUM",
            "Artist", "ARTIST", "artist",
            "Album", "ALBUM", "album"
        }
        
        # Patrones problemáticos en nombres
        self.problematic_patterns = [
            r"^\d{4}\s+.*victim.*$",  # "2008 Universal Fire Victim"
            r"^feat\.?\s+.*$",        # Nombres que empiezan con "feat."
            r"^ft\.?\s+.*$",          # Nombres que empiezan con "ft."
            r"^\(\d+\).*$",           # Nombres que empiezan con números entre paréntesis
            r"^track\s+\d+.*$",       # "Track 01", "Track 1", etc.
            r"^cd\s+\d+.*$",          # "CD 1", "CD 01", etc.
            r"^disc\s+\d+.*$",        # "Disc 1", "Disc 01", etc.
            r"^unknown.*artist.*$",   # Variaciones de "unknown artist"
            r"^unknown.*album.*$",    # Variaciones de "unknown album"
            r"^.*\[.*\]$",           # Nombres con corchetes al final
            r"^.*\(.*\)$",           # Nombres con paréntesis al final (algunos casos)
        ]
        
        # Mapeo de aliases comunes de artistas
        self.artist_aliases = {
            # Variaciones comunes
            "dj": "DJ",
            "mc": "MC",
            "dr": "Dr.",
            "mr": "Mr.",
            "ms": "Ms.",
            "mrs": "Mrs.",
            
            # Casos específicos conocidos
            "eminem": "Eminem",
            "dr dre": "Dr. Dre",
            "dr. dre": "Dr. Dre",
            "jay z": "Jay-Z",
            "jay-z": "Jay-Z",
            "50 cent": "50 Cent",
            "2pac": "2Pac",
            "tupac": "2Pac",
            "biggie": "The Notorious B.I.G.",
            "notorious big": "The Notorious B.I.G.",
            "wu tang": "Wu-Tang Clan",
            "wu-tang": "Wu-Tang Clan",
        }
        
        # Sufijos comunes a remover/normalizar
        self.common_suffixes_to_clean = [
            " - Single", " - EP", " - Album", " - Deluxe", " - Deluxe Edition",
            " - Remastered", " - Remaster", " - Extended", " - Radio Edit",
            " - Club Mix", " - Original Mix", " - Remix", " - VIP Mix",
            " (Single)", " (EP)", " (Album)", " (Deluxe)", " (Deluxe Edition)",
            " (Remastered)", " (Remaster)", " (Extended)", " (Radio Edit)",
            " (Club Mix)", " (Original Mix)", " (Remix)", " (VIP Mix)",
        ]
    
    def is_invalid_value(self, value: str) -> bool:
        """Determina si un valor de artista/álbum es inválido."""
        if not value or value.strip() == "":
            return True
        
        # Verificar valores comunes inválidos
        if value.strip() in self.common_invalid_values:
            return True
        
        # Verificar patrones problemáticos
        for pattern in self.problematic_patterns:
            if re.match(pattern, value.strip(), re.IGNORECASE):
                return True
        
        return False
    
    def normalize_artist_name(self, artist: str) -> str:
        """Normaliza el nombre de un artista."""
        if not artist or self.is_invalid_value(artist):
            return ""
        
        # Limpiar espacios extra
        normalized = re.sub(r'\s+', ' ', artist.strip())
        
        # Aplicar aliases conocidos
        lower_normalized = normalized.lower()
        if lower_normalized in self.artist_aliases:
            return self.artist_aliases[lower_normalized]
        
        # Capitalización apropiada
        # Mantener acrónimos en mayúsculas
        words = normalized.split()
        result_words = []
        
        for word in words:
            # Si es un acrónimo (todas mayúsculas), mantenerlo
            if word.isupper() and len(word) <= 4:
                result_words.append(word)
            # Si contiene puntos (Dr., Mr., etc.), capitalizar apropiadamente
            elif '.' in word:
                result_words.append(word.title())
            # Casos especiales
            elif word.lower() in ['dj', 'mc', 'dr', 'mr', 'ms', 'mrs']:
                result_words.append(word.upper() if word.lower() in ['dj', 'mc'] else word.title())
            else:
                result_words.append(word.title())
        
        return ' '.join(result_words)
    
    def normalize_album_name(self, album: str) -> str:
        """Normaliza el nombre de un álbum."""
        if not album or self.is_invalid_value(album):
            return ""
        
        # Limpiar espacios extra
        normalized = re.sub(r'\s+', ' ', album.strip())
        
        # Remover sufijos comunes innecesarios
        for suffix in self.common_suffixes_to_clean:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
                break
        
        # Capitalización apropiada para álbumes
        # Los álbumes suelen tener capitalización de título
        return normalized.title()
    
    def suggest_artist_from_filename(self, file_path: str) -> Optional[str]:
        """Intenta extraer el artista del nombre del archivo."""
        import os
        filename = os.path.basename(file_path)
        
        # Patrones comunes: "Artista - Canción.ext"
        patterns = [
            r'^([^-]+)\s*-\s*[^-]+\.[a-zA-Z0-9]+$',  # Artista - Canción.ext
            r'^([^_]+)_[^_]+\.[a-zA-Z0-9]+$',        # Artista_Canción.ext
            r'^([^\(]+)\s*\([^\)]*\)\.[a-zA-Z0-9]+$', # Artista (info).ext
        ]
        
        for pattern in patterns:
            match = re.match(pattern, filename)
            if match:
                potential_artist = match.group(1).strip()
                # Verificar que no sea un patrón problemático
                if not self.is_invalid_value(potential_artist):
                    return self.normalize_artist_name(potential_artist)
        
        return None
    
    def suggest_album_from_context(self, artist: str, title: str) -> Optional[str]:
        """Sugiere un álbum basado en el contexto del artista y título."""
        # Esta es una implementación básica
        # En una versión más avanzada, se podría consultar APIs
        
        # Si el título contiene información de álbum
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                potential_album = parts[0].strip()
                if not self.is_invalid_value(potential_album):
                    return self.normalize_album_name(potential_album)
        
        return None
    
    def find_similar_artists(self, db_path: str, target_artist: str, threshold: float = 0.8) -> List[str]:
        """Encuentra artistas similares en la base de datos."""
        if not target_artist or self.is_invalid_value(target_artist):
            return []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT artist FROM tracks WHERE artist IS NOT NULL AND artist != ''")
            all_artists = [row[0] for row in cursor.fetchall() if not self.is_invalid_value(row[0])]
            
            conn.close()
            
            # Usar difflib para encontrar coincidencias similares
            similar = difflib.get_close_matches(
                target_artist, all_artists, n=5, cutoff=threshold
            )
            
            return similar
            
        except sqlite3.Error:
            return []
    
    def analyze_artist_album_issues(self, db_path: str) -> List[ArtistAlbumCorrection]:
        """Analiza problemas en artistas y álbumes de la base de datos."""
        corrections = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT file_path, title, artist, album
                FROM tracks
                ORDER BY artist, album
            """)
            
            tracks = cursor.fetchall()
            conn.close()
            
            for file_path, title, artist, album in tracks:
                # Analizar artista
                if self.is_invalid_value(artist):
                    # Intentar extraer del nombre del archivo
                    suggested_artist = self.suggest_artist_from_filename(file_path)
                    if suggested_artist:
                        corrections.append(ArtistAlbumCorrection(
                            file_path=file_path,
                            field="artist",
                            current_value=artist or "N/A",
                            suggested_value=suggested_artist,
                            confidence=0.7,
                            reason="Extraído del nombre del archivo",
                            source="filename_analysis"
                        ))
                elif artist:
                    # Verificar si necesita normalización
                    normalized_artist = self.normalize_artist_name(artist)
                    if normalized_artist != artist:
                        corrections.append(ArtistAlbumCorrection(
                            file_path=file_path,
                            field="artist",
                            current_value=artist,
                            suggested_value=normalized_artist,
                            confidence=0.9,
                            reason="Normalización de formato",
                            source="normalization"
                        ))
                
                # Analizar álbum
                if self.is_invalid_value(album):
                    # Intentar sugerir álbum del contexto
                    if artist and not self.is_invalid_value(artist):
                        suggested_album = self.suggest_album_from_context(artist, title or "")
                        if suggested_album:
                            corrections.append(ArtistAlbumCorrection(
                                file_path=file_path,
                                field="album",
                                current_value=album or "N/A",
                                suggested_value=suggested_album,
                                confidence=0.6,
                                reason="Inferido del contexto",
                                source="context_inference"
                            ))
                elif album:
                    # Verificar si necesita normalización
                    normalized_album = self.normalize_album_name(album)
                    if normalized_album != album:
                        corrections.append(ArtistAlbumCorrection(
                            file_path=file_path,
                            field="album",
                            current_value=album,
                            suggested_value=normalized_album,
                            confidence=0.8,
                            reason="Normalización de formato",
                            source="normalization"
                        ))
            
        except sqlite3.Error as e:
            print(f"Error analizando base de datos: {e}")
        
        return corrections
    
    def get_artist_album_statistics(self, db_path: str) -> Dict:
        """Genera estadísticas de artistas y álbumes."""
        stats = {
            "total_tracks": 0,
            "tracks_with_artist": 0,
            "tracks_with_album": 0,
            "invalid_artists": 0,
            "invalid_albums": 0,
            "unique_artists": 0,
            "unique_albums": 0,
            "most_common_artists": [],
            "most_common_albums": [],
            "problematic_artists": [],
            "problematic_albums": []
        }
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT artist, album FROM tracks")
            tracks = cursor.fetchall()
            conn.close()
            
            artists = []
            albums = []
            problematic_artists = []
            problematic_albums = []
            
            stats["total_tracks"] = len(tracks)
            
            for artist, album in tracks:
                # Analizar artistas
                if artist and not self.is_invalid_value(artist):
                    stats["tracks_with_artist"] += 1
                    artists.append(artist)
                else:
                    stats["invalid_artists"] += 1
                    if artist:
                        problematic_artists.append(artist)
                
                # Analizar álbumes
                if album and not self.is_invalid_value(album):
                    stats["tracks_with_album"] += 1
                    albums.append(album)
                else:
                    stats["invalid_albums"] += 1
                    if album:
                        problematic_albums.append(album)
            
            # Estadísticas de artistas
            stats["unique_artists"] = len(set(artists))
            artist_counts = Counter(artists)
            stats["most_common_artists"] = artist_counts.most_common(10)
            stats["problematic_artists"] = list(set(problematic_artists))[:10]
            
            # Estadísticas de álbumes
            stats["unique_albums"] = len(set(albums))
            album_counts = Counter(albums)
            stats["most_common_albums"] = album_counts.most_common(10)
            stats["problematic_albums"] = list(set(problematic_albums))[:10]
            
        except sqlite3.Error as e:
            print(f"Error generando estadísticas: {e}")
        
        return stats
    
    def apply_corrections(self, db_path: str, corrections: List[ArtistAlbumCorrection], 
                         min_confidence: float = 0.7) -> int:
        """Aplica correcciones de artistas y álbumes a la base de datos."""
        applied = 0
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for correction in corrections:
                if correction.confidence >= min_confidence:
                    if correction.field == "artist":
                        cursor.execute(
                            "UPDATE tracks SET artist = ? WHERE file_path = ?",
                            (correction.suggested_value, correction.file_path)
                        )
                    elif correction.field == "album":
                        cursor.execute(
                            "UPDATE tracks SET album = ? WHERE file_path = ?",
                            (correction.suggested_value, correction.file_path)
                        )
                    applied += 1
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            print(f"Error aplicando correcciones: {e}")
        
        return applied


def main():
    """Función principal para análisis de artistas y álbumes."""
    import os
    
    # Determinar ruta de la base de datos
    project_root = os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(project_root, "config")
    db_path = os.path.join(config_path, "library.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        return
    
    print("🎵 Analizando metadatos de artistas y álbumes...")
    
    enhancer = ArtistAlbumEnhancer()
    
    # Generar estadísticas
    print("📊 Generando estadísticas...")
    stats = enhancer.get_artist_album_statistics(db_path)
    
    print(f"\n📈 Estadísticas Generales:")
    print(f"  • Total de pistas: {stats['total_tracks']}")
    print(f"  • Pistas con artista válido: {stats['tracks_with_artist']} ({stats['tracks_with_artist']/stats['total_tracks']*100:.1f}%)")
    print(f"  • Pistas con álbum válido: {stats['tracks_with_album']} ({stats['tracks_with_album']/stats['total_tracks']*100:.1f}%)")
    print(f"  • Artistas inválidos: {stats['invalid_artists']}")
    print(f"  • Álbumes inválidos: {stats['invalid_albums']}")
    print(f"  • Artistas únicos: {stats['unique_artists']}")
    print(f"  • Álbumes únicos: {stats['unique_albums']}")
    
    # Mostrar artistas más comunes
    if stats['most_common_artists']:
        print(f"\n🎤 Top 5 Artistas:")
        for artist, count in stats['most_common_artists'][:5]:
            print(f"  • {artist}: {count} pistas")
    
    # Mostrar álbumes más comunes
    if stats['most_common_albums']:
        print(f"\n💿 Top 5 Álbumes:")
        for album, count in stats['most_common_albums'][:5]:
            print(f"  • {album}: {count} pistas")
    
    # Mostrar problemas detectados
    if stats['problematic_artists']:
        print(f"\n⚠️  Artistas Problemáticos:")
        for artist in stats['problematic_artists'][:5]:
            print(f"  • '{artist}'")
    
    if stats['problematic_albums']:
        print(f"\n⚠️  Álbumes Problemáticos:")
        for album in stats['problematic_albums'][:5]:
            print(f"  • '{album}'")
    
    # Analizar correcciones
    print(f"\n🔍 Analizando correcciones sugeridas...")
    corrections = enhancer.analyze_artist_album_issues(db_path)
    
    if corrections:
        print(f"📝 Se encontraron {len(corrections)} correcciones sugeridas:")
        
        # Agrupar por tipo
        artist_corrections = [c for c in corrections if c.field == "artist"]
        album_corrections = [c for c in corrections if c.field == "album"]
        
        if artist_corrections:
            print(f"\n🎤 Correcciones de Artistas ({len(artist_corrections)}):")
            for correction in artist_corrections[:5]:
                filename = os.path.basename(correction.file_path)
                print(f"  • {filename}")
                print(f"    '{correction.current_value}' → '{correction.suggested_value}'")
                print(f"    Confianza: {correction.confidence:.1f}, Razón: {correction.reason}")
        
        if album_corrections:
            print(f"\n💿 Correcciones de Álbumes ({len(album_corrections)}):")
            for correction in album_corrections[:5]:
                filename = os.path.basename(correction.file_path)
                print(f"  • {filename}")
                print(f"    '{correction.current_value}' → '{correction.suggested_value}'")
                print(f"    Confianza: {correction.confidence:.1f}, Razón: {correction.reason}")
        
        # Preguntar si aplicar correcciones de alta confianza
        high_confidence = [c for c in corrections if c.confidence >= 0.8]
        if high_confidence:
            print(f"\n💡 {len(high_confidence)} correcciones tienen alta confianza (≥0.8)")
            print("Estas correcciones se pueden aplicar automáticamente.")
    else:
        print("✅ No se encontraron problemas que requieran corrección")


if __name__ == "__main__":
    main()