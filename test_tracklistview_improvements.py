#!/usr/bin/env python3
"""
Script para validar las mejoras del TrackListView:
- Ordenamiento por columnas funcional
- Tamaños de columnas optimizados
- Auto-ajuste inteligente
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from ui.main_window import MainWindow


class TrackListValidator:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.track_list = self.window.track_list_view
        
    def test_column_order_and_sizes(self):
        """Verifica el nuevo orden y tamaños de columnas."""
        print("🔍 VALIDANDO ORDEN Y TAMAÑOS DE COLUMNAS")
        
        col_mgr = self.track_list.column_manager
        visible_columns = col_mgr.get_visible_columns()
        
        # Verificar orden optimizado para DJs
        expected_order = ['title', 'artist', 'bpm', 'key', 'genre', 'album', 'duration']
        actual_order = [col.key for col in visible_columns]
        
        print(f"  Orden esperado: {expected_order}")
        print(f"  Orden actual:   {actual_order}")
        
        order_correct = actual_order == expected_order
        print(f"  ✅ Orden optimizado: {'CORRECTO' if order_correct else 'INCORRECTO'}")
        
        # Verificar tamaños balanceados
        print(f"  📏 Anchos de columnas:")
        for col in visible_columns:
            print(f"    {col.title}: {col.width}px (min: {col.min_width}, max: {col.max_width})")
        
        # Verificar que título no sea excesivamente grande
        title_col = next((col for col in visible_columns if col.key == 'title'), None)
        title_size_ok = title_col and title_col.width <= 250
        print(f"  ✅ Título razonable: {'SÍ' if title_size_ok else 'NO'} ({title_col.width if title_col else 'N/A'}px)")
        
        return order_correct and title_size_ok
    
    def test_sorting_functionality(self):
        """Verifica que el ordenamiento por columnas funcione."""
        print("\\n🔍 VALIDANDO FUNCIONALIDAD DE ORDENAMIENTO")
        
        table_view = self.track_list.table_view
        model = self.track_list.proxy_model
        
        # Verificar que sorting está habilitado
        sorting_enabled = table_view.isSortingEnabled()
        print(f"  ✅ Sorting habilitado: {'SÍ' if sorting_enabled else 'NO'}")
        
        if not sorting_enabled:
            return False
        
        # Obtener datos iniciales
        initial_data = []
        for row in range(min(5, model.rowCount())):
            title = model.data(model.index(row, 0), Qt.ItemDataRole.DisplayRole)
            initial_data.append(title)
        
        print(f"  📊 Datos iniciales (primeros 5): {initial_data}")
        
        # Probar ordenamiento por título (columna 0)
        print("  🔄 Probando ordenamiento por título...")
        table_view.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        
        # Obtener datos después del ordenamiento
        sorted_data = []
        for row in range(min(5, model.rowCount())):
            title = model.data(model.index(row, 0), Qt.ItemDataRole.DisplayRole)
            sorted_data.append(title)
        
        print(f"  📊 Datos ordenados desc: {sorted_data}")
        
        # Verificar que el orden cambió
        order_changed = initial_data != sorted_data
        print(f"  ✅ Orden cambió: {'SÍ' if order_changed else 'NO'}")
        
        # Probar ordenamiento por BPM (columna 2)
        print("  🔄 Probando ordenamiento por BPM...")
        table_view.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        
        bpm_data = []
        for row in range(min(3, model.rowCount())):
            bpm = model.data(model.index(row, 2), Qt.ItemDataRole.DisplayRole)
            bpm_data.append(bpm)
        
        print(f"  📊 BPM ordenados asc: {bpm_data}")
        
        return sorting_enabled and order_changed
    
    def test_auto_resize_functionality(self):
        """Verifica el auto-ajuste de columnas."""
        print("\\n🔍 VALIDANDO AUTO-AJUSTE DE COLUMNAS")
        
        # Obtener anchos actuales
        table_view = self.track_list.table_view
        current_widths = []
        
        for col in range(table_view.model().columnCount()):
            width = table_view.columnWidth(col)
            current_widths.append(width)
        
        print(f"  📏 Anchos actuales: {current_widths}")
        
        # Probar auto-ajuste manual
        self.track_list._auto_resize_columns()
        
        # Obtener anchos después del auto-ajuste
        new_widths = []
        for col in range(table_view.model().columnCount()):
            width = table_view.columnWidth(col)
            new_widths.append(width)
        
        print(f"  📏 Anchos después auto-ajuste: {new_widths}")
        
        # Verificar que las columnas tienen tamaños razonables
        total_width = sum(new_widths)
        viewport_width = table_view.viewport().width()
        
        print(f"  📐 Ancho total: {total_width}px, Viewport: {viewport_width}px")
        
        width_ratio = total_width / max(viewport_width, 1)
        reasonable_fit = 0.8 <= width_ratio <= 1.2
        
        print(f"  ✅ Ajuste razonable: {'SÍ' if reasonable_fit else 'NO'} (ratio: {width_ratio:.2f})")
        
        return reasonable_fit
    
    def test_header_functionality(self):
        """Verifica funcionalidad del header."""
        print("\\n🔍 VALIDANDO FUNCIONALIDAD DEL HEADER")
        
        header = self.track_list.header_view
        
        # Verificar que tiene column manager
        has_col_mgr = header.column_manager is not None
        print(f"  ✅ Column manager: {'SÍ' if has_col_mgr else 'NO'}")
        
        # Verificar que las secciones son móviles
        sections_movable = header.sectionsMovable()
        print(f"  ✅ Columnas movibles: {'SÍ' if sections_movable else 'NO'}")
        
        # Verificar menú contextual
        has_context_menu = header.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
        print(f"  ✅ Menú contextual: {'SÍ' if has_context_menu else 'NO'}")
        
        # Verificar última sección stretch
        stretch_last = header.stretchLastSection()
        print(f"  ✅ Última sección expandible: {'SÍ' if stretch_last else 'NO'}")
        
        return has_col_mgr and sections_movable and has_context_menu
    
    def run_validation(self):
        """Ejecuta todas las validaciones."""
        print("🧪 VALIDACIÓN DE MEJORAS DEL TRACKLISTVIEW")
        print("=" * 60)
        
        self.window.show()
        
        # Esperar a que se carguen los datos
        QTimer.singleShot(1500, self._run_tests)
        
        return self.app.exec()
    
    def _run_tests(self):
        """Ejecuta los tests después de cargar la UI."""
        results = []
        
        # Ejecutar todos los tests
        results.append(("Orden y tamaños de columnas", self.test_column_order_and_sizes()))
        results.append(("Funcionalidad de ordenamiento", self.test_sorting_functionality()))
        results.append(("Auto-ajuste de columnas", self.test_auto_resize_functionality()))
        results.append(("Funcionalidad del header", self.test_header_functionality()))
        
        # Resumen
        print("\\n" + "=" * 60)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results:
            symbol = "✅" if success else "❌"
            status = "EXITOSO" if success else "FALLIDO"
            print(f"{symbol} {test_name}: {status}")
            if success:
                passed += 1
        
        success_rate = (passed / total) * 100
        print(f"\\n🎯 Tasa de éxito: {success_rate:.1f}% ({passed}/{total})")
        
        if success_rate >= 80:
            print("🎉 MEJORAS IMPLEMENTADAS EXITOSAMENTE!")
            print("   - Ordenamiento funcional")
            print("   - Columnas balanceadas")
            print("   - Auto-ajuste inteligente")
        else:
            print("⚠️ ALGUNAS MEJORAS NECESITAN AJUSTES")
        
        # Cerrar aplicación
        QTimer.singleShot(3000, self.app.quit)


if __name__ == "__main__":
    validator = TrackListValidator()
    sys.exit(validator.run_validation())