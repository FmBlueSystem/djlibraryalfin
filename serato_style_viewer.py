#!/usr/bin/env python3
"""
🎯 DjAlfin - Serato Style Cue Points Viewer
Interfaz visual tipo Serato DJ para mostrar cue points
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QListWidget, QPushButton, QFrame,
                             QSplitter, QGroupBox, QGridLayout, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QBrush, QPen
from basic_metadata_reader import BasicMetadataReader

class WaveformWidget(QWidget):
    """Widget que simula la forma de onda de Serato con cue points."""
    
    def __init__(self):
        super().__init__()
        self.cue_points = []
        self.duration = 300  # 5 minutos por defecto
        self.current_position = 0
        self.setMinimumHeight(80)
        self.setMaximumHeight(80)
        
        # Timer para simular reproducción
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        
    def set_cue_points(self, cue_points, duration=300):
        """Establecer cue points y duración."""
        self.cue_points = cue_points
        self.duration = duration
        self.current_position = 0
        self.update()
    
    def start_playback(self):
        """Iniciar simulación de reproducción."""
        self.timer.start(100)  # Actualizar cada 100ms
    
    def stop_playback(self):
        """Detener simulación de reproducción."""
        self.timer.stop()
    
    def update_position(self):
        """Actualizar posición de reproducción."""
        self.current_position += 0.1
        if self.current_position >= self.duration:
            self.current_position = 0
        self.update()
    
    def paintEvent(self, event):
        """Dibujar forma de onda y cue points."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fondo oscuro tipo Serato
        painter.fillRect(0, 0, width, height, QColor(20, 20, 20))
        
        # Dibujar forma de onda simulada
        painter.setPen(QPen(QColor(0, 150, 255), 1))
        import random
        random.seed(42)  # Para consistencia
        
        for x in range(0, width, 2):
            wave_height = random.randint(10, height - 20)
            y_center = height // 2
            painter.drawLine(x, y_center - wave_height//2, x, y_center + wave_height//2)
        
        # Dibujar cue points
        for cue in self.cue_points:
            if cue.position <= self.duration:
                x_pos = int((cue.position / self.duration) * width)
                
                # Color del cue point
                try:
                    color = QColor(cue.color)
                except:
                    color = QColor(255, 0, 0)
                
                # Línea vertical del cue point
                painter.setPen(QPen(color, 3))
                painter.drawLine(x_pos, 0, x_pos, height)
                
                # Círculo en la parte superior
                painter.setBrush(QBrush(color))
                painter.drawEllipse(x_pos - 4, 2, 8, 8)
                
                # Número del hot cue
                if cue.hotcue_index > 0:
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    painter.setFont(QFont("Arial", 8, QFont.Bold))
                    painter.drawText(x_pos - 3, 18, str(cue.hotcue_index))
        
        # Dibujar posición actual de reproducción
        if self.duration > 0:
            current_x = int((self.current_position / self.duration) * width)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(current_x, 0, current_x, height)

class HotCueButton(QPushButton):
    """Botón de hot cue estilo Serato."""
    
    def __init__(self, number):
        super().__init__()
        self.number = number
        self.cue_point = None
        self.setFixedSize(80, 60)
        self.setup_style()
    
    def setup_style(self):
        """Configurar estilo del botón."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a2a;
                border: 2px solid #444;
                border-radius: 8px;
                color: #888;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: #666;
                background-color: #333;
            }}
            QPushButton:pressed {{
                background-color: #555;
            }}
        """)
        self.setText(str(self.number))
    
    def set_cue_point(self, cue_point):
        """Asignar cue point al botón."""
        self.cue_point = cue_point
        
        if cue_point:
            # Obtener color
            try:
                color = cue_point.color
                if not color.startswith('#'):
                    color = '#FF0000'
            except:
                color = '#FF0000'
            
            # Calcular color de texto (claro u oscuro)
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = '#000000' if brightness > 128 else '#FFFFFF'
            
            # Aplicar estilo con color
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid {color};
                    border-radius: 8px;
                    color: {text_color};
                    font-weight: bold;
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    border-color: #FFFFFF;
                }}
                QPushButton:pressed {{
                    background-color: {color};
                    border-color: #FFFFFF;
                }}
            """)
            
            # Texto del botón
            minutes = int(cue_point.position // 60)
            seconds = int(cue_point.position % 60)
            self.setText(f"{self.number}\n{cue_point.name[:8]}\n{minutes}:{seconds:02d}")
        else:
            self.setup_style()
            self.setText(str(self.number))

class SeratoStyleViewer(QMainWindow):
    """Visor de cue points estilo Serato DJ."""
    
    def __init__(self):
        super().__init__()
        self.audio_folder = "/Volumes/KINGSTON/Audio"
        self.metadata_reader = BasicMetadataReader()
        self.files_with_cues = []
        self.current_file = None
        
        self.init_ui()
        self.load_files_with_cues()
    
    def init_ui(self):
        """Inicializar interfaz de usuario."""

        self.setWindowTitle("🎯 DjAlfin - Serato Style Cue Viewer")
        self.setGeometry(100, 100, 1600, 1000)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Header estilo Serato
        self.create_header(main_layout)

        # Área principal con splitter
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setSizes([400, 1200])  # Proporción 1:3
        main_layout.addWidget(content_splitter)

        # Panel izquierdo - Lista de tracks
        self.create_track_list(content_splitter)

        # Panel derecho - Deck y cue points
        self.create_deck_panel(content_splitter)

        # Aplicar tema Serato
        self.apply_serato_style()
    
    def create_header(self, parent_layout):
        """Crear header estilo Serato."""
        
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a4a4a, stop:1 #2a2a2a);
                border-bottom: 2px solid #1a1a1a;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Logo y título
        title_label = QLabel("🎯 DjAlfin - Serato Style")
        title_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Información del track actual
        self.track_info_label = QLabel("No track loaded")
        self.track_info_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                background: transparent;
            }
        """)
        header_layout.addWidget(self.track_info_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_track_list(self, parent):
        """Crear lista de tracks estilo Serato."""
        
        track_widget = QWidget()
        track_layout = QVBoxLayout(track_widget)
        
        # Título
        list_title = QLabel("📁 TRACKS WITH CUE POINTS")
        list_title.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #1a1a1a;
            }
        """)
        track_layout.addWidget(list_title)
        
        # Lista de tracks
        self.track_list = QListWidget()
        self.track_list.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #333;
                font-size: 12px;
                selection-background-color: #00d4ff;
                selection-color: #000000;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #222;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        self.track_list.itemClicked.connect(self.on_track_selected)
        track_layout.addWidget(self.track_list)
        
        # Botón de recarga
        reload_btn = QPushButton("🔄 Reload Tracks")
        reload_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #000000;
                border: none;
                padding: 10px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00b8e6;
            }
            QPushButton:pressed {
                background-color: #0099cc;
            }
        """)
        reload_btn.clicked.connect(self.load_files_with_cues)
        track_layout.addWidget(reload_btn)
        
        parent.addWidget(track_widget)
    
    def create_deck_panel(self, parent):
        """Crear panel del deck estilo Serato."""

        deck_widget = QWidget()
        deck_layout = QVBoxLayout(deck_widget)
        deck_layout.setContentsMargins(5, 5, 5, 5)
        deck_layout.setSpacing(8)

        # Información del track
        self.create_track_info_panel(deck_layout)

        # Waveform
        self.create_waveform_panel(deck_layout)

        # Hot cues
        self.create_hotcues_panel(deck_layout)

        # Controles de reproducción
        self.create_playback_controls(deck_layout)

        # Lista detallada de cue points
        self.create_cue_list_panel(deck_layout)

        parent.addWidget(deck_widget)
    
    def create_track_info_panel(self, parent_layout):
        """Crear panel de información del track."""

        info_frame = QFrame()
        info_frame.setFixedHeight(90)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(4)

        self.track_title_label = QLabel("Select a track to view cue points")
        self.track_title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
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
                font-size: 11px;
                background: transparent;
            }
        """)
        self.track_details_label.setWordWrap(True)
        info_layout.addWidget(self.track_details_label)

        parent_layout.addWidget(info_frame)
    
    def create_waveform_panel(self, parent_layout):
        """Crear panel de forma de onda."""

        waveform_frame = QFrame()
        waveform_frame.setFixedHeight(120)
        waveform_frame.setStyleSheet("""
            QFrame {
                background-color: #0a0a0a;
                border: 2px solid #333;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        waveform_layout = QVBoxLayout(waveform_frame)
        waveform_layout.setContentsMargins(8, 5, 8, 5)
        waveform_layout.setSpacing(2)

        # Título
        wave_title = QLabel("🌊 WAVEFORM")
        wave_title.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        wave_title.setFixedHeight(20)
        waveform_layout.addWidget(wave_title)

        # Widget de forma de onda
        self.waveform = WaveformWidget()
        waveform_layout.addWidget(self.waveform)

        parent_layout.addWidget(waveform_frame)
    
    def create_hotcues_panel(self, parent_layout):
        """Crear panel de hot cues estilo Serato."""

        hotcues_frame = QFrame()
        hotcues_frame.setFixedHeight(150)
        hotcues_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        hotcues_layout = QVBoxLayout(hotcues_frame)
        hotcues_layout.setContentsMargins(8, 5, 8, 5)
        hotcues_layout.setSpacing(5)

        # Título
        hotcues_title = QLabel("🔥 HOT CUES")
        hotcues_title.setStyleSheet("""
            QLabel {
                color: #ff6600;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        hotcues_title.setFixedHeight(20)
        hotcues_layout.addWidget(hotcues_title)

        # Grid de hot cues
        hotcues_grid = QGridLayout()
        hotcues_grid.setSpacing(4)
        self.hotcue_buttons = {}

        for i in range(8):
            row = i // 4
            col = i % 4

            hotcue_btn = HotCueButton(i + 1)
            hotcue_btn.clicked.connect(lambda _, idx=i+1: self.on_hotcue_clicked(idx))

            self.hotcue_buttons[i + 1] = hotcue_btn
            hotcues_grid.addWidget(hotcue_btn, row, col)

        hotcues_layout.addLayout(hotcues_grid)
        parent_layout.addWidget(hotcues_frame)
    
    def create_playback_controls(self, parent_layout):
        """Crear controles de reproducción."""

        controls_frame = QFrame()
        controls_frame.setFixedHeight(70)
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(15, 10, 15, 10)
        controls_layout.setSpacing(10)

        # Botón play/pause
        self.play_btn = QPushButton("▶️ PLAY")
        self.play_btn.setFixedSize(120, 50)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #000000;
                border: none;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
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

        controls_layout.addStretch()

        # Información de tiempo
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                background: transparent;
            }
        """)
        controls_layout.addWidget(self.time_label)

        parent_layout.addWidget(controls_frame)
    
    def create_cue_list_panel(self, parent_layout):
        """Crear panel de lista detallada de cue points."""

        cue_list_frame = QFrame()
        cue_list_frame.setStyleSheet("""
            QFrame {
                background-color: #0a0a0a;
                border: 1px solid #333;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        cue_list_layout = QVBoxLayout(cue_list_frame)
        cue_list_layout.setContentsMargins(8, 5, 8, 8)
        cue_list_layout.setSpacing(5)

        # Título
        cue_list_title = QLabel("🎯 CUE POINTS DETAILS")
        cue_list_title.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        cue_list_title.setFixedHeight(20)
        cue_list_layout.addWidget(cue_list_title)

        # Lista de cue points
        self.cue_details_list = QListWidget()
        self.cue_details_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-size: 10px;
                font-family: 'Courier New', monospace;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #222;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        cue_list_layout.addWidget(self.cue_details_list)

        parent_layout.addWidget(cue_list_frame)
    
    def apply_serato_style(self):
        """Aplicar tema general estilo Serato."""
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
                color: #ffffff;
            }
            QSplitter::handle {
                background-color: #333;
                width: 2px;
            }
        """)
    
    def load_files_with_cues(self):
        """Cargar archivos que tienen cue points."""
        
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
                                
                                # Agregar a la lista
                                display_text = f"🎵 {item}\n"
                                display_text += f"   {len(cue_points)} cues • {file_info['software']} • {file_size:.1f}MB"
                                
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
        """Cargar cue points del track seleccionado."""
        
        if not self.current_file:
            return
        
        filename = self.current_file['filename']
        cue_points = self.current_file['cue_points']
        
        # Actualizar información del track
        self.track_title_label.setText(filename)
        self.track_details_label.setText(f"{len(cue_points)} cue points • {self.current_file['software']} • {self.current_file['size_mb']:.1f}MB")
        self.track_info_label.setText(f"🎵 {filename}")
        
        # Actualizar waveform
        max_position = max([cue.position for cue in cue_points]) if cue_points else 300
        duration = max(max_position + 30, 300)  # Al menos 5 minutos
        self.waveform.set_cue_points(cue_points, duration)
        
        # Actualizar hot cues
        for i in range(1, 9):
            self.hotcue_buttons[i].set_cue_point(None)
        
        for cue in cue_points:
            if 1 <= cue.hotcue_index <= 8:
                self.hotcue_buttons[cue.hotcue_index].set_cue_point(cue)
        
        # Actualizar lista detallada
        self.cue_details_list.clear()
        for i, cue in enumerate(cue_points):
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            
            detail_text = f"{i+1:2d}. {cue.name:<20} {minutes:02d}:{seconds:02d} Hot:{cue.hotcue_index} {cue.color} [{cue.software}]"
            self.cue_details_list.addItem(detail_text)
        
        # Actualizar tiempo
        total_minutes = int(duration // 60)
        total_seconds = int(duration % 60)
        self.time_label.setText(f"00:00 / {total_minutes:02d}:{total_seconds:02d}")
        
        print(f"✅ Loaded track: {filename} with {len(cue_points)} cue points")
    
    def on_hotcue_clicked(self, hotcue_number):
        """Manejar clic en hot cue."""
        
        button = self.hotcue_buttons[hotcue_number]
        if button.cue_point:
            cue = button.cue_point
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            print(f"🎯 Hot Cue {hotcue_number}: {cue.name} @ {minutes}:{seconds:02d}")
            
            # Simular salto a la posición
            self.waveform.current_position = cue.position
            self.waveform.update()
    
    def toggle_playback(self):
        """Alternar reproducción."""
        
        if self.play_btn.text() == "▶️ PLAY":
            self.play_btn.setText("⏸️ PAUSE")
            self.waveform.start_playback()
        else:
            self.play_btn.setText("▶️ PLAY")
            self.waveform.stop_playback()

def main():
    """Función principal."""
    
    app = QApplication(sys.argv)
    app.setApplicationName("DjAlfin Serato Style Viewer")
    
    window = SeratoStyleViewer()
    window.show()
    
    print("🎯 DjAlfin Serato Style Cue Viewer")
    print("Professional DJ interface for cue points")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
