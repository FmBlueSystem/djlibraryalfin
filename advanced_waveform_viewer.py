#!/usr/bin/env python3
"""
🎯 DjAlfin - Advanced Waveform Viewer
Interfaz avanzada con zoom, análisis de cue points y waveform mejorada
"""

import sys
import os
import math
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QListWidget, QPushButton, QFrame,
                             QSplitter, QGridLayout, QTabWidget, QSlider, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPolygon, QLinearGradient
from PyQt5.QtCore import QPoint
from basic_metadata_reader import BasicMetadataReader

class AdvancedWaveformWidget(QWidget):
    """Widget avanzado de waveform con zoom y análisis real."""
    
    def __init__(self):
        super().__init__()
        self.cue_points = []
        self.duration = 300
        self.current_position = 0
        self.zoom_level = 1.0  # 1.0 = vista completa
        self.zoom_center = 0.5  # Centro del zoom (0-1)
        self.setMinimumHeight(80)
        self.setMaximumHeight(80)
        
        # Datos simulados de análisis
        self.beats = []
        self.downbeats = []
        self.energy_curve = []
        self.generate_simulated_analysis()
        
        # Timer para reproducción
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        
        # Interacción
        self.setMouseTracking(True)
        self.mouse_pos = None
        
    def generate_simulated_analysis(self):
        """Generar análisis simulado hasta que tengamos librosa."""
        
        if self.duration <= 0:
            return
            
        # Simular beats cada ~0.5 segundos (120 BPM)
        beat_interval = 0.5
        current_time = 0
        beat_count = 0
        
        while current_time < self.duration:
            # Añadir variación al tempo
            variation = random.uniform(-0.05, 0.05)
            actual_interval = beat_interval + variation
            
            self.beats.append(current_time)
            
            # Cada 4to beat es un downbeat
            if beat_count % 4 == 0:
                self.downbeats.append(current_time)
            
            current_time += actual_interval
            beat_count += 1
        
        # Simular curva de energía
        points = 200
        for i in range(points):
            t = (i / points) * self.duration
            # Energía simulada con variaciones
            base_energy = 0.3 + 0.4 * math.sin(t * 0.1)  # Variación lenta
            noise = random.uniform(-0.1, 0.1)
            energy = max(0, min(1, base_energy + noise))
            self.energy_curve.append(energy)
    
    def set_cue_points(self, cue_points, duration=300):
        """Establecer cue points y duración."""
        self.cue_points = cue_points
        self.duration = duration
        self.current_position = 0
        self.generate_simulated_analysis()
        self.update()
    
    def set_zoom(self, zoom_level, center=None):
        """Establecer nivel de zoom."""
        self.zoom_level = max(1.0, min(20.0, zoom_level))
        if center is not None:
            self.zoom_center = max(0.0, min(1.0, center))
        self.update()
    
    def get_time_range(self):
        """Obtener rango de tiempo visible."""
        if self.zoom_level == 1.0:
            return 0, self.duration
        
        visible_duration = self.duration / self.zoom_level
        start_time = self.zoom_center * self.duration - visible_duration / 2
        start_time = max(0, min(self.duration - visible_duration, start_time))
        end_time = start_time + visible_duration
        
        return start_time, end_time
    
    def start_playback(self):
        """Iniciar reproducción simulada."""
        self.timer.start(50)  # 20 FPS
    
    def stop_playback(self):
        """Detener reproducción."""
        self.timer.stop()
    
    def update_position(self):
        """Actualizar posición de reproducción."""
        self.current_position += 0.05
        if self.current_position >= self.duration:
            self.current_position = 0
        
        # Auto-seguimiento en zoom
        if self.zoom_level > 1.0:
            self.zoom_center = self.current_position / self.duration
        
        self.update()
    
    def mousePressEvent(self, event):
        """Manejar clic del mouse."""
        if event.button() == Qt.LeftButton:
            # Calcular posición en el tiempo
            start_time, end_time = self.get_time_range()
            relative_x = event.x() / self.width()
            clicked_time = start_time + (end_time - start_time) * relative_x
            
            # Saltar a esa posición
            self.current_position = clicked_time
            self.update()
            
            print(f"🎯 Jumped to {clicked_time:.1f}s")
    
    def wheelEvent(self, event):
        """Manejar zoom con rueda del mouse."""
        delta = event.angleDelta().y()
        zoom_factor = 1.2 if delta > 0 else 1/1.2
        
        # Calcular nuevo zoom centrado en la posición del mouse
        mouse_x = event.x() / self.width()
        start_time, end_time = self.get_time_range()
        mouse_time = start_time + (end_time - start_time) * mouse_x
        new_center = mouse_time / self.duration
        
        self.set_zoom(self.zoom_level * zoom_factor, new_center)
    
    def mouseMoveEvent(self, event):
        """Manejar movimiento del mouse."""
        self.mouse_pos = event.pos()
        self.update()
    
    def leaveEvent(self, event):
        """Mouse sale del widget."""
        self.mouse_pos = None
        self.update()
    
    def paintEvent(self, event):
        """Dibujar waveform avanzada."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Obtener rango de tiempo visible
        start_time, end_time = self.get_time_range()
        visible_duration = end_time - start_time
        
        # Fondo con gradiente
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(15, 15, 15))
        gradient.setColorAt(1, QColor(25, 25, 25))
        painter.fillRect(0, 0, width, height, QBrush(gradient))
        
        # Dibujar grid de tiempo
        self.draw_time_grid(painter, start_time, end_time, width, height)
        
        # Dibujar curva de energía de fondo
        self.draw_energy_background(painter, start_time, end_time, width, height)
        
        # Dibujar waveform principal
        self.draw_main_waveform(painter, start_time, end_time, width, height)
        
        # Dibujar beats y downbeats
        self.draw_beats(painter, start_time, end_time, width, height)
        
        # Dibujar cue points
        self.draw_cue_points(painter, start_time, end_time, width, height)
        
        # Dibujar posición actual
        self.draw_playhead(painter, start_time, end_time, width, height)
        
        # Dibujar información del mouse
        if self.mouse_pos:
            self.draw_mouse_info(painter, start_time, end_time, width, height)
        
        # Dibujar información de zoom
        self.draw_zoom_info(painter, width, height)
    
    def draw_time_grid(self, painter, start_time, end_time, width, height):
        """Dibujar grid de tiempo."""
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        
        # Calcular intervalo de grid apropiado
        visible_duration = end_time - start_time
        if visible_duration > 60:
            interval = 10  # 10 segundos
        elif visible_duration > 20:
            interval = 5   # 5 segundos
        else:
            interval = 1   # 1 segundo
        
        # Dibujar líneas verticales
        first_mark = math.ceil(start_time / interval) * interval
        current_mark = first_mark
        
        while current_mark <= end_time:
            x = int((current_mark - start_time) / (end_time - start_time) * width)
            painter.drawLine(x, 0, x, height)
            current_mark += interval
    
    def draw_energy_background(self, painter, start_time, end_time, width, height):
        """Dibujar curva de energía como fondo."""
        if not self.energy_curve:
            return
        
        painter.setPen(QPen(QColor(0, 100, 200, 50), 1))
        painter.setBrush(QBrush(QColor(0, 100, 200, 20)))
        
        points = []
        points.append((0, height))  # Esquina inferior izquierda
        
        for i in range(width):
            time_pos = start_time + (end_time - start_time) * (i / width)
            energy_idx = int((time_pos / self.duration) * len(self.energy_curve))
            energy_idx = max(0, min(len(self.energy_curve) - 1, energy_idx))
            
            energy = self.energy_curve[energy_idx]
            y = height - (energy * height * 0.3)  # 30% del height máximo
            points.append((i, int(y)))
        
        points.append((width, height))  # Esquina inferior derecha
        
        polygon = QPolygon([QPoint(x, y) for x, y in points])
        painter.drawPolygon(polygon)
    
    def draw_main_waveform(self, painter, start_time, end_time, width, height):
        """Dibujar waveform principal."""
        painter.setPen(QPen(QColor(0, 150, 255), 2))
        
        # Simular waveform con datos más realistas
        random.seed(42)  # Para consistencia
        
        for x in range(0, width, 2):
            time_pos = start_time + (end_time - start_time) * (x / width)
            
            # Simular amplitud basada en energía y variación
            energy_idx = int((time_pos / self.duration) * len(self.energy_curve)) if self.energy_curve else 0
            energy_idx = max(0, min(len(self.energy_curve) - 1, energy_idx))
            
            base_energy = self.energy_curve[energy_idx] if self.energy_curve else 0.5
            variation = random.uniform(0.5, 1.0)
            amplitude = base_energy * variation
            
            wave_height = int(amplitude * height * 0.8)
            y_center = height // 2
            
            painter.drawLine(x, y_center - wave_height//2, x, y_center + wave_height//2)
    
    def draw_beats(self, painter, start_time, end_time, width, height):
        """Dibujar beats y downbeats."""
        
        # Downbeats (más prominentes)
        painter.setPen(QPen(QColor(255, 255, 0, 150), 2))
        for downbeat in self.downbeats:
            if start_time <= downbeat <= end_time:
                x = int((downbeat - start_time) / (end_time - start_time) * width)
                painter.drawLine(x, 0, x, height)
        
        # Beats regulares
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        for beat in self.beats:
            if start_time <= beat <= end_time:
                x = int((beat - start_time) / (end_time - start_time) * width)
                painter.drawLine(x, height//4, x, 3*height//4)
    
    def draw_cue_points(self, painter, start_time, end_time, width, height):
        """Dibujar cue points con análisis."""
        
        for cue in self.cue_points:
            if start_time <= cue.position <= end_time:
                x = int((cue.position - start_time) / (end_time - start_time) * width)
                
                # Determinar color y estado
                try:
                    color = QColor(cue.color)
                except:
                    color = QColor(255, 0, 0)
                
                # Verificar si está en downbeat
                is_on_downbeat = any(abs(cue.position - db) < 0.1 for db in self.downbeats)
                
                if is_on_downbeat:
                    # Cue point correcto - borde verde
                    painter.setPen(QPen(QColor(0, 255, 0), 3))
                    painter.setBrush(QBrush(color))
                else:
                    # Cue point mal ubicado - borde rojo
                    painter.setPen(QPen(QColor(255, 0, 0), 3))
                    painter.setBrush(QBrush(color))
                
                # Línea vertical
                painter.drawLine(x, 0, x, height)
                
                # Círculo superior
                painter.drawEllipse(x - 6, 2, 12, 12)
                
                # Número del hot cue
                if cue.hotcue_index > 0:
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    painter.setFont(QFont("Arial", 8, QFont.Bold))
                    painter.drawText(x - 4, 22, str(cue.hotcue_index))
                
                # Indicador de problema si no está en downbeat
                if not is_on_downbeat:
                    # Encontrar downbeat más cercano
                    nearest_db = min(self.downbeats, key=lambda db: abs(db - cue.position))
                    if abs(nearest_db - cue.position) < 2.0:  # Solo si está cerca
                        db_x = int((nearest_db - start_time) / (end_time - start_time) * width)
                        
                        # Línea punteada hacia el downbeat sugerido
                        painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
                        painter.drawLine(x, height//2, db_x, height//2)
                        
                        # Círculo en la posición sugerida
                        painter.setPen(QPen(QColor(255, 255, 0), 2))
                        painter.setBrush(QBrush(QColor(255, 255, 0, 100)))
                        painter.drawEllipse(db_x - 4, height//2 - 4, 8, 8)
    
    def draw_playhead(self, painter, start_time, end_time, width, height):
        """Dibujar línea de reproducción actual."""
        if start_time <= self.current_position <= end_time:
            x = int((self.current_position - start_time) / (end_time - start_time) * width)
            
            # Línea principal
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(x, 0, x, height)
            
            # Triángulo superior
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            triangle = QPolygon([
                QPoint(x, 0),
                QPoint(x - 5, 10),
                QPoint(x + 5, 10)
            ])
            painter.drawPolygon(triangle)
    
    def draw_mouse_info(self, painter, start_time, end_time, width, height):
        """Dibujar información en la posición del mouse."""
        mouse_x = self.mouse_pos.x()
        mouse_time = start_time + (end_time - start_time) * (mouse_x / width)
        
        # Línea vertical del mouse
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawLine(mouse_x, 0, mouse_x, height)
        
        # Información de tiempo
        minutes = int(mouse_time // 60)
        seconds = int(mouse_time % 60)
        time_text = f"{minutes}:{seconds:02d}"
        
        # Fondo para el texto
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        text_rect = QRect(mouse_x + 5, 5, 50, 20)
        painter.drawRect(text_rect)
        
        # Texto
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(text_rect, Qt.AlignCenter, time_text)
    
    def draw_zoom_info(self, painter, width, height):
        """Dibujar información de zoom."""
        if self.zoom_level > 1.0:
            zoom_text = f"Zoom: {self.zoom_level:.1f}x"
            
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
            text_rect = QRect(width - 80, height - 25, 75, 20)
            painter.drawRect(text_rect)
            
            painter.setPen(QPen(QColor(0, 212, 255), 1))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(text_rect, Qt.AlignCenter, zoom_text)

class ZoomControlWidget(QWidget):
    """Widget de control de zoom."""
    
    zoom_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        layout.addWidget(QLabel("🔍 Zoom:"))
        
        # Slider de zoom
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)  # 1.0x
        self.zoom_slider.setMaximum(200)  # 20.0x
        self.zoom_slider.setValue(10)  # 1.0x inicial
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        layout.addWidget(self.zoom_slider)
        
        # Combo de presets
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems([
            "Full Song", "2 Minutes", "1 Minute", "30 Seconds", "16 Beats", "8 Beats"
        ])
        self.zoom_combo.currentTextChanged.connect(self.on_preset_changed)
        layout.addWidget(self.zoom_combo)
        
        # Botones
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_zoom)
        layout.addWidget(reset_btn)
    
    def on_zoom_changed(self, value):
        zoom_level = value / 10.0  # Convertir a factor real
        self.zoom_changed.emit(zoom_level)
    
    def on_preset_changed(self, preset):
        zoom_levels = {
            "Full Song": 1.0,
            "2 Minutes": 2.5,
            "1 Minute": 5.0,
            "30 Seconds": 10.0,
            "16 Beats": 15.0,
            "8 Beats": 20.0
        }
        
        if preset in zoom_levels:
            zoom_level = zoom_levels[preset]
            self.zoom_slider.setValue(int(zoom_level * 10))
    
    def reset_zoom(self):
        self.zoom_slider.setValue(10)
        self.zoom_combo.setCurrentText("Full Song")

def test_advanced_waveform():
    """Test del widget avanzado."""
    
    app = QApplication(sys.argv)
    
    # Crear ventana de prueba
    window = QWidget()
    window.setWindowTitle("🎯 Advanced Waveform Test")
    window.setGeometry(100, 100, 1000, 200)
    
    layout = QVBoxLayout(window)
    
    # Widget de waveform
    waveform = AdvancedWaveformWidget()
    layout.addWidget(waveform)
    
    # Controles de zoom
    zoom_control = ZoomControlWidget()
    zoom_control.zoom_changed.connect(waveform.set_zoom)
    layout.addWidget(zoom_control)
    
    # Simular algunos cue points
    class MockCue:
        def __init__(self, pos, name, color, hotcue):
            self.position = pos
            self.name = name
            self.color = color
            self.hotcue_index = hotcue
    
    mock_cues = [
        MockCue(30, "Intro", "#FF0000", 1),
        MockCue(65, "Drop", "#00FF00", 2),
        MockCue(120, "Breakdown", "#0000FF", 3),
        MockCue(180, "Build", "#FFFF00", 4),
    ]
    
    waveform.set_cue_points(mock_cues, 240)
    
    window.show()
    
    print("🎯 Advanced Waveform Test")
    print("Features:")
    print("- Mouse wheel: Zoom in/out")
    print("- Click: Jump to position")
    print("- Hover: Show time info")
    print("- Red borders: Cue points not on downbeat")
    print("- Green borders: Cue points on downbeat")
    print("- Yellow dots: Suggested positions")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_advanced_waveform()
