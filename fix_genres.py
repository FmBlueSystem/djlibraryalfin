#!/usr/bin/env python3
"""
Script para corregir géneros problemáticos en la base de datos de DjAlfin
Corrige géneros como "N/A", "2008 Universal Fire Victim" y géneros muy largos
"""

import sqlite3
import os

def fix_genres():
    """Corrige los géneros problemáticos en la base de datos."""
    # Usar la misma ruta que DatabaseManager
    project_root = os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(project_root, "config")
    db_path = os.path.join(config_path, "library.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        return
    
    print(f"🔧 Iniciando corrección de géneros: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Mostrar estado actual
            print("\n📊 Estado actual de géneros problemáticos:")
            show_problematic_genres(cursor)
            
            # Correcciones específicas basadas en artista y título
            corrections = [
                # Pistas con género "N/A" - asignar géneros apropiados
                ("DJ Edits Boom Shack-A-Lak", "Apache Indian", "Reggae"),
                ("DJ Edits: Monster", "Automatic", "Electronic"),
                ("In' All Over The World DJ Edit", "N A", "Pop"),
                ("School'S Out DJ Edit", "N A", "Rock"),
                ("She's Electric (DJ Edit)", "N/A", "Rock"),
                
                # Pistas con género "2008 Universal Fire Victim" - corregir a géneros apropiados
                ("9 To 5 DJ Edit", "Dolly Parton", "Country"),
                ("The Night Away DJ Edit", "Mavericks", "Country Rock"),
                
                # Género muy largo - simplificar
                ("I Will Always Love You Hex Hector Club Mix", "Whitney Houston", "R&B")
            ]
            
            print("\n🔄 Aplicando correcciones:")
            
            for title, artist, new_genre in corrections:
                # Actualizar el género
                cursor.execute("""
                    UPDATE tracks 
                    SET genre = ? 
                    WHERE title = ? AND artist = ?
                """, (new_genre, title, artist))
                
                if cursor.rowcount > 0:
                    print(f"✅ '{title}' por {artist} → '{new_genre}'")
                else:
                    print(f"⚠️  No se encontró: '{title}' por {artist}")
            
            conn.commit()
            
            # Mostrar estado después de las correcciones
            print("\n📊 Estado después de las correcciones:")
            show_genre_summary(cursor)
            
            print("\n🎉 Corrección de géneros completada exitosamente.")
            
    except sqlite3.Error as e:
        print(f"❌ Error durante la corrección: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def show_problematic_genres(cursor):
    """Muestra los géneros problemáticos actuales."""
    problematic_genres = ["N/A", "2008 Universal Fire Victim", "Easy Listening Pop Soul Contemporary R & B"]
    
    for genre in problematic_genres:
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE genre = ?", (genre,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  • '{genre}': {count} pistas")

def show_genre_summary(cursor):
    """Muestra un resumen de todos los géneros."""
    cursor.execute("""
        SELECT genre, COUNT(*) as count 
        FROM tracks 
        WHERE genre IS NOT NULL AND genre != '' 
        GROUP BY genre 
        ORDER BY count DESC
    """)
    
    genres = cursor.fetchall()
    print(f"  📈 Total de géneros únicos: {len(genres)}")
    
    for genre, count in genres:
        print(f"  • {genre}: {count} pistas")
    
    # Verificar si quedan géneros problemáticos
    cursor.execute("""
        SELECT COUNT(*) FROM tracks 
        WHERE genre IN ('N/A', '2008 Universal Fire Victim', 'Easy Listening Pop Soul Contemporary R & B')
    """)
    problematic_count = cursor.fetchone()[0]
    
    if problematic_count == 0:
        print("\n✅ No quedan géneros problemáticos")
    else:
        print(f"\n⚠️  Quedan {problematic_count} géneros problemáticos")

if __name__ == "__main__":
    fix_genres()