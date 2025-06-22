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
    "background_main": "#2B2B2B",  # Alias para background_dark
    "background_secondary": "#353535",  # Alias para background
    "background_tertiary": "#4A4A4A",   # Alias for background_light
    "background_panel": "#3A3A3A", # Panel background
    "background_input": "#404040", # Input background
    "foreground": "#E0E0E0",       # Color de texto principal
    "foreground_dark": "#B0B0B0",  # Color de texto secundario o deshabilitado
    
    # ----- Colores de Acento -----
    "primary": "#4682B4",          # Azul acero: para elementos principales (selección, progreso)
    "primary_dark": "#2E5A7A",     # Versión más oscura del primario
    "primary_light": "#87CEEB",    # Azul cielo claro para mejor contraste
    "primary_bright": "#FFA366",   # Naranja: para etiquetas, notificaciones y enfoque
    "secondary": "#606060",        # Gris medio: para botones secundarios y bordes
    
    # ----- Colores de Estado -----
    "success": "#5cb85c",          # Verde para operaciones exitosas
    "warning": "#f0ad4e",          # Amarillo para advertencias
    "error": "#d9534f",            # Rojo para errores
    
    # ----- Componentes Específicos -----
    "border": "#606060",
    "border_focus": "#4682B4",     # Border color when focused
    "border_light": "#808080",     # Light border color
    "selection": "#5A5A5A",
    "text_placeholder": "#999999",
    "text_primary": "#E0E0E0",     # Alias for foreground
    "text_secondary": "#B0B0B0",   # Alias for foreground_dark
    "text_muted": "#999999",       # Very dim text
    "text_accent": "#FFA366",      # Accent text color
    "separator": "#606060",        # Separator lines
    
    # ----- Table específicos -----
    "table_row_even": "#383838",   # Even row color
    "table_selected": "#4682B4",   # Selected row
    "table_hover": "#424242",      # Hover row
    
    # ----- Button específicos -----
    "button_hover": "#5A94C7",     # Button hover
    "button_secondary": "#606060", # Secondary button
    "button_secondary_hover": "#707070", # Secondary button hover
    
    # ----- Slider específicos -----
    "slider_handle": "#4682B4",    # Slider handle color
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
    "title": "Segoe UI, Arial, sans-serif",  # Title font family
    "title_size": "12pt",
    "section_header_size": "11px",
    'mono': '"Consolas", "Monaco", "Courier New", monospace',
    'Medium': 'QFont("Segoe UI", 10, QFont.Medium)',  # For QFont objects
    'Timecode': '"Consolas", "Monaco", "Courier New", monospace',  # Timecode font
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
        selection-background-color: {COLORS['primary_light']};
        selection-color: #1a1a1a;
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
        background: {COLORS['primary_light']};
        color: #1a1a1a;
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

def get_minimalist_components_style():
    """Estilos para componentes minimalistas base."""
    return f"""
    /* Componentes Base Minimalistas */
    
    /* Base Panel */
    QWidget[class="base_panel"] {{
        background: {COLORS['background']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        color: {COLORS['text_primary']};
    }}
    
    /* Headers Minimalistas */
    QWidget[class="minimalist_header"] {{
        background: {COLORS['background_panel']};
        border: none;
        border-bottom: 1px solid {COLORS['border']};
        min-height: 28px;
        max-height: 32px;
    }}
    
    QLabel[class="header_title"] {{
        color: {COLORS['text_primary']};
        font-family: {FONTS['title']};
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    
    QPushButton[class="header_button"] {{
        background: transparent;
        border: none;
        border-radius: 8px;
        color: {COLORS['text_secondary']};
        min-width: 16px;
        max-width: 20px;
        min-height: 16px;
        max-height: 20px;
    }}
    
    QPushButton[class="header_button"]:hover {{
        background: {COLORS['background_tertiary']};
        color: {COLORS['text_primary']};
    }}
    
    /* Form Sections */
    QWidget[class="form_section"] {{
        background: transparent;
        border: none;
    }}
    
    QLabel[class="section_title"] {{
        color: {COLORS['text_primary']};
        font-family: {FONTS['title']};
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 2px 0px;
        margin-bottom: 4px;
        border-bottom: 1px solid {COLORS['border_light']};
    }}
    
    QLabel[class="field_label"] {{
        color: {COLORS['text_secondary']};
        font-family: {FONTS['main']};
        font-size: 10px;
        min-width: 50px;
        max-width: 70px;
        padding-right: 8px;
        text-align: right;
    }}
    
    QLineEdit[class="form_field"] {{
        background: {COLORS['background_input']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        padding: 3px 6px;
        color: {COLORS['text_primary']};
        font-family: {FONTS['main']};
        font-size: 10px;
        min-height: 18px;
        max-height: 22px;
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
    
    /* Action Bars */
    QWidget[class="action_bar"] {{
        background: {COLORS['background_panel']};
        border: none;
        border-top: 1px solid {COLORS['border']};
        min-height: 32px;
        max-height: 36px;
    }}
    
    QLabel[class="status_text"] {{
        color: {COLORS['text_secondary']};
        font-family: {FONTS['main']};
        font-size: 9px;
        font-style: italic;
    }}
    
    QPushButton[class^="action_button"] {{
        border: none;
        border-radius: 3px;
        padding: 3px 8px;
        font-family: {FONTS['main']};
        font-size: 10px;
        font-weight: 500;
        min-height: 22px;
        max-height: 26px;
    }}
    
    QPushButton[class="action_button_primary"] {{
        background: {COLORS['primary']};
        color: white;
    }}
    
    QPushButton[class="action_button_primary"]:hover {{
        background: {COLORS['primary_light']};
    }}
    
    QPushButton[class="action_button_secondary"] {{
        background: {COLORS['button_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
    }}
    
    QPushButton[class="action_button_secondary"]:hover {{
        background: {COLORS['button_secondary_hover']};
        border-color: {COLORS['primary']};
    }}
    
    /* Paneles específicos minimalistas */
    QWidget[class="panel_minimal"] {{
        background: {COLORS['background']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 6px;
    }}
    
    QLabel[class="panel_title_minimal"] {{
        color: {COLORS['text_primary']};
        font-family: {FONTS['title']};
        font-size: 11px;
        font-weight: bold;
        padding: 2px 0px 6px 0px;
        border-bottom: 1px solid {COLORS['border_light']};
        margin-bottom: 6px;
    }}
    
    /* Badges y valores */
    QLabel[class="value_badge_minimal"] {{
        color: {COLORS['text_primary']};
        background: {COLORS['background_tertiary']};
        padding: 2px 6px;
        border-radius: 3px;
        font-family: {FONTS['mono']};
        font-size: 10px;
        font-weight: bold;
        border-left: 2px solid {COLORS['primary']};
    }}
    
    /* Botones minimalistas */
    QPushButton[class="btn_minimal"] {{
        background: {COLORS['background_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 10px;
        color: {COLORS['text_primary']};
        min-height: 20px;
    }}
    
    QPushButton[class="btn_minimal"]:hover {{
        background: {COLORS['background_tertiary']};
        border-color: {COLORS['primary']};
    }}
    
    QPushButton[class="btn_minimal_primary"] {{
        background: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 10px;
        font-weight: bold;
        min-height: 20px;
    }}
    
    QPushButton[class="btn_minimal_primary"]:hover {{
        background: {COLORS['primary_light']};
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
        get_scrollbar_style() +
        get_minimalist_components_style()
    )