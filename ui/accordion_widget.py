# ui/accordion_widget.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QEasingCurve, QPropertyAnimation, QRect, QSize
from PySide6.QtGui import QFont

try:
    import os
    os.environ['QT_API'] = 'pyside6'
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False

from ui.theme import COLORS, FONTS


class AccordionSection(QFrame):
    """Una sección individual del acordeón que puede expandirse/contraerse."""
    
    toggled = Signal(bool)  # True cuando se expande, False cuando se contrae
    
    def __init__(self, title: str, content_widget: QWidget, expanded: bool = False, parent=None):
        super().__init__(parent)
        self.content_widget = content_widget
        self.is_expanded = expanded
        
        self.setup_ui(title)
        self.apply_styles()
        
        # Configurar estado inicial
        if not expanded:
            self.content_widget.hide()
        
    def setup_ui(self, title: str):
        """Configura la interfaz de la sección."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header clickeable
        self.header = QPushButton()
        self.header.setObjectName("accordionHeader")
        self.header.clicked.connect(self.toggle)
        
        # Layout del header
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        # Ícono de expansión
        if HAS_QTAWESOME:
            self.expand_icon = QLabel()
            self.expand_icon.setPixmap(qta.icon("fa5s.chevron-right", color=COLORS['text_primary']).pixmap(12, 12))
        else:
            self.expand_icon = QLabel("▶")
        self.expand_icon.setFixedSize(16, 16)
        
        # Título
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont(FONTS['title'], 11, QFont.Weight.Bold))
        
        header_layout.addWidget(self.expand_icon)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Contenedor para el contenido
        self.content_container = QFrame()
        self.content_container.setObjectName("accordionContent")
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.addWidget(self.content_widget)
        
        main_layout.addWidget(self.header)
        main_layout.addWidget(self.content_container)
        
        # Actualizar ícono inicial
        self._update_icon()
        
    def toggle(self):
        """Alternar entre expandido y contraído."""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content_container.show()
        else:
            self.content_container.hide()
            
        self._update_icon()
        self.toggled.emit(self.is_expanded)
        
    def _update_icon(self):
        """Actualiza el ícono de expansión."""
        if HAS_QTAWESOME:
            if self.is_expanded:
                self.expand_icon.setPixmap(qta.icon("fa5s.chevron-down", color=COLORS['text_primary']).pixmap(12, 12))
            else:
                self.expand_icon.setPixmap(qta.icon("fa5s.chevron-right", color=COLORS['text_primary']).pixmap(12, 12))
        else:
            self.expand_icon.setText("▼" if self.is_expanded else "▶")
            
    def expand(self):
        """Expandir la sección."""
        if not self.is_expanded:
            self.toggle()
            
    def collapse(self):
        """Contraer la sección."""
        if self.is_expanded:
            self.toggle()
            
    def apply_styles(self):
        """Aplica estilos a la sección."""
        self.setStyleSheet(f"""
        AccordionSection {{
            background: {COLORS['background_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            margin: 2px 0;
        }}
        
        QPushButton#accordionHeader {{
            background: {COLORS['background_panel']};
            border: none;
            border-radius: 6px 6px 0 0;
            text-align: left;
            padding: 0;
        }}
        
        QPushButton#accordionHeader:hover {{
            background: {COLORS['background_tertiary']};
        }}
        
        QPushButton#accordionHeader:pressed {{
            background: {COLORS['primary']};
        }}
        
        QFrame#accordionContent {{
            background: {COLORS['background']};
            border: none;
            border-radius: 0 0 6px 6px;
        }}
        
        QLabel {{
            color: {COLORS['text_primary']};
        }}
        """)


class AccordionWidget(QScrollArea):
    """Widget acordeón que contiene múltiples secciones expandibles."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sections = []
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """Configura la interfaz del acordeón."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget contenedor
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(2)
        
        # Spacer para empujar contenido hacia arriba
        self.content_layout.addStretch()
        
        self.setWidget(self.content_widget)
        
    def add_section(self, title: str, content_widget: QWidget, expanded: bool = False):
        """Añade una nueva sección al acordeón."""
        section = AccordionSection(title, content_widget, expanded)
        section.toggled.connect(self._on_section_toggled)
        
        # Insertar antes del spacer
        self.content_layout.insertWidget(len(self.sections), section)
        self.sections.append(section)
        
        return section
        
    def _on_section_toggled(self, expanded: bool):
        """Maneja cuando una sección se expande/contrae."""
        # Opcional: implementar lógica para cerrar otras secciones
        # si solo queremos una abierta a la vez
        pass
        
    def expand_all(self):
        """Expande todas las secciones."""
        for section in self.sections:
            section.expand()
            
    def collapse_all(self):
        """Contrae todas las secciones."""
        for section in self.sections:
            section.collapse()
            
    def expand_section(self, index: int):
        """Expande una sección específica por índice."""
        if 0 <= index < len(self.sections):
            self.sections[index].expand()
            
    def collapse_section(self, index: int):
        """Contrae una sección específica por índice."""
        if 0 <= index < len(self.sections):
            self.sections[index].collapse()
            
    def apply_styles(self):
        """Aplica estilos al acordeón."""
        self.setStyleSheet(f"""
        AccordionWidget {{
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
        }}
        
        QScrollBar:vertical {{
            background: {COLORS['background_secondary']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {COLORS['border_light']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {COLORS['primary']};
        }}
        """)