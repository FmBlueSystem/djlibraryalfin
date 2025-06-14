#!/usr/bin/env python3
"""
Script para corregir géneros Unknown restantes en la base de datos de DjAlfin
"""

import sqlite3
import os

def get_db_path():
    """Get the correct database path"""
    return os.path.join("config", "library.db")

def fix_unknown_genres():
    """Fix remaining Unknown genres based on artist and track context"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    print(f"🔧 Corrigiendo géneros Unknown en: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tracks with Unknown genre
        cursor.execute("""
            SELECT id, file_path, title, artist, album, year 
            FROM tracks 
            WHERE genre = 'Unknown'
        """)
        
        unknown_tracks = cursor.fetchall()
        
        if not unknown_tracks:
            print("✅ No se encontraron géneros Unknown para corregir")
            return
        
        print(f"📝 Encontradas {len(unknown_tracks)} pistas con género Unknown")
        
        # Genre corrections based on artist knowledge and track analysis
        genre_corrections = {
            # Electronic/Dance artists and remixes
            'spice girls': 'Pop',
            'coldplay': 'Alternative Rock',
            'the chainsmokers': 'Electronic',
            'stephane deschezeaux': 'Electronic',
            'alice cooper': 'Rock',
            'status quo': 'Rock',
        }
        
        # Track name patterns that suggest genres
        track_patterns = {
            'club mix': 'Electronic',
            'remix': 'Electronic',
            'dj beats': 'Electronic',
            'don diablo': 'Electronic',
            'original mix': 'Electronic',
        }
        
        corrections = 0
        
        for track_id, file_path, title, artist, album, year in unknown_tracks:
            new_genre = 'Unknown'
            reason = ''
            
            # Check artist-based corrections
            artist_lower = artist.lower() if artist else ''
            for artist_key, genre in genre_corrections.items():
                if artist_key in artist_lower:
                    new_genre = genre
                    reason = f'basado en artista: {artist}'
                    break
            
            # If still unknown, check track patterns
            if new_genre == 'Unknown':
                title_lower = title.lower() if title else ''
                filename_lower = os.path.basename(file_path).lower()
                
                for pattern, genre in track_patterns.items():
                    if pattern in title_lower or pattern in filename_lower:
                        new_genre = genre
                        reason = f'basado en patrón: {pattern}'
                        break
            
            # Year-based inference as last resort
            if new_genre == 'Unknown' and year:
                if year < 1980:
                    new_genre = 'Rock'
                    reason = 'inferido por año (pre-1980)'
                elif year < 1990:
                    new_genre = 'Pop'
                    reason = 'inferido por año (1980s)'
                elif year < 2000:
                    new_genre = 'Pop'
                    reason = 'inferido por año (1990s)'
                else:
                    new_genre = 'Electronic'
                    reason = 'inferido por año (2000+)'
            
            # Apply correction if found
            if new_genre != 'Unknown':
                cursor.execute("""
                    UPDATE tracks 
                    SET genre = ?
                    WHERE id = ?
                """, (new_genre, track_id))
                
                corrections += 1
                print(f"  🎼 '{title}' por {artist} → '{new_genre}' ({reason})")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Se aplicaron {corrections} correcciones de género")
        print("🎉 Corrección de géneros Unknown completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_genre_stats():
    """Show current genre statistics"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get genre distribution
        cursor.execute("""
            SELECT genre, COUNT(*) as count
            FROM tracks
            GROUP BY genre
            ORDER BY count DESC, genre
        """)
        
        genres = cursor.fetchall()
        total_tracks = sum(count for _, count in genres)
        
        print("📊 DISTRIBUCIÓN DE GÉNEROS:")
        print("=" * 40)
        print(f"📈 Total de pistas: {total_tracks}")
        print("\n🎼 Géneros:")
        
        for i, (genre, count) in enumerate(genres[:10], 1):
            percentage = (count / total_tracks) * 100
            print(f"   {i:2d}. {genre}: {count} pistas ({percentage:.1f}%)")
        
        # Count unknowns
        unknown_count = sum(count for genre, count in genres if genre == 'Unknown')
        print(f"\n⚠️  Géneros Unknown restantes: {unknown_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎼 CORRECTOR DE GÉNEROS UNKNOWN - DjAlfin")
    print("=" * 50)
    
    # Show stats before
    print("\n📊 ANTES:")
    show_genre_stats()
    
    # Apply fixes
    print("\n🔧 APLICANDO CORRECCIONES:")
    fix_unknown_genres()
    
    # Show stats after
    print("\n📊 DESPUÉS:")
    show_genre_stats()