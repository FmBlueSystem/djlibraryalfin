#!/usr/bin/env python3
"""
Script para corregir valores NA en la base de datos de DjAlfin
"""

import sqlite3
import os
import re

def get_db_path():
    """Get the correct database path"""
    return os.path.join("config", "library.db")

def fix_na_values():
    """Fix NA values in the database"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    print(f"🔧 Corrigiendo valores NA en: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tracks with NA values
        cursor.execute("""
            SELECT id, file_path, title, artist, album 
            FROM tracks 
            WHERE artist = 'N/A' OR artist = 'N A' OR artist = 'NA' 
               OR album = 'N/A' OR album = 'N A' OR album = 'NA'
               OR title = 'N/A' OR title = 'N A' OR title = 'NA'
        """)
        
        tracks_with_na = cursor.fetchall()
        
        if not tracks_with_na:
            print("✅ No se encontraron valores NA para corregir")
            return
        
        print(f"📝 Encontradas {len(tracks_with_na)} pistas con valores NA")
        
        corrections = 0
        
        for track_id, file_path, title, artist, album in tracks_with_na:
            # Extract info from filename
            filename = os.path.basename(file_path)
            filename_without_ext = os.path.splitext(filename)[0]
            
            # Try to extract artist and title from filename
            # Common patterns: "Artist - Title", "Artist-Title"
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
            
            # Clean up extracted names
            if extracted_artist:
                # Remove common suffixes
                extracted_artist = re.sub(r'_PN$', '', extracted_artist)
                extracted_artist = re.sub(r'\(.*\)$', '', extracted_artist).strip()
            
            if extracted_title:
                # Remove common suffixes and clean up
                extracted_title = re.sub(r'_PN$', '', extracted_title)
                extracted_title = re.sub(r'\(.*\)$', '', extracted_title).strip()
            
            # Apply corrections
            new_artist = artist
            new_title = title
            new_album = album
            
            if artist in ['N/A', 'N A', 'NA'] and extracted_artist:
                new_artist = extracted_artist
                corrections += 1
                print(f"  🎤 Artist: '{artist}' → '{new_artist}'")
            
            if title in ['N/A', 'N A', 'NA'] and extracted_title:
                new_title = extracted_title
                corrections += 1
                print(f"  🎵 Title: '{title}' → '{new_title}'")
            
            if album in ['N/A', 'N A', 'NA']:
                # Try to infer album from common patterns or set to Unknown
                new_album = 'Unknown Album'
                corrections += 1
                print(f"  💿 Album: '{album}' → '{new_album}'")
            
            # Update the record if any changes were made
            if new_artist != artist or new_title != title or new_album != album:
                cursor.execute("""
                    UPDATE tracks 
                    SET artist = ?, title = ?, album = ?
                    WHERE id = ?
                """, (new_artist, new_title, new_album, track_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Se aplicaron {corrections} correcciones")
        print("🎉 Corrección de valores NA completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_stats():
    """Show current database statistics"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count NA values
        cursor.execute("""
            SELECT 
                COUNT(*) as total_tracks,
                SUM(CASE WHEN artist IN ('N/A', 'N A', 'NA') THEN 1 ELSE 0 END) as na_artists,
                SUM(CASE WHEN album IN ('N/A', 'N A', 'NA') THEN 1 ELSE 0 END) as na_albums,
                SUM(CASE WHEN title IN ('N/A', 'N A', 'NA') THEN 1 ELSE 0 END) as na_titles,
                SUM(CASE WHEN genre = 'Unknown' THEN 1 ELSE 0 END) as unknown_genres
            FROM tracks
        """)
        
        stats = cursor.fetchone()
        total, na_artists, na_albums, na_titles, unknown_genres = stats
        
        print("📊 ESTADÍSTICAS ACTUALES:")
        print("=" * 50)
        print(f"📈 Total de pistas: {total}")
        print(f"🎤 Artistas N/A: {na_artists}")
        print(f"💿 Álbumes N/A: {na_albums}")
        print(f"🎵 Títulos N/A: {na_titles}")
        print(f"🎼 Géneros Unknown: {unknown_genres}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎵 CORRECTOR DE VALORES NA - DjAlfin")
    print("=" * 50)
    
    # Show stats before
    print("\n📊 ANTES:")
    show_stats()
    
    # Apply fixes
    print("\n🔧 APLICANDO CORRECCIONES:")
    fix_na_values()
    
    # Show stats after
    print("\n📊 DESPUÉS:")
    show_stats()