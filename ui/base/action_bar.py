# ui/base/action_bar.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.theme import COLORS, FONTS

try:
    import os
    os.environ['QT_API'] = 'pyside6'
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False


class ActionBar(QWidget):
    """
    Barra de acciones minimalista para paneles con botones y status.
    """
    
    def __init__(self, align_right=True, compact=False, parent=None):
        super().__init__(parent)
        self.align_right = align_right
        self.compact = compact
        self.buttons = {}
        self.status_label = None
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """Configura la interfaz de la barra de acciones."""
        self.setProperty("class", "action_bar")
        
        height = 32 if self.compact else 40
        self.setFixedHeight(height)
        
        self.layout = QHBoxLayout(self)
        margin = 4 if self.compact else 8
        self.layout.setContentsMargins(margin, margin, margin, margin)
        self.layout.setSpacing(8)
        
        # Status label (opcional, a la izquierda)
        self.status_label = QLabel()
        self.status_label.setProperty("class", "status_text")
        self.layout.addWidget(self.status_label)
        
        # Spacer para alinear botones a la derecha
        if self.align_right:
            self.layout.addStretch()
            
    def add_button(self, name, text, icon=None, button_type="primary", 
                   enabled=True, tooltip=None):
        """
        Añade un botón a la barra de acciones.
        
        Args:
            name: Nombre interno del botón
            text: Texto del botón
            icon: Ícono del botón (qtawesome string o emoji)
            button_type: Tipo de botón ('primary', 'secondary', 'danger', 'success')
            enabled: Si el botón está habilitado
            tooltip: Tooltip del botón
        """
        button = QPushButton()
        button.setProperty("class", f"action_button_{button_type}")
        button.setEnabled(enabled)
        
        # Configurar texto e ícono
        if icon and not HAS_QTAWESOME:
            # Usar emoji si no hay qtawesome
            button.setText(f"{icon} {text}" if text else icon)
        elif icon and HAS_QTAWESOME:
            # Usar qtawesome
            color = self._get_icon_color(button_type)
            button.setIcon(qta.icon(icon, color=color))
            button.setText(text)
        else:
            button.setText(text)
            
        if tooltip:
            button.setToolTip(tooltip)
            
        # Tamaño del botón
        if self.compact:
            button.setFixedHeight(24)
        else:
            button.setFixedHeight(32)
            
        self.layout.addWidget(button)
        self.buttons[name] = button
        
        return button
        
    def add_separator(self):
        """Añade un separador visual."""
        separator = QLabel("|")
        separator.setProperty("class", "separator")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(separator)
        
    def set_status(self, text, status_type="normal"):
        """
        Actualiza el texto de status.
        
        Args:
            text: Texto a mostrar
            status_type: Tipo de status ('normal', 'success', 'warning', 'error')
        """
        if self.status_label:
            self.status_label.setText(text)
            self.status_label.setProperty("status_type", status_type)
            self.status_label.setStyleSheet(self._get_status_style(status_type))
            
    def get_button(self, name):
        """Obtiene referencia a un botón por nombre."""
        return self.buttons.get(name)
        
    def set_button_enabled(self, name, enabled):
        """Habilita/deshabilita un botón específico."""
        if name in self.buttons:
            self.buttons[name].setEnabled(enabled)
            
    def set_all_buttons_enabled(self, enabled):
        """Habilita/deshabilita todos los botones."""
        for button in self.buttons.values():
            button.setEnabled(enabled)
            
    def _get_icon_color(self, button_type):
        """Obtiene el color del ícono según el tipo de botón."""
        colors = {
            'primary': COLORS['text_primary'],
            'secondary': COLORS['text_secondary'],
            'danger': COLORS['error'],
            'success': COLORS['success']
        }
        return colors.get(button_type, COLORS['text_primary'])
        
    def _get_status_style(self, status_type):
        """Obtiene el estilo CSS para el status."""
        colors = {
            'normal': COLORS['text_secondary'],
            'success': COLORS['success'],
            'warning': COLORS['warning'],
            'error': COLORS['error']
        }
        color = colors.get(status_type, COLORS['text_secondary'])
        
        return f"""
        QLabel[class="status_text"] {{
            color: {color};
            font-family: {FONTS['main']};
            font-size: 10px;
        }}
        """
        
    def apply_styles(self):
        """Aplica estilos a la barra de acciones."""
        self.setStyleSheet(f"""
        QWidget[class="action_bar"] {{
            background: {COLORS['background_panel']};
            border: none;
            border-top: 1px solid {COLORS['border']};
        }}
        
        QLabel[class="status_text"] {{
            color: {COLORS['text_secondary']};
            font-family: {FONTS['main']};
            font-size: 10px;
        }}
        
        QLabel[class="separator"] {{
            color: {COLORS['border']};
            font-size: 12px;
            padding: 0px 4px;
        }}
        
        QPushButton[class="action_button_primary"] {{
            background: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 12px;
            font-family: {FONTS['main']};
            font-size: 11px;
            font-weight: bold;
        }}
        
        QPushButton[class="action_button_primary"]:hover {{
            background: {COLORS['primary_light']};
        }}
        
        QPushButton[class="action_button_primary"]:disabled {{
            background: {COLORS['background_tertiary']};
            color: {COLORS['text_muted']};
        }}
        
        QPushButton[class="action_button_secondary"] {{
            background: {COLORS['button_secondary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 4px 12px;
            font-family: {FONTS['main']};
            font-size: 11px;
        }}
        
        QPushButton[class="action_button_secondary"]:hover {{
            background: {COLORS['button_secondary_hover']};
            border-color: {COLORS['primary']};
        }}
        
        QPushButton[class="action_button_danger"] {{
            background: {COLORS['error']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 12px;
            font-family: {FONTS['main']};
            font-size: 11px;
            font-weight: bold;
        }}
        
        QPushButton[class="action_button_success"] {{
            background: {COLORS['success']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 12px;
            font-family: {FONTS['main']};
            font-size: 11px;
            font-weight: bold;
        }}
        """)