#!/usr/bin/env python3
"""
🎯 Crear archivos de cue points de demostración
Script para generar archivos de ejemplo para testing
"""

import json
import time
import os
from dataclasses import dataclass, asdict

@dataclass
class CuePoint:
    position: float
    type: str
    color: str
    name: str
    hotcue_index: int
    created_at: float
    energy_level: int = 5
    source: str = "manual"

def create_demo_cue_files():
    """Crear archivos de cue points de demostración."""
    
    # Lista de tracks de ejemplo basados en archivos reales
    demo_tracks = [
        {
            "artist": "Deadmau5",
            "title": "Strobe",
            "duration": 645.0,
            "cues": [
                CuePoint(15.0, "cue", "#FF6600", "Intro", 1, time.time(), 3, "manual"),
                CuePoint(120.5, "cue", "#FFFF00", "Build Up", 2, time.time(), 6, "manual"),
                CuePoint(240.8, "cue", "#FF0000", "Main Drop", 3, time.time(), 9, "manual"),
                CuePoint(360.2, "cue", "#0066FF", "Breakdown", 4, time.time(), 4, "manual"),
                CuePoint(480.7, "cue", "#00FF00", "Second Drop", 5, time.time(), 8, "manual"),
                CuePoint(580.1, "cue", "#9900FF", "Outro", 6, time.time(), 5, "manual"),
            ]
        },
        {
            "artist": "Coldplay",
            "title": "A Sky Full Of Stars (DJ Beats)",
            "duration": 268.0,
            "cues": [
                CuePoint(8.2, "cue", "#FF6600", "Intro", 1, time.time(), 4, "manual"),
                CuePoint(32.5, "cue", "#FFFF00", "Verse 1", 2, time.time(), 5, "manual"),
                CuePoint(64.8, "cue", "#FF0000", "Chorus 1", 3, time.time(), 8, "manual"),
                CuePoint(96.3, "cue", "#00FFFF", "Verse 2", 4, time.time(), 6, "manual"),
                CuePoint(128.7, "cue", "#FF0000", "Chorus 2", 5, time.time(), 9, "manual"),
                CuePoint(192.4, "cue", "#0066FF", "Bridge", 6, time.time(), 7, "manual"),
                CuePoint(224.1, "cue", "#FF0000", "Final Chorus", 7, time.time(), 10, "manual"),
                CuePoint(250.8, "cue", "#9900FF", "Outro", 8, time.time(), 4, "manual"),
            ]
        },
        {
            "artist": "Rihanna Feat. Drake",
            "title": "Work",
            "duration": 219.0,
            "cues": [
                CuePoint(5.1, "cue", "#FF6600", "Intro", 1, time.time(), 3, "manual"),
                CuePoint(28.4, "cue", "#FFFF00", "Verse Start", 2, time.time(), 5, "manual"),
                CuePoint(52.7, "cue", "#FF0000", "Hook", 3, time.time(), 8, "manual"),
                CuePoint(76.2, "cue", "#00FF00", "Verse 2", 4, time.time(), 6, "manual"),
                CuePoint(99.8, "cue", "#FF0000", "Chorus", 5, time.time(), 9, "manual"),
                CuePoint(142.3, "cue", "#0066FF", "Bridge", 6, time.time(), 7, "manual"),
                CuePoint(165.9, "cue", "#FF0000", "Final Hook", 7, time.time(), 9, "manual"),
                CuePoint(195.2, "cue", "#9900FF", "Outro", 8, time.time(), 4, "manual"),
            ]
        },
        {
            "artist": "The Chainsmokers & Coldplay",
            "title": "Something Just Like This (Don Diablo Remix)",
            "duration": 245.0,
            "cues": [
                CuePoint(12.3, "cue", "#FF6600", "Intro", 1, time.time(), 4, "manual"),
                CuePoint(35.7, "cue", "#FFFF00", "Build Up 1", 2, time.time(), 6, "manual"),
                CuePoint(58.9, "cue", "#FF0000", "Drop 1", 3, time.time(), 9, "manual"),
                CuePoint(89.4, "cue", "#00FFFF", "Breakdown", 4, time.time(), 5, "manual"),
                CuePoint(112.8, "cue", "#FFFF00", "Build Up 2", 5, time.time(), 7, "manual"),
                CuePoint(136.2, "cue", "#FF0000", "Main Drop", 6, time.time(), 10, "manual"),
                CuePoint(182.6, "cue", "#0066FF", "Break", 7, time.time(), 6, "manual"),
                CuePoint(215.4, "cue", "#9900FF", "Outro", 8, time.time(), 5, "manual"),
            ]
        },
        {
            "artist": "Ed Sheeran, T2",
            "title": "Bad Heartbroken Habits (Ben Phillips Edit)",
            "duration": 312.0,
            "cues": [
                CuePoint(8.7, "cue", "#FF6600", "Intro", 1, time.time(), 3, "manual"),
                CuePoint(32.1, "cue", "#FFFF00", "Verse 1", 2, time.time(), 5, "manual"),
                CuePoint(64.5, "cue", "#FF0000", "Chorus 1", 3, time.time(), 8, "manual"),
                CuePoint(96.8, "cue", "#00FF00", "Verse 2", 4, time.time(), 6, "manual"),
                CuePoint(128.3, "cue", "#FF0000", "Chorus 2", 5, time.time(), 9, "manual"),
                CuePoint(192.7, "cue", "#0066FF", "Bridge", 6, time.time(), 7, "manual"),
                CuePoint(224.9, "cue", "#FF0000", "Final Chorus", 7, time.time(), 10, "manual"),
                CuePoint(280.2, "cue", "#9900FF", "Outro", 8, time.time(), 4, "manual"),
            ]
        }
    ]
    
    created_files = []
    
    for track in demo_tracks:
        # Crear nombre de archivo
        filename = f"{track['artist']} - {track['title']}_cues.json"
        
        # Crear datos del archivo
        file_data = {
            "version": "2.1",
            "file_info": {
                "artist": track["artist"],
                "title": track["title"],
                "duration": track["duration"],
                "format": "MP3",
                "bitrate": "320 kbps"
            },
            "cue_points": [asdict(cue) for cue in track["cues"]],
            "spotify_enhanced": False,
            "created_at": time.time(),
            "demo_file": True
        }
        
        # Guardar archivo
        try:
            with open(filename, 'w') as f:
                json.dump(file_data, f, indent=2)
            
            created_files.append(filename)
            print(f"✅ Created: {filename}")
            
        except Exception as e:
            print(f"❌ Error creating {filename}: {e}")
    
    return created_files

