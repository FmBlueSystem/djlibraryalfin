#!/usr/bin/env python3
"""
Script de demostración de las mejoras en clasificación de géneros
y validación histórica para DjAlfin
"""

import os
import sys
import sqlite3
from typing import Dict, List

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.genre_classifier import GenreClassifier, GenreClassification
from core.historical_analyzer import HistoricalConsistencyAnalyzer


def demo_genre_classification():
    """Demuestra las capacidades del clasificador de géneros."""
    print("🎵 DEMOSTRACIÓN: Clasificación Inteligente de Géneros")
    print("=" * 60)
    
    classifier = GenreClassifier()
    
    # Casos de prueba con géneros problemáticos
    test_cases = [
        {
            "raw_genres": ["N/A"],
            "artist": "Apache Indian",
            "year": 1993,
            "description": "Género inválido"
        },
        {
            "raw_genres": ["2008 Universal Fire Victim"],
            "artist": "Dolly Parton",
            "year": 1980,
            "description": "Género corrupto"
        },
        {
            "raw_genres": ["Easy Listening Pop Soul Contemporary R & B"],
            "artist": "Whitney Houston",
            "year": 1992,
            "description": "Género demasiado específico"
        },
        {
            "raw_genres": ["electronic dance music", "EDM", "house"],
            "artist": "Daft Punk",
            "year": 2001,
            "sources": ["spotify", "musicbrainz"],
            "description": "Múltiples fuentes, aliases"
        },
        {
            "raw_genres": ["hip-hop", "rap music"],
            "artist": "Eminem",
            "year": 2000,
            "sources": ["spotify"],
            "description": "Aliases de Hip Hop"
        },
        {
            "raw_genres": ["Dubstep"],
            "artist": "Skrillex",
            "year": 1970,  # Año incorrecto intencionalmente
            "description": "Género anacrónicamente temprano"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Caso {i}: {case['description']}")
        print(f"   Géneros originales: {case['raw_genres']}")
        print(f"   Artista: {case['artist']}, Año: {case['year']}")
        
        classification = classifier.classify_genre(
            raw_genres=case["raw_genres"],
            artist=case["artist"],
            year=case["year"],
            sources=case.get("sources", ["file_metadata"])
        )
        
        print(f"   ✅ Género principal: {classification.primary_genre}")
        print(f"   📊 Confianza: {classification.confidence.name} ({classification.confidence.value})")
        
        if classification.subgenres:
            print(f"   🎼 Subgéneros: {', '.join(classification.subgenres)}")
        
        if classification.historical_context:
            print(f"   ⚠️  Contexto histórico: {classification.historical_context}")
        
        if classification.decade:
            print(f"   📅 Década: {classification.decade}")
        
        print(f"   🔍 Fuentes: {', '.join(classification.sources)}")


def demo_normalization():
    """Demuestra la normalización de géneros."""
    print("\n\n🔧 DEMOSTRACIÓN: Normalización de Géneros")
    print("=" * 60)
    
    classifier = GenreClassifier()
    
    # Casos de normalización
    normalization_cases = [
        "electronic dance music",
        "hip-hop",
        "r&b",
        "rock and roll",
        "N/A",
        "2008 universal fire victim",
        "HEAVY METAL",
        "pop music",
        "rhythm and blues",
        "country & western"
    ]
    
    print("Género Original → Género Normalizado")
    print("-" * 40)
    
    for genre in normalization_cases:
        normalized = classifier.normalize_genre(genre)
        status = "✅" if normalized else "❌"
        result = normalized if normalized else "INVÁLIDO"
        print(f"{status} '{genre}' → '{result}'")


def demo_historical_validation():
    """Demuestra la validación histórica."""
    print("\n\n🕰️  DEMOSTRACIÓN: Validación Histórica")
    print("=" * 60)
    
    classifier = GenreClassifier()
    
    # Casos de validación histórica
    historical_cases = [
        ("Rock & Roll", 1955, "Género apropiado para la época"),
        ("Dubstep", 2010, "Género apropiado para la época"),
        ("Dubstep", 1970, "Género anacrónicamente temprano"),
        ("Hip Hop", 1975, "Género en sus inicios"),
        ("Trap", 2015, "Género apropiado para la época"),
        ("Hyperpop", 2020, "Género muy reciente"),
        ("Jazz", 1920, "Género clásico apropiado")
    ]
    
    print("Género | Año | Validación | Descripción")
    print("-" * 50)
    
    for genre, year, description in historical_cases:
        is_valid = classifier.validate_historical_context(genre, year)
        status = "✅ VÁLIDO" if is_valid else "⚠️  SOSPECHOSO"
        print(f"{genre:<12} | {year} | {status:<12} | {description}")


def demo_database_analysis():
    """Demuestra el análisis de base de datos."""
    print("\n\n📊 DEMOSTRACIÓN: Análisis de Base de Datos")
    print("=" * 60)
    
    # Buscar base de datos
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "config")
    db_path = os.path.join(config_path, "library.db")
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada. Creando datos de ejemplo...")
        create_demo_database(db_path)
    
    classifier = GenreClassifier()
    
    # Generar estadísticas
    print("📈 Generando estadísticas de géneros...")
    stats = classifier.get_genre_statistics(db_path)
    
    print(f"\n📊 Estadísticas:")
    print(f"  • Total de pistas: {stats['total_tracks']}")
    print(f"  • Pistas con género: {stats['tracks_with_genre']}")
    print(f"  • Géneros únicos: {stats['unique_genres']}")
    print(f"  • Géneros inválidos: {stats['invalid_genres']}")
    
    if stats['problematic_genres']:
        print(f"\n⚠️  Géneros problemáticos encontrados:")
        for genre, count in stats['problematic_genres'][:5]:
            print(f"  • '{genre}': {count} pistas")
    
    # Sugerencias de corrección
    print(f"\n🔍 Analizando correcciones sugeridas...")
    corrections = classifier.suggest_corrections(db_path)
    
    if corrections:
        print(f"📝 Se sugieren {len(corrections)} correcciones:")
        for i, (file_path, old_genre, new_genre, reason) in enumerate(corrections[:3], 1):
            filename = os.path.basename(file_path)
            print(f"  {i}. {filename}")
            print(f"     '{old_genre}' → '{new_genre}' ({reason})")
    else:
        print("✅ No se encontraron géneros que requieran corrección")


def demo_historical_consistency():
    """Demuestra el análisis de consistencia histórica."""
    print("\n\n🕰️  DEMOSTRACIÓN: Análisis de Consistencia Histórica")
    print("=" * 60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "config")
    db_path = os.path.join(config_path, "library.db")
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    analyzer = HistoricalConsistencyAnalyzer()
    
    print("🔍 Analizando consistencia histórica...")
    report = analyzer.generate_consistency_report(db_path)
    
    print(f"\n📊 Resumen del análisis:")
    print(f"  • Total de inconsistencias: {report['summary']['total_inconsistencies']}")
    print(f"  • Alta severidad: {report['summary']['high_severity']}")
    print(f"  • Media severidad: {report['summary']['medium_severity']}")
    print(f"  • Baja severidad: {report['summary']['low_severity']}")
    
    if report['by_type']:
        print(f"\n📋 Tipos de problemas encontrados:")
        for issue_type, count in report['by_type'].items():
            print(f"  • {issue_type.replace('_', ' ').title()}: {count}")
    
    if report['recommendations']:
        print(f"\n💡 Recomendaciones:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")


def create_demo_database(db_path: str):
    """Crea una base de datos de demostración con datos problemáticos."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tabla
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            title TEXT,
            artist TEXT,
            album TEXT,
            genre TEXT,
            year INTEGER,
            bpm REAL,
            key TEXT,
            duration REAL,
            bitrate INTEGER,
            sample_rate INTEGER,
            file_size INTEGER,
            energy REAL,
            rating INTEGER,
            play_count INTEGER DEFAULT 0,
            last_played TIMESTAMP,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Datos de ejemplo con problemas
    demo_tracks = [
        ("demo1.mp3", "Boom Shack-A-Lak", "Apache Indian", "No Reservations", "N/A", 1993, 95.0, "Am", 240.5),
        ("demo2.mp3", "9 To 5", "Dolly Parton", "9 to 5 and Odd Jobs", "2008 Universal Fire Victim", 1980, 110.0, "G", 165.2),
        ("demo3.mp3", "I Will Always Love You", "Whitney Houston", "The Bodyguard", "Easy Listening Pop Soul Contemporary R & B", 1992, 68.0, "A", 273.8),
        ("demo4.mp3", "One More Time", "Daft Punk", "Discovery", "electronic dance music", 2001, 123.0, "Em", 320.4),
        ("demo5.mp3", "Lose Yourself", "Eminem", "8 Mile", "hip-hop", 2002, 86.0, "Bm", 326.1),
        ("demo6.mp3", "Scary Monsters", "Skrillex", "Scary Monsters and Nice Sprites", "Dubstep", 1970, 140.0, "F#m", 270.3),  # Año incorrecto
        ("demo7.mp3", "Stayin' Alive", "Bee Gees", "Saturday Night Fever", "Disco", 1977, 103.0, "Bm", 285.7),
        ("demo8.mp3", "Smells Like Teen Spirit", "Nirvana", "Nevermind", "Grunge", 1991, 117.0, "F", 301.9),
    ]
    
    for track in demo_tracks:
        cursor.execute("""
            INSERT OR REPLACE INTO tracks 
            (file_path, title, artist, album, genre, year, bpm, key, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, track)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Base de datos de demostración creada en: {db_path}")


def main():
    """Función principal de demostración."""
    print("🎵 DEMOSTRACIÓN DE MEJORAS EN METADATOS MUSICALES")
    print("=" * 80)
    print("Este script demuestra las mejoras implementadas para elevar")
    print("la exactitud y consistencia de los metadatos musicales en DjAlfin")
    print("=" * 80)
    
    try:
        # Demostrar clasificación de géneros
        demo_genre_classification()
        
        # Demostrar normalización
        demo_normalization()
        
        # Demostrar validación histórica
        demo_historical_validation()
        
        # Demostrar análisis de base de datos
        demo_database_analysis()
        
        # Demostrar análisis de consistencia histórica
        demo_historical_consistency()
        
        print("\n\n🎉 RESUMEN DE MEJORAS IMPLEMENTADAS")
        print("=" * 60)
        print("✅ Clasificación inteligente de géneros con jerarquías")
        print("✅ Normalización automática de géneros y aliases")
        print("✅ Validación histórica contra contexto temporal")
        print("✅ Detección de géneros inválidos y corruptos")
        print("✅ Sugerencias de corrección automáticas")
        print("✅ Análisis de consistencia histórica")
        print("✅ Integración con múltiples fuentes de metadatos")
        print("✅ Sistema de confianza basado en múltiples factores")
        
        print("\n💡 BENEFICIOS PARA DJs:")
        print("• Géneros más precisos y consistentes")
        print("• Mejor organización de la biblioteca musical")
        print("• Detección automática de metadatos problemáticos")
        print("• Validación histórica para evitar anacronismos")
        print("• Clasificación inteligente que aprende de múltiples fuentes")
        
    except Exception as e:
        print(f"❌ Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()