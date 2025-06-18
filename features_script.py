#!/usr/bin/env python3
"""
Script de prueba rápida para verificar las funcionalidades principales de DjAlfin.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.audio_player import AudioPlayer
from core.database import create_connection, get_db_path
from core.smart_playlist_engine import SmartPlaylistEngine
from PySide6.QtCore import QCoreApplication

def test_audio_player():
    """Prueba básica del reproductor de audio."""
    print("🎵 Probando AudioPlayer...")
    
    app = QCoreApplication([])
    player = AudioPlayer()
    
    # Probar configuración de volumen
    player.set_volume(50)
    assert player._volume == 0.5, "Error en configuración de volumen"
    
    print("✅ AudioPlayer: OK")
    return True

def test_database():
    """Prueba la conexión a la base de datos."""
    print("💾 Probando Base de Datos...")
    
    try:
        db_path = get_db_path()
        conn = create_connection()
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tracks")
        count = cursor.fetchone()[0]
        
        print(f"✅ Base de Datos: {count} pistas encontradas")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        return False

def test_smart_playlists():
    """Prueba el motor de Smart Playlists."""
    print("🎛️ Probando Smart Playlists...")
    
    try:
        db_path = get_db_path()
        engine = SmartPlaylistEngine(db_path)
        
        # Probar obtener playlists
        playlists = engine.get_smart_playlists()
        print(f"✅ Smart Playlists: {len(playlists)} listas encontradas")
        return True
    except Exception as e:
        print(f"❌ Error en Smart Playlists: {e}")
        return False

def main():
    """Ejecuta todas las pruebas."""
    print("🚀 Ejecutando pruebas de funcionalidades de DjAlfin...\n")
    
    results = [
        test_database(),
        test_smart_playlists(),
        test_audio_player()
    ]
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 Resultados: {success_count}/{total_count} pruebas pasaron")
    
    if success_count == total_count:
        print("🎉 ¡Todas las funcionalidades están operativas!")
        return 0
    else:
        print("⚠️ Algunas funcionalidades necesitan atención")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 