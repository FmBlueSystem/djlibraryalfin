#!/usr/bin/env python3
"""
🎯 DjAlfin - Prototipo Desktop con Archivos Reales
Versión mejorada que funciona con archivos de audio reales de /Volumes/KINGSTON/Audio
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import glob
import json
import time
import random
import threading
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import subprocess
import platform

@dataclass
class CuePoint:
    """Estructura de cue point."""
    position: float
    type: str
    color: str
    name: str
    hotcue_index: int
    created_at: float
    energy_level: int = 5

@dataclass
class AudioFile:
    """Estructura de archivo de audio."""
    path: str
    filename: str
    artist: str
    title: str
    duration: float
    size_mb: float
    format: str
    bitrate: str = "Unknown"

class AudioFileScanner:
    """Escáner de archivos de audio reales."""
    
    AUDIO_EXTENSIONS = ['.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg']
    
    @staticmethod
    def scan_audio_folder(folder_path: str) -> List[AudioFile]:
        """Escanear carpeta de audio y extraer información."""
        audio_files = []
        
        if not os.path.exists(folder_path):
            print(f"❌ Carpeta no encontrada: {folder_path}")
            return audio_files
        
        print(f"🔍 Escaneando: {folder_path}")
        
        try:
            for file_path in glob.glob(os.path.join(folder_path, "*")):
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file_path)
                    
                    if ext.lower() in AudioFileScanner.AUDIO_EXTENSIONS:
                        audio_file = AudioFileScanner.analyze_audio_file(file_path)
                        if audio_file:
                            audio_files.append(audio_file)
                            
        except Exception as e:
            print(f"❌ Error escaneando carpeta: {e}")
        
        print(f"✅ Encontrados {len(audio_files)} archivos de audio")
        return audio_files
    
    @staticmethod
    def analyze_audio_file(file_path: str) -> Optional[AudioFile]:
        """Analizar archivo de audio individual."""
        try:
            filename = os.path.basename(file_path)
            
            # Extraer artista y título del nombre del archivo
            artist, title = AudioFileScanner.parse_filename(filename)
            
            # Obtener información del archivo
            file_stats = os.stat(file_path)
            size_mb = file_stats.st_size / (1024 * 1024)
            
            # Determinar formato
            _, ext = os.path.splitext(filename)
            format_name = ext.upper().replace('.', '')
            
            # Estimar duración (simulada por ahora)
            duration = AudioFileScanner.estimate_duration(size_mb, format_name)
            
            return AudioFile(
                path=file_path,
                filename=filename,
                artist=artist,
                title=title,
                duration=duration,
                size_mb=size_mb,
                format=format_name,
                bitrate="320 kbps" if format_name in ['MP3', 'M4A'] else "Lossless"
            )
            
        except Exception as e:
            print(f"❌ Error analizando {file_path}: {e}")
            return None
    
    @staticmethod
    def parse_filename(filename: str) -> tuple:
        """Extraer artista y título del nombre del archivo."""
        # Remover extensión
        name_without_ext = os.path.splitext(filename)[0]
        
        # Buscar patrones comunes
        if " - " in name_without_ext:
            parts = name_without_ext.split(" - ", 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        elif " feat. " in name_without_ext.lower():
            # Manejar colaboraciones
            parts = name_without_ext.split(" feat. ", 1)
            artist = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else "Unknown Title"
        elif " Feat. " in name_without_ext:
            parts = name_without_ext.split(" Feat. ", 1)
            artist = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else "Unknown Title"
        else:
            # Si no hay separador claro, usar todo como título
            artist = "Unknown Artist"
            title = name_without_ext
        
        # Limpiar caracteres especiales
        artist = artist.replace("_PN", "").replace("_", " ").strip()
        title = title.replace("_PN", "").replace("_", " ").strip()
        
        return artist, title
    
    @staticmethod
    def estimate_duration(size_mb: float, format_name: str) -> float:
        """Estimar duración basada en el tamaño del archivo."""
        # Estimaciones aproximadas basadas en bitrates típicos
        if format_name == 'FLAC':
            # FLAC: ~1MB por minuto (aproximado)
            return size_mb * 60
        elif format_name in ['MP3', 'M4A']:
            # MP3/M4A 320kbps: ~2.4MB por minuto
            return (size_mb / 2.4) * 60
        else:
            # Estimación genérica
            return size_mb * 30
    
    @staticmethod
    def get_audio_duration_real(file_path: str) -> float:
        """Obtener duración real usando ffprobe (si está disponible)."""
        try:
            # Intentar usar ffprobe para obtener duración real
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, ValueError):
            pass
        
        # Fallback a estimación
        file_stats = os.stat(file_path)
        size_mb = file_stats.st_size / (1024 * 1024)
        _, ext = os.path.splitext(file_path)
        format_name = ext.upper().replace('.', '')
        
        return AudioFileScanner.estimate_duration(size_mb, format_name)

class DjAlfinDesktopReal:
    """Aplicación desktop con archivos reales."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin Desktop - Real Audio Files")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Variables del estado
        self.audio_files: List[AudioFile] = []
        self.current_file: Optional[AudioFile] = None
        self.cue_points: List[CuePoint] = []
        self.current_position = 0.0
        self.is_playing = False
        self.selected_file_index = -1
        
        # Colores profesionales
        self.dj_colors = {
            'Hot Red': '#FF0000',
            'Electric Orange': '#FF6600',
            'Neon Yellow': '#FFFF00',
            'Laser Green': '#00FF00',
            'Cyber Cyan': '#00FFFF',
            'Electric Blue': '#0066FF',
            'Neon Purple': '#9900FF',
            'Hot Pink': '#FF00CC'
        }
        
        self.setup_ui()
        self.scan_audio_files()
        
    def setup_ui(self):
        """Configurar interfaz de usuario."""
        
        # Header
        self.create_header()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Panel izquierdo - Lista de archivos
        self.create_file_list_panel(main_frame)
        
        # Panel central - Controles
        self.create_control_panel(main_frame)
        
        # Panel derecho - Cue points
        self.create_cue_panel(main_frame)
        
        # Footer - Hot cues
        self.create_hotcue_panel()
        
    def create_header(self):
        """Crear header."""
        header_frame = tk.Frame(self.root, bg='#0d1117', height=60)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🎯 DjAlfin Desktop - Real Audio Files",
            font=('Arial', 18, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        )
        title_label.pack(side='left', padx=20, pady=15)
        
        self.file_count_label = tk.Label(
            header_frame,
            text="📁 Escaneando archivos...",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.file_count_label.pack(side='right', padx=20, pady=15)
        
    def create_file_list_panel(self, parent):
        """Crear panel de lista de archivos."""
        file_frame = tk.LabelFrame(
            parent,
            text="📁 Audio Files",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        file_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Lista de archivos
        list_frame = tk.Frame(file_frame, bg='#21262d')
        list_frame.pack(fill='both', expand=True)
        
        # Treeview para archivos
        columns = ('Artist', 'Title', 'Duration', 'Format', 'Size')
        self.file_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # Configurar columnas
        self.file_tree.heading('Artist', text='Artist')
        self.file_tree.heading('Title', text='Title')
        self.file_tree.heading('Duration', text='Duration')
        self.file_tree.heading('Format', text='Format')
        self.file_tree.heading('Size', text='Size')
        
        self.file_tree.column('Artist', width=150)
        self.file_tree.column('Title', width=200)
        self.file_tree.column('Duration', width=80)
        self.file_tree.column('Format', width=60)
        self.file_tree.column('Size', width=80)
        
        # Scrollbar
        file_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        file_scrollbar.pack(side='right', fill='y')
        
        # Botones de archivo
        file_button_frame = tk.Frame(file_frame, bg='#21262d')
        file_button_frame.pack(fill='x', pady=10)
        
        tk.Button(
            file_button_frame,
            text="🔄 Rescan",
            command=self.scan_audio_files,
            bg='#0969da',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            file_button_frame,
            text="📁 Browse",
            command=self.browse_folder,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            file_button_frame,
            text="▶️ Load",
            command=self.load_selected_file,
            bg='#238636',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        # Bind eventos
        self.file_tree.bind('<ButtonRelease-1>', self.on_file_select)
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        
    def create_control_panel(self, parent):
        """Crear panel de controles."""
        control_frame = tk.LabelFrame(
            parent,
            text="🎛️ Controls",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        control_frame.pack(side='left', fill='y', padx=5)
        control_frame.configure(width=300)
        control_frame.pack_propagate(False)
        
        # Información del archivo actual
        self.create_current_file_info(control_frame)
        
        # Controles de reproducción
        self.create_playback_controls(control_frame)
        
        # Creador de cue points
        self.create_cue_creator(control_frame)
        
    def create_current_file_info(self, parent):
        """Crear información del archivo actual."""
        info_frame = tk.LabelFrame(
            parent,
            text="🎵 Current Track",
            bg='#21262d',
            fg='#f0f6fc'
        )
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.current_file_label = tk.Label(
            info_frame,
            text="No file loaded",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 10),
            wraplength=250,
            justify='left'
        )
        self.current_file_label.pack(padx=10, pady=10)
        
    def create_playback_controls(self, parent):
        """Crear controles de reproducción."""
        playback_frame = tk.LabelFrame(
            parent,
            text="▶️ Playback",
            bg='#21262d',
            fg='#f0f6fc'
        )
        playback_frame.pack(fill='x', pady=(0, 10))
        
        # Display de posición
        self.position_var = tk.StringVar(value="0:00 / 0:00")
        position_display = tk.Label(
            playback_frame,
            textvariable=self.position_var,
            font=('Courier', 14, 'bold'),
            bg='#0d1117',
            fg='#f85149',
            relief='sunken',
            bd=2,
            padx=10,
            pady=5
        )
        position_display.pack(fill='x', padx=5, pady=5)
        
        # Slider de posición
        self.position_scale = tk.Scale(
            playback_frame,
            from_=0,
            to=300,
            orient='horizontal',
            bg='#21262d',
            fg='#f0f6fc',
            highlightbackground='#21262d',
            command=self.on_position_change,
            length=250
        )
        self.position_scale.pack(fill='x', padx=5, pady=5)
        
        # Botones de control
        button_frame = tk.Frame(playback_frame, bg='#21262d')
        button_frame.pack(fill='x', padx=5, pady=5)
        
        self.play_button = tk.Button(
            button_frame,
            text="▶️",
            command=self.toggle_play,
            bg='#238636',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=3
        )
        self.play_button.pack(side='left', padx=2)
        
        tk.Button(
            button_frame,
            text="⏹️",
            command=self.stop_playback,
            bg='#da3633',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=3
        ).pack(side='left', padx=2)
        
        tk.Button(
            button_frame,
            text="🎧",
            command=self.open_in_system_player,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=3
        ).pack(side='left', padx=2)
