#!/usr/bin/env python3
"""
🧪 Test de carga de archivos de audio
Script para verificar que podemos cargar archivos de /Volumes/KINGSTON/Audio
"""

import os
import glob
from basic_metadata_reader import BasicMetadataReader

def test_folder_access():
    """Test básico de acceso a la carpeta."""
    
    print("🧪 Testing Folder Access")
    print("=" * 50)
    
    audio_folder = "/Volumes/KINGSTON/Audio"
    print(f"📁 Testing folder: {audio_folder}")
    
    # Check if folder exists
    if os.path.exists(audio_folder):
        print("✅ Folder exists")
        
        try:
            # List files
            files = os.listdir(audio_folder)
            print(f"📊 Total items in folder: {len(files)}")
            
            # Filter audio files
            audio_extensions = ['.mp3', '.m4a', '.flac', '.wav']
            audio_files = []
            
            for filename in files:
                if not filename.startswith('.'):  # Skip hidden files
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in audio_extensions:
                        audio_files.append(filename)
            
            print(f"🎵 Audio files found: {len(audio_files)}")
            
            if audio_files:
                print(f"\n📋 First 10 audio files:")
                for i, filename in enumerate(audio_files[:10]):
                    file_path = os.path.join(audio_folder, filename)
                    try:
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        _, ext = os.path.splitext(filename)
                        print(f"   {i+1:2d}. {filename} ({size_mb:.1f} MB, {ext.upper()})")
                    except Exception as e:
                        print(f"   {i+1:2d}. {filename} (Error: {e})")
                
                return audio_files
            else:
                print("❌ No audio files found")
                return []
                
        except Exception as e:
            print(f"❌ Error listing folder: {e}")
            return []
    else:
        print("❌ Folder does not exist")
        return []

def test_cue_reading(audio_files):
    """Test de lectura de cue points."""
    
    print(f"\n🎯 Testing Cue Point Reading")
    print("=" * 50)
    
    if not audio_files:
        print("❌ No audio files to test")
        return
    
    reader = BasicMetadataReader()
    audio_folder = "/Volumes/KINGSTON/Audio"
    
    files_with_cues = 0
    total_cues = 0
    
    # Test first 5 files
    test_files = audio_files[:5]
    print(f"🔍 Testing {len(test_files)} files for cue points...")
    
    for i, filename in enumerate(test_files):
        file_path = os.path.join(audio_folder, filename)
        
        print(f"\n📀 {i+1}. {filename}")
        print("-" * 40)
        
        try:
            # Read metadata
            metadata = reader.scan_file(file_path)
            cue_points = metadata.get('cue_points', [])
            
            print(f"📊 File size: {metadata.get('size_mb', 0):.1f} MB")
            print(f"🎵 Format: {metadata.get('format', 'Unknown')}")
            print(f"🏷️ Metadata frames: {len(metadata.get('metadata_found', []))}")
            
            if cue_points:
                files_with_cues += 1
                total_cues += len(cue_points)
                software = cue_points[0].software.title()
                
                print(f"🎯 Cue points: {len(cue_points)} from {software}")
                
                # Show first 3 cue points
                for j, cue in enumerate(cue_points[:3]):
                    minutes = int(cue.position // 60)
                    seconds = int(cue.position % 60)
                    print(f"   {j+1}. {cue.name} @ {minutes}:{seconds:02d} {cue.color}")
                
                if len(cue_points) > 3:
                    print(f"   ... and {len(cue_points) - 3} more")
                
                print("✅ SUCCESS")
            else:
                print("❌ No cue points found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n📊 Test Results:")
    print(f"   Files tested: {len(test_files)}")
    print(f"   Files with cues: {files_with_cues}")
    print(f"   Total cue points: {total_cues}")
    
    if files_with_cues > 0:
        print(f"✅ SUCCESS! Cue point reading is working!")
    else:
        print(f"❌ No cue points found in test files")

def test_specific_file():
    """Test de un archivo específico que sabemos que tiene cue points."""
    
    print(f"\n🎯 Testing Specific File")
    print("=" * 50)
    
    # Try known file with cue points
    test_filename = "Ricky Martin - Livin' La Vida Loca (Joey Musaphia's Carnival Mix).mp3"
    audio_folder = "/Volumes/KINGSTON/Audio"
    file_path = os.path.join(audio_folder, test_filename)
    
    print(f"🔍 Testing: {test_filename}")
    
    if os.path.exists(file_path):
        print("✅ File exists")
        
        try:
            reader = BasicMetadataReader()
            metadata = reader.scan_file(file_path)
            cue_points = metadata.get('cue_points', [])
            
            print(f"📊 Results:")
            print(f"   File size: {metadata.get('size_mb', 0):.1f} MB")
            print(f"   Format: {metadata.get('format', 'Unknown')}")
            print(f"   Metadata frames: {len(metadata.get('metadata_found', []))}")
            print(f"   Cue points: {len(cue_points)}")
            
            if cue_points:
                software = cue_points[0].software.title()
                print(f"   Software: {software}")
                
                print(f"\n🎯 All cue points:")
                for i, cue in enumerate(cue_points):
                    minutes = int(cue.position // 60)
                    seconds = int(cue.position % 60)
                    print(f"   {i+1:2d}. {cue.name}")
                    print(f"       Time: {minutes}:{seconds:02d} ({cue.position:.1f}s)")
                    print(f"       Color: {cue.color}")
                    print(f"       Hot Cue: #{cue.hotcue_index}")
                
                print(f"\n✅ SPECIFIC FILE TEST SUCCESSFUL!")
            else:
                print(f"❌ No cue points found in specific file")
                
        except Exception as e:
            print(f"❌ Error reading specific file: {e}")
    else:
        print(f"❌ Specific test file not found")

def main():
    """Función principal."""
    
    print("🧪 DjAlfin - Audio Loading Test")
    print("Testing file loading from /Volumes/KINGSTON/Audio")
    print("=" * 60)
    
    # Test 1: Folder access
    audio_files = test_folder_access()
    
    # Test 2: Cue point reading
    if audio_files:
        test_cue_reading(audio_files)
    
    # Test 3: Specific file
    test_specific_file()
    
    print(f"\n" + "=" * 60)
    print("🎯 Testing completed!")
    
    if audio_files:
        print("✅ Audio folder access: WORKING")
        print("✅ File listing: WORKING")
        print("✅ Ready for GUI application")
    else:
        print("❌ Audio folder access: FAILED")
        print("❌ Check USB drive connection")

if __name__ == "__main__":
    main()
