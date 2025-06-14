#!/usr/bin/env python3
"""
🎯 DjAlfin - Audio Analyzer with PyQt5
Versión con Qt que SÍ funciona correctamente en macOS
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QListWidget, QTextEdit, QPushButton,
                             QSplitter, QGroupBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from basic_metadata_reader import BasicMetadataReader

class AudioAnalyzerThread(QThread):
    """Thread para analizar archivos sin bloquear la UI."""
    
    file_analyzed = pyqtSignal(dict)
    analysis_complete = pyqtSignal(dict)
    status_update = pyqtSignal(str)
    
    def __init__(self, audio_folder):
        super().__init__()
        self.audio_folder = audio_folder
        self.metadata_reader = BasicMetadataReader()
    
    def run(self):
        """Ejecutar análisis de archivos."""
        
        if not os.path.exists(self.audio_folder):
            self.status_update.emit("❌ Audio folder not found")
            return
        
        try:
            # Buscar archivos de audio
            all_items = os.listdir(self.audio_folder)
            audio_extensions = ['.mp3', '.m4a', '.flac', '.wav']
            
            audio_files = []
            for item in all_items:
                if not item.startswith('.'):
                    _, ext = os.path.splitext(item)
                    if ext.lower() in audio_extensions:
                        audio_files.append(item)
            
            audio_files.sort()
            
            # Analizar cada archivo
            results = {
                'total_files': len(audio_files),
                'files_with_cues': 0,
                'total_cues': 0,
                'files': []
            }
            
            for i, filename in enumerate(audio_files):
                file_path = os.path.join(self.audio_folder, filename)
                
                self.status_update.emit(f"🔍 Analyzing {i+1}/{len(audio_files)}: {filename[:30]}...")
                
                try:
                    # Información básica
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    _, ext = os.path.splitext(filename)
                    format_name = ext.upper().replace('.', '')
                    
                    # Analizar cue points
                    metadata = self.metadata_reader.scan_file(file_path)
                    cue_points = metadata.get('cue_points', [])
                    
                    file_info = {
                        'filename': filename,
                        'path': file_path,
                        'size_mb': file_size,
                        'format': format_name,
                        'has_cues': len(cue_points) > 0,
                        'cue_count': len(cue_points),
                        'software': cue_points[0].software.title() if cue_points else 'None',
                        'cue_points': cue_points
                    }
                    
                    results['files'].append(file_info)
                    
                    if file_info['has_cues']:
                        results['files_with_cues'] += 1
                        results['total_cues'] += len(cue_points)
                    
                    # Emitir resultado del archivo
                    self.file_analyzed.emit(file_info)
                    
                except Exception as e:
                    file_info = {
                        'filename': filename,
                        'path': file_path,
                        'size_mb': 0,
                        'format': format_name if 'format_name' in locals() else 'Unknown',
                        'has_cues': False,
                        'cue_count': 0,
                        'software': 'Error',
                        'error': str(e)
                    }
                    
                    results['files'].append(file_info)
                    self.file_analyzed.emit(file_info)
            
            # Análisis completo
            self.analysis_complete.emit(results)
            
        except Exception as e:
            self.status_update.emit(f"❌ Error: {str(e)}")

class AudioAnalyzerQt(QMainWindow):
    """Aplicación principal con PyQt5."""
    
    def __init__(self):
        super().__init__()
        self.audio_folder = "/Volumes/KINGSTON/Audio"
        self.all_files = []
        self.current_file = None
        
        self.init_ui()
        self.start_analysis()
    
    def init_ui(self):
        """Inicializar interfaz de usuario."""
        
        self.setWindowTitle("🎯 DjAlfin - Audio Files Analyzer (Qt)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter para dividir la ventana
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Panel izquierdo - Lista de archivos
        self.create_files_panel(splitter)
        
        # Panel derecho - Detalles
        self.create_details_panel(splitter)
        
        # Barra de estado
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("🔍 Starting analysis...")
        
        # Aplicar estilo oscuro
        self.apply_dark_style()
    
    def create_files_panel(self, parent):
        """Crear panel de lista de archivos."""
        
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        
        # Título
        files_group = QGroupBox("📁 ALL AUDIO FILES - /Volumes/KINGSTON/Audio")
        files_group_layout = QVBoxLayout(files_group)
        
        # Lista de archivos
        self.files_list = QListWidget()
        self.files_list.itemClicked.connect(self.on_file_selected)
        files_group_layout.addWidget(self.files_list)
        
        # Botones de control
        buttons_layout = QHBoxLayout()
        
        self.rescan_btn = QPushButton("🔄 Rescan")
        self.rescan_btn.clicked.connect(self.start_analysis)
        buttons_layout.addWidget(self.rescan_btn)
        
        self.filter_cues_btn = QPushButton("✅ With Cues Only")
        self.filter_cues_btn.clicked.connect(self.show_with_cues_only)
        buttons_layout.addWidget(self.filter_cues_btn)
        
        self.show_all_btn = QPushButton("📁 Show All")
        self.show_all_btn.clicked.connect(self.show_all_files)
        buttons_layout.addWidget(self.show_all_btn)
        
        files_group_layout.addLayout(buttons_layout)
        files_layout.addWidget(files_group)
        
        parent.addWidget(files_widget)
    
    def create_details_panel(self, parent):
        """Crear panel de detalles."""
        
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Resumen
        summary_group = QGroupBox("📊 Analysis Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setPlainText("🔍 Starting analysis...")
        summary_layout.addWidget(self.summary_text)
        
        details_layout.addWidget(summary_group)
        
        # Detalles del archivo
        file_details_group = QGroupBox("🎯 Selected File Details")
        file_details_layout = QVBoxLayout(file_details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setPlainText("Select a file from the list to view details")
        file_details_layout.addWidget(self.details_text)
        
        details_layout.addWidget(file_details_group)
        
        parent.addWidget(details_widget)
    
    def apply_dark_style(self):
        """Aplicar estilo oscuro."""
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #f0f6fc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #58a6ff;
                border-radius: 5px;
                margin-top: 1ex;
                color: #58a6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QListWidget {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                selection-background-color: #58a6ff;
            }
            QTextEdit {
                background-color: #0d1117;
                color: #f0f6fc;
                border: 1px solid #30363d;
                font-family: 'Courier New', monospace;
            }
            QPushButton {
                background-color: #21262d;
                color: #f0f6fc;
                border: 1px solid #30363d;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
            QPushButton:pressed {
                background-color: #58a6ff;
            }
            QStatusBar {
                background-color: #0d1117;
                color: #f0f6fc;
            }
        """)
    
    def start_analysis(self):
        """Iniciar análisis de archivos."""
        
        self.status_bar.showMessage("🔍 Analyzing audio files...")
        self.files_list.clear()
        self.all_files = []
        
        # Crear y iniciar thread de análisis
        self.analysis_thread = AudioAnalyzerThread(self.audio_folder)
        self.analysis_thread.file_analyzed.connect(self.on_file_analyzed)
        self.analysis_thread.analysis_complete.connect(self.on_analysis_complete)
        self.analysis_thread.status_update.connect(self.on_status_update)
        self.analysis_thread.start()
    
    def on_file_analyzed(self, file_info):
        """Manejar archivo analizado."""
        
        self.all_files.append(file_info)
        
        # Agregar a la lista
        status_icon = "✅" if file_info['has_cues'] else "❌"
        display_text = f"{status_icon} {file_info['filename']} ({file_info['size_mb']:.1f}MB, {file_info['format']}"
        
        if file_info['has_cues']:
            display_text += f", {file_info['cue_count']} cues, {file_info['software']})"
        else:
            display_text += ", No cues)"
        
        self.files_list.addItem(display_text)
    
    def on_analysis_complete(self, results):
        """Manejar análisis completo."""
        
        # Actualizar resumen
        summary = f"📊 ANALYSIS COMPLETE\n"
        summary += f"=" * 40 + "\n"
        summary += f"📁 Total files: {results['total_files']}\n"
        summary += f"✅ Files with cues: {results['files_with_cues']}\n"
        summary += f"❌ Files without cues: {results['total_files'] - results['files_with_cues']}\n"
        summary += f"🎯 Total cue points: {results['total_cues']}\n"
        summary += f"📈 Success rate: {(results['files_with_cues']/results['total_files']*100):.1f}%"
        
        self.summary_text.setPlainText(summary)
        
        # Actualizar barra de estado
        if results['files_with_cues'] > 0:
            self.status_bar.showMessage(f"✅ Found {results['files_with_cues']} files with {results['total_cues']} cue points")
        else:
            self.status_bar.showMessage(f"❌ No cue points found in {results['total_files']} files")
        
        print(f"📊 Analysis complete: {results['files_with_cues']}/{results['total_files']} files with {results['total_cues']} cue points")
    
    def on_status_update(self, message):
        """Actualizar barra de estado."""
        self.status_bar.showMessage(message)
    
    def on_file_selected(self, item):
        """Manejar selección de archivo."""
        
        row = self.files_list.row(item)
        if 0 <= row < len(self.all_files):
            file_info = self.all_files[row]
            self.show_file_details(file_info)
    
    def show_file_details(self, file_info):
        """Mostrar detalles del archivo."""
        
        details = f"📁 FILE DETAILS\n"
        details += f"=" * 50 + "\n"
        details += f"📄 Filename: {file_info['filename']}\n"
        details += f"📊 Size: {file_info['size_mb']:.1f} MB\n"
        details += f"🎵 Format: {file_info['format']}\n"
        details += f"📍 Path: {file_info['path']}\n\n"
        
        if file_info['has_cues']:
            details += f"🎯 CUE POINTS: {file_info['cue_count']}\n"
            details += f"🎛️ Software: {file_info['software']}\n"
            details += f"=" * 50 + "\n\n"
            
            for i, cue in enumerate(file_info['cue_points']):
                minutes = int(cue.position // 60)
                seconds = int(cue.position % 60)
                
                details += f"{i+1:2d}. {cue.name}\n"
                details += f"    ⏰ Time: {minutes}:{seconds:02d} ({cue.position:.1f}s)\n"
                details += f"    🎨 Color: {cue.color}\n"
                details += f"    🔥 Hot Cue: #{cue.hotcue_index}\n"
                details += f"    ⚡ Energy: {cue.energy_level}/10\n\n"
        else:
            details += f"❌ NO CUE POINTS FOUND\n"
            if 'error' in file_info:
                details += f"🚨 Error: {file_info['error']}\n"
            else:
                details += f"This file has not been processed by DJ software.\n"
        
        self.details_text.setPlainText(details)
    
    def show_with_cues_only(self):
        """Mostrar solo archivos con cue points."""
        
        self.files_list.clear()
        
        for file_info in self.all_files:
            if file_info['has_cues']:
                display_text = f"✅ {file_info['filename']} ({file_info['size_mb']:.1f}MB, {file_info['format']}, {file_info['cue_count']} cues, {file_info['software']})"
                self.files_list.addItem(display_text)
    
    def show_all_files(self):
        """Mostrar todos los archivos."""
        
        self.files_list.clear()
        
        for file_info in self.all_files:
            status_icon = "✅" if file_info['has_cues'] else "❌"
            display_text = f"{status_icon} {file_info['filename']} ({file_info['size_mb']:.1f}MB, {file_info['format']}"
            
            if file_info['has_cues']:
                display_text += f", {file_info['cue_count']} cues, {file_info['software']})"
            else:
                display_text += ", No cues)"
            
            self.files_list.addItem(display_text)

def main():
    """Función principal."""
    
    app = QApplication(sys.argv)
    
    # Configurar aplicación
    app.setApplicationName("DjAlfin Audio Analyzer")
    app.setApplicationVersion("1.0")
    
    # Crear y mostrar ventana principal
    window = AudioAnalyzerQt()
    window.show()
    
    print("🎯 DjAlfin Audio Analyzer (PyQt5)")
    print("Analyzing files in /Volumes/KINGSTON/Audio")
    
    # Ejecutar aplicación
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
