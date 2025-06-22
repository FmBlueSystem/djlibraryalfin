#!/usr/bin/env python3
"""
Loading Widget - DjAlfin
Widget para mostrar estados de carga con spinners y progress bars.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QGraphicsOpacityEffect, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QPainter, QPen, QColor
import math

class SpinnerWidget(QWidget):
    """Widget de spinner animado personalizado."""
    
    def __init__(self, size=32, color="#2196F3", parent=None):
        super().__init__(parent)
        self.size = size
        self.color = QColor(color)
        self.angle = 0
        
        self.setFixedSize(size, size)
        
        # Timer para animación
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        
    def start(self):
        """Inicia la animación del spinner."""
        self.timer.start(50)  # 20 FPS
        self.show()
    
    def stop(self):
        """Detiene la animación del spinner."""
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        """Rota el spinner."""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Dibuja el spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Configurar pen
        pen = QPen(self.color)
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Calcular dimensiones
        rect_size = self.size - 8
        rect = self.rect()
        rect.setSize(rect.size() - rect.size() * 0.2)
        rect.moveCenter(self.rect().center())
        
        # Dibujar arcos con diferentes opacidades
        for i in range(8):
            angle_start = self.angle + (i * 45)
            angle_span = 30
            
            # Opacidad decremental
            opacity = 1.0 - (i * 0.125)
            color_with_opacity = QColor(self.color)
            color_with_opacity.setAlphaF(opacity)
            
            pen.setColor(color_with_opacity)
            painter.setPen(pen)
            
            # Dibujar arco
            painter.drawArc(rect, angle_start * 16, angle_span * 16)


class LoadingOverlay(QWidget):
    """Overlay de loading que se superpone sobre otros widgets."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        
        # Configurar overlay
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        self.setup_ui()
        
        # Efecto de opacidad para animaciones
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Animación de fade in/out
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def setup_ui(self):
        """Configura la interfaz del overlay."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Frame contenedor con estilo
        self.container = QFrame()
        self.container.setObjectName("loadingContainer")
        self.container.setStyleSheet("""
            QFrame#loadingContainer {
                background-color: rgba(45, 45, 45, 0.95);
                border: 2px solid #2196F3;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(15)
        
        # Spinner
        self.spinner = SpinnerWidget(48, "#2196F3")
        
        # Texto de estado
        self.status_label = QLabel("Cargando...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: #FFFFFF; padding: 5px;")
        
        # Progress bar (opcional)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 5px;
                text-align: center;
                background-color: #2D2D2D;
                color: #FFFFFF;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setFixedHeight(25)
        
        # Agregar widgets al layout
        container_layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)
        container_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.container, 0, Qt.AlignmentFlag.AlignCenter)
    
    def show_loading(self, message="Cargando...", show_progress=False):
        """Muestra el overlay de loading."""
        self.status_label.setText(message)
        self.progress_bar.setVisible(show_progress)
        
        if show_progress:
            self.progress_bar.setRange(0, 0)  # Indeterminado por defecto
        
        # Hacer visible y animar entrada
        self.setVisible(True)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        # Iniciar spinner
        self.spinner.start()
        
        # Posicionar correctamente
        if self.parent():
            self.resize(self.parent().size())
    
    def hide_loading(self):
        """Oculta el overlay de loading."""
        # Detener spinner
        self.spinner.stop()
        
        # Animar salida
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(lambda: self.setVisible(False))
        self.fade_animation.start()
    
    def update_progress(self, current, total, message=None):
        """Actualiza el progress bar."""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        
        if message:
            self.status_label.setText(message)
    
    def update_message(self, message):
        """Actualiza solo el mensaje."""
        self.status_label.setText(message)
    
    def resizeEvent(self, event):
        """Maneja el redimensionamiento del overlay."""
        super().resizeEvent(event)
        # El overlay debe cubrir todo el widget padre
        if self.parent():
            self.resize(self.parent().size())


class ProgressToast(QWidget):
    """Toast pequeño para mostrar progreso de operaciones rápidas."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setFixedSize(300, 80)
        
        # Configurar propiedades del widget
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        
        self.setup_ui()
        
        # Timer para auto-hide
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.hide_toast)
        
        # Animación de posición
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def setup_ui(self):
        """Configura la interfaz del toast."""
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 0.95);
                border: 1px solid #2196F3;
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Mini spinner
        self.mini_spinner = SpinnerWidget(24, "#2196F3")
        
        # Información
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.title_label = QLabel("Operación")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #FFFFFF;")
        
        self.detail_label = QLabel("En progreso...")
        detail_font = QFont()
        detail_font.setPointSize(9)
        self.detail_label.setFont(detail_font)
        self.detail_label.setStyleSheet("color: #BDBDBD;")
        
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.detail_label)
        
        layout.addWidget(self.mini_spinner)
        layout.addLayout(info_layout)
    
    def show_toast(self, title, detail="", duration=3000):
        """Muestra el toast."""
        self.title_label.setText(title)
        self.detail_label.setText(detail)
        
        # Posicionar en la esquina superior derecha del parent
        if self.parent():
            parent_rect = self.parent().rect()
            target_pos = parent_rect.topRight() - self.rect().topRight() - self.pos().__class__(20, 20)
            start_pos = target_pos + self.pos().__class__(self.width() + 50, 0)
            
            self.move(start_pos)
            self.setVisible(True)
            self.mini_spinner.start()
            
            # Animar entrada
            self.slide_animation.setStartValue(start_pos)
            self.slide_animation.setEndValue(target_pos)
            self.slide_animation.start()
            
            # Auto-hide
            if duration > 0:
                self.auto_hide_timer.start(duration)
    
    def hide_toast(self):
        """Oculta el toast."""
        self.mini_spinner.stop()
        
        if self.parent():
            parent_rect = self.parent().rect()
            start_pos = self.pos()
            end_pos = start_pos + self.pos().__class__(self.width() + 50, 0)
            
            # Animar salida
            self.slide_animation.setStartValue(start_pos)
            self.slide_animation.setEndValue(end_pos)
            self.slide_animation.finished.connect(lambda: self.setVisible(False))
            self.slide_animation.start()
    
    def update_detail(self, detail):
        """Actualiza el texto de detalle."""
        self.detail_label.setText(detail)