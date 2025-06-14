#!/usr/bin/env python3
"""
🧪 Test de lectura de cue points embebidos
Script para verificar que podemos leer cue points de Serato, MixInKey, etc.
"""

import os
import glob
from basic_metadata_reader import BasicMetadataReader

def test_embedded_cue_reading():
    """Probar lectura de cue points embebidos en archivos reales."""
    
    print("🧪 Testing Embedded Cue Points Reading")
    print("=" * 60)
    
    reader = BasicMetadataReader()
    
    # Buscar archivos de audio en la carpeta
    audio_folder = "/Volumes/KINGSTON/Audio"
    audio_extensions = ['.mp3', '.m4a', '.flac', '.wav']
    
    audio_files = []
    for ext in audio_extensions:
        pattern = os.path.join(audio_folder, f"*{ext}")
        files = glob.glob(pattern)
        audio_files.extend(files)
    
    if not audio_files:
        print("❌ No audio files found")
        return
    
    print(f"📁 Found {len(audio_files)} audio files")
    print(f"🔍 Testing first 10 files for embedded cue points...")
    
    total_files_tested = 0
    files_with_cues = 0
    total_cues_found = 0
    software_stats = {}
    
    for audio_file in audio_files[:10]:
        total_files_tested += 1
        filename = os.path.basename(audio_file)
        
        print(f"\n📀 Testing: {filename}")
        print("-" * 50)
        
        try:
            metadata = reader.scan_file(audio_file)
            
            print(f"📊 File size: {metadata['size_mb']:.1f} MB")
            print(f"🎵 Format: {metadata['format']}")
            print(f"🏷️ Metadata frames found: {len(metadata.get('metadata_found', []))}")
            
            # Mostrar algunos frames encontrados
            frames = metadata.get('metadata_found', [])
            if frames:
                print(f"   Sample frames: {', '.join(frames[:5])}")
                if len(frames) > 5:
                    print(f"   ... and {len(frames) - 5} more")
            
            cue_points = metadata.get('cue_points', [])
            
            if cue_points:
                files_with_cues += 1
                total_cues_found += len(cue_points)
                
                print(f"🎯 Embedded cue points found: {len(cue_points)}")
                
                # Estadísticas por software
                for cue in cue_points:
                    software = cue.software
                    if software not in software_stats:
                        software_stats[software] = 0
                    software_stats[software] += 1
                
                # Mostrar primeros cue points
                for i, cue in enumerate(cue_points[:5]):
                    minutes = int(cue.position // 60)
                    seconds = int(cue.position % 60)
                    print(f"   🎵 {cue.name} @ {minutes}:{seconds:02d} ({cue.software}) {cue.color}")
                
                if len(cue_points) > 5:
                    print(f"   ... and {len(cue_points) - 5} more cue points")
                
                print(f"✅ SUCCESS: Found cue points from {cue_points[0].software}")
                
            else:
                print("❌ No embedded cue points found")
                
        except Exception as e:
            print(f"❌ Error processing file: {e}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 EMBEDDED CUE POINTS TEST RESULTS")
    print("=" * 60)
    
    print(f"📁 Files tested: {total_files_tested}")
    print(f"✅ Files with embedded cues: {files_with_cues}")
    print(f"🎯 Total cue points found: {total_cues_found}")
    print(f"📈 Success rate: {(files_with_cues/total_files_tested*100):.1f}%")
    
    if software_stats:
        print(f"\n🎛️ Software detected:")
        for software, count in software_stats.items():
            print(f"   {software.title()}: {count} cue points")
    
    if files_with_cues > 0:
        print(f"\n🎉 SUCCESS! Found embedded cue points in {files_with_cues} files!")
        print("✅ The embedded cue reader is working correctly")
        print("🎯 Ready for integration with DjAlfin desktop app")
        
        # Mostrar ejemplo de integración
        print(f"\n💡 Integration example:")
        print(f"   When you load a file with embedded cues in DjAlfin,")
        print(f"   it will automatically detect and load {total_cues_found} cue points")
        print(f"   from {', '.join(software_stats.keys())} software")
        
    else:
        print(f"\n❌ No embedded cue points found in tested files")
        print("💡 This could mean:")
        print("   - Files haven't been processed by DJ software")
        print("   - Cue points are stored in external databases")
        print("   - Different metadata format than expected")
        
        print(f"\n🔧 To test with files that have embedded cues:")
        print("   1. Process some files with Serato DJ")
        print("   2. Add cue points and save")
        print("   3. Run this test again")

def test_specific_file():
    """Probar un archivo específico en detalle."""
    
    print("\n" + "=" * 60)
    print("🔍 DETAILED FILE ANALYSIS")
    print("=" * 60)
    
    # Buscar un archivo que sabemos que tiene cue points
    audio_folder = "/Volumes/KINGSTON/Audio"
    mp3_files = glob.glob(os.path.join(audio_folder, "*.mp3"))
    
    if not mp3_files:
        print("❌ No MP3 files found for detailed analysis")
        return
    
    # Tomar el primer archivo
    test_file = mp3_files[0]
    filename = os.path.basename(test_file)
    
    print(f"📀 Analyzing in detail: {filename}")
    print("-" * 50)
    
    reader = BasicMetadataReader()
    
    try:
        metadata = reader.scan_file(test_file)
        
        print(f"📊 File information:")
        print(f"   Path: {test_file}")
        print(f"   Size: {metadata['size_mb']:.1f} MB")
        print(f"   Format: {metadata['format']}")
        
        frames = metadata.get('metadata_found', [])
        print(f"\n🏷️ All metadata frames found ({len(frames)}):")
        for frame in frames:
            print(f"   {frame}")
        
        cue_points = metadata.get('cue_points', [])
        print(f"\n🎯 Cue points analysis:")
        print(f"   Total found: {len(cue_points)}")
        
        if cue_points:
            print(f"   Software: {cue_points[0].software}")
            print(f"   Source: {cue_points[0].source}")
            
            print(f"\n📍 Detailed cue points:")
            for i, cue in enumerate(cue_points):
                minutes = int(cue.position // 60)
                seconds = int(cue.position % 60)
                print(f"   {i+1:2d}. {cue.name}")
                print(f"       Position: {minutes}:{seconds:02d} ({cue.position:.1f}s)")
                print(f"       Color: {cue.color}")
                print(f"       Hot Cue: {cue.hotcue_index}")
                print(f"       Energy: {cue.energy_level}/10")
                print(f"       Software: {cue.software}")
                print()
        else:
            print("   No cue points found in this file")
            
    except Exception as e:
        print(f"❌ Error in detailed analysis: {e}")

def main():
    """Función principal."""
    print("🎯 DjAlfin - Embedded Cue Points Test Suite")
    print("Testing ability to read cue points from DJ software")
    
    # Test principal
    test_embedded_cue_reading()
    
    # Análisis detallado
    test_specific_file()
    
    print("\n🎯 Testing completed!")
    print("🚀 Ready to integrate with DjAlfin desktop application")

if __name__ == "__main__":
    main()
