# ui/widgets.py

from PySide6.QtWidgets import QSlider, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .theme import COLORS, FONTS

class CustomSlider(QSlider):
    """Un QSlider con un estilo personalizado que coincide con el tema."""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def mousePressEvent(self, event):
        """Permite al usuario hacer clic en cualquier punto del slider para cambiar el valor."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.orientation() == Qt.Orientation.Horizontal:
                value = self.minimum() + (self.maximum() - self.minimum()) * event.pos().x() / self.width()
            else:
                value = self.minimum() + (self.maximum() - self.minimum()) * (self.height() - event.pos().y()) / self.height()
            
            self.setValue(int(value))
            event.accept()
            # La señal valueChanged se emite automáticamente
        
        super().mousePressEvent(event)

class TimeLabel(QLabel):
    """Una QLabel diseñada para mostrar el tiempo (ej. 00:00)."""
    
    def __init__(self, text="00:00", parent=None):
        super().__init__(text, parent)
        self.setFont(FONTS["Timecode"])
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(60)
        self.setStyleSheet(f"color: {COLORS['text_secondary']};")

# Otros widgets personalizados pueden ser añadidos aquí si son necesarios 