#!/usr/bin/env python3
"""
Script de prueba para el sistema de recomendaciones.
Diagnostica problemas y verifica el funcionamiento paso a paso.
"""

import sys
import os
import sqlite3
from typing import Dict, List

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import create_connection, get_db_path
from services.recommendation_service import get_recommendation_service
from core.dj_transition_analyzer import get_dj_transition_analyzer

def test_database_connection():
    """Prueba la conexión a la base de datos."""
    print("🔍 Probando conexión a la base de datos...")
    
    try:
        conn = create_connection()
        if not conn:
            print("❌ No se pudo conectar a la base de datos")
            return False
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tracks")
        track_count = cursor.fetchone()[0]
        
        print(f"✅ Conexión exitosa. {track_count} tracks en la base de datos")
        
        # Verificar que hay tracks con datos necesarios
        cursor.execute("""
            SELECT COUNT(*) FROM tracks 
            WHERE bpm IS NOT NULL AND bpm > 0 
            AND key IS NOT NULL AND key != 'Unknown'
        """)
        tracks_with_data = cursor.fetchone()[0]
        
        print(f"📊 {tracks_with_data} tracks tienen BPM y key válidos")
        
        conn.close()
        return track_count > 0
        
    except Exception as e:
        print(f"❌ Error en conexión a BD: {e}")
        return False

