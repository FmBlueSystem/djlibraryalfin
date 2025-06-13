#!/usr/bin/env python3
"""
Script de Validación y Corrección de Artistas y Álbumes
Herramienta para mejorar metadatos de artistas y álbumes en DjAlfin
"""

import os
import sys
import argparse
from typing import List

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.artist_album_enhancer import ArtistAlbumEnhancer, ArtistAlbumCorrection


def print_statistics(stats: dict):
    """Imprime estadísticas de artistas y álbumes."""
    print("=" * 60)
    print("📊 ESTADÍSTICAS DE ARTISTAS Y ÁLBUMES")
    print("=" * 60)
    
    total = stats['total_tracks']
    valid_artists = stats['tracks_with_artist']
    valid_albums = stats['tracks_with_album']
    
    print(f"📈 Resumen General:")
    print(f"  • Total de pistas: {total:,}")
    print(f"  • Pistas con artista válido: {valid_artists:,} ({valid_artists/total*100:.1f}%)")
    print(f"  • Pistas con álbum válido: {valid_albums:,} ({valid_albums/total*100:.1f}%)")
    print(f"  • Artistas inválidos: {stats['invalid_artists']:,}")
    print(f"  • Álbumes inválidos: {stats['invalid_albums']:,}")
    print(f"  • Artistas únicos: {stats['unique_artists']:,}")
    print(f"  • Álbumes únicos: {stats['unique_albums']:,}")
    
    # Calidad de metadatos
    artist_quality = (valid_artists / total) * 100
    album_quality = (valid_albums / total) * 100
    overall_quality = (artist_quality + album_quality) / 2
    
    print(f"\n🎯 Calidad de Metadatos:")
    print(f"  • Calidad de artistas: {artist_quality:.1f}%")
    print(f"  • Calidad de álbumes: {album_quality:.1f}%")
    print(f"  • Calidad general: {overall_quality:.1f}%")
    
    # Indicador visual de calidad
    if overall_quality >= 90:
        quality_indicator = "🟢 EXCELENTE"
    elif overall_quality >= 75:
        quality_indicator = "🟡 BUENA"
    elif overall_quality >= 50:
        quality_indicator = "🟠 REGULAR"
    else:
        quality_indicator = "🔴 NECESITA MEJORA"
    
    print(f"  • Estado: {quality_indicator}")
    
    # Top artistas
    if stats['most_common_artists']:
        print(f"\n🎤 Top 10 Artistas:")
        for i, (artist, count) in enumerate(stats['most_common_artists'], 1):
            print(f"  {i:2d}. {artist}: {count} pistas")
    
    # Top álbumes
    if stats['most_common_albums']:
        print(f"\n💿 Top 10 Álbumes:")
        for i, (album, count) in enumerate(stats['most_common_albums'], 1):
            print(f"  {i:2d}. {album}: {count} pistas")
    
    # Problemas detectados
    if stats['problematic_artists']:
        print(f"\n⚠️  Artistas Problemáticos (muestra):")
        for artist in stats['problematic_artists'][:10]:
            print(f"  • '{artist}'")
    
    if stats['problematic_albums']:
        print(f"\n⚠️  Álbumes Problemáticos (muestra):")
        for album in stats['problematic_albums'][:10]:
            print(f"  • '{album}'")


