# ui/base/minimalist_header.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
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


class MinimalistHeader(QWidget):
    """
    Encabezado minimalista para paneles con título e íconos opcionales.
    """
    
    # Señales para botones de acción
    closeRequested = Signal()
    minimizeRequested = Signal()
    refreshRequested = Signal()
    
    def __init__(self, title, icon=None, show_close=False, show_minimize=False, 
                 show_refresh=False, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.show_close = show_close
        self.show_minimize = show_minimize  
        self.show_refresh = show_refresh
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """Configura la interfaz del encabezado."""
        self.setProperty("class", "minimalist_header")
        self.setFixedHeight(32)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Ícono opcional
        if self.icon:
            icon_label = QLabel()
            if HAS_QTAWESOME and isinstance(self.icon, str):
                icon_label.setPixmap(qta.icon(self.icon, color=COLORS['text_primary']).pixmap(16, 16))
            else:
                icon_label.setText(self.icon if isinstance(self.icon, str) else "")
            icon_label.setFixedSize(16, 16)
            layout.addWidget(icon_label)
        
        # Título
        title_label = QLabel(self.title)
        title_label.setProperty("class", "header_title")
        layout.addWidget(title_label)
        
        # Spacer
        layout.addStretch()
        
        # Botones de acción
        if self.show_refresh:
            refresh_btn = QPushButton()
            refresh_btn.setProperty("class", "header_button")
            refresh_btn.setFixedSize(20, 20)
            if HAS_QTAWESOME:
                refresh_btn.setIcon(qta.icon("fa5s.sync-alt", color=COLORS['text_secondary']))
            else:
                refresh_btn.setText("↻")
            refresh_btn.clicked.connect(self.refreshRequested.emit)
            layout.addWidget(refresh_btn)
            
        if self.show_minimize:
            minimize_btn = QPushButton()
            minimize_btn.setProperty("class", "header_button")
            minimize_btn.setFixedSize(20, 20)
            if HAS_QTAWESOME:
                minimize_btn.setIcon(qta.icon("fa5s.minus", color=COLORS['text_secondary']))
            else:
                minimize_btn.setText("−")
            minimize_btn.clicked.connect(self.minimizeRequested.emit)
            layout.addWidget(minimize_btn)
            
        if self.show_close:
            close_btn = QPushButton()
            close_btn.setProperty("class", "header_button")
            close_btn.setFixedSize(20, 20)
            if HAS_QTAWESOME:
                close_btn.setIcon(qta.icon("fa5s.times", color=COLORS['text_secondary']))
            else:
                close_btn.setText("×")
            close_btn.clicked.connect(self.closeRequested.emit)
            layout.addWidget(close_btn)
            
    def set_title(self, title):
        """Actualiza el título del encabezado."""
        self.title = title
        # Encontrar y actualizar el label del título
        for child in self.findChildren(QLabel):
            if child.property("class") == "header_title":
                child.setText(title)
                break
                
    def apply_styles(self):
        """Aplica estilos al encabezado."""
        self.setStyleSheet(f"""
        QWidget[class="minimalist_header"] {{
            background: {COLORS['background_panel']};
            border: none;
            border-bottom: 1px solid {COLORS['border']};
        }}
        
        QLabel[class="header_title"] {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['title']};
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        QPushButton[class="header_button"] {{
            background: transparent;
            border: none;
            border-radius: 10px;
            color: {COLORS['text_secondary']};
        }}
        
        QPushButton[class="header_button"]:hover {{
            background: {COLORS['background_tertiary']};
            color: {COLORS['text_primary']};
        }}
        
        QPushButton[class="header_button"]:pressed {{
            background: {COLORS['primary']};
            color: white;
        }}
        """)