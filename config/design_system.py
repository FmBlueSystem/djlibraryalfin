"""
Design System for DjAlfin - Centralized visual constants and utilities
Following material design principles adapted for DJ software
"""

class Theme:
    """Main color palette for the application"""
    
    # Primary Colors
    PRIMARY = "#2196F3"
    PRIMARY_DARK = "#1976D2"
    PRIMARY_LIGHT = "#87CEEB"  # Azul cielo claro para excelente contraste
    PRIMARY_VARIANT = "#0D47A1"
    
    # Secondary Colors  
    SECONDARY = "#FF9800"
    SECONDARY_DARK = "#F57C00"
    SECONDARY_LIGHT = "#FFE0B2"
    
    # Background Colors
    BACKGROUND = "#FAFAFA"
    BACKGROUND_DARK = "#2B2B2B"
    SURFACE = "#FFFFFF"
    SURFACE_DARK = "#353535"
    
    # Text Colors
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#BDBDBD"
    TEXT_ON_PRIMARY = "#FFFFFF"
    TEXT_ON_SECONDARY = "#000000"
    
    # Status Colors
    ERROR = "#F44336"
    WARNING = "#FF9800"
    SUCCESS = "#4CAF50"
    INFO = "#2196F3"
    
    # DJ-specific Colors
    CUE_POINT = "#FF5722"
    BPM_MATCH = "#4CAF50"
    KEY_MATCH = "#9C27B0"
    WAVEFORM = "#00BCD4"
    
    # Borders and Dividers
    BORDER = "#E0E0E0"
    BORDER_LIGHT = "#F5F5F5"
    DIVIDER = "#EEEEEE"
    SELECTION = "#E3F2FD"
    
    # Additional aliases for DJ interface
    BACKGROUND_PANEL = SURFACE_DARK
    BACKGROUND_TERTIARY = "#4A4A4A"
    BACKGROUND_INPUT = "#FFFFFF"
    BACKGROUND_SECONDARY = "#F5F5F5"


class Typography:
    """Typography scale and font definitions"""
    
    # Font Families
    FONT_FAMILY = "Segoe UI, system-ui, -apple-system, sans-serif"
    MONO_FAMILY = "Consolas, Monaco, 'Courier New', monospace"
    
    # Aliases for common usage
    TITLE_FONT = FONT_FAMILY
    BODY_FONT = FONT_FAMILY
    MONO_FONT = MONO_FAMILY
    
    # Font Sizes (in px)
    H1 = 32
    H2 = 24
    H3 = 20
    H4 = 18
    H5 = 16
    H6 = 14
    BODY_LARGE = 16
    BODY = 14
    BODY_SMALL = 12
    CAPTION = 12
    OVERLINE = 10
    
    # Font Weights
    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMI_BOLD = 600
    BOLD = 700
    
    # Line Heights (multipliers)
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.4
    LINE_HEIGHT_RELAXED = 1.6


class Spacing:
    """Consistent spacing scale"""
    
    # Base unit (4px)
    BASE = 4
    
    # Common spacing values
    XS = BASE      # 4px
    SM = BASE * 2  # 8px
    MD = BASE * 4  # 16px
    LG = BASE * 6  # 24px
    XL = BASE * 8  # 32px
    XXL = BASE * 12 # 48px
    
    # Aliases for easier usage
    EXTRA_SMALL = XS
    SMALL = SM
    MEDIUM = MD
    LARGE = LG
    EXTRA_LARGE = XL
    
    # Component-specific spacing
    COMPONENT_PADDING = MD
    SECTION_MARGIN = LG
    BUTTON_PADDING_H = MD
    BUTTON_PADDING_V = SM
    INPUT_PADDING = SM


class Layout:
    """Layout constants and breakpoints"""
    
    # Border radius
    BORDER_RADIUS_SM = 4
    BORDER_RADIUS_MD = 8
    BORDER_RADIUS_LG = 12
    BORDER_RADIUS_XL = 16
    
    # Shadows (box-shadow equivalent for Qt)
    SHADOW_LIGHT = "0px 1px 3px rgba(0, 0, 0, 0.12)"
    SHADOW_MEDIUM = "0px 4px 6px rgba(0, 0, 0, 0.1)"
    SHADOW_HEAVY = "0px 10px 25px rgba(0, 0, 0, 0.15)"
    
    # Component dimensions
    BUTTON_HEIGHT = 36
    INPUT_HEIGHT = 36
    HEADER_HEIGHT = 64
    SIDEBAR_WIDTH = 280
    TOOLBAR_HEIGHT = 48


class DarkTheme(Theme):
    """Dark theme variant"""
    
    # Override colors for dark theme
    BACKGROUND = "#121212"
    BACKGROUND_DARK = "#000000"
    SURFACE = "#1E1E1E"
    SURFACE_DARK = "#2D2D2D"
    
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B3B3B3"
    TEXT_DISABLED = "#666666"
    
    BORDER = "#333333"
    DIVIDER = "#2D2D2D"
    SELECTION = "#1976D2"


def get_theme_colors(dark_mode=False):
    """Get the appropriate theme colors based on mode"""
    return DarkTheme if dark_mode else Theme


class Animation:
    """Animation constants for smooth transitions"""
    
    # Duration in milliseconds
    FAST = 150
    NORMAL = 250
    SLOW = 400
    
    # Easing curves (Qt equivalents)
    EASE_IN_OUT = "ease-in-out"
    EASE_OUT = "ease-out"
    EASE_IN = "ease-in"


class IconSizes:
    """Standard icon sizes"""
    
    SMALL = 16
    MEDIUM = 24
    LARGE = 32
    XLARGE = 48


# Utility functions for converting to Qt-compatible formats
def px(value):
    """Convert value to px string for Qt stylesheets"""
    return f"{value}px"

def color_with_alpha(color, alpha):
    """Add alpha channel to hex color"""
    if color.startswith('#'):
        color = color[1:]
    return f"rgba({int(color[0:2], 16)}, {int(color[2:4], 16)}, {int(color[4:6], 16)}, {alpha})"

def font_css(size, weight=Typography.REGULAR, family=Typography.FONT_FAMILY):
    """Generate font CSS for Qt stylesheets"""
    return f"font: {weight} {px(size)} {family};"