# ui/theme.py

"""
Tema visual moderno y profesional para DjAlfin
Inspirado en aplicaciones DJ profesionales como Serato y rekordbox
"""

"""
Módulo para centralizar la paleta de colores y las fuentes de la aplicación.
"""

COLORS = {
    # ----- Paleta Base -----
    "background_dark": "#2B2B2B",  # Fondo principal muy oscuro
    "background": "#353535",       # Fondo de paneles y entradas de texto
    "background_light": "#4A4A4A", # Fondos ligeramente más claros
    "foreground": "#E0E0E0",       # Color de texto principal
    "foreground_dark": "#B0B0B0",  # Color de texto secundario o deshabilitado
    
    # ----- Colores de Acento -----
    "primary": "#4682B4",          # Azul acero: para elementos principales (selección, progreso)
    "primary_bright": "#FFA366",   # Naranja: para etiquetas, notificaciones y enfoque
    "secondary": "#606060",        # Gris medio: para botones secundarios y bordes
    
    # ----- Colores de Estado -----
    "success": "#5cb85c",          # Verde para operaciones exitosas
    "warning": "#f0ad4e",          # Amarillo para advertencias
    "error": "#d9534f",            # Rojo para errores
    
    # ----- Componentes Específicos -----
    "border": "#606060",
    "selection": "#5A5A5A",
    "text_placeholder": "#999999",
}

# Gradientes
GRADIENTS = {
    'primary': f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_dark']})",
    'background': f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLORS['background_main']}, stop:1 {COLORS['background_secondary']})",
    'panel': f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['background_panel']}, stop:1 {COLORS['background_secondary']})",
}

# Sombras
SHADOWS = {
    'light': "0px 2px 4px rgba(0, 0, 0, 0.3)",
    'medium': "0px 4px 8px rgba(0, 0, 0, 0.4)",
    'heavy': "0px 8px 16px rgba(0, 0, 0, 0.5)",
}

# Fuentes
FONTS = {
    "main": "Segoe UI, Arial, sans-serif",
    "main_size": "10pt",
    "title_size": "12pt",
    "section_header_size": "11px",
    'mono': '"Consolas", "Monaco", "Courier New", monospace',
}

def get_main_window_style():
    """Estilo principal de la ventana"""
    return f"""
    QMainWindow {{
        background: {GRADIENTS['background']};
        color: {COLORS['text_primary']};
        font-family: {FONTS['main']};
        font-size: 13px;
    }}
    
    QMainWindow::separator {{
        background: {COLORS['separator']};
        width: 2px;
        height: 2px;
    }}
    """

def get_table_style():
    """Estilo moderno para la tabla de pistas"""
    return f"""
    QTableView {{
        background-color: {COLORS['background_main']};
        alternate-background-color: {COLORS['table_row_even']};
        color: {COLORS['text_primary']};
        gridline-color: {COLORS['border']};
        selection-background-color: {COLORS['table_selected']};
        selection-color: {COLORS['text_primary']};
        font-family: {FONTS['main']};
        font-size: 12px;
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
    }}
    
    QTableView::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {COLORS['border']};
    }}
    
    QTableView::item:selected {{
        background: {GRADIENTS['primary']};
        color: {COLORS['text_primary']};
        font-weight: bold;
    }}
    
    QTableView::item:hover {{
        background-color: {COLORS['table_hover']};
    }}
    
    QHeaderView::section {{
        background: {GRADIENTS['panel']};
        color: {COLORS['text_primary']};
        padding: 12px 8px;
        border: none;
        border-right: 1px solid {COLORS['border']};
        border-bottom: 2px solid {COLORS['primary']};
        font-family: {FONTS['title']};
        font-size: 13px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    QHeaderView::section:hover {{
        background: {COLORS['background_tertiary']};
    }}
    
    QHeaderView::section:pressed {{
        background: {COLORS['primary_dark']};
    }}
    
    /* Scrollbars modernos */
    QScrollBar:vertical {{
        background: {COLORS['background_secondary']};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background: {GRADIENTS['primary']};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['primary_light']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background: {COLORS['background_secondary']};
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {GRADIENTS['primary']};
        border-radius: 6px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS['primary_light']};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    """

def get_panel_style():
    """Estilo para paneles laterales"""
    return f"""
    QWidget[class="panel"] {{
        background: {GRADIENTS['panel']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 16px;
    }}
    
    QLabel {{
        color: {COLORS['text_primary']};
        font-family: {FONTS['main']};
        font-size: 13px;
    }}
    
    QLabel[class="title"] {{
        color: {COLORS['text_primary']};
        font-family: {FONTS['title']};
        font-size: 16px;
        font-weight: bold;
        padding: 8px 0px;
        border-bottom: 2px solid {COLORS['primary']};
        margin-bottom: 12px;
    }}
    
    QLabel[class="subtitle"] {{
        color: {COLORS['text_secondary']};
        font-family: {FONTS['main']};
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 8px;
        margin-bottom: 4px;
    }}
    
    QLabel[class="value"] {{
        color: {COLORS['text_primary']};
        font-family: {FONTS['mono']};
        font-size: 14px;
        font-weight: bold;
        background: {COLORS['background_tertiary']};
        padding: 6px 12px;
        border-radius: 6px;
        border-left: 3px solid {COLORS['primary']};
    }}
    """

