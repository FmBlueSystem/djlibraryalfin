#!/usr/bin/env python3
"""
🎯 DjAlfin - Serato Pro Style Interface
Interfaz exacta como Serato DJ Pro con colores de energía y hot cues
"""

import sys
import os
import math
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QListWidget, QPushButton, QFrame,
                             QGridLayout, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPolygon, QLinearGradient
from basic_metadata_reader import BasicMetadataReader
from audio_player import AudioPlayerWidget

class SeratoProWaveformWidget(QWidget):
    """Waveform exacto como Serato DJ Pro con colores de energía."""
    
    def __init__(self):
        super().__init__()
        self.cue_points = []
        self.duration = 300
        self.current_position = 0
        self.zoom_level = 1.0
        self.zoom_center = 0.5
        self.setMinimumHeight(150)
        self.setMaximumHeight(150)
        
        # Datos de análisis
        self.beats = []
        self.downbeats = []
        self.energy_levels = []  # Niveles de energía por sección
        self.spectral_data = []  # Datos espectrales para colores
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        
        self.setMouseTracking(True)
        self.mouse_pos = None
        
    def generate_serato_analysis(self):
        """Generar análisis estilo Serato DJ Pro."""
        if self.duration <= 0:
            return
            
        # Generar beats
        self.beats = []
        self.downbeats = []
        beat_interval = 0.5  # 120 BPM
        current_time = 0
        beat_count = 0
        
        while current_time < self.duration:
            self.beats.append(current_time)
            if beat_count % 4 == 0:
                self.downbeats.append(current_time)
            current_time += beat_interval + random.uniform(-0.02, 0.02)
            beat_count += 1
        
        # Generar niveles de energía (1-10 como Serato)
        self.energy_levels = []
        sections = 50  # Dividir en secciones
        for i in range(sections):
            # Simular variación de energía realista
            base_energy = 4 + 3 * math.sin(i * 0.3) + random.uniform(-1, 1)
            energy = max(1, min(10, int(base_energy)))
            self.energy_levels.append(energy)
        
        # Generar datos espectrales para colores
        self.spectral_data = []
        points = 200
        for i in range(points):
            t = (i / points) * self.duration
            
            # Simular análisis espectral
            low_freq = 0.3 + 0.4 * math.sin(t * 0.1) + random.uniform(-0.1, 0.1)
            mid_freq = 0.4 + 0.3 * math.sin(t * 0.15) + random.uniform(-0.1, 0.1)
            high_freq = 0.2 + 0.5 * math.sin(t * 0.2) + random.uniform(-0.1, 0.1)
            
            # Normalizar
            total = low_freq + mid_freq + high_freq
            if total > 0:
                low_freq /= total
                mid_freq /= total
                high_freq /= total
            
            self.spectral_data.append({
                'low': max(0, min(1, low_freq)),
                'mid': max(0, min(1, mid_freq)),
                'high': max(0, min(1, high_freq)),
                'energy': random.uniform(0.2, 1.0)
            })
    
    def set_cue_points(self, cue_points, duration=300):
        """Establecer cue points con análisis de energía."""
        self.cue_points = cue_points
        self.duration = duration
        self.current_position = 0
        self.generate_serato_analysis()
        
        # Calcular energía para cada cue point
        for cue in self.cue_points:
            energy_level = self.get_energy_at_position(cue.position)
            cue.energy_level = energy_level
        
        self.update()
    
    def get_energy_at_position(self, position):
        """Obtener nivel de energía en una posición específica."""
        if not self.energy_levels:
            return 5
        
        # Mapear posición a índice de energía
        section_duration = self.duration / len(self.energy_levels)
        section_index = int(position / section_duration)
        section_index = max(0, min(len(self.energy_levels) - 1, section_index))
        
        return self.energy_levels[section_index]
    
    def get_spectral_color(self, position, amplitude):
        """Obtener color basado en análisis espectral."""
        if not self.spectral_data:
            return QColor(0, 150, 255)
        
        # Mapear posición a datos espectrales
        data_index = int((position / self.duration) * len(self.spectral_data))
        data_index = max(0, min(len(self.spectral_data) - 1, data_index))
        
        spectral = self.spectral_data[data_index]
        
        # Colores basados en frecuencias (como Serato)
        if spectral['low'] > 0.5:
            # Graves dominantes - Rosa/Magenta
            intensity = int(amplitude * 255)
            return QColor(intensity, 0, intensity // 2)
        elif spectral['high'] > 0.4:
            # Agudos dominantes - Azul
            intensity = int(amplitude * 255)
            return QColor(0, intensity // 2, intensity)
        else:
            # Medios dominantes - Naranja/Rojo
            intensity = int(amplitude * 255)
            return QColor(intensity, intensity // 2, 0)
    
    def get_time_range(self):
        """Obtener rango de tiempo visible."""
        if self.zoom_level == 1.0:
            return 0, self.duration
        
        visible_duration = self.duration / self.zoom_level
        start_time = self.zoom_center * self.duration - visible_duration / 2
        start_time = max(0, min(self.duration - visible_duration, start_time))
        end_time = start_time + visible_duration
        
        return start_time, end_time
    
    def set_zoom(self, zoom_level, center=None):
        """Establecer zoom."""
        self.zoom_level = max(1.0, min(20.0, zoom_level))
        if center is not None:
            self.zoom_center = max(0.0, min(1.0, center))
        self.update()
    
    def start_playback(self):
        self.timer.start(50)
    
    def stop_playback(self):
        self.timer.stop()
    
    def update_position(self):
        self.current_position += 0.05
        if self.current_position >= self.duration:
            self.current_position = 0
        
        if self.zoom_level > 1.0:
            self.zoom_center = self.current_position / self.duration
        
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            start_time, end_time = self.get_time_range()
            relative_x = event.x() / self.width()
            clicked_time = start_time + (end_time - start_time) * relative_x
            self.current_position = clicked_time
            self.update()
    
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 1.3 if delta > 0 else 1/1.3
        
        mouse_x = event.x() / self.width()
        start_time, end_time = self.get_time_range()
        mouse_time = start_time + (end_time - start_time) * mouse_x
        new_center = mouse_time / self.duration
        
        self.set_zoom(self.zoom_level * zoom_factor, new_center)
    
    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        self.update()
    
    def leaveEvent(self, event):
        self.mouse_pos = None
        self.update()
    
    def paintEvent(self, event):
        """Dibujar waveform estilo Serato DJ Pro."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        start_time, end_time = self.get_time_range()
        
        # Fondo negro como Serato
        painter.fillRect(0, 0, width, height, QColor(20, 20, 20))
        
        # Grid de tiempo
        self.draw_time_grid(painter, start_time, end_time, width, height)
        
        # Waveform con colores espectrales
        self.draw_spectral_waveform(painter, start_time, end_time, width, height)
        
        # Downbeats (líneas blancas verticales)
        self.draw_downbeats(painter, start_time, end_time, width, height)
        
        # Cue points con análisis
        self.draw_cue_points_pro(painter, start_time, end_time, width, height)
        
        # Playhead
        self.draw_playhead(painter, start_time, end_time, width, height)
        
        # Info del mouse
        if self.mouse_pos:
            self.draw_mouse_info(painter, start_time, end_time, width, height)
    
    def draw_time_grid(self, painter, start_time, end_time, width, height):
        """Grid de tiempo sutil."""
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        
        visible_duration = end_time - start_time
        if visible_duration > 60:
            interval = 10
        elif visible_duration > 20:
            interval = 5
        else:
            interval = 1
        
        first_mark = math.ceil(start_time / interval) * interval
        current_mark = first_mark
        
        while current_mark <= end_time:
            x = int((current_mark - start_time) / (end_time - start_time) * width)
            painter.drawLine(x, 0, x, height)
            current_mark += interval
    
    def draw_spectral_waveform(self, painter, start_time, end_time, width, height):
        """Waveform con colores espectrales como Serato."""
        
        y_center = height // 2
        
        # Dibujar cada píxel con color espectral
        for x in range(width):
            time_pos = start_time + (end_time - start_time) * (x / width)
            
            # Obtener amplitud simulada
            if self.spectral_data:
                data_index = int((time_pos / self.duration) * len(self.spectral_data))
                data_index = max(0, min(len(self.spectral_data) - 1, data_index))
                amplitude = self.spectral_data[data_index]['energy']
            else:
                amplitude = random.uniform(0.3, 1.0)
            
            # Altura de la waveform
            wave_height = int(amplitude * height * 0.4)  # 40% del height máximo
            
            # Color basado en análisis espectral
            color = self.get_spectral_color(time_pos, amplitude)
            
            # Dibujar waveform superior
            painter.setPen(QPen(color, 1))
            painter.drawLine(x, y_center, x, y_center - wave_height)
            
            # Waveform inferior (más oscura)
            darker_color = QColor(color.red() // 2, color.green() // 2, color.blue() // 2)
            painter.setPen(QPen(darker_color, 1))
            painter.drawLine(x, y_center, x, y_center + wave_height)
    
    def draw_downbeats(self, painter, start_time, end_time, width, height):
        """Líneas de downbeats como Serato."""
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        
        for downbeat in self.downbeats:
            if start_time <= downbeat <= end_time:
                x = int((downbeat - start_time) / (end_time - start_time) * width)
                painter.drawLine(x, 0, x, height)
    
    def draw_cue_points_pro(self, painter, start_time, end_time, width, height):
        """Cue points estilo Serato Pro."""
        
        for cue in self.cue_points:
            if start_time <= cue.position <= end_time:
                x = int((cue.position - start_time) / (end_time - start_time) * width)
                
                try:
                    color = QColor(cue.color)
                except:
                    color = QColor(255, 0, 0)
                
                # Línea vertical del cue
                painter.setPen(QPen(color, 3))
                painter.drawLine(x, 0, x, height)
                
                # Marcador superior
                painter.setBrush(QBrush(color))
                painter.drawRect(x - 3, 0, 6, 8)
                
                # Número del hot cue
                if hasattr(cue, 'hotcue_index') and cue.hotcue_index > 0:
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    painter.setFont(QFont("Arial", 8, QFont.Bold))
                    painter.drawText(x - 4, 20, str(cue.hotcue_index))
    
    def draw_playhead(self, painter, start_time, end_time, width, height):
        """Playhead como Serato."""
        if start_time <= self.current_position <= end_time:
            x = int((self.current_position - start_time) / (end_time - start_time) * width)
            
            # Línea blanca
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(x, 0, x, height)
            
            # Triángulo superior
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            triangle = QPolygon([
                QPoint(x, 0),
                QPoint(x - 5, 12),
                QPoint(x + 5, 12)
            ])
            painter.drawPolygon(triangle)
    
    def draw_mouse_info(self, painter, start_time, end_time, width, height):
        """Info del mouse."""
        mouse_x = self.mouse_pos.x()
        mouse_time = start_time + (end_time - start_time) * (mouse_x / width)
        
        # Línea vertical
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawLine(mouse_x, 0, mouse_x, height)
        
        # Tiempo
        minutes = int(mouse_time // 60)
        seconds = int(mouse_time % 60)
        time_text = f"{minutes}:{seconds:02d}"
        
        # Fondo para texto
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
        text_rect = QRect(mouse_x + 5, 5, 40, 15)
        painter.drawRect(text_rect)
        
        # Texto
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(text_rect, Qt.AlignCenter, time_text)

class SeratoProHotCueButton(QPushButton):
    """Hot cue button exacto como Serato DJ Pro."""
    
    def __init__(self, number):
        super().__init__()
        self.number = number
        self.cue_point = None
        self.energy_level = 5
        self.setFixedSize(90, 50)
        self.setup_empty_style()
    
    def setup_empty_style(self):
        """Estilo para botón vacío."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a2a;
                border: 2px solid #444;
                border-radius: 6px;
                color: #666;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                border-color: #666;
                background-color: #333;
            }}
        """)
        self.setText(f"+")
    
    def set_cue_point(self, cue_point):
        """Asignar cue point con estilo Serato."""
        self.cue_point = cue_point
        
        if cue_point:
            try:
                color = cue_point.color
                if not color.startswith('#'):
                    color = '#FF0000'
            except:
                color = '#FF0000'
            
            # Obtener nivel de energía
            if hasattr(cue_point, 'energy_level'):
                self.energy_level = cue_point.energy_level
            else:
                self.energy_level = 5
            
            # Color de texto
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = '#000000' if brightness > 128 else '#FFFFFF'
            
            # Estilo con color y energía
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {color}, stop:1 {self.darken_color(color)});
                    border: 2px solid {color};
                    border-radius: 6px;
                    color: {text_color};
                    font-weight: bold;
                    font-size: 9px;
                }}
                QPushButton:hover {{
                    border-color: #FFFFFF;
                    border-width: 3px;
                }}
                QPushButton:pressed {{
                    background: {color};
                }}
            """)
            
            # Texto como Serato
            energy_text = f"Energy {self.energy_level}"
            self.setText(f"▶\n{energy_text}")
        else:
            self.setup_empty_style()
    
    def darken_color(self, hex_color):
        """Oscurecer color para gradiente."""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # Oscurecer 30%
            r = int(r * 0.7)
            g = int(g * 0.7)
            b = int(b * 0.7)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#333333"