def create_spotify_enhanced_demo():
    """Crear un archivo de demostración con datos de Spotify."""
    
    spotify_track = {
        "artist": "Deadmau5",
        "title": "Strobe - Radio Edit",
        "duration": 214.2,
        "spotify_metadata": {
            "spotify_id": "4uLU6hMCjMI75M1A2tKUQC",
            "spotify_name": "Strobe - Radio Edit",
            "spotify_artist": "deadmau5",
            "spotify_album": "Strobe",
            "spotify_bpm": 128,
            "spotify_key": "F# minor",
            "spotify_energy": 7,
            "spotify_danceability": 6,
            "spotify_popularity": 52
        },
        "cues": [
            CuePoint(8.5, "cue", "#FF6600", "Intro", 1, time.time(), 4, "spotify_analysis"),
            CuePoint(32.1, "cue", "#FFFF00", "Build Up", 2, time.time(), 6, "spotify_analysis"),
            CuePoint(64.8, "cue", "#FF0000", "Drop 1", 3, time.time(), 8, "spotify_analysis"),
            CuePoint(96.3, "cue", "#0066FF", "Breakdown", 4, time.time(), 4, "spotify_analysis"),
            CuePoint(128.7, "cue", "#FF0000", "Main Drop", 5, time.time(), 9, "spotify_analysis"),
            CuePoint(160.2, "cue", "#00FFFF", "Bridge", 6, time.time(), 6, "spotify_analysis"),
            CuePoint(192.4, "cue", "#9900FF", "Outro", 7, time.time(), 5, "spotify_analysis"),
        ]
    }
    
    filename = f"{spotify_track['artist']} - {spotify_track['title']}_cues.json"
    
    file_data = {
        "version": "2.1",
        "file_info": {
            "artist": spotify_track["artist"],
            "title": spotify_track["title"],
            "duration": spotify_track["duration"],
            "format": "MP3",
            "bitrate": "320 kbps",
            "spotify_metadata": spotify_track["spotify_metadata"]
        },
        "cue_points": [asdict(cue) for cue in spotify_track["cues"]],
        "spotify_enhanced": True,
        "created_at": time.time(),
        "demo_file": True
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(file_data, f, indent=2)
        
        print(f"🎵 Created Spotify enhanced: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error creating Spotify demo: {e}")
        return None

def main():
    """Función principal."""
    print("🎯 Creating demo cue point files...")
    print("=" * 50)
    
    # Crear archivos de demostración normales
    created_files = create_demo_cue_files()
    
    # Crear archivo con datos de Spotify
    spotify_file = create_spotify_enhanced_demo()
    if spotify_file:
        created_files.append(spotify_file)
    
    print("\n" + "=" * 50)
    print(f"✅ Created {len(created_files)} demo cue point files:")
    
    for filename in created_files:
        print(f"   📁 {filename}")
    
    print("\n🎯 Demo files ready for testing!")
    print("🎵 Load any of these tracks in the desktop app to see cue points")

if __name__ == "__main__":
    main()
