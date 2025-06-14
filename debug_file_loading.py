#!/usr/bin/env python3
"""
🔧 Debug de carga de archivos
Script para diagnosticar problemas con la carga de archivos de audio
"""

import os
import glob
import sys

def debug_file_access():
    """Debuggear acceso a archivos."""
    print("🔧 Debugging File Access")
    print("=" * 50)
    
    # Verificar directorio actual
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Verificar si la carpeta de audio existe
    audio_folder = "/Volumes/KINGSTON/Audio"
    print(f"🔍 Checking audio folder: {audio_folder}")
    
    if os.path.exists(audio_folder):
        print("✅ Audio folder exists")
        
        # Listar archivos
        try:
            files = os.listdir(audio_folder)
            audio_files = [f for f in files if f.lower().endswith(('.mp3', '.m4a', '.flac', '.wav'))]
            
            print(f"📊 Total files in folder: {len(files)}")
            print(f"🎵 Audio files found: {len(audio_files)}")
            
            if audio_files:
                print(f"\n📋 First 5 audio files:")
                for i, file in enumerate(audio_files[:5]):
                    file_path = os.path.join(audio_folder, file)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"   {i+1}. {file} ({file_size:.1f} MB)")
                
                # Probar leer un archivo específico
                test_file = os.path.join(audio_folder, audio_files[0])
                print(f"\n🧪 Testing file access: {audio_files[0]}")
                
                try:
                    with open(test_file, 'rb') as f:
                        header = f.read(10)
                        print(f"✅ File readable, header: {header}")
                        
                        # Verificar si es MP3
                        if header[:3] == b'ID3':
                            print("🎵 ID3 tag detected - this is a valid MP3")
                        elif header[:4] == b'RIFF':
                            print("🎵 RIFF header detected - this is a WAV file")
                        else:
                            print(f"🎵 Other format detected: {header}")
                            
                except Exception as e:
                    print(f"❌ Error reading file: {e}")
            else:
                print("❌ No audio files found")
                
        except Exception as e:
            print(f"❌ Error listing directory: {e}")
    else:
        print("❌ Audio folder does not exist")
        
        # Buscar carpetas alternativas
        print("\n🔍 Looking for alternative audio folders...")
        possible_paths = [
            "/Volumes/KINGSTON",
            "/Volumes",
            ".",
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Desktop")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Found: {path}")
                try:
                    contents = os.listdir(path)[:5]
                    print(f"   Contents: {contents}")
                except:
                    print(f"   (Cannot list contents)")
            else:
                print(f"❌ Not found: {path}")

def test_basic_metadata_reader():
    """Probar el lector básico de metadatos."""
    print("\n" + "=" * 50)
    print("🧪 Testing Basic Metadata Reader")
    print("=" * 50)
    
    try:
        # Importar el módulo
        sys.path.append('/Volumes/KINGSTON/DjAlfin')
        from basic_metadata_reader import BasicMetadataReader
        
        reader = BasicMetadataReader()
        print("✅ BasicMetadataReader imported successfully")
        
        # Buscar archivos de audio
        audio_folder = "/Volumes/KINGSTON/Audio"
        if os.path.exists(audio_folder):
            mp3_files = glob.glob(os.path.join(audio_folder, "*.mp3"))
            
            if mp3_files:
                test_file = mp3_files[0]
                print(f"🎵 Testing with: {os.path.basename(test_file)}")
                
                try:
                    metadata = reader.scan_file(test_file)
                    print(f"✅ Scan completed")
                    print(f"📊 Results:")
                    print(f"   File: {metadata.get('filename', 'Unknown')}")
                    print(f"   Size: {metadata.get('size_mb', 0):.1f} MB")
                    print(f"   Format: {metadata.get('format', 'Unknown')}")
                    print(f"   Metadata frames: {len(metadata.get('metadata_found', []))}")
                    print(f"   Cue points: {len(metadata.get('cue_points', []))}")
                    
                    cue_points = metadata.get('cue_points', [])
                    if cue_points:
                        print(f"\n🎯 Cue points found:")
                        for i, cue in enumerate(cue_points[:3]):
                            print(f"   {i+1}. {cue.name} @ {cue.position:.1f}s ({cue.software})")
                    else:
                        print("❌ No cue points found")
                        
                except Exception as e:
                    print(f"❌ Error scanning file: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ No MP3 files found")
        else:
            print("❌ Audio folder not accessible")
            
    except ImportError as e:
        print(f"❌ Cannot import BasicMetadataReader: {e}")
    except Exception as e:
        print(f"❌ Error testing metadata reader: {e}")

def test_desktop_app_integration():
    """Probar integración con la app desktop."""
    print("\n" + "=" * 50)
    print("🖥️ Testing Desktop App Integration")
    print("=" * 50)
    
    try:
        # Verificar que los archivos de la app existen
        app_files = [
            'cuepoint_desktop_spotify.py',
            'cuepoint_desktop_complete.py',
            'basic_metadata_reader.py'
        ]
        
        for app_file in app_files:
            file_path = f'/Volumes/KINGSTON/DjAlfin/{app_file}'
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / 1024
                print(f"✅ {app_file} ({file_size:.1f} KB)")
            else:
                print(f"❌ {app_file} not found")
        
        # Verificar imports
        print(f"\n🔍 Testing imports...")
        
        try:
            sys.path.append('/Volumes/KINGSTON/DjAlfin')
            
            # Test import básico
            import basic_metadata_reader
            print("✅ basic_metadata_reader imported")
            
            # Test import de dataclasses
            from basic_metadata_reader import EmbeddedCuePoint
            print("✅ EmbeddedCuePoint imported")
            
            # Test creación de objeto
            test_cue = EmbeddedCuePoint(
                position=60.0,
                type="cue",
                color="#FF0000",
                name="Test Cue",
                hotcue_index=1,
                created_at=1234567890.0
            )
            print(f"✅ EmbeddedCuePoint created: {test_cue.name}")
            
        except Exception as e:
            print(f"❌ Import error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error testing desktop integration: {e}")

def main():
    """Función principal de debugging."""
    print("🔧 DjAlfin - File Loading Debug")
    print("Diagnosing issues with audio file loading")
    
    # Test 1: Acceso a archivos
    debug_file_access()
    
    # Test 2: Lector de metadatos
    test_basic_metadata_reader()
    
    # Test 3: Integración con app
    test_desktop_app_integration()
    
    print("\n" + "=" * 50)
    print("🎯 Debug completed!")
    print("Check the results above to identify the issue.")

if __name__ == "__main__":
    main()
