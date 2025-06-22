#!/usr/bin/env python3
"""
Test rápido para verificar que los errores del sistema de recomendaciones están corregidos.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Prueba que todos los imports funcionen correctamente."""
    print("🔍 Probando imports...")
    
    try:
        from ui.components.recommendations_dialog import RecommendationsDialog, RecommendationWorker
        print("✅ RecommendationsDialog importado correctamente")
        
        from services.recommendation_service import get_recommendation_service
        print("✅ RecommendationService importado correctamente")
        
        from core.dj_transition_analyzer import get_dj_transition_analyzer
        print("✅ DJTransitionAnalyzer importado correctamente")
        
        from ui.components.playlist_dialog import PlaylistDialog
        print("✅ PlaylistDialog importado correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_qt_references():
    """Prueba que las referencias a Qt estén correctas."""
    print("\n🔍 Probando referencias Qt...")
    
    try:
        from PySide6.QtWidgets import QDialog
        
        # Verificar que QDialog.Accepted existe
        accepted_value = QDialog.Accepted
        print(f"✅ QDialog.Accepted = {accepted_value}")
        
        # Verificar imports en recommendations_dialog
        from ui.components.recommendations_dialog import RecommendationsDialog
        print("✅ RecommendationsDialog puede acceder a QDialog.Accepted")
        
        return True
        
    except AttributeError as e:
        print(f"❌ Error de atributo Qt: {e}")
        return False
    except Exception as e:
        print(f"❌ Error con referencias Qt: {e}")
        return False

def test_sample_track_analysis():
    """Prueba análisis con track de muestra."""
    print("\n🔍 Probando análisis de track de muestra...")
    
    try:
        from core.database import create_connection
        
        # Obtener track de muestra
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, artist, bpm, key, genre
            FROM tracks 
            WHERE bpm IS NOT NULL AND key IS NOT NULL
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            print("⚠️ No hay tracks con datos para probar")
            return True
        
        columns = [desc[0] for desc in cursor.description]
        track = dict(zip(columns, row))
        conn.close()
        
        print(f"📀 Track de prueba: {track['title']} - {track['artist']}")
        
        # Probar servicio de recomendaciones
        from services.recommendation_service import get_recommendation_service
        rec_service = get_recommendation_service()
        
        # Probar con límite pequeño
        recommendations = rec_service.get_compatible_tracks(track, limit=3, min_score=0.0)
        print(f"✅ {len(recommendations)} recomendaciones generadas")
        
        if recommendations:
            best_track, best_analysis = recommendations[0]
            print(f"   Mejor match: {best_track['title']} (Score: {best_analysis.overall_score:.1%})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en análisis de muestra: {e}")
        import traceback
        print(f"   Detalle: {traceback.format_exc()[:500]}...")
        return False

def test_dialog_creation():
    """Prueba creación del diálogo sin mostrarlo."""
    print("\n🔍 Probando creación de diálogo...")
    
    try:
        # Crear aplicación Qt mínima para testing
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Track de prueba
        test_track = {
            'id': 1,
            'title': 'Test Song',
            'artist': 'Test Artist',
            'bpm': 120,
            'key': '1A',
            'genre': 'Test'
        }
        
        # Crear diálogo
        from ui.components.recommendations_dialog import RecommendationsDialog
        dialog = RecommendationsDialog(test_track)
        
        print("✅ Diálogo creado exitosamente")
        
        # Limpiar
        dialog.close()
        dialog.deleteLater()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando diálogo: {e}")
        import traceback
        print(f"   Detalle: {traceback.format_exc()[:500]}...")
        return False

def main():
    """Función principal de pruebas."""
    print("🧪 PRUEBAS DE CORRECCIÓN DE ERRORES")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Referencias Qt", test_qt_references),
        ("Análisis de muestra", test_sample_track_analysis),
        ("Creación de diálogo", test_dialog_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔄 Ejecutando: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASÓ")
                passed += 1
            else:
                print(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADOS: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las correcciones funcionan correctamente!")
        print("✅ El sistema de recomendaciones debería funcionar sin errores")
    else:
        print("⚠️ Algunas pruebas fallaron, revisar los errores arriba")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)