def print_corrections_summary(corrections: List[ArtistAlbumCorrection]):
    """Imprime resumen de correcciones sugeridas."""
    if not corrections:
        print("\n✅ No se encontraron problemas que requieran corrección")
        return
    
    print("=" * 60)
    print("🔧 CORRECCIONES SUGERIDAS")
    print("=" * 60)
    
    # Agrupar por tipo y confianza
    artist_corrections = [c for c in corrections if c.field == "artist"]
    album_corrections = [c for c in corrections if c.field == "album"]
    
    high_confidence = [c for c in corrections if c.confidence >= 0.8]
    medium_confidence = [c for c in corrections if 0.6 <= c.confidence < 0.8]
    low_confidence = [c for c in corrections if c.confidence < 0.6]
    
    print(f"📝 Resumen de Correcciones:")
    print(f"  • Total de correcciones: {len(corrections)}")
    print(f"  • Correcciones de artistas: {len(artist_corrections)}")
    print(f"  • Correcciones de álbumes: {len(album_corrections)}")
    print(f"  • Alta confianza (≥80%): {len(high_confidence)}")
    print(f"  • Confianza media (60-79%): {len(medium_confidence)}")
    print(f"  • Baja confianza (<60%): {len(low_confidence)}")
    
    # Mostrar correcciones por categoría
    if high_confidence:
        print(f"\n🟢 Correcciones de Alta Confianza ({len(high_confidence)}):")
        for correction in high_confidence[:10]:
            filename = os.path.basename(correction.file_path)
            print(f"  • {filename}")
            print(f"    {correction.field.title()}: '{correction.current_value}' → '{correction.suggested_value}'")
            print(f"    Confianza: {correction.confidence:.1%}, Razón: {correction.reason}")
    
    if medium_confidence:
        print(f"\n🟡 Correcciones de Confianza Media ({len(medium_confidence)}):")
        for correction in medium_confidence[:5]:
            filename = os.path.basename(correction.file_path)
            print(f"  • {filename}")
            print(f"    {correction.field.title()}: '{correction.current_value}' → '{correction.suggested_value}'")
            print(f"    Confianza: {correction.confidence:.1%}, Razón: {correction.reason}")
    
    if low_confidence:
        print(f"\n🟠 Correcciones de Baja Confianza ({len(low_confidence)}):")
        print(f"  • {len(low_confidence)} correcciones requieren revisión manual")


