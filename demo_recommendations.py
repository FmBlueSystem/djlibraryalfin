#!/usr/bin/env python3
"""
Demo del sistema de recomendaciones de DjAlfin.
Muestra las mejores recomendaciones para cada track en la biblioteca.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import create_connection
from services.recommendation_service import get_recommendation_service

def demo_recommendations():
    """Demuestra el sistema de recomendaciones."""
    print("🎯 DEMO: Sistema de Recomendaciones DJ Profesional")
    print("=" * 60)
    
    # Obtener todos los tracks
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, artist, bpm, key, genre
        FROM tracks 
        WHERE bpm IS NOT NULL AND bpm > 0 
        AND key IS NOT NULL AND key != 'Unknown'
        ORDER BY title
        LIMIT 5
    """)
    
    tracks = []
    for row in cursor.fetchall():
        columns = [desc[0] for desc in cursor.description]
        track = dict(zip(columns, row))
        tracks.append(track)
    
    conn.close()
    
    if not tracks:
        print("❌ No se encontraron tracks con datos completos")
        return
    
    rec_service = get_recommendation_service()
    
    for i, track in enumerate(tracks, 1):
        print(f"\n📀 TRACK #{i}: {track['title']} - {track['artist']}")
        print(f"   🎛️ {track['bpm']:.0f} BPM | 🎼 {track['key']} | 🎨 {track.get('genre', 'N/A')}")
        print("   " + "-" * 50)
        
        # Obtener recomendaciones
        recommendations = rec_service.get_compatible_tracks(
            track, limit=5, min_score=0.6  # Solo mostrar buenas recomendaciones
        )
        
        if recommendations:
            print(f"   💡 Top {len(recommendations)} recomendaciones compatibles:")
            
            for j, (rec_track, analysis) in enumerate(recommendations, 1):
                score = analysis.overall_score
                quality = analysis.transition_quality.value
                transition_type = analysis.recommended_type.value.replace('_', ' ').title()
                
                # Emoji según calidad
                if score >= 0.9:
                    emoji = "🔥"
                elif score >= 0.8:
                    emoji = "✨"
                elif score >= 0.7:
                    emoji = "👍"
                else:
                    emoji = "👌"
                
                print(f"   {j}. {emoji} {rec_track['title']} - {rec_track['artist']}")
                print(f"      Score: {score:.1%} | {quality.title()} | {transition_type}")
                
                # Mostrar compatibilidades específicas
                bpm_compat = analysis.bpm_compatibility
                key_compat = max(analysis.key_compatibility, analysis.fuzzy_key_compatibility)
                
                print(f"      🎛️ BPM: {bpm_compat:.0%} | 🎼 Key: {key_compat:.0%}")
                
                # Mostrar recomendación principal
                if analysis.recommendations:
                    main_rec = analysis.recommendations[0].replace("✅", "").replace("🎛️", "").replace("🎵", "").strip()
                    if len(main_rec) > 60:
                        main_rec = main_rec[:57] + "..."
                    print(f"      💡 {main_rec}")
                
                print()
        else:
            print("   ⚠️ No se encontraron recomendaciones con score >= 60%")
        
        print()