def get_sample_track():
    """Obtiene un track de muestra para las pruebas."""
    print("\n🎵 Obteniendo track de muestra...")
    
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        # Buscar un track con datos completos
        cursor.execute("""
            SELECT id, title, artist, album, genre, bpm, key, energy, valence, 
                   danceability, acousticness, duration, file_path
            FROM tracks 
            WHERE bpm IS NOT NULL AND bpm > 0 
            AND key IS NOT NULL AND key != 'Unknown'
            AND title IS NOT NULL
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            print("❌ No se encontraron tracks con datos completos")
            conn.close()
            return None
        
        # Convertir a diccionario
        columns = [desc[0] for desc in cursor.description]
        track = dict(zip(columns, row))
        
        print(f"✅ Track encontrado: '{track['title']}' - {track['artist']}")
        print(f"   BPM: {track['bpm']}, Key: {track['key']}, Genre: {track.get('genre', 'N/A')}")
        
        conn.close()
        return track
        
    except Exception as e:
        print(f"❌ Error obteniendo track de muestra: {e}")
        return None

def test_candidate_tracks(current_track):
    """Prueba la obtención de tracks candidatos."""
    print("\n🔍 Probando obtención de candidatos...")
    
    try:
        rec_service = get_recommendation_service()
        
        # Usar método interno para obtener candidatos
        candidates = rec_service._get_candidate_tracks(current_track)
        
        print(f"📊 {len(candidates)} candidatos encontrados")
        
        if candidates:
            # Mostrar algunos ejemplos
            print("   Ejemplos de candidatos:")
            for i, candidate in enumerate(candidates[:5]):
                title = candidate.get('title', 'Unknown')
                artist = candidate.get('artist', 'Unknown')
                bpm = candidate.get('bpm', 'N/A')
                key = candidate.get('key', 'Unknown')
                print(f"   {i+1}. {title} - {artist} (BPM: {bpm}, Key: {key})")
        
        return len(candidates) > 0
        
    except Exception as e:
        print(f"❌ Error obteniendo candidatos: {e}")
        return False

def test_single_transition_analysis(current_track, candidate_track):
    """Prueba el análisis de transición entre dos tracks específicos."""
    print("\n🔬 Probando análisis de transición individual...")
    
    try:
        analyzer = get_dj_transition_analyzer()
        
        print(f"   Desde: {current_track['title']} - {current_track['artist']}")
        print(f"   Hacia: {candidate_track['title']} - {candidate_track['artist']}")
        
        analysis = analyzer.analyze_transition(current_track, candidate_track)
        
        print(f"✅ Análisis completado:")
        print(f"   Score general: {analysis.overall_score:.2%}")
        print(f"   BPM compatibility: {analysis.bpm_compatibility:.2%}")
        print(f"   Key compatibility: {analysis.key_compatibility:.2%}")
        print(f"   Fuzzy key compatibility: {analysis.fuzzy_key_compatibility:.2%}")
        print(f"   Energy compatibility: {analysis.energy_compatibility:.2%}")
        print(f"   Tipo recomendado: {analysis.recommended_type.value}")
        print(f"   Calidad: {analysis.transition_quality.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en análisis de transición: {e}")
        import traceback
        print(f"   Detalle: {traceback.format_exc()}")
        return False

def test_recommendation_service(current_track):
    """Prueba el servicio de recomendaciones completo."""
    print("\n🎯 Probando servicio de recomendaciones...")
    
    try:
        rec_service = get_recommendation_service()
        
        print("   Generando recomendaciones (min_score=0.0, limit=10)...")
        recommendations = rec_service.get_compatible_tracks(
            current_track, 
            limit=10, 
            min_score=0.0  # Sin filtro de score mínimo
        )
        
        print(f"📊 {len(recommendations)} recomendaciones generadas")
        
        if recommendations:
            print("   Top 5 recomendaciones:")
            for i, (track, analysis) in enumerate(recommendations[:5]):
                title = track.get('title', 'Unknown')
                artist = track.get('artist', 'Unknown')
                score = analysis.overall_score
                quality = analysis.transition_quality.value
                print(f"   {i+1}. {title} - {artist} (Score: {score:.1%}, {quality})")
        else:
            print("⚠️ No se generaron recomendaciones")
            
            # Diagnosticar por qué no hay recomendaciones
            print("\n🔍 Diagnosticando problema...")
            
            # Verificar candidatos
            candidates = rec_service._get_candidate_tracks(current_track)
            print(f"   Candidatos disponibles: {len(candidates)}")
            
            if candidates:
                # Probar análisis con el primer candidato
                print("   Probando análisis con primer candidato...")
                test_single_transition_analysis(current_track, candidates[0])
        
        return len(recommendations) > 0
        
    except Exception as e:
        print(f"❌ Error en servicio de recomendaciones: {e}")
        import traceback
        print(f"   Detalle: {traceback.format_exc()}")
        return False

def test_database_content():
    """Examina el contenido de la base de datos en detalle."""
    print("\n📋 Examinando contenido de la base de datos...")
    
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("SELECT COUNT(*) FROM tracks")
        total_tracks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE bpm IS NOT NULL AND bpm > 0")
        tracks_with_bpm = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE key IS NOT NULL AND key != 'Unknown'")
        tracks_with_key = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tracks WHERE energy IS NOT NULL")
        tracks_with_energy = cursor.fetchone()[0]
        
        print(f"   Total tracks: {total_tracks}")
        print(f"   Con BPM válido: {tracks_with_bpm}")
        print(f"   Con key válida: {tracks_with_key}")
        print(f"   Con energy: {tracks_with_energy}")
        
        # Mostrar algunos ejemplos de datos
        cursor.execute("""
            SELECT title, artist, bpm, key, energy, genre
            FROM tracks 
            WHERE bpm IS NOT NULL AND key IS NOT NULL
            LIMIT 5
        """)
        
        print("\n   Ejemplos de tracks con datos:")
        for row in cursor.fetchall():
            title, artist, bpm, key, energy, genre = row
            print(f"   - {title} - {artist}: BPM={bpm}, Key={key}, Energy={energy}, Genre={genre}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error examinando BD: {e}")
        return False

def main():
    """Función principal de pruebas."""
    print("🧪 PRUEBA DEL SISTEMA DE RECOMENDACIONES")
    print("=" * 50)
    
    # Paso 1: Verificar conexión a BD
    if not test_database_connection():
        print("\n❌ Prueba fallida: Problemas con la base de datos")
        return
    
    # Paso 2: Examinar contenido de BD
    test_database_content()
    
    # Paso 3: Obtener track de muestra
    current_track = get_sample_track()
    if not current_track:
        print("\n❌ Prueba fallida: No se pudo obtener track de muestra")
        return
    
    # Paso 4: Probar obtención de candidatos
    if not test_candidate_tracks(current_track):
        print("\n❌ Prueba fallida: Problemas obteniendo candidatos")
        return
    
    # Paso 5: Probar análisis individual
    rec_service = get_recommendation_service()
    candidates = rec_service._get_candidate_tracks(current_track)
    if candidates:
        test_single_transition_analysis(current_track, candidates[0])
    
    # Paso 6: Probar servicio completo
    success = test_recommendation_service(current_track)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ TODAS LAS PRUEBAS EXITOSAS")
        print("   El sistema de recomendaciones está funcionando correctamente")
    else:
        print("❌ PRUEBAS FALLIDAS")
        print("   Revisar los errores arriba para diagnosticar el problema")

if __name__ == "__main__":
    main()