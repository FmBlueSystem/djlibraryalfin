"""
Modern Theme Manager for DJ Library Application
Provides consistent styling, colors, and visual elements across the application.
"""

import tkinter as tk
from tkinter import ttk
import platform

class ThemeManager:
    """Manages application-wide theming and styling."""
    
    def __init__(self):
        self.current_theme = "dark"  # Default to dark theme for DJ applications
        self.themes = {
            "dark": {
                "bg_primary": "#1E1E1E",      # Main background
                "bg_secondary": "#2D2D2D",    # Secondary panels
                "bg_tertiary": "#3C3C3C",     # Elevated elements
                "fg_primary": "#FFFFFF",      # Primary text
                "fg_secondary": "#B0B0B0",    # Secondary text
                "fg_muted": "#808080",        # Muted text
                "accent_primary": "#0078D4",  # Primary accent (Microsoft Blue)
                "accent_secondary": "#106EBE", # Darker accent
                "accent_success": "#107C10",  # Success green
                "accent_warning": "#FF8C00",  # Warning orange
                "accent_error": "#D13438",    # Error red
                "border_color": "#484848",    # Border color
                "hover_color": "#404040",     # Hover state
                "selection_color": "#0078D4", # Selection highlight
                "waveform_color": "#00D4FF",  # Cyan for waveforms
                "waveform_bg": "#1A1A1A",     # Waveform background
            },
            "light": {
                "bg_primary": "#FFFFFF",
                "bg_secondary": "#F5F5F5",
                "bg_tertiary": "#E5E5E5",
                "fg_primary": "#000000",
                "fg_secondary": "#666666",
                "fg_muted": "#999999",
                "accent_primary": "#0078D4",
                "accent_secondary": "#106EBE",
                "accent_success": "#107C10",
                "accent_warning": "#FF8C00",
                "accent_error": "#D13438",
                "border_color": "#CCCCCC",
                "hover_color": "#F0F0F0",
                "selection_color": "#0078D4",
                "waveform_color": "#0078D4",
                "waveform_bg": "#FAFAFA",
            }
        }
        
        # Typography settings
        self.fonts = {
            "heading_large": ("Segoe UI", 18, "bold"),
            "heading_medium": ("Segoe UI", 14, "bold"),
            "heading_small": ("Segoe UI", 12, "bold"),
            "body_large": ("Segoe UI", 11),
            "body_medium": ("Segoe UI", 10),
            "body_small": ("Segoe UI", 9),
            "monospace": ("Consolas", 10),
        }
        
        # Spacing and sizing
        self.spacing = {
            "xs": 4,
            "sm": 8,
            "md": 16,
            "lg": 24,
            "xl": 32,
        }
        
        self.sizes = {
            "button_height": 32,
            "input_height": 28,
            "toolbar_height": 40,
            "statusbar_height": 24,
            "sidebar_width": 250,
        }

    def get_color(self, color_name):
        """Get a color from the current theme."""
        return self.themes[self.current_theme].get(color_name, "#000000")
    
    def get_font(self, font_name):
        """Get a font configuration."""
        return self.fonts.get(font_name, ("Segoe UI", 10))
    
    def get_spacing(self, size_name):
        """Get spacing value."""
        return self.spacing.get(size_name, 8)
    
    def get_size(self, size_name):
        """Get size value."""
        return self.sizes.get(size_name, 32)
    
    def configure_ttk_styles(self, root):
        """Configure ttk styles for consistent theming."""
        style = ttk.Style(root)
        
        # Configure the overall theme
        if platform.system() == "Windows":
            style.theme_use("vista")
        elif platform.system() == "Darwin":  # macOS
            style.theme_use("aqua")
        else:
            style.theme_use("clam")
        
        # Custom styles for dark theme
        if self.current_theme == "dark":
            # Configure Treeview
            style.configure("Custom.Treeview",
                background=self.get_color("bg_secondary"),
                foreground=self.get_color("fg_primary"),
                fieldbackground=self.get_color("bg_secondary"),
                borderwidth=0,
                font=self.get_font("body_medium"))
            
            style.configure("Custom.Treeview.Heading",
                background=self.get_color("bg_tertiary"),
                foreground=self.get_color("fg_primary"),
                font=self.get_font("heading_small"),
                borderwidth=1,
                relief="solid")
            
            # Configure Frames
            style.configure("Custom.TFrame",
                background=self.get_color("bg_primary"),
                borderwidth=0)
            
            style.configure("Card.TFrame",
                background=self.get_color("bg_secondary"),
                borderwidth=1,
                relief="solid")
            
            # Configure Labels
            style.configure("Custom.TLabel",
                background=self.get_color("bg_primary"),
                foreground=self.get_color("fg_primary"),
                font=self.get_font("body_medium"))
            
            style.configure("Heading.TLabel",
                background=self.get_color("bg_primary"),
                foreground=self.get_color("fg_primary"),
                font=self.get_font("heading_medium"))
            
            # Configure Buttons
            style.configure("Custom.TButton",
                background=self.get_color("accent_primary"),
                foreground="#FFFFFF",
                font=self.get_font("body_medium"),
                borderwidth=0,
                focuscolor="none")
            
            style.map("Custom.TButton",
                background=[("active", self.get_color("accent_secondary")),
                           ("pressed", self.get_color("accent_secondary"))])
            
            # Configure Entry widgets
            style.configure("Custom.TEntry",
                fieldbackground=self.get_color("bg_tertiary"),
                foreground=self.get_color("fg_primary"),
                borderwidth=1,
                insertcolor=self.get_color("fg_primary"))
            
            # Configure Scrollbars
            style.configure("Custom.Vertical.TScrollbar",
                background=self.get_color("bg_secondary"),
                troughcolor=self.get_color("bg_primary"),
                borderwidth=0,
                arrowcolor=self.get_color("fg_secondary"))
    
    def switch_theme(self, theme_name):
        """Switch to a different theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False

# Global theme manager instance
theme_manager = ThemeManager()
