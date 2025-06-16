#!/usr/bin/env python3
"""
🎯 DjAlfin - Serato Style Compact (13" Mac)
Interfaz optimizada para MacBook de 13 pulgadas
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QListWidget, QPushButton, QFrame,
                             QSplitter, QGridLayout, QTabWidget, QSlider, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPolygon, QLinearGradient
from basic_metadata_reader import BasicMetadataReader
from audio_player import AudioPlayerWidget
import math
import random

class SeratoProWaveformWidget(QWidget):
    """Widget avanzado de waveform compacto para 13 pulgadas."""

    def __init__(self):
        super().__init__()
        self.cue_points = []
        self.duration = 300
        self.current_position = 0
        self.zoom_level = 1.0
        self.zoom_center = 0.5
        self.setMinimumHeight(120)
        self.setMaximumHeight(120)

        # Datos de análisis estilo Serato Pro
        self.beats = []
        self.downbeats = []
        self.energy_levels = []  # Niveles de energía por sección (1-10)
        self.spectral_data = []  # Datos espectrales para colores

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)

        # Interacción
        self.setMouseTracking(True)
        self.mouse_pos = None

    def generate_simulated_analysis(self):
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
        self.generate_simulated_analysis()

        # Calcular energía para cada cue point
        for cue in self.cue_points:
            energy_level = self.get_energy_at_position(cue.position)
            cue.energy_level = energy_level

        self.update()

    def get_energy_at_position(self, position):
        """Obtener nivel de energía en una posición específica."""
        if not hasattr(self, 'energy_levels') or not self.energy_levels:
            return 5

        # Mapear posición a índice de energía
        section_duration = self.duration / len(self.energy_levels)
        section_index = int(position / section_duration)
        section_index = max(0, min(len(self.energy_levels) - 1, section_index))

        return self.energy_levels[section_index]

    def get_spectral_color(self, position, amplitude):
        """Obtener color basado en análisis espectral."""
        if not hasattr(self, 'spectral_data') or not self.spectral_data:
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

    def set_zoom(self, zoom_level, center=None):
        """Establecer zoom."""
        self.zoom_level = max(1.0, min(10.0, zoom_level))
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
        self.timer.start(50)

    def stop_playback(self):
        self.timer.stop()

    def update_position(self):
        self.current_position += 0.05
        if self.current_position >= self.duration:
            self.current_position = 0

        # Auto-seguimiento en zoom
        if self.zoom_level > 1.0:
            self.zoom_center = self.current_position / self.duration

        self.update()

    def mousePressEvent(self, event):
        """Manejar clic."""
        if event.button() == Qt.LeftButton:
            start_time, end_time = self.get_time_range()
            relative_x = event.x() / self.width()
            clicked_time = start_time + (end_time - start_time) * relative_x
            self.current_position = clicked_time
            self.update()

    def wheelEvent(self, event):
        """Manejar zoom."""
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
        """Dibujar waveform avanzada compacta."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        start_time, end_time = self.get_time_range()

        # Fondo con gradiente
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(15, 15, 15))
        gradient.setColorAt(1, QColor(25, 25, 25))
        painter.fillRect(0, 0, width, height, QBrush(gradient))

        # Grid de tiempo (simplificado)
        self.draw_time_grid(painter, start_time, end_time, width, height)

        # Waveform principal
        self.draw_waveform(painter, start_time, end_time, width, height)

        # Beats y downbeats
        self.draw_beats(painter, start_time, end_time, width, height)

        # Cue points con análisis
        self.draw_cue_points_analyzed(painter, start_time, end_time, width, height)

        # Posición actual
        self.draw_playhead(painter, start_time, end_time, width, height)

        # Info del mouse
        if self.mouse_pos:
            self.draw_mouse_info(painter, start_time, end_time, width, height)

        # Info de zoom
        if self.zoom_level > 1.0:
            self.draw_zoom_info(painter, width, height)

    def draw_time_grid(self, painter, start_time, end_time, width, height):
        """Grid de tiempo simplificado."""
        painter.setPen(QPen(QColor(40, 40, 40), 1))

        visible_duration = end_time - start_time
        if visible_duration > 30:
            interval = 10
        elif visible_duration > 10:
            interval = 5
        else:
            interval = 1

        first_mark = math.ceil(start_time / interval) * interval
        current_mark = first_mark

        while current_mark <= end_time:
            x = int((current_mark - start_time) / (end_time - start_time) * width)
            painter.drawLine(x, 0, x, height)
            current_mark += interval

    def draw_waveform(self, painter, start_time, end_time, width, height):
        """Waveform con colores espectrales como Serato DJ Pro."""

        y_center = height // 2

        # Dibujar cada píxel con color espectral
        for x in range(width):
            time_pos = start_time + (end_time - start_time) * (x / width)

            # Obtener amplitud simulada
            if hasattr(self, 'spectral_data') and self.spectral_data:
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

    def draw_beats(self, painter, start_time, end_time, width, height):
        """Beats y downbeats."""
        # Downbeats
        painter.setPen(QPen(QColor(255, 255, 0, 120), 2))
        for downbeat in self.downbeats:
            if start_time <= downbeat <= end_time:
                x = int((downbeat - start_time) / (end_time - start_time) * width)
                painter.drawLine(x, 0, x, height)

        # Beats regulares (solo en zoom alto)
        if self.zoom_level > 3.0:
            painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
            for beat in self.beats:
                if start_time <= beat <= end_time:
                    x = int((beat - start_time) / (end_time - start_time) * width)
                    painter.drawLine(x, height//3, x, 2*height//3)

    def draw_cue_points_analyzed(self, painter, start_time, end_time, width, height):
        """Cue points con análisis de downbeat."""
        for cue in self.cue_points:
            if start_time <= cue.position <= end_time:
                x = int((cue.position - start_time) / (end_time - start_time) * width)

                try:
                    color = QColor(cue.color)
                except:
                    color = QColor(255, 0, 0)

                # Verificar si está en downbeat
                is_on_downbeat = any(abs(cue.position - db) < 0.1 for db in self.downbeats)

                if is_on_downbeat:
                    # Correcto - borde verde
                    painter.setPen(QPen(QColor(0, 255, 0), 2))
                else:
                    # Incorrecto - borde rojo
                    painter.setPen(QPen(QColor(255, 0, 0), 2))

                painter.setBrush(QBrush(color))

                # Línea vertical
                painter.drawLine(x, 0, x, height)

                # Círculo
                painter.drawEllipse(x - 3, 2, 6, 6)

                # Número de hot cue
                if cue.hotcue_index > 0:
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    painter.setFont(QFont("Arial", 7, QFont.Bold))
                    painter.drawText(x - 2, 16, str(cue.hotcue_index))

                # Sugerencia si no está en downbeat
                if not is_on_downbeat and self.zoom_level > 2.0:
                    nearest_db = min(self.downbeats, key=lambda db: abs(db - cue.position))
                    if abs(nearest_db - cue.position) < 1.0:
                        db_x = int((nearest_db - start_time) / (end_time - start_time) * width)

                        # Línea punteada
                        painter.setPen(QPen(QColor(255, 255, 0), 1, Qt.DashLine))
                        painter.drawLine(x, height//2, db_x, height//2)

                        # Punto sugerido
                        painter.setPen(QPen(QColor(255, 255, 0), 1))
                        painter.setBrush(QBrush(QColor(255, 255, 0, 100)))
                        painter.drawEllipse(db_x - 2, height//2 - 2, 4, 4)

    def draw_playhead(self, painter, start_time, end_time, width, height):
        """Línea de reproducción."""
        if start_time <= self.current_position <= end_time:
            x = int((self.current_position - start_time) / (end_time - start_time) * width)

            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(x, 0, x, height)

            # Triángulo
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            triangle = QPolygon([
                QPoint(x, 0),
                QPoint(x - 3, 8),
                QPoint(x + 3, 8)
            ])
            painter.drawPolygon(triangle)

    def draw_mouse_info(self, painter, start_time, end_time, width, height):
        """Info del mouse."""
        mouse_x = self.mouse_pos.x()
        mouse_time = start_time + (end_time - start_time) * (mouse_x / width)

        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawLine(mouse_x, 0, mouse_x, height)

        minutes = int(mouse_time // 60)
        seconds = int(mouse_time % 60)
        time_text = f"{minutes}:{seconds:02d}"

        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        text_rect = QRect(mouse_x + 3, 2, 35, 12)
        painter.drawRect(text_rect)

        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 7))
        painter.drawText(text_rect, Qt.AlignCenter, time_text)

    def draw_zoom_info(self, painter, width, height):
        """Info de zoom."""
        zoom_text = f"{self.zoom_level:.1f}x"

        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        text_rect = QRect(width - 35, height - 15, 30, 12)
        painter.drawRect(text_rect)

        painter.setPen(QPen(QColor(0, 212, 255), 1))
        painter.setFont(QFont("Arial", 7, QFont.Bold))
        painter.drawText(text_rect, Qt.AlignCenter, zoom_text)

class SeratoProHotCueButton(QPushButton):
    """Hot cue button exacto como Serato DJ Pro."""

    def __init__(self, number):
        super().__init__()
        self.number = number
        self.cue_point = None
        self.energy_level = 5
        self.setFixedSize(75, 45)  # Tamaño Serato
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
                font-size: 10px;
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

            # Estilo con gradiente como Serato
            darker_color = self.darken_color(color)
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {color}, stop:1 {darker_color});
                    border: 2px solid {color};
                    border-radius: 6px;
                    color: {text_color};
                    font-weight: bold;
                    font-size: 8px;
                }}
                QPushButton:hover {{
                    border-color: #FFFFFF;
                    border-width: 3px;
                }}
                QPushButton:pressed {{
                    background: {color};
                }}
            """)

            # Texto como Serato: "▶ Energy X"
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

class SeratoCompact13Inch(QMainWindow):
    """Interfaz compacta para MacBook 13 pulgadas."""
    
    def __init__(self):
        super().__init__()
        self.audio_folder = "/Volumes/KINGSTON/Audio"
        self.metadata_reader = BasicMetadataReader()
        self.files_with_cues = []
        self.current_file = None

        # Reproductor de audio (se inicializa después de crear la UI)
        self.audio_player = None

        self.init_ui()
        self.setup_audio_player()
        self.load_files_with_cues()
    
    def init_ui(self):
        """Inicializar UI optimizada para 13 pulgadas."""
        
        self.setWindowTitle("🎯 DjAlfin - Compact (13\")")
        
        # Tamaño optimizado para 13 pulgadas (1280x800 típico)
        self.setGeometry(50, 50, 1200, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(3)
        
        # Panel izquierdo - Lista de tracks (más estrecho)
        self.create_compact_track_list(main_layout)
        
        # Panel derecho - Deck compacto
        self.create_compact_deck(main_layout)
        
        self.apply_compact_style()

    def setup_audio_player(self):
        """Configurar reproductor de audio."""
        try:
            self.audio_player = AudioPlayerWidget(self.waveform)
            print("🎵 Audio player initialized")
        except Exception as e:
            print(f"⚠️ Audio player setup failed: {e}")
            self.audio_player = None

    def create_compact_track_list(self, parent_layout):
        """Lista compacta de tracks."""
        
        track_widget = QWidget()
        track_widget.setFixedWidth(300)  # Más estrecho
        track_layout = QVBoxLayout(track_widget)
        track_layout.setContentsMargins(3, 3, 3, 3)
        track_layout.setSpacing(3)
        
        # Título compacto
        title_label = QLabel("🎵 TRACKS WITH CUES")
        title_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
                background-color: #1a1a1a;
                border-radius: 3px;
            }
        """)
        title_label.setFixedHeight(25)
        track_layout.addWidget(title_label)
        
        # Lista compacta
        self.track_list = QListWidget()
        self.track_list.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #333;
                font-size: 10px;
                selection-background-color: #00d4ff;
                selection-color: #000000;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #222;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        self.track_list.itemClicked.connect(self.on_track_selected)
        track_layout.addWidget(self.track_list)
        
        # Botón compacto
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.setFixedHeight(30)
        reload_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #000000;
                border: none;
                padding: 5px;
                font-weight: bold;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #00b8e6;
            }
        """)
        reload_btn.clicked.connect(self.load_files_with_cues)
        track_layout.addWidget(reload_btn)
        
        parent_layout.addWidget(track_widget)
    
    def create_compact_deck(self, parent_layout):
        """Deck compacto para 13 pulgadas."""
        
        deck_widget = QWidget()
        deck_layout = QVBoxLayout(deck_widget)
        deck_layout.setContentsMargins(3, 3, 3, 3)
        deck_layout.setSpacing(3)
        
        # Info del track compacta
        self.create_compact_track_info(deck_layout)
        
        # Tabs para organizar mejor el espacio
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px 15px;
                margin-right: 2px;
                border-radius: 3px 3px 0px 0px;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #00d4ff;
                color: #000000;
            }
            QTabBar::tab:hover {
                background-color: #333;
            }
        """)
        
        # Tab 1: Waveform y Hot Cues
        waveform_tab = QWidget()
        waveform_layout = QVBoxLayout(waveform_tab)
        waveform_layout.setContentsMargins(5, 5, 5, 5)
        waveform_layout.setSpacing(5)
        
        self.create_compact_waveform(waveform_layout)
        self.create_zoom_controls(waveform_layout)
        self.create_compact_hotcues(waveform_layout)
        self.create_compact_controls(waveform_layout)
        
        tabs.addTab(waveform_tab, "🌊 Waveform")
        
        # Tab 2: Lista de Cue Points
        cues_tab = QWidget()
        cues_layout = QVBoxLayout(cues_tab)
        cues_layout.setContentsMargins(5, 5, 5, 5)
        
        self.create_compact_cue_list(cues_layout)
        
        tabs.addTab(cues_tab, "🎯 Cue List")
        
        deck_layout.addWidget(tabs)
        parent_layout.addWidget(deck_widget)
    
    def create_compact_track_info(self, parent_layout):
        """Info compacta del track."""
        
        info_frame = QFrame()
        info_frame.setFixedHeight(50)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 3px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(5, 3, 5, 3)
        info_layout.setSpacing(1)
        
        self.track_title_label = QLabel("Select a track")
        self.track_title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        self.track_title_label.setWordWrap(True)
        info_layout.addWidget(self.track_title_label)
        
        self.track_details_label = QLabel("")
        self.track_details_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 9px;
                background: transparent;
            }
        """)
        info_layout.addWidget(self.track_details_label)
        
        parent_layout.addWidget(info_frame)
    
    def create_compact_waveform(self, parent_layout):
        """Waveform compacta."""
        
        wave_frame = QFrame()
        wave_frame.setFixedHeight(140)
        wave_frame.setStyleSheet("""
            QFrame {
                background-color: #0a0a0a;
                border: 1px solid #333;
                border-radius: 3px;
            }
        """)
        
        wave_layout = QVBoxLayout(wave_frame)
        wave_layout.setContentsMargins(3, 3, 3, 3)
        wave_layout.setSpacing(2)
        
        wave_title = QLabel("🌊 WAVEFORM")
        wave_title.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }
        """)
        wave_title.setFixedHeight(15)
        wave_layout.addWidget(wave_title)
        
        self.waveform = SeratoProWaveformWidget()
        wave_layout.addWidget(self.waveform)
        
        parent_layout.addWidget(wave_frame)

    def create_zoom_controls(self, parent_layout):
        """Controles de zoom compactos."""

        zoom_frame = QFrame()
        zoom_frame.setFixedHeight(35)
        zoom_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 3px;
            }
        """)

        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(5, 3, 5, 3)
        zoom_layout.setSpacing(5)

        # Label
        zoom_label = QLabel("🔍")
        zoom_label.setStyleSheet("color: #00d4ff; font-weight: bold;")
        zoom_layout.addWidget(zoom_label)

        # Botones de zoom rápido
        zoom_out_btn = QPushButton("1x")
        zoom_out_btn.setFixedSize(25, 25)
        zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 8px;
            }
            QPushButton:hover { background-color: #555; }
            QPushButton:pressed { background-color: #00d4ff; color: black; }
        """)
        zoom_out_btn.clicked.connect(lambda: self.waveform.set_zoom(1.0))
        zoom_layout.addWidget(zoom_out_btn)

        zoom_2x_btn = QPushButton("2x")
        zoom_2x_btn.setFixedSize(25, 25)
        zoom_2x_btn.setStyleSheet(zoom_out_btn.styleSheet())
        zoom_2x_btn.clicked.connect(lambda: self.waveform.set_zoom(2.0))
        zoom_layout.addWidget(zoom_2x_btn)

        zoom_5x_btn = QPushButton("5x")
        zoom_5x_btn.setFixedSize(25, 25)
        zoom_5x_btn.setStyleSheet(zoom_out_btn.styleSheet())
        zoom_5x_btn.clicked.connect(lambda: self.waveform.set_zoom(5.0))
        zoom_layout.addWidget(zoom_5x_btn)

        zoom_layout.addStretch()

        # Info de análisis
        self.analysis_label = QLabel("🎯 Analysis: Ready")
        self.analysis_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 8px;
                background: transparent;
            }
        """)
        zoom_layout.addWidget(self.analysis_label)

        parent_layout.addWidget(zoom_frame)

    def create_compact_hotcues(self, parent_layout):
        """Hot cues compactos."""
        
        hotcues_frame = QFrame()
        hotcues_frame.setFixedHeight(100)
        hotcues_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 3px;
            }
        """)
        
        hotcues_layout = QVBoxLayout(hotcues_frame)
        hotcues_layout.setContentsMargins(3, 3, 3, 3)
        hotcues_layout.setSpacing(2)
        
        hotcues_title = QLabel("🔥 HOT CUES")
        hotcues_title.setStyleSheet("""
            QLabel {
                color: #ff6600;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }
        """)
        hotcues_title.setFixedHeight(15)
        hotcues_layout.addWidget(hotcues_title)
        
        # Grid compacto 2x4
        hotcues_grid = QGridLayout()
        hotcues_grid.setSpacing(2)
        self.hotcue_buttons = {}
        
        for i in range(8):
            row = i // 4
            col = i % 4
            
            hotcue_btn = SeratoProHotCueButton(i + 1)
            hotcue_btn.clicked.connect(lambda _, idx=i+1: self.on_hotcue_clicked(idx))
            
            self.hotcue_buttons[i + 1] = hotcue_btn
            hotcues_grid.addWidget(hotcue_btn, row, col)
        
        hotcues_layout.addLayout(hotcues_grid)
        parent_layout.addWidget(hotcues_frame)
    
    def create_compact_controls(self, parent_layout):
        """Controles compactos."""
        
        controls_frame = QFrame()
        controls_frame.setFixedHeight(45)
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 3px;
            }
        """)
        
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        controls_layout.setSpacing(5)
        
        self.play_btn = QPushButton("▶️ PLAY")
        self.play_btn.setFixedSize(80, 35)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #000000;
                border: none;
                font-weight: bold;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #00b8e6;
            }
            QPushButton:pressed {
                background-color: #0099cc;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)

        # Botón STOP
        self.stop_btn = QPushButton("⏹️ STOP")
        self.stop_btn.setFixedSize(60, 35)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: #ffffff;
                border: none;
                font-weight: bold;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
            QPushButton:pressed {
                background-color: #cc3333;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_playback)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()

        # BPM Display
        self.bpm_label = QLabel("120.0 BPM")
        self.bpm_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }
        """)
        controls_layout.addWidget(self.bpm_label)

        # Volume indicator
        self.volume_label = QLabel("🔊 75%")
        self.volume_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 9px;
                background: transparent;
            }
        """)
        controls_layout.addWidget(self.volume_label)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                background: transparent;
            }
        """)
        controls_layout.addWidget(self.time_label)
        
        parent_layout.addWidget(controls_frame)
    
    def create_compact_cue_list(self, parent_layout):
        """Lista compacta de cue points."""
        
        self.cue_details_list = QListWidget()
        self.cue_details_list.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #333;
                font-size: 9px;
                font-family: 'Courier New', monospace;
            }
            QListWidget::item {
                padding: 2px;
                border-bottom: 1px solid #222;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        parent_layout.addWidget(self.cue_details_list)
    
    def apply_compact_style(self):
        """Estilo compacto general."""
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
                color: #ffffff;
            }
        """)
    
    def load_files_with_cues(self):
        """Cargar archivos con cue points."""
        
        self.track_list.clear()
        self.files_with_cues = []
        
        if not os.path.exists(self.audio_folder):
            return
        
        try:
            all_items = os.listdir(self.audio_folder)
            audio_extensions = ['.mp3', '.m4a', '.flac', '.wav']
            
            for item in all_items:
                if not item.startswith('.'):
                    _, ext = os.path.splitext(item)
                    if ext.lower() in audio_extensions:
                        file_path = os.path.join(self.audio_folder, item)
                        
                        try:
                            metadata = self.metadata_reader.scan_file(file_path)
                            cue_points = metadata.get('cue_points', [])
                            
                            if cue_points:
                                file_size = os.path.getsize(file_path) / (1024 * 1024)
                                
                                file_info = {
                                    'filename': item,
                                    'path': file_path,
                                    'size_mb': file_size,
                                    'format': ext.upper().replace('.', ''),
                                    'cue_points': cue_points,
                                    'software': cue_points[0].software.title()
                                }
                                
                                self.files_with_cues.append(file_info)
                                
                                # Texto compacto
                                display_text = f"🎵 {item[:35]}{'...' if len(item) > 35 else ''}\n"
                                display_text += f"   {len(cue_points)} cues • {file_info['software']}"
                                
                                self.track_list.addItem(display_text)
                        
                        except Exception as e:
                            continue
            
            print(f"✅ Loaded {len(self.files_with_cues)} tracks with cue points")
            
        except Exception as e:
            print(f"❌ Error loading files: {e}")
    
    def on_track_selected(self, item):
        """Manejar selección de track."""
        
        row = self.track_list.row(item)
        if 0 <= row < len(self.files_with_cues):
            self.current_file = self.files_with_cues[row]
            self.load_track_cues()
    
    def load_track_cues(self):
        """Cargar cue points del track."""
        
        if not self.current_file:
            return
        
        filename = self.current_file['filename']
        cue_points = self.current_file['cue_points']
        
        # Actualizar info (texto más corto)
        short_name = filename[:40] + '...' if len(filename) > 40 else filename
        self.track_title_label.setText(short_name)
        self.track_details_label.setText(f"{len(cue_points)} cues • {self.current_file['software']}")
        
        # Actualizar waveform
        max_position = max([cue.position for cue in cue_points]) if cue_points else 300
        duration = max(max_position + 30, 300)
        self.waveform.set_cue_points(cue_points, duration)
        
        # Actualizar hot cues
        for i in range(1, 9):
            self.hotcue_buttons[i].set_cue_point(None)
        
        for cue in cue_points:
            if 1 <= cue.hotcue_index <= 8:
                self.hotcue_buttons[cue.hotcue_index].set_cue_point(cue)
        
        # Actualizar lista con análisis
        self.cue_details_list.clear()
        on_downbeat_count = 0

        for i, cue in enumerate(cue_points):
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)

            # Verificar si está en downbeat
            is_on_downbeat = any(abs(cue.position - db) < 0.1 for db in self.waveform.downbeats)
            if is_on_downbeat:
                on_downbeat_count += 1
                status = "✅"
            else:
                status = "❌"

            detail_text = f"{status} {i+1:2d}. {cue.name[:12]:<12} {minutes:02d}:{seconds:02d} H{cue.hotcue_index} {cue.color[:7]}"
            self.cue_details_list.addItem(detail_text)

        # Actualizar análisis
        total_cues = len(cue_points)
        if total_cues > 0:
            accuracy = (on_downbeat_count / total_cues) * 100
            self.analysis_label.setText(f"🎯 Analysis: {on_downbeat_count}/{total_cues} on downbeat ({accuracy:.0f}%)")
        else:
            self.analysis_label.setText("🎯 Analysis: No cue points")
        
        # Actualizar tiempo
        total_minutes = int(duration // 60)
        total_seconds = int(duration % 60)
        self.time_label.setText(f"00:00/{total_minutes:02d}:{total_seconds:02d}")

        # Actualizar BPM (estimado basado en beats simulados)
        if len(self.waveform.beats) > 4:
            # Calcular BPM promedio de los primeros beats
            intervals = []
            for i in range(1, min(5, len(self.waveform.beats))):
                interval = self.waveform.beats[i] - self.waveform.beats[i-1]
                intervals.append(interval)

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                estimated_bpm = 60.0 / avg_interval
                self.bpm_label.setText(f"{estimated_bpm:.1f} BPM")
            else:
                self.bpm_label.setText("120.0 BPM")
        else:
            self.bpm_label.setText("120.0 BPM")

        print(f"✅ Loaded: {filename} ({len(cue_points)} cues)")
    
    def on_hotcue_clicked(self, hotcue_number):
        """Manejar clic en hot cue con reproducción real."""

        button = self.hotcue_buttons[hotcue_number]
        if button.cue_point:
            cue = button.cue_point
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            print(f"🎯 Hot Cue {hotcue_number}: {cue.name} @ {minutes}:{seconds:02d}")

            # Saltar en el reproductor real
            if self.audio_player and self.current_file:
                # Cargar archivo si es necesario
                if self.audio_player.current_file_path != self.current_file['path']:
                    self.audio_player.load_track(self.current_file['path'])

                # Saltar a la posición del cue
                self.audio_player.seek_to_cue(cue.position)

            # Actualizar visualización
            self.waveform.current_position = cue.position
            self.waveform.update()

            # Actualizar tiempo mostrado
            total_minutes = int(self.waveform.duration // 60)
            total_seconds = int(self.waveform.duration % 60)
            self.time_label.setText(f"{minutes:02d}:{seconds:02d} / {total_minutes:02d}:{total_seconds:02d}")
    
    def toggle_playback(self):
        """Alternar reproducción real."""

        if not self.current_file:
            print("❌ No track loaded")
            return

        if self.audio_player:
            # Cargar archivo si es necesario
            if self.audio_player.current_file_path != self.current_file['path']:
                success = self.audio_player.load_track(self.current_file['path'])
                if not success:
                    print("❌ Failed to load track for playback")
                    return

            # Alternar reproducción
            if self.play_btn.text() == "▶️ PLAY":
                self.play_btn.setText("⏸️ PAUSE")
                self.audio_player.play_pause()
                self.waveform.start_playback()  # Mantener simulación visual
            else:
                self.play_btn.setText("▶️ PLAY")
                self.audio_player.play_pause()
                self.waveform.stop_playback()
        else:
            # Fallback a simulación
            if self.play_btn.text() == "▶️ PLAY":
                self.play_btn.setText("⏸️ PAUSE")
                self.waveform.start_playback()
            else:
                self.play_btn.setText("▶️ PLAY")
                self.waveform.stop_playback()

    def stop_playback(self):
        """Detener reproducción."""

        if self.audio_player:
            self.audio_player.stop()

        self.waveform.stop_playback()
        self.waveform.current_position = 0
        self.waveform.update()

        self.play_btn.setText("▶️ PLAY")
        self.time_label.setText("00:00 / 00:00")

        print("⏹️ Playback stopped")

def main():
    """Función principal."""
    
    app = QApplication(sys.argv)
    app.setApplicationName("DjAlfin Compact 13\"")
    
    window = SeratoCompact13Inch()
    window.show()
    
    print("🎯 DjAlfin Compact for 13\" MacBook")
    print("Optimized interface for smaller screens")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
