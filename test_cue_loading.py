#!/usr/bin/env python3
"""
🧪 Test de carga automática de cue points
Script para verificar que la carga automática funciona correctamente
"""

import os
import json
import glob
from dataclasses import dataclass

@dataclass
class AudioFile:
    path: str
    filename: str
    artist: str
    title: str
    duration: float
    size_mb: float
    format: str

def clean_filename(name):
    """Limpiar nombre de archivo para búsqueda."""
    cleaned = name.replace("_PN", "").replace("_", " ")
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()

def find_cue_file_for_track(artist, title):
    """Buscar archivo de cue points para un track específico."""
    
    # Limpiar nombres para búsqueda
    artist_clean = clean_filename(artist)
    title_clean = clean_filename(title)
    
    # Múltiples patrones de búsqueda
    search_patterns = [
        f"{artist} - {title}_cues.json",
        f"{artist_clean} - {title_clean}_cues.json",
        f"{artist} - {title.split('(')[0].strip()}_cues.json",
        f"{artist_clean} - {title_clean.split('(')[0].strip()}_cues.json"
    ]
    
    # Buscar en múltiples ubicaciones
    search_paths = [
        ".",  # Directorio actual
        "/Volumes/KINGSTON/DjAlfin",  # Directorio del proyecto
    ]
    
    print(f"🔍 Searching cue points for: {artist} - {title}")
    
    # Buscar archivo de cue points
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
            
        for pattern in search_patterns:
            full_path = os.path.join(search_path, pattern)
            print(f"   Checking: {full_path}")
            
            if os.path.exists(full_path):
                print(f"✅ Found cue file: {full_path}")
                return full_path
    
    print(f"❌ No cue points found for: {artist} - {title}")
    return None

def test_cue_loading():
    """Probar carga de cue points para tracks de ejemplo."""
    
    # Lista de tracks de ejemplo que deberían tener cue points
    test_tracks = [
        {"artist": "Deadmau5", "title": "Strobe"},
        {"artist": "Coldplay", "title": "A Sky Full Of Stars (DJ Beats)"},
        {"artist": "Rihanna Feat. Drake", "title": "Work"},
        {"artist": "The Chainsmokers & Coldplay", "title": "Something Just Like This (Don Diablo Remix)"},
        {"artist": "Ed Sheeran, T2", "title": "Bad Heartbroken Habits (Ben Phillips Edit)"},
        {"artist": "Deadmau5", "title": "Strobe - Radio Edit"},
    ]
    
    print("🧪 Testing cue point loading...")
    print("=" * 60)
    
    found_count = 0
    total_cues = 0
    
    for track in test_tracks:
        print(f"\n📀 Testing: {track['artist']} - {track['title']}")
        
        cue_file = find_cue_file_for_track(track['artist'], track['title'])
        
        if cue_file:
            try:
                with open(cue_file, 'r') as f:
                    data = json.load(f)
                
                cue_points = data.get('cue_points', [])
                spotify_enhanced = data.get('spotify_enhanced', False)
                demo_file = data.get('demo_file', False)
                
                print(f"   📊 Cue points: {len(cue_points)}")
                print(f"   🎵 Spotify enhanced: {'Yes' if spotify_enhanced else 'No'}")
                print(f"   🎯 Demo file: {'Yes' if demo_file else 'No'}")
                
                # Mostrar algunos cue points
                for i, cue in enumerate(cue_points[:3]):
                    minutes = int(cue['position'] // 60)
                    seconds = int(cue['position'] % 60)
                    source_icon = "🎵" if cue.get('source') == "spotify_analysis" else "👤"
                    print(f"   {source_icon} {cue['name']} @ {minutes}:{seconds:02d} (Energy: {cue.get('energy_level', 5)}/10)")
                
                if len(cue_points) > 3:
                    print(f"   ... and {len(cue_points) - 3} more cue points")
                
                found_count += 1
                total_cues += len(cue_points)
                
            except Exception as e:
                print(f"   ❌ Error loading cue file: {e}")
        else:
            print(f"   ❌ No cue file found")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results:")
    print(f"   🎵 Tracks tested: {len(test_tracks)}")
    print(f"   ✅ Cue files found: {found_count}")
    print(f"   📍 Total cue points: {total_cues}")
    print(f"   📈 Success rate: {(found_count/len(test_tracks)*100):.1f}%")
    
    if found_count == len(test_tracks):
        print("\n🎉 All tests passed! Cue loading is working correctly.")
    else:
        print(f"\n⚠️ {len(test_tracks) - found_count} tracks missing cue files.")

def list_available_cue_files():
    """Listar todos los archivos de cue points disponibles."""
    
    print("\n🗂️ Available cue point files:")
    print("=" * 60)
    
    # Buscar archivos JSON de cue points
    cue_files = glob.glob("*_cues.json")
    
    if not cue_files:
        print("❌ No cue point files found in current directory")
        return
    
    for cue_file in sorted(cue_files):
        try:
            with open(cue_file, 'r') as f:
                data = json.load(f)
            
            file_info = data.get('file_info', {})
            cue_points = data.get('cue_points', [])
            spotify_enhanced = data.get('spotify_enhanced', False)
            demo_file = data.get('demo_file', False)
            
            artist = file_info.get('artist', 'Unknown')
            title = file_info.get('title', 'Unknown')
            
            print(f"\n📁 {cue_file}")
            print(f"   🎵 {artist} - {title}")
            print(f"   📍 {len(cue_points)} cue points")
            
            flags = []
            if spotify_enhanced:
                flags.append("🎵 Spotify")
            if demo_file:
                flags.append("🎯 Demo")
            
            if flags:
                print(f"   🏷️ {' • '.join(flags)}")
            
        except Exception as e:
            print(f"❌ Error reading {cue_file}: {e}")

def main():
    """Función principal."""
    print("🧪 DjAlfin - Cue Point Loading Test")
    print("Testing automatic cue point loading functionality")
    print("=" * 60)
    
    # Listar archivos disponibles
    list_available_cue_files()
    
    # Probar carga automática
    test_cue_loading()
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    main()
