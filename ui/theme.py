# ui/theme.py

"""
Define la paleta de colores, fuentes y estilos para la aplicación DjAlfin.
"""

# --- Paleta de Colores ---
BACKGROUND_PRIMARY = "#2B2B2B"
BACKGROUND_SECONDARY = "#3C3F41"
TEXT_PRIMARY = "#A9B7C6"
TEXT_SECONDARY = "#888888"
ACCENT_PRIMARY = "#4682B4"  # Un azul acero
ACCENT_SECONDARY = "#5E9ACD"
BORDERS = "#4A4A4A"
SUCCESS = "#6A8759"
ERROR = "#AB5454"

# --- Tipografía ---
FONT_FAMILY_MAIN = "Helvetica"
FONT_FAMILY_MONO = "Courier New"

FONT_SIZE_NORMAL = 10
FONT_SIZE_LARGE = 12
FONT_SIZE_XLARGE = 14

FONT_NORMAL = (FONT_FAMILY_MAIN, FONT_SIZE_NORMAL)
FONT_BOLD = (FONT_FAMILY_MAIN, FONT_SIZE_NORMAL, "bold")
FONT_LARGE_BOLD = (FONT_FAMILY_MAIN, FONT_SIZE_LARGE, "bold")
FONT_XLARGE_BOLD = (FONT_FAMILY_MAIN, FONT_SIZE_XLARGE, "bold")

# --- Estilos de Widgets (Ejemplos) ---
STYLE_CONFIG = {
    "TFrame": {
        "configure": {"background": BACKGROUND_PRIMARY}
    },
    "TLabel": {
        "configure": {
            "background": BACKGROUND_PRIMARY,
            "foreground": TEXT_PRIMARY,
            "font": FONT_NORMAL
        }
    },
    "TButton": {
        "configure": {
            "background": ACCENT_PRIMARY,
            "foreground": "white",
            "font": FONT_BOLD,
            "padding": (10, 5),
            "relief": "flat",
            "borderwidth": 0
        },
        "map": {
            "background": [("active", ACCENT_SECONDARY)],
        }
    },
    "Treeview": {
        "configure": {
            "background": BACKGROUND_SECONDARY,
            "foreground": TEXT_PRIMARY,
            "fieldbackground": BACKGROUND_SECONDARY,
            "font": FONT_NORMAL,
            "rowheight": 25,
        },
        "map": {
            "background": [("selected", ACCENT_PRIMARY)],
            "foreground": [("selected", "white")]
        }
    },
    "Treeview.Heading": {
        "configure": {
            "background": BACKGROUND_PRIMARY,
            "foreground": TEXT_PRIMARY,
            "font": FONT_BOLD,
            "relief": "flat"
        }
    },
    "Vertical.TScrollbar": {
        "configure": {"background": BACKGROUND_PRIMARY, "troughcolor": BACKGROUND_SECONDARY}
    }
} 