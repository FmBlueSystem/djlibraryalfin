from .theme_manager import theme_manager

def get_dark_theme_qss():
    """
    Genera una hoja de estilos (QSS) para un tema oscuro, basada en la paleta
    de colores del ThemeManager existente.
    """
    colors = theme_manager.themes["dark"]

    qss = f"""
        /* --- General --- */
        QWidget {{
            background-color: {colors['bg_primary']};
            color: {colors['fg_primary']};
            border: none;
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 11pt;
        }}

        /* --- Ventana Principal --- */
        QMainWindow {{
            background-color: {colors['bg_primary']};
        }}

        /* --- Tabla (Tracklist) --- */
        QTableView {{
            background-color: {colors['bg_secondary']};
            gridline-color: {colors['border_color']};
            border: 1px solid {colors['border_color']};
            font-size: 10pt;
        }}
        
        QTableView::item {{
            padding: 5px;
            border-bottom: 1px solid {colors['border_color']};
        }}

        QTableView::item:selected {{
            background-color: {colors['selection_color']};
            color: {colors['fg_primary']};
        }}
        
        QTableView::item:hover {{
            background-color: {colors['hover_color']};
        }}

        /* --- Cabecera de la Tabla --- */
        QHeaderView::section {{
            background-color: {colors['bg_tertiary']};
            color: {colors['fg_secondary']};
            padding: 8px;
            border: 1px solid {colors['border_color']};
            font-size: 10pt;
            font-weight: bold;
        }}

        /* --- Barras de Desplazamiento --- */
        QScrollBar:vertical {{
            background: {colors['bg_secondary']};
            width: 12px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {colors['bg_tertiary']};
            min-height: 20px;
            border-radius: 6px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}

        QScrollBar:horizontal {{
            background: {colors['bg_secondary']};
            height: 12px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {colors['bg_tertiary']};
            min-width: 20px;
            border-radius: 6px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
            background: none;
        }}

        /* --- Botones --- */
        QPushButton {{
            background-color: {colors['accent_primary']};
            color: #FFFFFF;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {colors['accent_secondary']};
        }}

        QPushButton:pressed {{
            background-color: {colors['bg_tertiary']};
        }}
    """
    return qss 