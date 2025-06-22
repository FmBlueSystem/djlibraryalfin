# ui/components/sliding_panel.py

from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, Signal, QRect
from PySide6.QtGui import QColor

class SlidingPanel(QWidget):
    """
    Clase base para paneles que se deslizan desde los bordes de la pantalla.
    Incluye animaciones suaves, auto-ocultamiento y detección de hover.
    """
    
    # Señales
    panelShown = Signal()
    panelHidden = Signal()
    
    def __init__(self, parent=None, side='left', width=300, auto_hide_delay=3000):
        super().__init__(parent)
        
        # Configuración
        self.side = side  # 'left' o 'right'
        self.panel_width = width
        self.auto_hide_delay = auto_hide_delay
        self.is_visible = False
        self.is_animating = False
        
        # Estado de hover
        self.mouse_inside = False
        
        # Configurar widget
        self.setup_widget()
        
        # Configurar animaciones
        self.setup_animations()
        
        # Timer para auto-ocultar
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.slide_out)
        
        # Configurar efectos visuales
        self.setup_visual_effects()
        
    def setup_widget(self):
        """Configura las propiedades básicas del widget."""
        self.setFixedWidth(self.panel_width)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("class", "sliding_panel")
        
        # Configurar como widget hijo correctamente integrado
        # Remover WindowStaysOnTopHint que causa problemas de superposición
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Configurar para que sea un overlay sin ventana independiente
        self.raise_()  # Elevar z-index dentro del widget padre
        
    def setup_animations(self):
        """Configura las animaciones de deslizamiento."""
        # Animación de posición
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)  # 300ms
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.finished.connect(self.on_animation_finished)
        
    def setup_visual_effects(self):
        """Configura efectos visuales como sombras."""
        # Sombra para darle profundidad
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(5 if self.side == 'left' else -5, 0)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
        
    def set_parent_geometry(self, parent_rect):
        """Establece la geometría basada en el widget padre."""
        self.parent_rect = parent_rect
        
        # Usar coordenadas relativas al widget padre
        # Altura del panel (toda la altura disponible del widget padre)
        panel_height = self.parent().height() if self.parent() else parent_rect.height()
        parent_width = self.parent().width() if self.parent() else parent_rect.width()
        
        if self.side == 'left':
            # Panel izquierdo: oculto inicialmente a la izquierda
            self.hidden_pos = QRect(-self.panel_width, 0, self.panel_width, panel_height)
            self.visible_pos = QRect(0, 0, self.panel_width, panel_height)
        else:  # right
            # Panel derecho: oculto inicialmente a la derecha
            self.hidden_pos = QRect(parent_width, 0, self.panel_width, panel_height)
            self.visible_pos = QRect(parent_width - self.panel_width, 0, self.panel_width, panel_height)
        
        # Posicionar inicialmente oculto
        self.setGeometry(self.hidden_pos)
        
    def slide_in(self):
        """Desliza el panel hacia adentro."""
        if self.is_animating or self.is_visible:
            return
            
        self.is_animating = True
        self.show()
        self.raise_()  # Asegurar que esté por encima de otros widgets
        
        # Configurar animación de entrada
        self.animation.setStartValue(self.hidden_pos)
        self.animation.setEndValue(self.visible_pos)
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)  # Efecto "bounce"
        
        self.animation.start()
        
    def slide_out(self):
        """Desliza el panel hacia afuera."""
        if self.is_animating or not self.is_visible or self.mouse_inside:
            return
            
        # Detener el timer de auto-ocultar
        self.hide_timer.stop()
        
        self.is_animating = True
        
        # Configurar animación de salida
        self.animation.setStartValue(self.visible_pos)
        self.animation.setEndValue(self.hidden_pos)
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.InQuart)
        
        self.animation.start()
        
    def on_animation_finished(self):
        """Maneja el final de la animación."""
        self.is_animating = False
        
        if self.geometry() == self.visible_pos:
            # Panel ahora visible
            self.is_visible = True
            self.panelShown.emit()
            
            # Llamar método específico cuando el panel se muestra
            if hasattr(self, 'on_panel_shown'):
                self.on_panel_shown()
                
            # Iniciar timer de auto-ocultar solo si auto_hide_delay > 0
            if self.auto_hide_delay > 0 and not self.mouse_inside:
                self.hide_timer.start(self.auto_hide_delay)
        else:
            # Panel ahora oculto
            self.is_visible = False
            self.hide()
            self.panelHidden.emit()
            
    def toggle(self):
        """Alterna la visibilidad del panel."""
        if self.is_visible:
            self.slide_out()
        else:
            self.slide_in()
            
    # --- Eventos de mouse para detección de hover ---
    
    def enterEvent(self, event):
        """Se ejecuta cuando el mouse entra al panel."""
        self.mouse_inside = True
        self.hide_timer.stop()  # Detener auto-ocultar mientras el mouse esté dentro
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Se ejecuta cuando el mouse sale del panel."""
        self.mouse_inside = False
        # Reiniciar timer de auto-ocultar solo si auto_hide_delay > 0
        if self.is_visible and not self.is_animating and self.auto_hide_delay > 0:
            self.hide_timer.start(self.auto_hide_delay)
        super().leaveEvent(event)
        
    # --- Métodos públicos para control externo ---
    
    def show_panel(self):
        """Muestra el panel (para control externo)."""
        self.slide_in()
        
    def hide_panel(self):
        """Oculta el panel (para control externo)."""
        self.slide_out()
        
    def is_panel_visible(self):
        """Retorna si el panel está visible."""
        return self.is_visible
        
    def set_auto_hide_delay(self, delay_ms):
        """Establece el delay de auto-ocultamiento."""
        self.auto_hide_delay = delay_ms