def apply_corrections_interactive(enhancer: ArtistAlbumEnhancer, db_path: str, 
                                corrections: List[ArtistAlbumCorrection]):
    """Aplica correcciones de forma interactiva."""
    print("\n" + "=" * 60)
    print("🔧 APLICACIÓN INTERACTIVA DE CORRECCIONES")
    print("=" * 60)
    
    applied = 0
    skipped = 0
    
    # Ordenar por confianza (mayor primero)
    corrections.sort(key=lambda x: x.confidence, reverse=True)
    
    for i, correction in enumerate(corrections, 1):
        filename = os.path.basename(correction.file_path)
        
        print(f"\n[{i}/{len(corrections)}] {filename}")
        print(f"Campo: {correction.field.title()}")
        print(f"Actual: '{correction.current_value}'")
        print(f"Sugerido: '{correction.suggested_value}'")
        print(f"Confianza: {correction.confidence:.1%}")
        print(f"Razón: {correction.reason}")
        
        while True:
            choice = input("\n¿Aplicar corrección? [s/n/q(salir)]: ").lower().strip()
            if choice in ['s', 'y', 'yes', 'sí', 'si']:
                # Aplicar corrección individual
                try:
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    if correction.field == "artist":
                        cursor.execute(
                            "UPDATE tracks SET artist = ? WHERE file_path = ?",
                            (correction.suggested_value, correction.file_path)
                        )
                    elif correction.field == "album":
                        cursor.execute(
                            "UPDATE tracks SET album = ? WHERE file_path = ?",
                            (correction.suggested_value, correction.file_path)
                        )
                    
                    conn.commit()
                    conn.close()
                    
                    print("✅ Corrección aplicada")
                    applied += 1
                    break
                    
                except Exception as e:
                    print(f"❌ Error aplicando corrección: {e}")
                    break
                    
            elif choice in ['n', 'no']:
                print("⏭️  Corrección omitida")
                skipped += 1
                break
            elif choice in ['q', 'quit', 'salir']:
                print(f"\n🏁 Proceso interrumpido por el usuario")
                print(f"Correcciones aplicadas: {applied}")
                print(f"Correcciones omitidas: {skipped}")
                return applied
            else:
                print("Por favor, ingrese 's' para sí, 'n' para no, o 'q' para salir")
    
    print(f"\n🏁 Proceso completado")
    print(f"Correcciones aplicadas: {applied}")
    print(f"Correcciones omitidas: {skipped}")
    
    return applied


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Validación y corrección de metadatos de artistas y álbumes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python validate_artists_albums.py --analyze                    # Solo análisis
  python validate_artists_albums.py --fix --min-confidence 0.8  # Corrección automática
  python validate_artists_albums.py --interactive               # Corrección interactiva
  python validate_artists_albums.py --stats-only                # Solo estadísticas
        """
    )
    
    parser.add_argument("--analyze", action="store_true",
                       help="Analizar problemas sin aplicar correcciones")
    parser.add_argument("--fix", action="store_true",
                       help="Aplicar correcciones automáticamente")
    parser.add_argument("--interactive", action="store_true",
                       help="Aplicar correcciones de forma interactiva")
    parser.add_argument("--stats-only", action="store_true",
                       help="Mostrar solo estadísticas")
    parser.add_argument("--min-confidence", type=float, default=0.8,
                       help="Confianza mínima para correcciones automáticas (default: 0.8)")
    parser.add_argument("--db-path", type=str,
                       help="Ruta personalizada a la base de datos")
    
    args = parser.parse_args()
    
    # Si no se especifica ninguna acción, mostrar análisis por defecto
    if not any([args.analyze, args.fix, args.interactive, args.stats_only]):
        args.analyze = True
    
    # Determinar ruta de la base de datos
    if args.db_path:
        db_path = args.db_path
    else:
        project_root = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(project_root, "config")
        db_path = os.path.join(config_path, "library.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        print("💡 Asegúrate de que la aplicación haya escaneado tu biblioteca musical")
        return 1
    
    print("🎵 VALIDADOR DE ARTISTAS Y ÁLBUMES - DjAlfin")
    print(f"📁 Base de datos: {db_path}")
    
    enhancer = ArtistAlbumEnhancer()
    
    # Generar estadísticas
    print("\n🔍 Analizando metadatos...")
    stats = enhancer.get_artist_album_statistics(db_path)
    
    if args.stats_only:
        print_statistics(stats)
        return 0
    
    # Mostrar estadísticas
    print_statistics(stats)
    
    if not args.stats_only:
        # Analizar correcciones
        print(f"\n🔍 Buscando correcciones sugeridas...")
        corrections = enhancer.analyze_artist_album_issues(db_path)
        
        # Mostrar resumen de correcciones
        print_corrections_summary(corrections)
        
        # Aplicar correcciones según el modo
        if args.fix and corrections:
            high_confidence = [c for c in corrections if c.confidence >= args.min_confidence]
            if high_confidence:
                print(f"\n🔧 Aplicando {len(high_confidence)} correcciones automáticas...")
                applied = enhancer.apply_corrections(db_path, high_confidence, args.min_confidence)
                print(f"✅ Se aplicaron {applied} correcciones automáticamente")
            else:
                print(f"\n💡 No hay correcciones con confianza ≥ {args.min_confidence:.1%}")
        
        elif args.interactive and corrections:
            applied = apply_corrections_interactive(enhancer, db_path, corrections)
            if applied > 0:
                print(f"\n🔄 Regenerando estadísticas...")
                new_stats = enhancer.get_artist_album_statistics(db_path)
                print(f"\n📊 Estadísticas Actualizadas:")
                print(f"  • Artistas inválidos: {stats['invalid_artists']} → {new_stats['invalid_artists']}")
                print(f"  • Álbumes inválidos: {stats['invalid_albums']} → {new_stats['invalid_albums']}")
    
    print(f"\n✨ Análisis completado")
    return 0


if __name__ == "__main__":
    sys.exit(main())