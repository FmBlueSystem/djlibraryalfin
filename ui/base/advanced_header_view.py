# ui/base/advanced_header_view.py

from PySide6.QtWidgets import (QHeaderView, QMenu, QDialog, QVBoxLayout, 
                               QCheckBox, QPushButton, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor, QPainter, QPen, QAction
from typing import List


class ColumnConfigDialog(QDialog):
    """Diálogo para configurar visibilidad de columnas."""
    
    def __init__(self, column_manager, parent=None):
        super().__init__(parent)
        self.column_manager = column_manager
        self.setWindowTitle("Configurar Columnas")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Selecciona las columnas a mostrar:")
        layout.addWidget(title)
        
        # Checkboxes para cada columna
        self.checkboxes = {}
        all_columns = self.column_manager.get_all_columns()
        
        for key, col in all_columns.items():
            if key != 'id':  # No mostrar ID en configuración
                checkbox = QCheckBox(col.title)
                checkbox.setChecked(col.visible)
                self.checkboxes[key] = checkbox
                layout.addWidget(checkbox)
        
        # Botones
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Restaurar Defecto")
        reset_btn.clicked.connect(self.reset_to_defaults)
        
        ok_btn = QPushButton("Aceptar")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def reset_to_defaults(self):
        """Restaura checkboxes a valores por defecto."""
        self.column_manager.reset_to_defaults()
        all_columns = self.column_manager.get_all_columns()
        for key, checkbox in self.checkboxes.items():
            if key in all_columns:
                checkbox.setChecked(all_columns[key].visible)
    
    def accept(self):
        """Aplica los cambios y cierra el diálogo."""
        for key, checkbox in self.checkboxes.items():
            self.column_manager.set_column_visible(key, checkbox.isChecked())
        super().accept()


class AdvancedHeaderView(QHeaderView):
    """HeaderView mejorado con soporte para reordenamiento y menús contextuales."""
    
    # Señales personalizadas
    columnAutoSizeRequested = Signal(int)
    columnConfigRequested = Signal()
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.column_manager = None
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Configurar drag & drop para reordenamiento
        self.setSectionsMovable(True)
        self.setDragDropMode(QHeaderView.DragDropMode.InternalMove)
        
        # Configurar resize
        self.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setStretchLastSection(False)
        
        # Conectar señales
        self.sectionMoved.connect(self._on_section_moved)
        self.sectionResized.connect(self._on_section_resized)
    
    def set_column_manager(self, column_manager):
        """Establece el gestor de columnas."""
        self.column_manager = column_manager
        if self.column_manager:
            self.column_manager.columnsChanged.connect(self.update_from_manager)
            self.update_from_manager()
    
    def update_from_manager(self):
        """Actualiza el header basado en la configuración del gestor."""
        if not self.column_manager:
            return
        
        visible_columns = self.column_manager.get_visible_columns()
        
        # Configurar anchos y modos de resize
        for i, col in enumerate(visible_columns):
            self.resizeSection(i, col.width)
            
            # Configurar modo de resize según si es redimensionable
            if col.resizable:
                # Usar Interactive para todas las columnas redimensionables
                # Esto permite control manual mientras mantiene funcionalidad
                self.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            else:
                self.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        # Configurar la última columna visible para que use el espacio restante
        if visible_columns:
            last_index = len(visible_columns) - 1
            last_col = visible_columns[last_index]
            if last_col.resizable:
                self.setStretchLastSection(True)
    
    def _on_section_moved(self, logical_index, old_visual_index, new_visual_index):
        """Maneja el movimiento de secciones."""
        if self.column_manager:
            # Obtener el orden actual de las columnas visibles
            visible_keys = self.column_manager.get_column_keys()
            if old_visual_index < len(visible_keys) and new_visual_index < len(visible_keys):
                # Mover en la lista
                key = visible_keys.pop(old_visual_index)
                visible_keys.insert(new_visual_index, key)
                
                # Reconstruir orden completo incluyendo columnas ocultas
                all_order = self.column_manager.get_column_order()
                visible_set = set(visible_keys)
                hidden_keys = [k for k in all_order if k not in visible_set]
                
                # Insertar columnas ocultas en sus posiciones aproximadas
                new_order = []
                visible_iter = iter(visible_keys)
                
                for key in all_order:
                    if key in visible_set:
                        try:
                            new_order.append(next(visible_iter))
                        except StopIteration:
                            break
                    else:
                        new_order.append(key)
                
                self.column_manager.set_column_order(new_order)
    
    def _on_section_resized(self, logical_index, old_size, new_size):
        """Maneja el redimensionamiento de secciones."""
        if self.column_manager:
            visible_columns = self.column_manager.get_visible_columns()
            if logical_index < len(visible_columns):
                col = visible_columns[logical_index]
                self.column_manager.set_column_width(col.key, new_size)
    
    def show_context_menu(self, position: QPoint):
        """Muestra el menú contextual."""
        if not self.column_manager:
            return
        
        menu = QMenu(self)
        
        # Obtener sección bajo el cursor
        logical_index = self.logicalIndexAt(position)
        
        if logical_index >= 0:
            visible_columns = self.column_manager.get_visible_columns()
            if logical_index < len(visible_columns):
                col = visible_columns[logical_index]
                
                # Opciones específicas de la columna
                menu.addSection(f"Columna: {col.title}")
                
                if col.resizable:
                    auto_size_action = QAction("Auto-ajustar", self)
                    auto_size_action.triggered.connect(
                        lambda: self.columnAutoSizeRequested.emit(logical_index)
                    )
                    menu.addAction(auto_size_action)
                
                hide_action = QAction(f"Ocultar '{col.title}'", self)
                hide_action.triggered.connect(
                    lambda: self.column_manager.set_column_visible(col.key, False)
                )
                menu.addAction(hide_action)
                
                menu.addSeparator()
        
        # Opciones generales
        config_action = QAction("Configurar Columnas...", self)
        config_action.triggered.connect(self.show_column_config)
        menu.addAction(config_action)
        
        reset_action = QAction("Restaurar Configuración", self)
        reset_action.triggered.connect(self.column_manager.reset_to_defaults)
        menu.addAction(reset_action)
        
        menu.addSeparator()
        
        # Opciones de auto-tamaño
        auto_size_all_action = QAction("Auto-ajustar Todas", self)
        auto_size_all_action.triggered.connect(self.auto_size_all_columns)
        menu.addAction(auto_size_all_action)
        
        # Mostrar menú
        menu.exec(self.mapToGlobal(position))
    
    def show_column_config(self):
        """Muestra el diálogo de configuración de columnas."""
        if self.column_manager:
            dialog = ColumnConfigDialog(self.column_manager, self)
            dialog.exec()
    
    def auto_size_all_columns(self):
        """Auto-ajusta todas las columnas redimensionables."""
        if not self.column_manager:
            return
        
        visible_columns = self.column_manager.get_visible_columns()
        for i, col in enumerate(visible_columns):
            if col.resizable and col.key != 'title':  # No auto-size la columna título
                self.columnAutoSizeRequested.emit(i)
    
    def paintSection(self, painter: QPainter, rect, logical_index):
        """Personaliza el pintado de las secciones del header."""
        super().paintSection(painter, rect, logical_index)
        
        # Agregar indicadores de ordenamiento más visibles si es necesario
        if self.isSortIndicatorShown() and logical_index == self.sortIndicatorSection():
            # Aquí se puede personalizar el indicador de ordenamiento
            pass
    
    def mousePressEvent(self, event):
        """Maneja clics en el header."""
        super().mousePressEvent(event)
        
        # Aquí se puede agregar lógica adicional para clics
        if event.button() == Qt.MouseButton.LeftButton:
            logical_index = self.logicalIndexAt(event.position().toPoint())
            if logical_index >= 0:
                # Lógica adicional para clics en columnas
                pass