#!/usr/bin/env python3
"""
🎯 DjAlfin - Serato Style Compact (13" Mac)
Interfaz optimizada para MacBook de 13 pulgadas
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QListWidget, QPushButton, QFrame,
                             QSplitter, QGridLayout, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen
from basic_metadata_reader import BasicMetadataReader

class CompactWaveformWidget(QWidget):
    """Widget compacto de waveform para 13 pulgadas."""
    
    def __init__(self):
        super().__init__()
        self.cue_points = []
        self.duration = 300
        self.current_position = 0
        self.setMinimumHeight(50)
        self.setMaximumHeight(50)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        
    def set_cue_points(self, cue_points, duration=300):
        self.cue_points = cue_points
        self.duration = duration
        self.current_position = 0
        self.update()
    
    def start_playback(self):
        self.timer.start(100)
    
    def stop_playback(self):
        self.timer.stop()
    
    def update_position(self):
        self.current_position += 0.1
        if self.current_position >= self.duration:
            self.current_position = 0
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Fondo
        painter.fillRect(0, 0, width, height, QColor(20, 20, 20))
        
        # Waveform compacta
        painter.setPen(QPen(QColor(0, 150, 255), 1))
        import random
        random.seed(42)
        
        for x in range(0, width, 3):
            wave_height = random.randint(5, height - 10)
            y_center = height // 2
            painter.drawLine(x, y_center - wave_height//2, x, y_center + wave_height//2)
        
        # Cue points
        for cue in self.cue_points:
            if cue.position <= self.duration:
                x_pos = int((cue.position / self.duration) * width)
                
                try:
                    color = QColor(cue.color)
                except:
                    color = QColor(255, 0, 0)
                
                painter.setPen(QPen(color, 2))
                painter.drawLine(x_pos, 0, x_pos, height)
                
                painter.setBrush(QBrush(color))
                painter.drawEllipse(x_pos - 2, 1, 4, 4)
        
        # Posición actual
        if self.duration > 0:
            current_x = int((self.current_position / self.duration) * width)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawLine(current_x, 0, current_x, height)

class CompactHotCueButton(QPushButton):
    """Botón compacto de hot cue para 13 pulgadas."""
    
    def __init__(self, number):
        super().__init__()
        self.number = number
        self.cue_point = None
        self.setFixedSize(60, 40)  # Más pequeño
        self.setup_style()
    
    def setup_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                color: #888;
                font-weight: bold;
                font-size: 10px;
            }}
            QPushButton:hover {{
                border-color: #666;
                background-color: #333;
            }}
        """)
        self.setText(str(self.number))
    
    def set_cue_point(self, cue_point):
        self.cue_point = cue_point
        
        if cue_point:
            try:
                color = cue_point.color
                if not color.startswith('#'):
                    color = '#FF0000'
            except:
                color = '#FF0000'
            
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = '#000000' if brightness > 128 else '#FFFFFF'
            
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 1px solid {color};
                    border-radius: 4px;
                    color: {text_color};
                    font-weight: bold;
                    font-size: 8px;
                }}
                QPushButton:hover {{
                    border-color: #FFFFFF;
                }}
            """)
            
            minutes = int(cue_point.position // 60)
            seconds = int(cue_point.position % 60)
            self.setText(f"{self.number}\n{minutes}:{seconds:02d}")
        else:
            self.setup_style()
            self.setText(str(self.number))

class SeratoCompact13Inch(QMainWindow):
    """Interfaz compacta para MacBook 13 pulgadas."""
    
    def __init__(self):
        super().__init__()
        self.audio_folder = "/Volumes/KINGSTON/Audio"
        self.metadata_reader = BasicMetadataReader()
        self.files_with_cues = []
        self.current_file = None
        
        self.init_ui()
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
        wave_frame.setFixedHeight(70)
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
        
        self.waveform = CompactWaveformWidget()
        wave_layout.addWidget(self.waveform)
        
        parent_layout.addWidget(wave_frame)
    
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
            
            hotcue_btn = CompactHotCueButton(i + 1)
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
        """)
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)
        
        controls_layout.addStretch()
        
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
        
        # Actualizar lista
        self.cue_details_list.clear()
        for i, cue in enumerate(cue_points):
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            
            detail_text = f"{i+1:2d}. {cue.name[:15]:<15} {minutes:02d}:{seconds:02d} H{cue.hotcue_index} {cue.color[:7]}"
            self.cue_details_list.addItem(detail_text)
        
        # Actualizar tiempo
        total_minutes = int(duration // 60)
        total_seconds = int(duration % 60)
        self.time_label.setText(f"00:00/{total_minutes:02d}:{total_seconds:02d}")
        
        print(f"✅ Loaded: {filename} ({len(cue_points)} cues)")
    
    def on_hotcue_clicked(self, hotcue_number):
        """Manejar clic en hot cue."""
        
        button = self.hotcue_buttons[hotcue_number]
        if button.cue_point:
            cue = button.cue_point
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            print(f"🎯 Hot Cue {hotcue_number}: {cue.name} @ {minutes}:{seconds:02d}")
            
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
    app.setApplicationName("DjAlfin Compact 13\"")
    
    window = SeratoCompact13Inch()
    window.show()
    
    print("🎯 DjAlfin Compact for 13\" MacBook")
    print("Optimized interface for smaller screens")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
