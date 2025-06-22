"""
Módulo para generar la hoja de estilos QSS global de la aplicación.
Refactorizado para usar el nuevo sistema de diseño.
"""
from .styles.ui_helpers import load_stylesheet

def get_stylesheet():
    """
    Carga y devuelve la hoja de estilos QSS principal de la aplicación.
    """
    # Try to load the new main stylesheet
    stylesheet = load_stylesheet("main_style.qss")
    
    if stylesheet:
        return stylesheet
    
    # Fallback to basic styling if file not found
    from config.design_system import Theme, Typography, Spacing
    return f"""
        QWidget {{
            font-family: {Typography.FONT_FAMILY};
            font-size: {Typography.BODY}px;
            color: {Theme.TEXT_PRIMARY};
            background-color: {Theme.BACKGROUND};
        }}
        
        QMainWindow {{
            background-color: {Theme.BACKGROUND};
        }}
        
        QPushButton {{
            background-color: {Theme.PRIMARY};
            color: {Theme.TEXT_ON_PRIMARY};
            border: none;
            border-radius: 4px;
            padding: {Spacing.SM}px {Spacing.MD}px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background-color: {Theme.PRIMARY_DARK};
        }}
    """

# Backward compatibility - keep the old theme import working
from .theme import COLORS, FONTS 