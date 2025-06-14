#!/usr/bin/env python3
"""
🔍 DjAlfin - Escáner de Carpeta de Audio
Script de línea de comandos para escanear /Volumes/KINGSTON/Audio
"""

import os
import glob
import time
from basic_metadata_reader import BasicMetadataReader

def scan_audio_folder():
    """Escanear carpeta de audio y mostrar resultados."""
    
    print("🔍 DjAlfin - Audio Folder Scanner")
    print("=" * 60)
    
    audio_folder = "/Volumes/KINGSTON/Audio"
    print(f"📁 Scanning: {audio_folder}")
    
    if not os.path.exists(audio_folder):
        print(f"❌ Folder not found: {audio_folder}")
        return
    
    # Inicializar lector
    reader = BasicMetadataReader()
    
    # Buscar archivos de audio
    extensions = ['*.mp3', '*.m4a', '*.flac', '*.wav']
    audio_files = []
    
    for ext in extensions:
        pattern = os.path.join(audio_folder, ext)
        files = glob.glob(pattern)
        
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Filtrar archivos ocultos
            if not filename.startswith('._'):
                audio_files.append({
                    'path': file_path,
                    'filename': filename,
                    'size_mb': os.path.getsize(file_path) / (1024 * 1024)
                })
    
    print(f"📊 Found {len(audio_files)} audio files")
    
    if not audio_files:
        print("❌ No audio files found")
        return
    
    # Escanear cue points
    print(f"\n🔍 Scanning for embedded cue points...")
    print("-" * 60)
    
    total_cues = 0
    files_with_cues = 0
    software_stats = {}
    
    for i, audio_file in enumerate(audio_files):
        filename = audio_file['filename']
        file_path = audio_file['path']
        size_mb = audio_file['size_mb']
        
        print(f"\n📀 {i+1:2d}/{len(audio_files)} {filename}")
        print(f"    📊 Size: {size_mb:.1f} MB")
        
        try:
            # Leer metadatos
            metadata = reader.scan_file(file_path)
            cue_points = metadata.get('cue_points', [])
            
            if cue_points:
                files_with_cues += 1
                total_cues += len(cue_points)
                software = cue_points[0].software
                
                # Estadísticas por software
                if software not in software_stats:
                    software_stats[software] = {'files': 0, 'cues': 0}
                software_stats[software]['files'] += 1
                software_stats[software]['cues'] += len(cue_points)
                
                print(f"    🎯 {len(cue_points)} cue points from {software.title()}")
                
                # Mostrar primeros 3 cue points
                for j, cue in enumerate(cue_points[:3]):
                    minutes = int(cue.position // 60)
                    seconds = int(cue.position % 60)
                    print(f"       {j+1}. {cue.name} @ {minutes}:{seconds:02d} {cue.color}")
                
                if len(cue_points) > 3:
                    print(f"       ... and {len(cue_points) - 3} more")
                
                print(f"    ✅ SUCCESS")
            else:
                print(f"    ❌ No cue points found")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 SCAN RESULTS")
    print("=" * 60)
    
    print(f"📁 Total files scanned: {len(audio_files)}")
    print(f"✅ Files with cue points: {files_with_cues}")
    print(f"🎯 Total cue points found: {total_cues}")
    print(f"📈 Success rate: {(files_with_cues/len(audio_files)*100):.1f}%")
    
    if software_stats:
        print(f"\n🎛️ Software detected:")
        for software, stats in software_stats.items():
            print(f"   {software.title()}: {stats['files']} files, {stats['cues']} cue points")
    
    if files_with_cues > 0:
        print(f"\n🎉 SUCCESS! Found embedded cue points!")
        print(f"✅ Ready for DjAlfin integration")
        
        # Calcular estadísticas adicionales
        avg_cues = total_cues / files_with_cues if files_with_cues > 0 else 0
        print(f"\n📊 Additional stats:")
        print(f"   Average cues per file: {avg_cues:.1f}")
        print(f"   Most common software: {max(software_stats.keys(), key=lambda x: software_stats[x]['cues']) if software_stats else 'None'}")
        
    else:
        print(f"\n❌ No embedded cue points found")
        print(f"💡 This could mean:")
        print(f"   - Files haven't been processed by DJ software")
        print(f"   - Cue points are stored externally")
        print(f"   - Different metadata format")

def scan_specific_files():
    """Escanear archivos específicos que sabemos que tienen cue points."""
    
    print(f"\n🎯 SPECIFIC FILES TEST")
    print("=" * 60)
    
    # Archivos que sabemos que tienen cue points
    test_files = [
        "Ricky Martin - Livin' La Vida Loca (Joey Musaphia's Carnival Mix).mp3",
        "Spice Girls - Who Do You Think You Are (Stop) (Morales Club Mix).mp3",
        "Steps - One For Sorrow (Almighty Mix).mp3",
        "The Tamperer feat. Maya - Feel It (Original Mix).mp3",
        "Whitney Houston - I Will Always Love You (Hex Hector Club Mix).mp3"
    ]
    
    audio_folder = "/Volumes/KINGSTON/Audio"
    reader = BasicMetadataReader()
    
    found_files = 0
    
    for filename in test_files:
        file_path = os.path.join(audio_folder, filename)
        
        print(f"\n🔍 Testing: {filename}")
        
        if os.path.exists(file_path):
            found_files += 1
            
            try:
                metadata = reader.scan_file(file_path)
                cue_points = metadata.get('cue_points', [])
                
                if cue_points:
                    print(f"   ✅ {len(cue_points)} cue points from {cue_points[0].software}")
                    
                    # Mostrar todos los cue points
                    for i, cue in enumerate(cue_points):
                        minutes = int(cue.position // 60)
                        seconds = int(cue.position % 60)
                        print(f"      {i+1}. {cue.name} @ {minutes}:{seconds:02d} (Hot {cue.hotcue_index}) {cue.color}")
                else:
                    print(f"   ❌ No cue points found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"   ❌ File not found")
    
    print(f"\n📊 Found {found_files}/{len(test_files)} test files")

def main():
    """Función principal."""
    print("🔍 DjAlfin - Audio Folder Scanner")
    print("Direct scanning of /Volumes/KINGSTON/Audio")
    
    start_time = time.time()
    
    # Escaneo general
    scan_audio_folder()
    
    # Escaneo específico
    scan_specific_files()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️ Scan completed in {duration:.1f} seconds")
    print("🚀 Ready for GUI integration!")

if __name__ == "__main__":
    main()
