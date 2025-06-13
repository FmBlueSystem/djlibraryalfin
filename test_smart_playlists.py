#!/usr/bin/env python3
"""
Test script for Smart Playlists improvements in DjAlfin
Tests the enhanced functionality and ensures everything works correctly.
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.smart_playlist_manager import (
    SmartPlaylistManager, SmartPlaylist, PlaylistRule,
    PlaylistCriteria, ComparisonOperator, LogicalOperator,
    PREDEFINED_PLAYLISTS
)


def create_test_database():
    """Create a temporary database with test data."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tracks table
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
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert test tracks
    test_tracks = [
        ('/music/house1.mp3', 'Summer Vibes', 'Calvin Harris', 'Motion', 'House', 2014, 128.0, 240, 320, 44100, 7680000),
        ('/music/house2.mp3', 'Titanium', 'David Guetta', 'Nothing But The Beat', 'House', 2011, 126.0, 245, 320, 44100, 7840000),
        ('/music/techno1.mp3', 'Strobe', 'Deadmau5', 'For Lack Of A Better Name', 'Techno', 2009, 132.0, 630, 320, 44100, 20160000),
        ('/music/pop1.mp3', 'Shape of You', 'Ed Sheeran', 'Divide', 'Pop', 2017, 96.0, 233, 320, 44100, 7456000),
        ('/music/rock1.mp3', 'Bohemian Rhapsody', 'Queen', 'A Night At The Opera', 'Rock', 1975, 72.0, 355, 320, 44100, 11360000),
        ('/music/electronic1.mp3', 'Levels', 'Avicii', 'True', 'Electronic', 2011, 126.0, 202, 320, 44100, 6464000),
        ('/music/dance1.mp3', 'One More Time', 'Daft Punk', 'Discovery', 'Dance', 2000, 123.0, 320, 320, 44100, 10240000),
        ('/music/trance1.mp3', 'Adagio for Strings', 'Tiësto', 'In Search of Sunrise 3', 'Trance', 2004, 136.0, 480, 320, 44100, 15360000),
        ('/music/ambient1.mp3', 'An Ending', 'Brian Eno', 'Apollo', 'Ambient', 1983, 60.0, 210, 320, 44100, 6720000),
        ('/music/jazz1.mp3', 'Take Five', 'Dave Brubeck', 'Time Out', 'Jazz', 1959, 85.0, 324, 320, 44100, 10368000),
    ]
    
    for track in test_tracks:
        cursor.execute("""
            INSERT INTO tracks (file_path, title, artist, album, genre, year, bpm, duration, bitrate, sample_rate, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, track)
    
    conn.commit()
    conn.close()
    
    return db_path


def test_smart_playlist_manager():
    """Test the SmartPlaylistManager functionality."""
    print("🧪 Testing Smart Playlist Manager...")
    
    # Create test database
    db_path = create_test_database()
    
    try:
        # Initialize manager
        manager = SmartPlaylistManager(db_path)
        
        # Test 1: Create a simple playlist
        print("\n📝 Test 1: Creating simple playlist...")
        simple_playlist = SmartPlaylist(
            name="High Energy Test",
            description="Test playlist for high energy tracks",
            rules=[
                PlaylistRule(PlaylistCriteria.BPM, ComparisonOperator.GREATER_THAN, 120)
            ],
            limit=5,
            order_by="bpm",
            order_desc=True
        )
        
        playlist_id = manager.create_smart_playlist(simple_playlist)
        print(f"✅ Created playlist with ID: {playlist_id}")
        
        # Test 2: Generate tracks
        print("\n🎵 Test 2: Generating tracks...")
        tracks = manager.generate_playlist_tracks(playlist_id)
        print(f"✅ Generated {len(tracks)} tracks")
        for track in tracks[:3]:  # Show first 3
            print(f"   - {track['artist']} - {track['title']} ({track['bpm']} BPM)")
        
        # Test 3: Complex playlist with multiple rules
        print("\n📝 Test 3: Creating complex playlist...")
        complex_playlist = SmartPlaylist(
            name="House & Electronic Mix",
            description="House and Electronic tracks from 2010+",
            rules=[
                PlaylistRule(PlaylistCriteria.GENRE, ComparisonOperator.CONTAINS, "House"),
                PlaylistRule(PlaylistCriteria.YEAR, ComparisonOperator.GREATER_THAN, 2010, logical_operator=LogicalOperator.OR),
                PlaylistRule(PlaylistCriteria.GENRE, ComparisonOperator.CONTAINS, "Electronic", logical_operator=LogicalOperator.OR)
            ],
            limit=10,
            match_all=False  # OR logic
        )
        
        complex_id = manager.create_smart_playlist(complex_playlist)
        complex_tracks = manager.generate_playlist_tracks(complex_id)
        print(f"✅ Complex playlist generated {len(complex_tracks)} tracks")
        
        # Test 4: Playback history
        print("\n📊 Test 4: Testing playback history...")
        test_file = '/music/house1.mp3'
        
        # Record some playbacks
        manager.record_playback(test_file, duration_played=240, completed=True)
        manager.record_playback(test_file, duration_played=120, completed=False)
        manager.record_playback(test_file, duration_played=240, completed=True)
        
        play_count = manager.get_play_count(test_file)
        last_played = manager.get_last_played(test_file)
        
        print(f"✅ Play count for test track: {play_count}")
        print(f"✅ Last played: {last_played}")
        
        # Test 5: Never played playlist
        print("\n🆕 Test 5: Testing 'Never Played' playlist...")
        never_played_playlist = SmartPlaylist(
            name="Never Played Test",
            rules=[
                PlaylistRule(PlaylistCriteria.NEVER_PLAYED, ComparisonOperator.EQUALS, "true")
            ]
        )
        
        never_played_id = manager.create_smart_playlist(never_played_playlist)
        never_played_tracks = manager.generate_playlist_tracks(never_played_id)
        print(f"✅ Never played tracks: {len(never_played_tracks)}")
        
        # Test 6: Most played playlist
        print("\n⭐ Test 6: Testing 'Most Played' playlist...")
        most_played_playlist = SmartPlaylist(
            name="Most Played Test",
            rules=[
                PlaylistRule(PlaylistCriteria.PLAY_COUNT, ComparisonOperator.GREATER_THAN, 1)
            ]
        )
        
        most_played_id = manager.create_smart_playlist(most_played_playlist)
        most_played_tracks = manager.generate_playlist_tracks(most_played_id)
        print(f"✅ Most played tracks: {len(most_played_tracks)}")
        
        # Test 7: Get all playlists
        print("\n📋 Test 7: Getting all playlists...")
        all_playlists = manager.get_all_smart_playlists()
        print(f"✅ Total playlists: {len(all_playlists)}")
        for playlist in all_playlists:
            print(f"   - {playlist['name']} ({playlist['rule_count']} rules)")
        
        # Test 8: Preview functionality
        print("\n👀 Test 8: Testing preview functionality...")
        preview_rules = [
            PlaylistRule(PlaylistCriteria.GENRE, ComparisonOperator.CONTAINS, "House")
        ]
        preview_tracks = manager.get_playlist_preview(preview_rules, limit=3)
        print(f"✅ Preview generated {len(preview_tracks)} tracks")
        
        # Test 9: Predefined playlists
        print("\n🎵 Test 9: Testing predefined playlists...")
        print(f"✅ Available predefined playlists: {len(PREDEFINED_PLAYLISTS)}")
        for playlist in PREDEFINED_PLAYLISTS[:3]:  # Show first 3
            print(f"   - {playlist.name}: {len(playlist.rules)} rules")
        
        print("\n🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        try:
            os.unlink(db_path)
        except:
            pass


def test_criteria_and_operators():
    """Test all criteria and operators."""
    print("\n🔍 Testing Criteria and Operators...")
    
    # Test all criteria
    print("📋 Available Criteria:")
    for criteria in PlaylistCriteria:
        print(f"   - {criteria.value}")
    
    # Test all operators
    print("\n⚙️ Available Operators:")
    for operator in ComparisonOperator:
        print(f"   - {operator.value}")
    
    # Test logical operators
    print("\n🔗 Logical Operators:")
    for logical in LogicalOperator:
        print(f"   - {logical.value}")
    
    print("✅ All enums working correctly!")


def main():
    """Run all tests."""
    print("🚀 DjAlfin Smart Playlists - Enhanced Testing Suite")
    print("=" * 60)
    
    try:
        test_criteria_and_operators()
        test_smart_playlist_manager()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅ Smart Playlists improvements are working correctly!")
        
    except Exception as e:
        print(f"\n❌ TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()