#!/usr/bin/env python3
"""
Demo específico para demostrar que el ordenamiento por columnas funciona
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from ui.main_window import MainWindow


def demo_sorting():
    """Demuestra el ordenamiento por columnas en TrackListView."""
    app = QApplication(sys.argv)
    window = MainWindow()
    track_list = window.track_list_view
    
    window.show()
    
    print("🎵 DEMO: Ordenamiento por Columnas en TrackListView")
    print("=" * 60)
    
    def run_demo():
        print("📊 Estado inicial de la tabla:")
        model = track_list.proxy_model
        
        # Mostrar primeros 5 tracks
        print("  Primeros 5 tracks (orden actual):")
        for row in range(min(5, model.rowCount())):
            title = model.data(model.index(row, 0), Qt.ItemDataRole.DisplayRole)
            artist = model.data(model.index(row, 1), Qt.ItemDataRole.DisplayRole)
            bpm = model.data(model.index(row, 2), Qt.ItemDataRole.DisplayRole)
            print(f"    {row+1}. {title} - {artist} ({bpm} BPM)")
        
        print("\n🔄 PROBANDO ORDENAMIENTO POR TÍTULO (Descendente)...")
        track_list.table_view.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        
        print("  Después de ordenar por título DESC:")
        for row in range(min(5, model.rowCount())):
            title = model.data(model.index(row, 0), Qt.ItemDataRole.DisplayRole)
            artist = model.data(model.index(row, 1), Qt.ItemDataRole.DisplayRole)
            print(f"    {row+1}. {title} - {artist}")
        
        print("\n🔄 PROBANDO ORDENAMIENTO POR BPM (Ascendente)...")
        track_list.table_view.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        
        print("  Después de ordenar por BPM ASC:")
        for row in range(min(5, model.rowCount())):
            title = model.data(model.index(row, 0), Qt.ItemDataRole.DisplayRole)
            bpm = model.data(model.index(row, 2), Qt.ItemDataRole.DisplayRole)
            print(f"    {row+1}. {title} ({bpm} BPM)")
        
        print("\n🔄 PROBANDO ORDENAMIENTO POR ARTISTA (Ascendente)...")
        track_list.table_view.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        
        print("  Después de ordenar por artista ASC:")
        for row in range(min(5, model.rowCount())):
            title = model.data(model.index(row, 0), Qt.ItemDataRole.DisplayRole)
            artist = model.data(model.index(row, 1), Qt.ItemDataRole.DisplayRole)
            print(f"    {row+1}. {artist} - {title}")
        
        print("\n✅ DEMOSTRACIÓN COMPLETADA")
        print("💡 Puedes hacer click en cualquier header para ordenar manualmente!")
        print("💡 Los indicadores de ordenamiento aparecen en los headers")
        
        # Dejar la aplicación corriendo para interacción manual
        print("\n🖱️  Aplicación lista para prueba manual - haz click en los headers!")
    
    # Ejecutar demo después de que se cargue la UI
    QTimer.singleShot(1000, run_demo)
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(demo_sorting())