def test_serato_pro_style():
    """Test del estilo Serato Pro."""
    
    app = QApplication(sys.argv)
    
    # Crear ventana de prueba
    window = QWidget()
    window.setWindowTitle("🎯 Serato DJ Pro Style Test")
    window.setGeometry(100, 100, 1200, 400)
    window.setStyleSheet("background-color: #1a1a1a;")
    
    layout = QVBoxLayout(window)
    
    # Waveform
    waveform = SeratoProWaveformWidget()
    layout.addWidget(waveform)
    
    # Hot cues
    hotcues_frame = QFrame()
    hotcues_layout = QHBoxLayout(hotcues_frame)
    
    # Crear 5 hot cues como en la imagen
    colors = ["#FF0066", "#FF6600", "#0066FF", "#FFCC00", "#00FF66"]
    energies = [6, 6, 7, 4, 8]
    
    for i in range(5):
        hotcue = SeratoProHotCueButton(i + 1)
        
        # Simular cue point
        class MockCue:
            def __init__(self, pos, color, energy):
                self.position = pos
                self.color = color
                self.energy_level = energy
                self.hotcue_index = i + 1
                self.name = f"Cue {i + 1}"
        
        mock_cue = MockCue(30 + i * 40, colors[i], energies[i])
        hotcue.set_cue_point(mock_cue)
        hotcues_layout.addWidget(hotcue)
    
    # Agregar botones vacíos
    for i in range(3):
        empty_hotcue = SeratoProHotCueButton(i + 6)
        hotcues_layout.addWidget(empty_hotcue)
    
    layout.addWidget(hotcues_frame)
    
    # Simular cue points en waveform
    mock_cues = []
    for i in range(5):
        mock_cue = type('MockCue', (), {
            'position': 30 + i * 40,
            'color': colors[i],
            'hotcue_index': i + 1,
            'name': f"Cue {i + 1}",
            'energy_level': energies[i]
        })()
        mock_cues.append(mock_cue)
    
    waveform.set_cue_points(mock_cues, 300)
    
    window.show()
    
    print("🎯 Serato DJ Pro Style Test")
    print("Features:")
    print("- Spectral waveform colors")
    print("- Energy levels on hot cues")
    print("- Professional Serato styling")
    print("- Mouse wheel: Zoom")
    print("- Click: Jump to position")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_serato_pro_style()
