# ui/widgets.py

import tkinter as tk
from tkinter import ttk
from . import theme

class ThemedFrame(ttk.Frame):
    """Un Frame que usa el color de fondo primario del tema."""
    def __init__(self, master, **kwargs):
        super().__init__(master, style="TFrame", **kwargs)

class HeaderLabel(ttk.Label):
    """Una Label con estilo de cabecera."""
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=text, style="Header.TLabel", **kwargs)
        self.configure(font=theme.FONT_LARGE_BOLD, foreground=theme.TEXT_PRIMARY)

class StyledButton(ttk.Button):
    """Un Button que usa los estilos primarios del tema."""
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=text, style="TButton", **kwargs) 