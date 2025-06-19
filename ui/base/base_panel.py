# ui/base/base_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.theme import COLORS, FONTS


class BasePanel(QWidget):
    """
    Panel minimalista base que proporciona un layout y estilo consistente
    para todos los paneles de la aplicación.
    """
    
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.content_layout = None
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """Configura la interfaz base del panel."""
        self.setProperty("class", "base_panel")
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # Título opcional
        if self.title:
            title_label = QLabel(self.title)
            title_label.setProperty("class", "panel_title")
            title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            main_layout.addWidget(title_label)
        
        # Layout de contenido donde los paneles hijos agregarán sus widgets
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        main_layout.addLayout(self.content_layout)
        
    def add_content(self, widget):
        """Añade un widget al área de contenido del panel."""
        if self.content_layout:
            self.content_layout.addWidget(widget)
            
    def add_stretch(self):
        """Añade un stretch al área de contenido."""
        if self.content_layout:
            self.content_layout.addStretch()
            
    def set_content_spacing(self, spacing):
        """Configura el espaciado del contenido."""
        if self.content_layout:
            self.content_layout.setSpacing(spacing)
            
    def set_content_margins(self, left, top, right, bottom):
        """Configura los márgenes del contenido."""
        if self.content_layout:
            self.content_layout.setContentsMargins(left, top, right, bottom)
            
    def apply_styles(self):
        """Aplica el estilo minimalista al panel."""
        self.setStyleSheet(f"""
        QWidget[class="base_panel"] {{
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            color: {COLORS['text_primary']};
        }}
        
        QLabel[class="panel_title"] {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['title']};
            font-size: 13px;
            font-weight: bold;
            padding: 0px 0px 8px 0px;
            border-bottom: 1px solid {COLORS['border']};
            margin-bottom: 8px;
        }}
        """)