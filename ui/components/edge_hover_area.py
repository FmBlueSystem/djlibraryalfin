# ui/components/edge_hover_area.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor

class EdgeHoverArea(QWidget):
    """
    Área invisible en los bordes de la pantalla para activar paneles deslizantes.
    """
    
    # Señales
    hoverEntered = Signal()
    hoverLeft = Signal()
    
    def __init__(self, edge='left', trigger_width=15, parent=None):
        super().__init__(parent)
        
        self.edge = edge  # 'left' o 'right'
        self.trigger_width = trigger_width
        self.hover_active = False
        
        # Configurar widget
        self.setup_widget()
        
        # Timer para evitar activaciones accidentales
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.confirm_hover)
        
    def setup_widget(self):
        """Configura las propiedades básicas del widget."""
        # Hacer el widget invisible pero funcional
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: transparent;")
        
        # Configurar tamaño fijo
        self.setFixedWidth(self.trigger_width)
        
    def set_parent_geometry(self, parent_rect):
        """Establece la geometría basada en el widget padre."""
        height = parent_rect.height()
        
        if self.edge == 'left':
            # Área de hover en el borde izquierdo
            self.setGeometry(0, 0, self.trigger_width, height)
        else:  # right
            # Área de hover en el borde derecho
            self.setGeometry(parent_rect.width() - self.trigger_width, 0, self.trigger_width, height)
            
    def enterEvent(self, event):
        """Se ejecuta cuando el mouse entra al área de hover."""
        if not self.hover_active:
            print(f"🎯 Mouse entered {self.edge} edge hover area")
            self.hover_timer.start(200)  # 200ms de delay para evitar activaciones accidentales
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Se ejecuta cuando el mouse sale del área de hover."""
        if self.hover_active:
            print(f"🎯 Mouse left {self.edge} edge hover area")
            self.hover_active = False
            self.hover_timer.stop()
            self.hoverLeft.emit()
        super().leaveEvent(event)
        
    def confirm_hover(self):
        """Confirma el hover después del delay."""
        if not self.hover_active:
            self.hover_active = True
            print(f"✅ Confirmed hover on {self.edge} edge")
            self.hoverEntered.emit()
            
    def paintEvent(self, event):
        """Dibuja el área de hover (opcional, para debug)."""
        # En producción, este método puede estar vacío para mantener transparencia
        # Descomenta las siguientes líneas para visualizar las áreas de hover durante desarrollo
        
        # painter = QPainter(self)
        # color = QColor(255, 0, 0, 30)  # Rojo semi-transparente
        # painter.fillRect(self.rect(), color)
        
        super().paintEvent(event)