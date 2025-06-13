#!/usr/bin/env python3
"""
Script avanzado para validación y corrección de géneros musicales en DjAlfin
Utiliza clasificación inteligente con validación histórica
"""

import os
import sys
import sqlite3
from typing import Dict, List, Tuple
import argparse

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.genre_classifier import GenreClassifier, validate_and_fix_genre_database


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Validación y corrección inteligente de géneros musicales"
    )
    parser.add_argument(
        "--analyze", 
        action="store_true", 
        help="Solo analizar sin aplicar correcciones"
    )
    parser.add_argument(
        "--fix", 
        action="store_true", 
        help="Aplicar correcciones automáticamente"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true", 
        help="Modo interactivo para revisar correcciones"
    )
    parser.add_argument(
        "--db-path", 
        type=str, 
        help="Ruta personalizada a la base de datos"
    )
    
    args = parser.parse_args()
    
    # Determinar ruta de la base de datos
    if args.db_path:
        db_path = args.db_path
    else:
        project_root = os.path.abspath(os.path.dirname(__file__))
        config_path = os.path.join(project_root, "config")
        db_path = os.path.join(config_path, "library.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        return
    
    print(f"🎵 Analizando géneros musicales en: {db_path}")
    print("=" * 60)
    
    # Inicializar clasificador
    classifier = GenreClassifier()
    
    # Generar estadísticas
    print("📊 Generando estadísticas de géneros...")
    stats = classifier.get_genre_statistics(db_path)
    
    print_statistics(stats)
    
    # Obtener sugerencias de corrección
    print("\n🔍 Analizando géneros problemáticos...")
    corrections = classifier.suggest_corrections(db_path)
    
    if not corrections:
        print("✅ No se encontraron géneros que requieran corrección")
        return
    
    print(f"\n📝 Se encontraron {len(corrections)} sugerencias de corrección:")
    print("-" * 60)
    
    # Mostrar correcciones por categoría
    show_corrections_by_category(corrections)
    
    # Decidir qué hacer según los argumentos
    if args.analyze:
        print("\n📋 Análisis completado. Use --fix para aplicar correcciones.")
        return
    
    if args.interactive:
        apply_corrections_interactively(db_path, corrections)
    elif args.fix:
        apply_corrections_automatically(db_path, corrections)
    else:
        print("\n💡 Opciones disponibles:")
        print("  --analyze     : Solo mostrar análisis")
        print("  --fix         : Aplicar todas las correcciones")
        print("  --interactive : Revisar cada corrección individualmente")


def print_statistics(stats: Dict):
    """Imprime estadísticas de géneros de forma organizada."""
    print(f"📈 Estadísticas Generales:")
    print(f"  • Total de pistas: {stats['total_tracks']:,}")
    print(f"  • Pistas con género: {stats['tracks_with_genre']:,}")
    print(f"  • Géneros únicos: {stats['unique_genres']:,}")
    print(f"  • Géneros inválidos: {stats['invalid_genres']:,}")
    
    if stats['problematic_genres']:
        print(f"\n⚠️  Géneros Problemáticos:")
        for genre, count in stats['problematic_genres']:
            print(f"  • '{genre}': {count} pistas")
    
    print(f"\n🎼 Top 10 Géneros:")
    sorted_genres = sorted(
        stats['genre_distribution'].items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    for i, (genre, count) in enumerate(sorted_genres[:10], 1):
        percentage = (count / stats['tracks_with_genre']) * 100
        print(f"  {i:2d}. {genre}: {count:,} pistas ({percentage:.1f}%)")
    
    if stats['decade_distribution']:
        print(f"\n📅 Distribución por Décadas:")
        for decade in sorted(stats['decade_distribution'].keys()):
            decade_stats = stats['decade_distribution'][decade]
            total_decade = sum(decade_stats.values())
            top_genre = max(decade_stats.items(), key=lambda x: x[1])
            print(f"  • {decade}: {total_decade:,} pistas (género principal: {top_genre[0]})")


def show_corrections_by_category(corrections: List[Tuple[str, str, str, str]]):
    """Muestra correcciones organizadas por categoría."""
    categories = {}
    
    for file_path, old_genre, new_genre, reason in corrections:
        if reason not in categories:
            categories[reason] = []
        categories[reason].append((file_path, old_genre, new_genre))
    
    for category, items in categories.items():
        print(f"\n📂 {category} ({len(items)} correcciones):")
        for file_path, old_genre, new_genre in items[:5]:  # Mostrar solo las primeras 5
            filename = os.path.basename(file_path)
            print(f"  • {filename}")
            print(f"    '{old_genre}' → '{new_genre}'")
        
        if len(items) > 5:
            print(f"  ... y {len(items) - 5} más")


def apply_corrections_interactively(db_path: str, corrections: List[Tuple[str, str, str, str]]):
    """Aplica correcciones de forma interactiva."""
    print(f"\n🔧 Modo Interactivo - Revisando {len(corrections)} correcciones")
    print("Opciones: (y)es, (n)o, (a)ll, (q)uit")
    print("-" * 40)
    
    applied = 0
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for i, (file_path, old_genre, new_genre, reason) in enumerate(corrections, 1):
            filename = os.path.basename(file_path)
            
            print(f"\n[{i}/{len(corrections)}] {filename}")
            print(f"Género actual: '{old_genre}'")
            print(f"Género sugerido: '{new_genre}'")
            print(f"Razón: {reason}")
            
            while True:
                choice = input("¿Aplicar corrección? (y/n/a/q): ").lower().strip()
                
                if choice == 'q':
                    print("❌ Cancelado por el usuario")
                    conn.close()
                    return
                elif choice == 'a':
                    # Aplicar todas las restantes
                    remaining = corrections[i-1:]
                    for file_path_r, old_genre_r, new_genre_r, reason_r in remaining:
                        cursor.execute("""
                            UPDATE tracks 
                            SET genre = ?, last_modified = datetime('now')
                            WHERE file_path = ?
                        """, (new_genre_r, file_path_r))
                        if cursor.rowcount > 0:
                            applied += 1
                    
                    conn.commit()
                    print(f"✅ Aplicadas {len(remaining)} correcciones restantes")
                    conn.close()
                    return
                elif choice == 'y':
                    cursor.execute("""
                        UPDATE tracks 
                        SET genre = ?, last_modified = datetime('now')
                        WHERE file_path = ?
                    """, (new_genre, file_path))
                    if cursor.rowcount > 0:
                        applied += 1
                        print("✅ Corrección aplicada")
                    break
                elif choice == 'n':
                    print("⏭️  Corrección omitida")
                    break
                else:
                    print("Opción inválida. Use y/n/a/q")
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Error en base de datos: {e}")
    
    print(f"\n🎉 Proceso completado. Correcciones aplicadas: {applied}")


def apply_corrections_automatically(db_path: str, corrections: List[Tuple[str, str, str, str]]):
    """Aplica todas las correcciones automáticamente."""
    print(f"\n🔧 Aplicando {len(corrections)} correcciones automáticamente...")
    
    applied = 0
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for file_path, old_genre, new_genre, reason in corrections:
            cursor.execute("""
                UPDATE tracks 
                SET genre = ?, last_modified = datetime('now')
                WHERE file_path = ?
            """, (new_genre, file_path))
            
            if cursor.rowcount > 0:
                applied += 1
                filename = os.path.basename(file_path)
                print(f"✅ {filename}: '{old_genre}' → '{new_genre}'")
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Error aplicando correcciones: {e}")
        return
    
    print(f"\n🎉 Correcciones aplicadas exitosamente: {applied}/{len(corrections)}")
    
    # Generar estadísticas actualizadas
    classifier = GenreClassifier()
    updated_stats = classifier.get_genre_statistics(db_path)
    
    print(f"\n📊 Estadísticas Actualizadas:")
    print(f"  • Géneros inválidos restantes: {updated_stats['invalid_genres']}")
    print(f"  • Géneros únicos: {updated_stats['unique_genres']}")


if __name__ == "__main__":
    main()