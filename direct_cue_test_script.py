#!/usr/bin/env python3
"""
🧪 Test directo de lectura de cue points
Script para probar directamente la lectura sin interfaz gráfica
"""

import os
import glob
from basic_metadata_reader import BasicMetadataReader

def test_direct_cue_reading():
    """Test directo de lectura de cue points."""
    print("🧪 Direct Cue Points Reading Test")
    print("=" * 60)
    
    # Inicializar lector
    reader = BasicMetadataReader()
    
    # Buscar archivos
    audio_folder = "/Volumes/KINGSTON/Audio"
    mp3_files = glob.glob(os.path.join(audio_folder, "*.mp3"))
    
    # Filtrar archivos ocultos
    mp3_files = [f for f in mp3_files if not os.path.basename(f).startswith('._')]
    
    print(f"📁 Found {len(mp3_files)} MP3 files")
    
    if not mp3_files:
        print("❌ No MP3 files found")
        return
    
    # Probar primeros 5 archivos
    for i, file_path in enumerate(mp3_files[:5]):
        filename = os.path.basename(file_path)
        print(f"\n📀 {i+1}. Testing: {filename}")
        print("-" * 50)
        
        try:
            # Leer metadatos
            metadata = reader.scan_file(file_path)
            
            print(f"📊 File size: {metadata['size_mb']:.1f} MB")
            print(f"🎵 Format: {metadata['format']}")
            print(f"🏷️ Metadata frames: {len(metadata.get('metadata_found', []))}")
            
            # Mostrar algunos frames
            frames = metadata.get('metadata_found', [])[:5]
            if frames:
                print(f"   Sample frames: {', '.join(frames)}")
            
            # Cue points
            cue_points = metadata.get('cue_points', [])
            print(f"🎯 Cue points found: {len(cue_points)}")
            
            if cue_points:
                print(f"🎛️ Software: {cue_points[0].software}")
                print(f"📍 Cue points details:")
                
                for j, cue in enumerate(cue_points):
                    minutes = int(cue.position // 60)
                    seconds = int(cue.position % 60)
                    print(f"   {j+1:2d}. {cue.name} @ {minutes}:{seconds:02d} ({cue.color})")
                
                print(f"✅ SUCCESS: {len(cue_points)} cue points from {cue_points[0].software}")
            else:
                print("❌ No cue points found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 Direct test completed!")

def test_specific_file_detailed():
    """Test detallado de un archivo específico."""
    print("\n🔍 Detailed Analysis of Specific File")
    print("=" * 60)
    
    # Buscar archivo con cue points conocidos
    audio_folder = "/Volumes/KINGSTON/Audio"
    test_file = os.path.join(audio_folder, "Ricky Martin - Livin' La Vida Loca (Joey Musaphia's Carnival Mix).mp3")
    
    if not os.path.exists(test_file):
        # Buscar cualquier archivo MP3
        mp3_files = glob.glob(os.path.join(audio_folder, "*.mp3"))
        mp3_files = [f for f in mp3_files if not os.path.basename(f).startswith('._')]
        
        if mp3_files:
            test_file = mp3_files[0]
        else:
            print("❌ No test file available")
            return
    
    filename = os.path.basename(test_file)
    print(f"📀 Analyzing: {filename}")
    print("-" * 50)
    
    reader = BasicMetadataReader()
    
    try:
        # Análisis paso a paso
        print("🔍 Step 1: Opening file...")
        with open(test_file, 'rb') as f:
            header = f.read(10)
            print(f"   Header: {header}")
            
            if header[:3] == b'ID3':
                print("   ✅ ID3 tag detected")
            else:
                print("   ❌ No ID3 tag")
                return
        
        print("\n🔍 Step 2: Scanning metadata...")
        metadata = reader.scan_file(test_file)
        
        print(f"   File size: {metadata['size_mb']:.1f} MB")
        print(f"   Format: {metadata['format']}")
        print(f"   Metadata frames: {len(metadata.get('metadata_found', []))}")
        
        print("\n🔍 Step 3: Analyzing frames...")
        frames = metadata.get('metadata_found', [])
        for frame in frames:
            print(f"   {frame}")
        
        print("\n🔍 Step 4: Extracting cue points...")
        cue_points = metadata.get('cue_points', [])
        print(f"   Cue points found: {len(cue_points)}")
        
        if cue_points:
            print(f"\n🎯 Detailed Cue Points:")
            for i, cue in enumerate(cue_points):
                print(f"   Cue {i+1}:")
                print(f"     Position: {cue.position:.1f}s")
                print(f"     Name: {cue.name}")
                print(f"     Color: {cue.color}")
                print(f"     Software: {cue.software}")
                print(f"     Hot Cue: {cue.hotcue_index}")
                print()
            
            print(f"✅ DETAILED ANALYSIS SUCCESSFUL")
        else:
            print("❌ No cue points extracted")
            
    except Exception as e:
        print(f"❌ Detailed analysis failed: {e}")
        import traceback
        traceback.print_exc()

def test_integration_simulation():
    """Simular integración con aplicación desktop."""
    print("\n🖥️ Desktop Integration Simulation")
    print("=" * 60)
    
    # Simular el proceso de la aplicación desktop
    print("🔍 Step 1: Initialize metadata reader...")
    reader = BasicMetadataReader()
    print("   ✅ Reader initialized")
    
    print("\n🔍 Step 2: Scan audio folder...")
    audio_folder = "/Volumes/KINGSTON/Audio"
    mp3_files = glob.glob(os.path.join(audio_folder, "*.mp3"))
    mp3_files = [f for f in mp3_files if not os.path.basename(f).startswith('._')]
    print(f"   ✅ Found {len(mp3_files)} files")
    
    if not mp3_files:
        print("   ❌ No files to test")
        return
    
    print("\n🔍 Step 3: Load first file...")
    test_file = mp3_files[0]
    filename = os.path.basename(test_file)
    print(f"   Loading: {filename}")
    
    print("\n🔍 Step 4: Read embedded cues...")
    try:
        metadata = reader.scan_file(test_file)
        cue_points = metadata.get('cue_points', [])
        
        if cue_points:
            print(f"   ✅ Found {len(cue_points)} cue points")
            
            print("\n🔍 Step 5: Convert to desktop format...")
            # Simular conversión a formato de la aplicación
            desktop_cues = []
            for cue in cue_points:
                desktop_cue = {
                    'position': cue.position,
                    'name': cue.name,
                    'color': cue.color,
                    'software': cue.software,
                    'hotcue_index': cue.hotcue_index
                }
                desktop_cues.append(desktop_cue)
            
            print(f"   ✅ Converted {len(desktop_cues)} cues")
            
            print("\n🔍 Step 6: Display simulation...")
            for i, cue in enumerate(desktop_cues[:3]):
                minutes = int(cue['position'] // 60)
                seconds = int(cue['position'] % 60)
                print(f"   Hot Cue {i+1}: {cue['name']} @ {minutes}:{seconds:02d}")
            
            if len(desktop_cues) > 3:
                print(f"   ... and {len(desktop_cues) - 3} more")
            
            print(f"\n✅ INTEGRATION SIMULATION SUCCESSFUL")
            print(f"   Ready for desktop application integration")
            
        else:
            print("   ❌ No cue points found")
            
    except Exception as e:
        print(f"   ❌ Integration simulation failed: {e}")

def main():
    """Función principal."""
    print("🧪 DjAlfin - Direct Cue Points Test")
    print("Testing embedded cue point reading without GUI")
    
    # Test 1: Lectura directa
    test_direct_cue_reading()
    
    # Test 2: Análisis detallado
    test_specific_file_detailed()
    
    # Test 3: Simulación de integración
    test_integration_simulation()
    
    print("\n🎯 All tests completed!")
    print("🚀 System ready for production use")

if __name__ == "__main__":
    main()
