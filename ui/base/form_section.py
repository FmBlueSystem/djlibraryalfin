# ui/base/form_section.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.theme import COLORS, FONTS


class FormSection(QWidget):
    """
    Sección de formulario minimalista que agrupa campos relacionados.
    """
    
    dataChanged = Signal(dict)
    
    def __init__(self, title=None, compact=False, parent=None):
        super().__init__(parent)
        self.title = title
        self.compact = compact
        self.fields = {}
        self.grid_layout = None
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """Configura la interfaz de la sección."""
        self.setProperty("class", "form_section")
        
        main_layout = QVBoxLayout(self)
        spacing = 4 if self.compact else 8
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(spacing)
        
        # Título opcional
        if self.title:
            title_label = QLabel(self.title)
            title_label.setProperty("class", "section_title")
            main_layout.addWidget(title_label)
        
        # Grid layout para los campos
        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(spacing)
        self.grid_layout.setColumnStretch(1, 1)  # La columna de inputs se expande
        
        main_layout.addLayout(self.grid_layout)
        
    def add_field(self, label_text, field_name, field_type="text", placeholder="", 
                  width=None, row=None):
        """
        Añade un campo al formulario.
        
        Args:
            label_text: Texto de la etiqueta
            field_name: Nombre interno del campo
            field_type: Tipo de campo ('text', 'number', 'readonly')
            placeholder: Texto placeholder
            width: Ancho específico del campo
            row: Fila específica (si None, se auto-asigna)
        """
        if row is None:
            row = self.grid_layout.rowCount()
            
        # Etiqueta
        label = QLabel(label_text)
        label.setProperty("class", "field_label")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Campo de entrada
        field = QLineEdit()
        field.setProperty("class", "form_field")
        field.setPlaceholderText(placeholder)
        
        if field_type == "readonly":
            field.setReadOnly(True)
            field.setProperty("class", "form_field_readonly")
        elif field_type == "number":
            field.setProperty("class", "form_field_numeric")
            
        if width:
            field.setFixedWidth(width)
            
        # Conectar señal de cambio
        field.textChanged.connect(lambda: self._emit_data_changed())
        
        # Añadir al grid
        self.grid_layout.addWidget(label, row, 0)
        self.grid_layout.addWidget(field, row, 1)
        
        # Guardar referencia
        self.fields[field_name] = field
        
        return field
        
    def add_field_pair(self, label1, field1, label2, field2, row=None):
        """Añade dos campos en la misma fila."""
        if row is None:
            row = self.grid_layout.rowCount()
            
        # Layout horizontal para los dos campos
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(12)
        
        # Primer campo
        field1_widget = self.add_field(label1, field1, row=row)
        field2_widget = self.add_field(label2, field2, row=row)
        
        return field1_widget, field2_widget
        
    def set_field_value(self, field_name, value):
        """Establece el valor de un campo."""
        if field_name in self.fields:
            self.fields[field_name].setText(str(value) if value is not None else "")
            
    def get_field_value(self, field_name):
        """Obtiene el valor de un campo."""
        if field_name in self.fields:
            return self.fields[field_name].text()
        return ""
        
    def get_all_values(self):
        """Obtiene todos los valores del formulario."""
        return {name: field.text() for name, field in self.fields.items()}
        
    def clear_all(self):
        """Limpia todos los campos."""
        for field in self.fields.values():
            field.clear()
            
    def set_enabled(self, enabled):
        """Habilita/deshabilita todos los campos."""
        for field in self.fields.values():
            field.setEnabled(enabled)
            
    def _emit_data_changed(self):
        """Emite la señal de cambio de datos."""
        self.dataChanged.emit(self.get_all_values())
        
    def apply_styles(self):
        """Aplica estilos a la sección."""
        self.setStyleSheet(f"""
        QWidget[class="form_section"] {{
            background: transparent;
        }}
        
        QLabel[class="section_title"] {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['title']};
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 4px 0px;
            margin-bottom: 4px;
        }}
        
        QLabel[class="field_label"] {{
            color: {COLORS['text_secondary']};
            font-family: {FONTS['main']};
            font-size: 11px;
            min-width: 60px;
            max-width: 80px;
        }}
        
        QLineEdit[class="form_field"] {{
            background: {COLORS['background_input']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 4px 8px;
            color: {COLORS['text_primary']};
            font-family: {FONTS['main']};
            font-size: 11px;
            min-height: 20px;
        }}
        
        QLineEdit[class="form_field"]:focus {{
            border-color: {COLORS['primary']};
            background: {COLORS['background']};
        }}
        
        QLineEdit[class="form_field_readonly"] {{
            background: {COLORS['background_secondary']};
            color: {COLORS['text_muted']};
            border-color: {COLORS['border_light']};
        }}
        
        QLineEdit[class="form_field_numeric"] {{
            text-align: right;
        }}
        """)