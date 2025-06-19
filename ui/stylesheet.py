"""
Módulo para generar la hoja de estilos QSS global de la aplicación.
"""
from .theme import COLORS, FONTS

def get_stylesheet():
    """
    Genera y devuelve la hoja de estilos QSS completa para la aplicación.
    """
    return f"""
        /* --- Estilos Globales --- */
        QWidget {{
            background-color: {COLORS['background_dark']};
            color: {COLORS['foreground']};
            font-family: {FONTS['main']};
            font-size: {FONTS['main_size']};
            border: none;
        }}

        QMainWindow, QDialog {{
            background-color: {COLORS['background_dark']};
        }}

        /* --- Paneles y Áreas Principales --- */
        QFrame, QGroupBox {{
            background-color: {COLORS['background']};
            border-radius: 4px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
            background-color: {COLORS['background_light']};
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-weight: bold;
            color: {COLORS['primary_bright']};
        }}
        
        /* --- Botones --- */
        QPushButton {{
            background-color: {COLORS['secondary']};
            color: {COLORS['foreground']};
            padding: 8px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLORS['background_light']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['primary']};
        }}
        QPushButton:disabled {{
            background-color: #555;
            color: {COLORS['foreground_dark']};
        }}

        /* --- Entradas de Texto --- */
        QLineEdit, QTextEdit, QSpinBox {{
            background-color: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            padding: 5px;
            border-radius: 4px;
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {{
            border: 1px solid {COLORS['primary_bright']};
        }}

        /* --- Listas y Tablas --- */
        QListView, QTableView, QTreeView {{
            background-color: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            alternate-background-color: {COLORS['background_light']};
        }}
        QTableView::item, QListView::item, QTreeView::item {{
            padding: 5px;
        }}
        QTableView::item:selected, QListView::item:selected, QTreeView::item:selected {{
            background-color: {COLORS['primary']};
            color: white;
        }}
        QHeaderView::section {{
            background-color: {COLORS['secondary']};
            padding: 5px;
            border: 1px solid {COLORS['background_dark']};
            font-weight: bold;
            color: {COLORS['primary_bright']};
        }}

        /* --- Sliders --- */
        QSlider::groove:horizontal {{
            border: 1px solid {COLORS['border']};
            height: 4px;
            background: {COLORS['background_dark']};
            margin: 2px 0;
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {COLORS['primary_bright']};
            border: 1px solid {COLORS['primary_bright']};
            width: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }}
        QSlider::sub-page:horizontal {{
            background: {COLORS['primary']};
        }}

        /* --- Barras de Scroll --- */
        QScrollBar:vertical, QScrollBar:horizontal {{
            border: none;
            background: {COLORS['background']};
            width: 10px;
            height: 10px;
            margin: 0px;
        }}
        QScrollBar::handle {{
            background: {COLORS['secondary']};
            min-height: 20px;
            min-width: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:hover {{
            background: {COLORS['background_light']};
        }}

        /* --- Labels Específicos --- */
        QLabel#SectionHeader {{
            color: {COLORS['primary_bright']};
            font-size: {FONTS['section_header_size']};
            font-weight: bold;
            background-color: transparent;
        }}

        QLabel#MetadataValue {{
            font-weight: bold;
            color: white;
            background-color: transparent;
        }}
    """ 