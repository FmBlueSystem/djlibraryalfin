# ui/theme.py

"""
Tema visual moderno y profesional para DjAlfin
Inspirado en aplicaciones DJ profesionales como Serato y rekordbox
"""

# Paleta de colores principal - Tema DJ Profesional (Mejorado para contraste)
COLORS = {
    # Colores principales
    'primary': '#FF6B35',           # Naranja vibrante (color principal)
    'primary_dark': '#E55A2B',      # Naranja oscuro
    'primary_light': '#FF8A5C',     # Naranja claro
    'primary_bright': '#FFA366',    # Naranja muy claro para texto
    
    # Colores de fondo
    'background_main': '#1A1A1A',   # Negro principal
    'background_secondary': '#2D2D2D', # Gris oscuro
    'background_tertiary': '#4A4A4A',  # Gris medio (más claro para mejor contraste)
    'background_panel': '#252525',   # Paneles laterales
    'background_input': '#353535',   # Fondo de campos de entrada (más claro)
    
    # Colores de texto
    'text_primary': '#FFFFFF',      # Blanco principal
    'text_secondary': '#E0E0E0',    # Gris muy claro (mejor contraste)
    'text_muted': '#B0B0B0',        # Gris medio claro (mejor contraste)
    'text_accent': '#FF8A5C',       # Naranja claro para acentos
    'text_placeholder': '#A0A0A0',  # Placeholder más visible
    
    # Colores de estado
    'success': '#00D4AA',           # Verde turquesa
    'warning': '#FFB800',           # Amarillo
    'error': '#FF4757',             # Rojo
    'info': '#3742FA',              # Azul
    
    # Colores de la tabla
    'table_header': '#333333',      # Header de tabla
    'table_row_even': '#242424',    # Filas pares (un poco más claras para contraste)
    'table_row_odd': '#1F1F1F',     # Filas impares (se mantiene oscuro)
    'table_selected': '#FF6B35',    # Fila seleccionada
    'table_hover': '#3A3A3A',       # Hover
    
    # Colores de controles
    'button_primary': '#FF6B35',    # Botón principal
    'button_secondary': '#606060',  # Botón secundario (más claro)
    'button_secondary_hover': '#707070', # Hover botón secundario
    'button_hover': '#FF8A5C',      # Hover de botón
    'slider_track': '#606060',      # Track del slider (más visible)
    'slider_handle': '#FF6B35',     # Handle del slider
    'slider_progress': '#FF8A5C',   # Progreso del slider
    
    # Bordes y separadores
    'border': '#606060',            # Bordes generales (más visibles)
    'border_light': '#707070',      # Bordes claros
    'border_focus': '#FF6B35',      # Borde de focus
    'separator': '#404040',         # Separadores
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
    'main': '"Segoe UI", "Roboto", "Arial", sans-serif',
    'mono': '"Consolas", "Monaco", "Courier New", monospace',
    'title': '"Segoe UI Semibold", "Roboto Medium", "Arial Bold", sans-serif',
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
        color: {COLORS['text_secondary']};
    }}
    
    QPushButton[class="secondary"]:hover {{
        background: {COLORS['background_tertiary']};
        color: {COLORS['text_primary']};
    }}
    """

def get_slider_style():
    """Estilo moderno para sliders"""
    return f"""
    QSlider::groove:horizontal {{
        background: {COLORS['slider_track']};
        height: 6px;
        border-radius: 3px;
    }}
    
    QSlider::handle:horizontal {{
        background: {GRADIENTS['primary']};
        border: 2px solid {COLORS['text_primary']};
        width: 20px;
        height: 20px;
        border-radius: 12px;
        margin: -8px 0;
    }}
    
    QSlider::handle:horizontal:hover {{
        background: {COLORS['primary_light']};
        border: 2px solid {COLORS['primary_light']};
    }}
    
    QSlider::handle:horizontal:pressed {{
        background: {COLORS['primary_dark']};
    }}
    
    QSlider::sub-page:horizontal {{
        background: {GRADIENTS['primary']};
        border-radius: 3px;
    }}
    """

def get_input_style():
    """Estilo para campos de entrada"""
    return f"""
    QLineEdit {{
        background: {COLORS['background_tertiary']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-family: {FONTS['main']};
        font-size: 13px;
    }}
    
    QLineEdit:focus {{
        border: 2px solid {COLORS['primary']};
        background: {COLORS['background_secondary']};
    }}
    
    QTextEdit {{
        background: {COLORS['background_tertiary']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px;
        font-family: {FONTS['main']};
        font-size: 13px;
    }}
    
    QTextEdit:focus {{
        border: 2px solid {COLORS['primary']};
        background: {COLORS['background_secondary']};
    }}
    """

def get_complete_style():
    """Retorna el estilo completo combinado"""
    return f"""
    {get_main_window_style()}
    {get_table_style()}
    {get_panel_style()}
    {get_button_style()}
    {get_slider_style()}
    {get_input_style()}
    """