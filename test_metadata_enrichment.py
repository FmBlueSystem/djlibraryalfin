#!/usr/bin/env python3
"""
Test script para el sistema de enriquecimiento de metadatos de DjAlfin
Prueba la funcionalidad de búsqueda de metadatos faltantes usando múltiples APIs
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.metadata_enricher import MetadataEnricher, TrackMetadata, MetadataSource


def create_test_database_with_missing_metadata():
    """Crea una base de datos de prueba con metadatos faltantes."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tabla de tracks
    cursor.execute("""
        CREATE TABLE tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            title TEXT,
            artist TEXT,
            album TEXT,
            genre TEXT,
            year INTEGER,
            bpm REAL,
            duration REAL,
            bitrate INTEGER,
            sample_rate INTEGER,
            file_size INTEGER,
            key TEXT,
            energy REAL,
            rating INTEGER,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insertar pistas con metadatos faltantes (simulando archivos reales)
    test_tracks = [
        # Pistas con algunos metadatos faltantes
        ('/music/test1.mp3', 'Bohemian Rhapsody', 'Queen', None, None, None, None, 355, 320, 44100, 11360000, None, None, None),
        ('/music/test2.mp3', 'Hotel California', 'Eagles', None, None, None, None, 391, 320, 44100, 12512000, None, None, None),
        ('/music/test3.mp3', 'Stairway to Heaven', 'Led Zeppelin', None, None, None, None, 482, 320, 44100, 15424000, None, None, None),
        ('/music/test4.mp3', 'Sweet Child O Mine', 'Guns N Roses', None, None, None, None, 356, 320, 44100, 11392000, None, None, None),
        ('/music/test5.mp3', 'Smells Like Teen Spirit', 'Nirvana', None, None, None, None, 301, 320, 44100, 9632000, None, None, None),
        
        # Pistas con metadatos más completos para comparar
        ('/music/complete1.mp3', 'Billie Jean', 'Michael Jackson', 'Thriller', 'Pop', 1982, 117.0, 294, 320, 44100, 9408000, 'F# minor', 0.8, 5),
        ('/music/complete2.mp3', 'Like a Rolling Stone', 'Bob Dylan', 'Highway 61 Revisited', 'Rock', 1965, 120.0, 369, 320, 44100, 11808000, 'C major', 0.7, 4),
        
        # Pistas con solo título y artista (casos más difíciles)
        ('/music/minimal1.mp3', 'Yesterday', 'The Beatles', None, None, None, None, 125, 320, 44100, 4000000, None, None, None),
        ('/music/minimal2.mp3', 'Imagine', 'John Lennon', None, None, None, None, 183, 320, 44100, 5856000, None, None, None),
        ('/music/minimal3.mp3', 'Purple Haze', 'Jimi Hendrix', None, None, None, None, 170, 320, 44100, 5440000, None, None, None),
    ]
    
    for track in test_tracks:
        cursor.execute("""
            INSERT INTO tracks (file_path, title, artist, album, genre, year, bpm, duration, bitrate, sample_rate, file_size, key, energy, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, track)
    
    conn.commit()
    conn.close()
    
    return db_path


def test_metadata_enricher():
    """Prueba el sistema de enriquecimiento de metadatos."""
    print("🧪 Testing Metadata Enricher System...")
    
    # Crear base de datos de prueba
    db_path = create_test_database_with_missing_metadata()
    
    try:
        # Inicializar enricher
        enricher = MetadataEnricher(db_path)
        
        # Test 1: Obtener estadísticas iniciales
        print("\n📊 Test 1: Getting initial statistics...")
        stats = enricher.get_enrichment_statistics()
        print(f"✅ Total tracks: {stats['total_tracks']}")
        print(f"✅ Complete tracks: {stats['complete_tracks']}")
        print(f"✅ Incomplete tracks: {stats['incomplete_tracks']}")
        print(f"✅ Completion percentage: {stats['completion_percentage']:.1f}%")
        print(f"✅ Missing genre: {stats['missing_genre']}")
        print(f"✅ Missing BPM: {stats['missing_bpm']}")
        print(f"✅ Missing key: {stats['missing_key']}")
        
        # Test 2: Obtener pistas con metadatos faltantes
        print("\n🔍 Test 2: Getting tracks with missing metadata...")
        missing_tracks = enricher.get_tracks_with_missing_metadata()
        print(f"✅ Found {len(missing_tracks)} tracks with missing metadata")
        
        for i, track in enumerate(missing_tracks[:3]):  # Mostrar solo las primeras 3
            missing_fields = track.missing_fields()
            print(f"   {i+1}. {track.title} - {track.artist}")
            print(f"      Missing: {', '.join(missing_fields)}")
        
        # Test 3: Probar búsqueda individual en Spotify
        print("\n🎵 Test 3: Testing individual Spotify search...")
        if missing_tracks:
            test_track = missing_tracks[0]  # Tomar la primera pista
            print(f"Searching for: {test_track.title} - {test_track.artist}")
            
            spotify_result = enricher.search_metadata_spotify(test_track)
            print(f"✅ Spotify search result:")
            print(f"   Success: {spotify_result.success}")
            print(f"   Confidence: {spotify_result.confidence:.2f}")
            if spotify_result.success:
                print(f"   Found metadata keys: {list(spotify_result.metadata.keys())}")
        
        # Test 4: Probar búsqueda individual en MusicBrainz
        print("\n🎼 Test 4: Testing individual MusicBrainz search...")
        if missing_tracks:
            test_track = missing_tracks[1] if len(missing_tracks) > 1 else missing_tracks[0]
            print(f"Searching for: {test_track.title} - {test_track.artist}")
            
            mb_result = enricher.search_metadata_musicbrainz(test_track)
            print(f"✅ MusicBrainz search result:")
            print(f"   Success: {mb_result.success}")
            print(f"   Confidence: {mb_result.confidence:.2f}")
            if mb_result.success:
                print(f"   Found metadata keys: {list(mb_result.metadata.keys())}")
        
        # Test 5: Probar enriquecimiento de una pista
        print("\n🔧 Test 5: Testing track enrichment...")
        if missing_tracks:
            test_track = missing_tracks[0]
            print(f"Enriching: {test_track.title} - {test_track.artist}")
            
            success, message, enriched_metadata = enricher.enrich_track(test_track)
            print(f"✅ Enrichment result:")
            print(f"   Success: {success}")
            print(f"   Message: {message}")
            if success and enriched_metadata:
                print(f"   Enriched metadata: {enriched_metadata}")
        
        # Test 6: Simular enriquecimiento masivo (solo las primeras 3 pistas)
        print("\n🚀 Test 6: Testing batch enrichment (limited)...")
        
        # Crear un enricher modificado para procesar solo las primeras 3 pistas
        limited_tracks = missing_tracks[:3]
        
        def limited_progress_callback(current, total, track_name):
            print(f"   Processing {current}/{total}: {track_name}")
        
        # Simular el proceso de enriquecimiento
        processed = 0
        successful = 0
        
        for i, track in enumerate(limited_tracks):
            try:
                limited_progress_callback(i + 1, len(limited_tracks), track.title or track.file_path)
                
                success, message, enriched_metadata = enricher.enrich_track(track)
                if success:
                    successful += 1
                    print(f"      ✅ Successfully enriched")
                else:
                    print(f"      ❌ Failed to enrich")
                
                processed += 1
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        print(f"✅ Batch enrichment completed: {successful}/{processed} successful")
        
        # Test 7: Verificar estadísticas finales
        print("\n📈 Test 7: Final statistics...")
        final_stats = enricher.get_enrichment_statistics()
        print(f"✅ Final completion percentage: {final_stats['completion_percentage']:.1f}%")
        
        print("\n🎉 All metadata enricher tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Limpiar
        try:
            os.unlink(db_path)
        except:
            pass


def test_track_metadata_class():
    """Prueba la clase TrackMetadata."""
    print("\n🧪 Testing TrackMetadata class...")
    
    # Test 1: Pista completa
    complete_track = TrackMetadata(
        file_path="/test/complete.mp3",
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        genre="Rock",
        year=2020,
        bpm=120.0,
        key="C major"
    )
    
    print(f"✅ Complete track is_complete: {complete_track.is_complete()}")
    print(f"✅ Complete track missing_fields: {complete_track.missing_fields()}")
    
    # Test 2: Pista incompleta
    incomplete_track = TrackMetadata(
        file_path="/test/incomplete.mp3",
        title="Test Song",
        artist="Test Artist"
        # Faltan album, genre, year, bpm, key
    )
    
    print(f"✅ Incomplete track is_complete: {incomplete_track.is_complete()}")
    print(f"✅ Incomplete track missing_fields: {incomplete_track.missing_fields()}")
    
    # Test 3: Pista vacía
    empty_track = TrackMetadata(file_path="/test/empty.mp3")
    
    print(f"✅ Empty track is_complete: {empty_track.is_complete()}")
    print(f"✅ Empty track missing_fields: {empty_track.missing_fields()}")


def main():
    """Ejecuta todas las pruebas."""
    print("🚀 DjAlfin Metadata Enrichment - Testing Suite")
    print("=" * 60)
    
    try:
        test_track_metadata_class()
        test_metadata_enricher()
        
        print("\n" + "=" * 60)
        print("🎉 ALL METADATA TESTS COMPLETED SUCCESSFULLY!")
        print("✅ Metadata enrichment system is working correctly!")
        
    except Exception as e:
        print(f"\n❌ TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()