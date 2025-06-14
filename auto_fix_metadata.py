#!/usr/bin/env python3
"""
Sistema automático de corrección de metadatos problemáticos para DjAlfin
Integra la lógica de corrección con el sistema de enriquecimiento existente
"""

import os
import re
import sqlite3
from typing import Dict, List, Optional, Any
from core.metadata_enricher import MetadataEnricher, TrackMetadata

class AutoMetadataFixer(MetadataEnricher):
    """
    Extensión del MetadataEnricher que incluye corrección automática 
    de valores problemáticos como N/A y Unknown
    """
    
    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        
        # Mapeo de correcciones de género basado en conocimiento de artistas
        self.artist_genre_map = {
            'spice girls': 'Pop',
            'coldplay': 'Alternative Rock',
            'the chainsmokers': 'Electronic',
            'stephane deschezeaux': 'Electronic',
            'alice cooper': 'Rock',
            'status quo': 'Rock',
            'oasis': 'Rock',
            'rolling stones': 'Rock',
            'blue oyster cult': 'Rock',
            'rihanna': 'R&B',
            'drake': 'Hip Hop',
            'whitney houston': 'R&B',
            'dolly parton': 'Country',
            'mavericks': 'Country Rock',
            'apache indian': 'Reggae',
            'sean paul': 'Reggae',
        }
        
        # Patrones en títulos que sugieren géneros
        self.title_genre_patterns = {
            'club mix': 'Electronic',
            'remix': 'Electronic',
            'dj beats': 'Electronic',
            'original mix': 'Electronic',
            'extended': 'Electronic',
            'radio edit': 'Pop',
        }
    
    def fix_na_values(self, track: TrackMetadata) -> TrackMetadata:
        """Corrige valores N/A extrayendo información del nombre del archivo"""
        invalid_values = {'N/A', 'N A', 'NA', 'Unknown', 'unknown', 'UNKNOWN'}
        
        # Extraer información del nombre del archivo si es necesario
        filename = os.path.basename(track.file_path)
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Patrones comunes: "Artist - Title", "Artist_Title"
        patterns = [
            r'^(.+?)\s*-\s*(.+)$',  # Artist - Title
            r'^(.+?)_(.+)$',        # Artist_Title
        ]
        
        extracted_artist = None
        extracted_title = None
        
        for pattern in patterns:
            match = re.match(pattern, filename_without_ext)
            if match:
                extracted_artist = match.group(1).strip()
                extracted_title = match.group(2).strip()
                break
        
        # Limpiar nombres extraídos
        if extracted_artist:
            extracted_artist = re.sub(r'_PN$', '', extracted_artist)
            extracted_artist = re.sub(r'\(.*\)$', '', extracted_artist).strip()
        
        if extracted_title:
            extracted_title = re.sub(r'_PN$', '', extracted_title)
            extracted_title = re.sub(r'\(.*\)$', '', extracted_title).strip()
        
        # Aplicar correcciones
        if track.artist and track.artist.strip() in invalid_values and extracted_artist:
            track.artist = extracted_artist
            
        if track.title and track.title.strip() in invalid_values and extracted_title:
            track.title = extracted_title
            
        if track.album and track.album.strip() in invalid_values:
            track.album = 'Unknown Album'
        
        return track
    
    def fix_unknown_genre(self, track: TrackMetadata) -> TrackMetadata:
        """Corrige géneros Unknown usando conocimiento de artistas y patrones"""
        if not track.genre or track.genre.strip() in {'Unknown', 'unknown', 'UNKNOWN'}:
            new_genre = 'Unknown'
            
            # Buscar por artista
            if track.artist:
                artist_lower = track.artist.lower()
                for artist_key, genre in self.artist_genre_map.items():
                    if artist_key in artist_lower:
                        new_genre = genre
                        break
            
            # Si aún es desconocido, buscar por patrones en el título
            if new_genre == 'Unknown' and track.title:
                title_lower = track.title.lower()
                filename_lower = os.path.basename(track.file_path).lower()
                
                for pattern, genre in self.title_genre_patterns.items():
                    if pattern in title_lower or pattern in filename_lower:
                        new_genre = 'Electronic'  # La mayoría de remixes son electrónicos
                        break
            
            # Inferencia por año como último recurso
            if new_genre == 'Unknown' and track.year:
                if track.year < 1980:
                    new_genre = 'Rock'
                elif track.year < 1990:
                    new_genre = 'Pop'
                elif track.year < 2000:
                    new_genre = 'Pop'
                else:
                    new_genre = 'Electronic'
            
            # Si todavía es desconocido, asignar Pop como género general
            if new_genre == 'Unknown':
                new_genre = 'Pop'
            
            track.genre = new_genre
        
        return track
    
    def auto_fix_track(self, track: TrackMetadata) -> TrackMetadata:
        """Aplica todas las correcciones automáticas a una pista"""
        # Primero corregir valores N/A
        track = self.fix_na_values(track)
        
        # Luego corregir géneros Unknown
        track = self.fix_unknown_genre(track)
        
        return track
    
    def enrich_track_with_auto_fix(self, track: TrackMetadata, write_to_file: bool = False) -> tuple:
        """
        Enriquece una pista aplicando primero correcciones automáticas
        y luego buscando en APIs externas si es necesario
        """
        # Aplicar correcciones automáticas primero
        original_track = TrackMetadata(
            file_path=track.file_path,
            title=track.title,
            artist=track.artist,
            album=track.album,
            genre=track.genre,
            year=track.year,
            bpm=track.bpm,
            key=track.key,
            energy=track.energy
        )
        
        fixed_track = self.auto_fix_track(track)
        
        # Verificar si se hicieron correcciones automáticas
        auto_fixed = False
        corrections = {}
        
        if original_track.artist != fixed_track.artist:
            corrections['artist'] = fixed_track.artist
            auto_fixed = True
            
        if original_track.title != fixed_track.title:
            corrections['title'] = fixed_track.title
            auto_fixed = True
            
        if original_track.album != fixed_track.album:
            corrections['album'] = fixed_track.album
            auto_fixed = True
            
        if original_track.genre != fixed_track.genre:
            corrections['genre'] = fixed_track.genre
            auto_fixed = True
        
        # Si se hicieron correcciones automáticas, actualizar la BD
        if auto_fixed:
            self._update_track_metadata(track.file_path, corrections)
            print(f"🔧 Auto-correcciones aplicadas a {os.path.basename(track.file_path)}")
            for field, value in corrections.items():
                print(f"  • {field}: '{getattr(original_track, field)}' → '{value}'")
        
        # Si después de las correcciones automáticas aún faltan metadatos,
        # usar el sistema de enriquecimiento de APIs
        if not fixed_track.is_complete():
            return super().enrich_track(fixed_track, write_to_file)
        else:
            return True, "Metadatos corregidos automáticamente.", corrections if auto_fixed else None
    
    def auto_fix_library(self, write_to_file: bool = False) -> List[tuple]:
        """Aplica correcciones automáticas a toda la biblioteca"""
        print("🔧 Iniciando corrección automática de metadatos...")
        
        # Obtener todas las pistas (no solo las incompletas)
        all_tracks = self.get_all_tracks()
        
        if not all_tracks:
            print("✅ No hay pistas en la biblioteca.")
            return []
        
        total_tracks = len(all_tracks)
        results = []
        fixed_count = 0
        
        for i, track in enumerate(all_tracks):
            print(f"\n[{i+1}/{total_tracks}] Procesando: {os.path.basename(track.file_path)}")
            
            success, message, metadata = self.enrich_track_with_auto_fix(track, write_to_file)
            results.append((track.file_path, success, message))
            
            if success and metadata:
                fixed_count += 1
        
        print(f"\n🎉 Corrección automática completada!")
        print(f"📊 Pistas procesadas: {total_tracks}")
        print(f"✅ Pistas corregidas: {fixed_count}")
        
        return results

