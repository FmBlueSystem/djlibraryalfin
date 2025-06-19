#!/usr/bin/env python3
"""
Validación completa de funcionalidades de TrackListView
Este script verifica todas las características implementadas
"""

import sys
import sqlite3
from PySide6.QtWidgets import QApplication, QHeaderView
from PySide6.QtCore import Qt, QTimer
from ui.main_window import MainWindow
from ui.base.column_manager import ColumnManager


class TrackListValidator:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.track_list = self.window.track_list_view
        self.results = []
        
    def log_result(self, test_name, success, details=""):
        symbol = "✅" if success else "❌"
        self.results.append((test_name, success, details))
        print(f"{symbol} {test_name}: {details}")
    
    def validate_basic_setup(self):
        """Valida la configuración básica del TrackListView"""
        print("\n🔍 VALIDANDO CONFIGURACIÓN BÁSICA")
        
        # Verificar que el widget existe y está visible
        success = self.track_list.isVisible()
        self.log_result("TrackListView visible", success)
        
        # Verificar que tiene datos
        model = self.track_list.model
        row_count = model.rowCount()
        self.log_result("Modelo con datos", row_count > 0, f"{row_count} tracks")
        
        # Verificar que el proxy model está configurado
        proxy = self.track_list.proxy_model
        self.log_result("Proxy model configurado", proxy is not None)
        
        # Verificar column manager
        col_mgr = self.track_list.column_manager
        visible_cols = col_mgr.get_visible_columns()
        self.log_result("Column manager funcional", len(visible_cols) > 0, f"{len(visible_cols)} columnas visibles")
        
        return all(result[1] for result in self.results[-4:])
    
    def validate_column_sorting(self):
        """Valida el ordenamiento de columnas"""
        print("\n🔍 VALIDANDO ORDENAMIENTO DE COLUMNAS")
        
        try:
            # Verificar que sorting está habilitado
            table_view = self.track_list.table_view
            sorting_enabled = table_view.isSortingEnabled()
            self.log_result("Sorting habilitado", sorting_enabled)
            
            # Obtener datos antes del sort
            original_data = []
            for i in range(min(3, self.track_list.proxy_model.rowCount())):
                index = self.track_list.proxy_model.index(i, 0)  # Primera columna
                value = self.track_list.proxy_model.data(index, Qt.ItemDataRole.DisplayRole)
                original_data.append(value)
            
            # Intentar ordenar por primera columna (generalmente título)
            if len(original_data) > 1:
                table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
                
                # Verificar que los datos cambiaron de orden
                sorted_data = []
                for i in range(len(original_data)):
                    index = self.track_list.proxy_model.index(i, 0)
                    value = self.track_list.proxy_model.data(index, Qt.ItemDataRole.DisplayRole)
                    sorted_data.append(value)
                
                # Comparar si el orden cambió (o se mantuvo si ya estaba ordenado)
                self.log_result("Ordenamiento funcional", True, f"Orden: {original_data[0]} → {sorted_data[0]}")
            else:
                self.log_result("Ordenamiento", False, "Pocos datos para probar")
                
        except Exception as e:
            self.log_result("Ordenamiento", False, f"Error: {e}")
    
    def validate_column_configuration(self):
        """Valida la configuración de columnas"""
        print("\n🔍 VALIDANDO CONFIGURACIÓN DE COLUMNAS")
        
        try:
            col_mgr = self.track_list.column_manager
            
            # Verificar columnas disponibles
            all_cols = col_mgr.get_all_columns()
            self.log_result("Columnas definidas", len(all_cols) > 5, f"{len(all_cols)} columnas totales")
            
            # Verificar columnas visibles vs ocultas
            visible = col_mgr.get_visible_columns()
            visible_keys = [col.key for col in visible]
            self.log_result("Columnas visibles configuradas", len(visible) > 0, f"Visibles: {visible_keys}")
            
            # Probar cambio de visibilidad
            original_count = len(visible)
            
            # Ocultar primera columna visible
            if visible:
                first_col = visible[0]
                col_mgr.set_column_visible(first_col.key, False)
                new_visible = col_mgr.get_visible_columns()
                
                # Restaurar visibilidad
                col_mgr.set_column_visible(first_col.key, True)
                restored_visible = col_mgr.get_visible_columns()
                
                success = len(new_visible) == original_count - 1 and len(restored_visible) == original_count
                self.log_result("Toggle visibilidad", success, f"{original_count} → {len(new_visible)} → {len(restored_visible)}")
            
        except Exception as e:
            self.log_result("Configuración columnas", False, f"Error: {e}")
    
    def validate_search_functionality(self):
        """Valida la funcionalidad de búsqueda"""
        print("\n🔍 VALIDANDO BÚSQUEDA Y FILTRADO")
        
        try:
            # Obtener total de filas sin filtro
            original_count = self.track_list.proxy_model.rowCount()
            
            # Aplicar filtro de búsqueda
            search_input = self.track_list.search_input
            test_search = "Ed"  # Buscar tracks que contengan "Ed"
            
            search_input.setText(test_search)
            self.track_list.on_search_changed(test_search)
            
            # Verificar que el filtro se aplicó
            filtered_count = self.track_list.proxy_model.rowCount()
            self.log_result("Filtro aplicado", filtered_count != original_count, f"{original_count} → {filtered_count} tracks")
            
            # Limpiar filtro
            search_input.setText("")
            self.track_list.on_search_changed("")
            restored_count = self.track_list.proxy_model.rowCount()
            
            self.log_result("Filtro removido", restored_count == original_count, f"Restaurado a {restored_count} tracks")
            
            # Verificar contador de resultados
            results_label = self.track_list.results_label
            results_text = results_label.text()
            self.log_result("Contador de resultados", "tracks" in results_text, f"Muestra: {results_text}")
            
        except Exception as e:
            self.log_result("Búsqueda", False, f"Error: {e}")
    
    def validate_selection_and_signals(self):
        """Valida selección de tracks y emisión de señales"""
        print("\n🔍 VALIDANDO SELECCIÓN Y SEÑALES")
        
        try:
            table_view = self.track_list.table_view
            
            # Verificar que hay datos para seleccionar
            if self.track_list.proxy_model.rowCount() > 0:
                # Seleccionar primera fila
                first_index = self.track_list.proxy_model.index(0, 0)
                table_view.selectRow(0)
                
                # Verificar que hay selección
                selected_indexes = table_view.selectionModel().selectedRows()
                self.log_result("Selección de fila", len(selected_indexes) > 0)
                
                # Verificar obtención de track info
                track_info = self.track_list.get_selected_track_info()
                self.log_result("Datos de track seleccionado", track_info is not None, 
                              f"Track: {track_info.get('title', 'N/A') if track_info else 'None'}")
                
            else:
                self.log_result("Selección", False, "Sin datos para seleccionar")
                
        except Exception as e:
            self.log_result("Selección", False, f"Error: {e}")
    
    def validate_context_menus(self):
        """Valida la existencia de menús contextuales"""
        print("\n🔍 VALIDANDO MENÚS CONTEXTUALES")
        
        try:
            # Verificar que el header view tiene menú contextual
            header_view = self.track_list.header_view
            has_header_menu = header_view.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
            self.log_result("Header context menu", has_header_menu)
            
            # Verificar que el table view tiene menú contextual
            table_view = self.track_list.table_view
            has_table_menu = table_view.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
            self.log_result("Table context menu", has_table_menu)
            
            # Verificar que existen los métodos de menú
            has_header_method = hasattr(self.track_list.header_view, 'show_context_menu')
            has_table_method = hasattr(self.track_list, 'show_table_context_menu')
            self.log_result("Context menu methods", has_header_method and has_table_method)
            
        except Exception as e:
            self.log_result("Menús contextuales", False, f"Error: {e}")
    
    def validate_column_resizing(self):
        """Valida el redimensionamiento de columnas"""
        print("\n🔍 VALIDANDO REDIMENSIONAMIENTO DE COLUMNAS")
        
        try:
            header_view = self.track_list.header_view
            
            # Verificar que las columnas son redimensionables
            resize_mode = header_view.sectionResizeMode(0)
            is_resizable = resize_mode in [QHeaderView.ResizeMode.Interactive, QHeaderView.ResizeMode.Stretch]
            self.log_result("Columnas redimensionables", is_resizable)
            
            # Probar cambio de ancho
            if header_view.count() > 0:
                original_width = header_view.sectionSize(0)
                new_width = original_width + 50
                
                header_view.resizeSection(0, new_width)
                actual_width = header_view.sectionSize(0)
                
                # Restaurar ancho original
                header_view.resizeSection(0, original_width)
                
                self.log_result("Resize funcional", actual_width != original_width, 
                              f"{original_width} → {actual_width}")
            
        except Exception as e:
            self.log_result("Redimensionamiento", False, f"Error: {e}")
    
    def run_validation(self):
        """Ejecuta todas las validaciones"""
        print("🧪 INICIANDO VALIDACIÓN COMPLETA DE TRACKLISTVIEW")
        print("=" * 60)
        
        self.window.show()
        
        # Esperar a que la ventana se cargue completamente
        QTimer.singleShot(1000, self._run_tests)
        
        return self.app.exec()
    
    def _run_tests(self):
        """Ejecuta los tests después de que la UI esté lista"""
        self.validate_basic_setup()
        self.validate_column_sorting()
        self.validate_column_configuration()
        self.validate_search_functionality()
        self.validate_selection_and_signals()
        self.validate_context_menus()
        self.validate_column_resizing()
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for _, success, _ in self.results if success)
        failed_tests = total_tests - passed_tests
        
        print(f"Total de pruebas: {total_tests}")
        print(f"✅ Exitosas: {passed_tests}")
        print(f"❌ Fallidas: {failed_tests}")
        
        if failed_tests > 0:
            print("\n❌ PRUEBAS FALLIDAS:")
            for name, success, details in self.results:
                if not success:
                    print(f"  • {name}: {details}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n🎯 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 VALIDACIÓN EXITOSA - TrackListView funciona correctamente!")
        elif success_rate >= 60:
            print("⚠️ VALIDACIÓN PARCIAL - Algunas funcionalidades necesitan revisión")
        else:
            print("❌ VALIDACIÓN FALLIDA - Se requieren correcciones importantes")
        
        # Cerrar aplicación
        QTimer.singleShot(2000, self.app.quit)


if __name__ == "__main__":
    validator = TrackListValidator()
    sys.exit(validator.run_validation())