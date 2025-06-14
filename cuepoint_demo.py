#!/usr/bin/env python3
"""
DjAlfin - Demo de Cue Points
Demostración práctica del sistema de cue points compatible con Serato y Mixed In Key
"""

import os
import sys
import time
from cuepoint_manager import (
    CuePointManager, 
    DjAlfinMetadataManager, 
    auto_detect_cue_points,
    CuePoint,
    LoopPoint
)

def demo_basic_cue_points():
    """Demo básico de cue points."""
    print("🎯 DEMO 1: Cue Points Básicos")
    print("=" * 40)
    
    manager = CuePointManager()
    
    # Agregar cue points típicos de una canción
    print("📍 Agregando cue points...")
    
    # Intro
    intro_cue = manager.add_cue_point(
        position=8.5,
        name="Intro Start", 
        color="#FF0000",
        hotcue_index=1
    )
    print(f"  ✅ {intro_cue.name} @ {intro_cue.position}s")
    
    # Verse
    verse_cue = manager.add_cue_point(
        position=32.2,
        name="Verse 1",
        color="#00FF00", 
        hotcue_index=2
    )
    print(f"  ✅ {verse_cue.name} @ {verse_cue.position}s")
    
    # Chorus
    chorus_cue = manager.add_cue_point(
        position=64.8,
        name="Chorus",
        color="#0000FF",
        hotcue_index=3
    )
    print(f"  ✅ {chorus_cue.name} @ {chorus_cue.position}s")
    
    # Drop
    drop_cue = manager.add_cue_point(
        position=96.5,
        name="Drop",
        color="#FFFF00",
        hotcue_index=4
    )
    print(f"  ✅ {drop_cue.name} @ {drop_cue.position}s")
    
    # Breakdown
    breakdown_cue = manager.add_cue_point(
        position=128.3,
        name="Breakdown",
        color="#FF00FF",
        hotcue_index=5
    )
    print(f"  ✅ {breakdown_cue.name} @ {breakdown_cue.position}s")
    
    # Outro
    outro_cue = manager.add_cue_point(
        position=180.7,
        name="Outro",
        color="#00FFFF",
        hotcue_index=6
    )
    print(f"  ✅ {outro_cue.name} @ {outro_cue.position}s")
    
    print(f"\n📊 Total cue points: {len(manager.cue_points)}")
    print(f"🔥 Hot cues: {len(manager.get_hotcues())}")
    
    return manager

def demo_loop_points():
    """Demo de loop points."""
    print("\n🔁 DEMO 2: Loop Points")
    print("=" * 40)
    
    manager = CuePointManager()
    
    # Loop principal
    main_loop = manager.add_loop_point(
        start_pos=64.0,
        end_pos=96.0,
        name="Main Loop",
        color="#FF8000"
    )
    print(f"  🔁 {main_loop.name}: {main_loop.start_position}s - {main_loop.end_position}s")
    
    # Loop de breakdown
    breakdown_loop = manager.add_loop_point(
        start_pos=128.0,
        end_pos=144.0,
        name="Breakdown Loop",
        color="#8000FF"
    )
    print(f"  🔁 {breakdown_loop.name}: {breakdown_loop.start_position}s - {breakdown_loop.end_position}s")
    
    # Loop corto para scratching
    scratch_loop = manager.add_loop_point(
        start_pos=32.0,
        end_pos=34.0,
        name="Scratch Loop",
        color="#FF0080"
    )
    print(f"  🔁 {scratch_loop.name}: {scratch_loop.start_position}s - {scratch_loop.end_position}s")
    
    print(f"\n📊 Total loops: {len(manager.loop_points)}")
    
    return manager