def main():
    """Función principal para ejecutar las correcciones automáticas"""
    print("🎵 SISTEMA AUTOMÁTICO DE CORRECCIÓN DE METADATOS - DjAlfin")
    print("=" * 60)
    
    fixer = AutoMetadataFixer()
    
    # Mostrar estadísticas antes
    stats_before = fixer.get_enrichment_statistics()
    print(f"\n📊 ESTADO ANTES:")
    print(f"  • Total de pistas: {stats_before['total_tracks']}")
    print(f"  • Pistas completas: {stats_before['complete_tracks']}")
    print(f"  • Pistas incompletas: {stats_before['incomplete_tracks']}")
    print(f"  • Porcentaje completado: {stats_before['completion_percentage']:.1f}%")
    
    # Aplicar correcciones
    fixer.auto_fix_library(write_to_file=False)
    
    # Mostrar estadísticas después
    stats_after = fixer.get_enrichment_statistics()
    print(f"\n📊 ESTADO DESPUÉS:")
    print(f"  • Total de pistas: {stats_after['total_tracks']}")
    print(f"  • Pistas completas: {stats_after['complete_tracks']}")
    print(f"  • Pistas incompletas: {stats_after['incomplete_tracks']}")
    print(f"  • Porcentaje completado: {stats_after['completion_percentage']:.1f}%")
    
    improvement = stats_after['completion_percentage'] - stats_before['completion_percentage']
    if improvement > 0:
        print(f"📈 Mejora: +{improvement:.1f}% de completitud")

if __name__ == "__main__":
    main()