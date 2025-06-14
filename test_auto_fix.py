#!/usr/bin/env python3
"""
Script de prueba para verificar que el sistema automático de corrección funciona
"""

import sqlite3
import os
from core.library_scanner import auto_fix_metadata

def test_auto_fix():
    """Prueba la función de auto-corrección con datos problemáticos"""
    print("🧪 PRUEBA DEL SISTEMA AUTOMÁTICO DE CORRECCIÓN")
    print("=" * 50)
    
    # Casos de prueba con datos problemáticos
    test_cases = [
        {
            "file_path": "/test/Spice Girls - Who Do You Think You Are.mp3",
            "metadata": {
                "title": "Who Do You Think You Are",
                "artist": "Spice Girls",
                "album": "N/A",
                "genre": "Unknown"
            }
        },
        {
            "file_path": "/test/N A - Some Song.mp3",
            "metadata": {
                "title": "N/A",
                "artist": "N A",
                "album": "Unknown",
                "genre": "Unknown"
            }
        },
        {
            "file_path": "/test/Coldplay - A Sky Full Of Stars (DJ Beats).m4a",
            "metadata": {
                "title": "A Sky Full Of Stars (DJ Beats)",
                "artist": "Coldplay",
                "album": "NA",
                "genre": "Unknown"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Caso de prueba {i}:")
        print(f"   Archivo: {os.path.basename(test_case['file_path'])}")
        print(f"   Antes: {test_case['metadata']}")
        
        # Aplicar correcciones
        fixed_metadata = auto_fix_metadata(test_case['metadata'].copy(), test_case['file_path'])
        
        print(f"   Después: {fixed_metadata}")
        
        # Verificar mejoras
        improvements = []
        if test_case['metadata']['artist'] != fixed_metadata['artist']:
            improvements.append(f"Artista: '{test_case['metadata']['artist']}' → '{fixed_metadata['artist']}'")
        if test_case['metadata']['title'] != fixed_metadata['title']:
            improvements.append(f"Título: '{test_case['metadata']['title']}' → '{fixed_metadata['title']}'")
        if test_case['metadata']['album'] != fixed_metadata['album']:
            improvements.append(f"Álbum: '{test_case['metadata']['album']}' → '{fixed_metadata['album']}'")
        if test_case['metadata']['genre'] != fixed_metadata['genre']:
            improvements.append(f"Género: '{test_case['metadata']['genre']}' → '{fixed_metadata['genre']}'")
        
        if improvements:
            print("   ✅ Mejoras aplicadas:")
            for improvement in improvements:
                print(f"      • {improvement}")
        else:
            print("   ℹ️  No se aplicaron correcciones")
    
    print(f"\n🎉 Prueba completada!")

def check_current_database():
    """Verifica el estado actual de la base de datos"""
    db_path = os.path.join("config", "library.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    print(f"\n📊 ESTADO ACTUAL DE LA BASE DE DATOS:")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar valores problemáticos
        cursor.execute("""
            SELECT 
                COUNT(*) as total_tracks,
                SUM(CASE WHEN artist IN ('N/A', 'N A', 'NA', 'Unknown', 'unknown', 'UNKNOWN') THEN 1 ELSE 0 END) as problematic_artists,
                SUM(CASE WHEN album IN ('N/A', 'N A', 'NA', 'Unknown', 'unknown', 'UNKNOWN') THEN 1 ELSE 0 END) as problematic_albums,
                SUM(CASE WHEN title IN ('N/A', 'N A', 'NA', 'Unknown', 'unknown', 'UNKNOWN') THEN 1 ELSE 0 END) as problematic_titles,
                SUM(CASE WHEN genre IN ('N/A', 'N A', 'NA', 'Unknown', 'unknown', 'UNKNOWN') THEN 1 ELSE 0 END) as problematic_genres
            FROM tracks
        """)
        
        stats = cursor.fetchone()
        total, prob_artists, prob_albums, prob_titles, prob_genres = stats
        
        print(f"📈 Total de pistas: {total}")
        print(f"🎤 Artistas problemáticos: {prob_artists}")
        print(f"💿 Álbumes problemáticos: {prob_albums}")
        print(f"🎵 Títulos problemáticos: {prob_titles}")
        print(f"🎼 Géneros problemáticos: {prob_genres}")
        
        total_problems = prob_artists + prob_albums + prob_titles + prob_genres
        
        if total_problems == 0:
            print("✅ ¡No hay valores problemáticos en la base de datos!")
        else:
            print(f"⚠️  Total de campos problemáticos: {total_problems}")
        
        # Mostrar distribución de géneros
        cursor.execute("""
            SELECT genre, COUNT(*) as count
            FROM tracks
            GROUP BY genre
            ORDER BY count DESC
            LIMIT 10
        """)
        
        genres = cursor.fetchall()
        print(f"\n🎼 Top 10 géneros:")
        for i, (genre, count) in enumerate(genres, 1):
            percentage = (count / total) * 100
            print(f"   {i:2d}. {genre}: {count} pistas ({percentage:.1f}%)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Probar función de auto-corrección
    test_auto_fix()
    
    # Verificar estado actual de la BD
    check_current_database()