def demo_hotcue_access():
    """Demo de acceso a hot cues."""
    print("\n🔥 DEMO 3: Acceso a Hot Cues")
    print("=" * 40)
    
    manager = demo_basic_cue_points()
    
    print("🎮 Simulando presión de hot cues...")
    
    # Simular presión de teclas 1-8
    for i in range(1, 9):
        cue = manager.get_cue_by_hotkey(i)
        if cue:
            print(f"  🔥 Hot Cue {i}: {cue.name} @ {cue.position}s {cue.color}")
        else:
            print(f"  ⚫ Hot Cue {i}: No asignado")
    
    print("\n🎯 Buscando cue point cerca de 65 segundos...")
    target_time = 65.0
    closest_cue = None
    min_distance = float('inf')
    
    for cue in manager.cue_points:
        distance = abs(cue.position - target_time)
        if distance < min_distance:
            min_distance = distance
            closest_cue = cue
    
    if closest_cue:
        print(f"  📍 Más cercano: {closest_cue.name} @ {closest_cue.position}s (distancia: {min_distance:.1f}s)")

def demo_serato_compatibility():
    """Demo de compatibilidad con Serato."""
    print("\n🎧 DEMO 4: Compatibilidad Serato")
    print("=" * 40)
    
    # Crear archivo de prueba (simulado)
    test_file = "test_track.mp3"
    print(f"📁 Archivo de prueba: {test_file}")
    
    # Crear gestor de metadatos
    print("🔧 Creando gestor de metadatos...")
    
    # Simular carga y guardado
    manager = CuePointManager()
    
    # Agregar cue points de ejemplo
    manager.add_cue_point(15.5, "Serato Cue 1", "#FF0000", 1)
    manager.add_cue_point(45.2, "Serato Cue 2", "#00FF00", 2)
    manager.add_cue_point(75.8, "Serato Cue 3", "#0000FF", 3)
    
    print(f"📍 Cue points creados: {len(manager.cue_points)}")
    
    # Simular conversión a formato Serato
    from cuepoint_manager import SeratoMetadataParser
    
    print("🔄 Convirtiendo a formato Serato...")
    serato_data = SeratoMetadataParser.create_serato_markers(manager.cue_points)
    print(f"📦 Datos Serato generados: {len(serato_data)} bytes")
    
    # Simular parsing de vuelta
    print("🔍 Parseando datos Serato...")
    parsed_cues = SeratoMetadataParser.parse_serato_markers(serato_data)
    print(f"📍 Cue points parseados: {len(parsed_cues)}")
    
    # Verificar integridad
    print("\n✅ Verificación de integridad:")
    for original, parsed in zip(manager.cue_points, parsed_cues):
        pos_match = abs(original.position - parsed.position) < 0.1
        color_match = original.color.upper() == parsed.color.upper()
        print(f"  • Posición: {'✅' if pos_match else '❌'} ({original.position:.1f}s vs {parsed.position:.1f}s)")
        print(f"  • Color: {'✅' if color_match else '❌'} ({original.color} vs {parsed.color})")

def demo_auto_detection():
    """Demo de detección automática de cue points."""
    print("\n🤖 DEMO 5: Detección Automática")
    print("=" * 40)
    
    print("🔍 Simulando detección automática de cue points...")
    
    # Simular posiciones detectadas automáticamente
    auto_positions = [12.3, 28.7, 45.1, 62.8, 89.4, 115.2, 142.6, 168.9]
    
    manager = CuePointManager()
    
    print("📊 Posiciones detectadas por análisis de energía:")
    for i, pos in enumerate(auto_positions):
        # Asignar colores automáticamente
        colors = list(manager.SERATO_COLORS.values())
        color = colors[i % len(colors)]
        
        cue = manager.add_cue_point(
            position=pos,
            name=f"Auto Cue {i+1}",
            color=color,
            hotcue_index=i+1 if i < 8 else 0
        )
        
        print(f"  🎯 {cue.name} @ {cue.position:.1f}s {cue.color}")
    
    print(f"\n📈 Análisis completado: {len(manager.cue_points)} cue points detectados")
    print(f"🔥 Hot cues asignados: {len(manager.get_hotcues())}")