def demo_detailed_analysis():
    """Muestra un análisis detallado entre dos tracks específicos."""
    print("🔬 DEMO: Análisis Detallado de Transición")
    print("=" * 60)
    
    conn = create_connection()
    cursor = conn.cursor()
    
    # Obtener dos tracks para análisis
    cursor.execute("""
        SELECT id, title, artist, bpm, key, genre, energy, valence, danceability
        FROM tracks 
        WHERE bpm IS NOT NULL AND key IS NOT NULL
        LIMIT 2
    """)
    
    rows = cursor.fetchall()
    if len(rows) < 2:
        print("❌ No hay suficientes tracks para análisis")
        return
    
    columns = [desc[0] for desc in cursor.description]
    track1 = dict(zip(columns, rows[0]))
    track2 = dict(zip(columns, rows[1]))
    
    conn.close()
    
    rec_service = get_recommendation_service()
    analysis_data = rec_service.get_detailed_analysis(track1, track2)
    
    if not analysis_data:
        print("❌ No se pudo realizar el análisis")
        return
    
    print(f"🎵 DESDE: {track1['title']} - {track1['artist']}")
    print(f"   BPM: {track1['bpm']:.0f} | Key: {track1['key']} | Genre: {track1.get('genre', 'N/A')}")
    
    print(f"\n🎵 HACIA: {track2['title']} - {track2['artist']}")
    print(f"   BPM: {track2['bpm']:.0f} | Key: {track2['key']} | Genre: {track2.get('genre', 'N/A')}")
    
    print(f"\n📊 RESULTADO DEL ANÁLISIS:")
    print(f"   🎯 Score General: {analysis_data['overall_score']:.1%}")
    print(f"   🏆 Calidad: {analysis_data['transition_quality'].title()}")
    print(f"   🔄 Tipo Recomendado: {analysis_data['recommended_type'].replace('_', ' ').title()}")
    
    print(f"\n📈 COMPATIBILIDADES ESPECÍFICAS:")
    compat = analysis_data['compatibility']
    print(f"   🎛️ BPM: {compat['bpm']:.1%}")
    print(f"   🎼 Tonalidad Tradicional: {compat['key']:.1%}")
    print(f"   🌈 Fuzzy Keymixing: {compat['fuzzy_key']:.1%}")
    print(f"   ⚡ Energía: {compat['energy']:.1%}")
    print(f"   🎨 Mood: {compat['mood']:.1%}")
    
    print(f"\n⚙️ DETALLES TÉCNICOS:")
    tech = analysis_data['technical_details']
    print(f"   🔄 Ratio BPM: {tech['bpm_ratio']:.2f}")
    print(f"   🎼 Relación Tonal: {tech['key_relationship']}")
    print(f"   🌈 Relación Fuzzy: {tech['fuzzy_key_relationship']}")
    print(f"   ⚡ Delta Energía: {tech['energy_delta']:+.2f}")
    print(f"   ⏯️ Punto Salida: {tech['mix_out_point']:.1f}s")
    print(f"   ▶️ Punto Entrada: {tech['mix_in_point']:.1f}s")
    print(f"   🌊 Duración Crossfade: {tech['crossfade_duration']:.1f}s")
    
    if analysis_data['recommendations']:
        print(f"\n💡 RECOMENDACIONES:")
        for i, rec in enumerate(analysis_data['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    if analysis_data['warnings']:
        print(f"\n⚠️ ADVERTENCIAS:")
        for i, warning in enumerate(analysis_data['warnings'], 1):
            print(f"   {i}. {warning}")
    
    if analysis_data.get('pitch_shift'):
        ps = analysis_data['pitch_shift']
        print(f"\n🎛️ PITCH SHIFT RECOMENDADO:")
        print(f"   📏 Ajuste: {ps['shift_semitones']:+.1f} semitonos")
        print(f"   📈 Mejora: {ps['improvement']:.1%}")
        print(f"   🎯 Confianza: {ps['confidence']:.1%}")
        print(f"   💭 Explicación: {ps['explanation']}")

def main():
    """Función principal del demo."""
    print("🎧 DjAlfin - Sistema de Recomendaciones Profesional")
    print("🔥 Análisis DJ con BPM, Harmonía Tradicional y Fuzzy Keymixing")
    print()
    
    # Demo 1: Recomendaciones generales
    demo_recommendations()
    
    print("\n" + "=" * 60)
    input("Presiona Enter para continuar con el análisis detallado...")
    print()
    
    # Demo 2: Análisis detallado
    demo_detailed_analysis()
    
    print("\n" + "=" * 60)
    print("✅ Demo completado!")
    print("\n💡 Para usar en la aplicación:")
    print("   1. Ejecuta 'python main.py'")
    print("   2. Haz clic derecho en cualquier track")
    print("   3. Selecciona '🎯 Sugerir canciones compatibles'")
    print("   4. ¡Explora las recomendaciones profesionales!")

if __name__ == "__main__":
    main()