def get_button_style():
    """Estilo moderno para botones"""
    return f"""
    QPushButton {{
        background: {GRADIENTS['primary']};
        color: {COLORS['text_primary']};
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-family: {FONTS['title']};
        font-size: 13px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    QPushButton:hover {{
        background: {COLORS['button_hover']};
        color: {COLORS['text_primary']};
    }}
    
    QPushButton:pressed {{
        background: {COLORS['primary_dark']};
    }}
    
    QPushButton:disabled {{
        background: {COLORS['background_tertiary']};
        color: {COLORS['text_muted']};
    }}
    
    QPushButton[class="secondary"] {{
        background: {COLORS['button_secondary']};
    }}
    
    QPushButton[class="secondary"]:hover {{
        background: {COLORS['button_secondary_hover']};
    }}
    """

def get_slider_style():
    """Estilo para sliders (usado en el reproductor)"""
    return f"""
    QSlider::groove:horizontal {{
        background: {COLORS['background_input']};
        border: 1px solid {COLORS['border']};
        height: 6px;
        border-radius: 3px;
    }}
    
    QSlider::handle:horizontal {{
        background: {COLORS['slider_handle']};
        border: 2px solid {COLORS['text_primary']};
        width: 14px;
        height: 14px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    
    QSlider::sub-page:horizontal {{
        background: {GRADIENTS['primary']};
        border-radius: 3px;
    }}
    """

def get_input_style():
    """Estilo para campos de entrada de texto"""
    return f"""
    QLineEdit {{
        background-color: {COLORS['background_input']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 6px 12px;
        color: {COLORS['text_primary']};
        font-family: {FONTS['main']};
        font-size: 13px;
    }}
    
    QLineEdit:focus {{
        border: 1px solid {COLORS['border_focus']};
        background-color: {COLORS['background_main']};
    }}
    """

def get_groupbox_style():
    """Estilo para QGroupBox."""
    return f"""
    QGroupBox {{
        background-color: transparent;
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        margin-top: 10px;
        font-family: {FONTS['title']};
        font-size: 12px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 10px;
        left: 10px;
        background-color: {COLORS['background_secondary']};
        color: {COLORS['text_accent']};
    }}
    """

def get_radiobutton_style():
    """Estilo para QRadioButton."""
    return f"""
    QRadioButton {{
        color: {COLORS['text_secondary']};
        font-size: 12px;
        spacing: 10px;
    }}

    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
    }}

    QRadioButton::indicator:unchecked {{
        border: 2px solid {COLORS['border']};
        border-radius: 9px;
        background-color: {COLORS['background_input']};
    }}

    QRadioButton::indicator:checked {{
        border: 2px solid {COLORS['primary']};
        border-radius: 9px;
        background-color: {COLORS['primary']};
    }}
    """

def get_combobox_style():
    """Estilo para QComboBox."""
    return f"""
    QComboBox {{
        background-color: {COLORS['background_input']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 12px;
        color: {COLORS['text_primary']};
        font-family: {FONTS['main']};
        font-size: 13px;
    }}

    QComboBox:hover {{
        border: 1px solid {COLORS['primary']};
    }}

    QComboBox:focus {{
        border: 1px solid {COLORS['border_focus']};
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left-width: 1px;
        border-left-color: {COLORS['border']};
        border-left-style: solid;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }}

    QComboBox::down-arrow {{
        border-style: solid;
        border-width: 5px;
        border-color: {COLORS['text_muted']} transparent transparent transparent;
        margin: auto;
    }}
    QComboBox::down-arrow:on {{
        border-color: {COLORS['text_primary']} transparent transparent transparent;
        margin-top: 3px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['background_panel']};
        border: 1px solid {COLORS['border']};
        selection-background-color: {COLORS['primary']};
        color: {COLORS['text_secondary']};
        padding: 4px;
    }}
    """

def get_scrollbar_style():
    """Estilo para QScrollBar."""
    return f"""
    QScrollBar:vertical {{
        border: none;
        background: {COLORS['background_secondary']};
        width: 12px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['primary']};
        min-height: 20px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['primary_bright']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        border: none;
        background: {COLORS['background_secondary']};
        height: 12px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLORS['primary']};
        min-width: 20px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS['primary_bright']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    """

def get_complete_style():
    """Combina todos los estilos en una sola hoja."""
    return (
        get_main_window_style() +
        get_table_style() +
        get_panel_style() +
        get_button_style() +
        get_slider_style() +
        get_input_style() +
        get_groupbox_style() +
        get_radiobutton_style() +
        get_combobox_style() +
        get_scrollbar_style()
    )