def demo_color_system():
    """Demo del sistema de colores."""
    print("\n🎨 DEMO 6: Sistema de Colores")
    print("=" * 40)
    
    manager = CuePointManager()
    
    print("🌈 Colores predefinidos compatibles con Serato:")
    for name, color in manager.SERATO_COLORS.items():
        print(f"  • {name.capitalize()}: {color}")
    
    print("\n🎯 Creando cue points con colores temáticos...")
    
    # Tema energético
    energy_cues = [
        (20.0, "Low Energy", "#0000FF"),    # Azul para baja energía
        (60.0, "Medium Energy", "#FFFF00"), # Amarillo para media energía  
        (100.0, "High Energy", "#FF8000"),  # Naranja para alta energía
        (140.0, "Peak Energy", "#FF0000")   # Rojo para pico de energía
    ]
    
    for pos, name, color in energy_cues:
        cue = manager.add_cue_point(pos, name, color)
        print(f"  ⚡ {cue.name} @ {cue.position}s {cue.color}")
    
    # Tema estructural
    print("\n🏗️ Estructura de canción:")
    structure_cues = [
        (8.0, "Intro", "#808080"),      # Gris para intro
        (32.0, "Verse", "#00FF00"),     # Verde para verse
        (64.0, "Chorus", "#FF00FF"),    # Magenta para chorus
        (96.0, "Bridge", "#00FFFF"),    # Cyan para bridge
        (128.0, "Outro", "#800080")     # Púrpura para outro
    ]
    
    for pos, name, color in structure_cues:
        cue = manager.add_cue_point(pos, name, color)
        print(f"  🎵 {cue.name} @ {cue.position}s {cue.color}")

def demo_performance_mixing():
    """Demo de mezcla en vivo."""
    print("\n🎧 DEMO 7: Mezcla en Vivo")
    print("=" * 40)
    
    # Simular dos tracks cargados
    track_a = CuePointManager()
    track_b = CuePointManager()
    
    # Track A - House progresivo
    print("🎵 Track A: Progressive House")
    track_a.add_cue_point(16.0, "Intro", "#FF0000", 1)
    track_a.add_cue_point(64.0, "Build Up", "#FF8000", 2)
    track_a.add_cue_point(128.0, "Drop", "#FFFF00", 3)
    track_a.add_cue_point(192.0, "Breakdown", "#00FF00", 4)
    
    for cue in track_a.cue_points:
        print(f"  🅰️ {cue.name} @ {cue.position}s")
    
    # Track B - Tech House
    print("\n🎵 Track B: Tech House")
    track_b.add_cue_point(8.0, "Intro", "#0000FF", 1)
    track_b.add_cue_point(40.0, "Groove", "#8000FF", 2)
    track_b.add_cue_point(88.0, "Peak", "#FF00FF", 3)
    track_b.add_cue_point(136.0, "Outro", "#00FFFF", 4)
    
    for cue in track_b.cue_points:
        print(f"  🅱️ {cue.name} @ {cue.position}s")
    
    # Simular mezcla
    print("\n🎛️ Simulando mezcla:")
    print("  1. Track A playing desde Intro (16s)")
    print("  2. Pre-cue Track B en Intro (8s)")
    print("  3. Crossfade durante Build Up de A (64s)")
    print("  4. Track B toma control en Groove (40s)")
    print("  5. Mezcla perfecta lograda! 🎉")

def main():
    """Función principal del demo."""
    print("🎯 DjAlfin - Sistema de Cue Points")
    print("🎧 Compatible con Serato DJ, Mixed In Key y Traktor")
    print("=" * 60)
    
    try:
        # Ejecutar todos los demos
        demo_basic_cue_points()
        demo_loop_points()
        demo_hotcue_access()
        demo_serato_compatibility()
        demo_auto_detection()
        demo_color_system()
        demo_performance_mixing()
        
        print("\n" + "=" * 60)
        print("✅ TODOS LOS DEMOS COMPLETADOS EXITOSAMENTE")
        print("🎵 El sistema de cue points está listo para usar!")
        print("🔗 Compatible con los principales software de DJ")
        print("🚀 DjAlfin - Llevando el DJing al siguiente nivel")
        
    except Exception as e:
        print(f"\n❌ Error durante el demo: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
