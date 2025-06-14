#!/usr/bin/env python3
"""
🎯 DjAlfin Desktop - Con Integración Spotify
Versión avanzada con metadatos y análisis desde Spotify API
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import glob
import json
import time
import threading
import subprocess
import platform
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

# Importar integración con Spotify
from spotify_integration import SpotifyIntegration, SpotifyTrack, AudioFeatures

# Importar lector de metadatos embebidos
from basic_metadata_reader import BasicMetadataReader, EmbeddedCuePoint

@dataclass
class CuePoint:
    position: float
    type: str
    color: str
    name: str
    hotcue_index: int
    created_at: float
    energy_level: int = 5
    source: str = "manual"  # manual, spotify_analysis, auto_detect

@dataclass
class AudioFile:
    path: str
    filename: str
    artist: str
    title: str
    duration: float
    size_mb: float
    format: str
    bitrate: str = "Unknown"
    spotify_metadata: Optional[Dict[str, Any]] = None

class AudioFileScanner:
    AUDIO_EXTENSIONS = ['.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg']
    
    @staticmethod
    def scan_audio_folder(folder_path: str) -> List[AudioFile]:
        audio_files = []
        if not os.path.exists(folder_path):
            return audio_files
        
        try:
            for file_path in glob.glob(os.path.join(folder_path, "*")):
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file_path)
                    if ext.lower() in AudioFileScanner.AUDIO_EXTENSIONS:
                        audio_file = AudioFileScanner.analyze_audio_file(file_path)
                        if audio_file:
                            audio_files.append(audio_file)
        except Exception as e:
            print(f"Error escaneando: {e}")
        
        return audio_files
    
    @staticmethod
    def analyze_audio_file(file_path: str) -> Optional[AudioFile]:
        try:
            filename = os.path.basename(file_path)
            artist, title = AudioFileScanner.parse_filename(filename)
            
            file_stats = os.stat(file_path)
            size_mb = file_stats.st_size / (1024 * 1024)
            
            _, ext = os.path.splitext(filename)
            format_name = ext.upper().replace('.', '')
            
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
            print(f"Error analizando {file_path}: {e}")
            return None
    
    @staticmethod
    def parse_filename(filename: str) -> tuple:
        name_without_ext = os.path.splitext(filename)[0]
        
        if " - " in name_without_ext:
            parts = name_without_ext.split(" - ", 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        elif " feat. " in name_without_ext.lower():
            parts = name_without_ext.split(" feat. ", 1)
            artist = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else "Unknown Title"
        else:
            artist = "Unknown Artist"
            title = name_without_ext
        
        artist = artist.replace("_PN", "").replace("_", " ").strip()
        title = title.replace("_PN", "").replace("_", " ").strip()
        
        return artist, title
    
    @staticmethod
    def estimate_duration(size_mb: float, format_name: str) -> float:
        if format_name == 'FLAC':
            return size_mb * 60
        elif format_name in ['MP3', 'M4A']:
            return (size_mb / 2.4) * 60
        else:
            return size_mb * 30

class DjAlfinDesktopSpotify:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin Desktop - Spotify Enhanced")
        self.root.geometry("1500x950")
        self.root.configure(bg='#1a1a1a')
        
        # Variables del estado
        self.audio_files: List[AudioFile] = []
        self.current_file: Optional[AudioFile] = None
        self.cue_points: List[CuePoint] = []
        self.current_position = 0.0
        self.is_playing = False
        self.selected_file_index = -1
        
        # Integración con Spotify
        self.spotify = SpotifyIntegration()
        self.spotify_connected = False

        # Lector de metadatos embebidos
        self.metadata_reader = BasicMetadataReader()
        
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
        self.test_spotify_connection()
        self.scan_audio_files()
        
    def setup_ui(self):
        # Header con información de Spotify
        self.create_header()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Panel izquierdo - Lista de archivos
        self.create_file_panel(main_frame)
        
        # Panel central - Controles
        self.create_control_panel(main_frame)
        
        # Panel derecho - Cue points
        self.create_cue_panel(main_frame)
        
        # Footer - Hot cues
        self.create_hotcue_panel()
        
    def create_header(self):
        header_frame = tk.Frame(self.root, bg='#0d1117', height=80)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        # Título principal
        title_frame = tk.Frame(header_frame, bg='#0d1117')
        title_frame.pack(side='left', fill='y', padx=20)
        
        tk.Label(
            title_frame,
            text="🎯 DjAlfin Desktop",
            font=('Arial', 20, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(anchor='w')
        
        tk.Label(
            title_frame,
            text="Spotify Enhanced Edition",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#1db954'
        ).pack(anchor='w')
        
        # Estado de Spotify
        spotify_frame = tk.Frame(header_frame, bg='#0d1117')
        spotify_frame.pack(side='right', fill='y', padx=20)
        
        self.spotify_status_label = tk.Label(
            spotify_frame,
            text="🎵 Conectando con Spotify...",
            font=('Arial', 12, 'bold'),
            bg='#0d1117',
            fg='#fd7e14'
        )
        self.spotify_status_label.pack(anchor='e', pady=5)
        
        self.file_count_label = tk.Label(
            spotify_frame,
            text="📁 Escaneando archivos...",
            font=('Arial', 10),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.file_count_label.pack(anchor='e')
        
    def test_spotify_connection(self):
        """Probar conexión con Spotify en hilo separado."""
        def test_thread():
            self.spotify_connected = self.spotify.test_connection()
            self.root.after(0, self.update_spotify_status)
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def update_spotify_status(self):
        """Actualizar estado de conexión con Spotify."""
        if self.spotify_connected:
            self.spotify_status_label.config(
                text="🎵 Spotify Connected ✅",
                fg='#1db954'
            )
        else:
            self.spotify_status_label.config(
                text="🎵 Spotify Offline ❌",
                fg='#f85149'
            )
    
    def create_file_panel(self, parent):
        file_frame = tk.LabelFrame(
            parent,
            text="📁 Audio Library",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        file_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Lista de archivos con información de Spotify
        columns = ('Artist', 'Title', 'Duration', 'Format', 'Spotify')
        self.file_tree = ttk.Treeview(
            file_frame,
            columns=columns,
            show='headings',
            height=18
        )
        
        # Configurar columnas
        self.file_tree.heading('Artist', text='Artist')
        self.file_tree.heading('Title', text='Title')
        self.file_tree.heading('Duration', text='Duration')
        self.file_tree.heading('Format', text='Format')
        self.file_tree.heading('Spotify', text='Spotify')
        
        self.file_tree.column('Artist', width=120)
        self.file_tree.column('Title', width=150)
        self.file_tree.column('Duration', width=80)
        self.file_tree.column('Format', width=60)
        self.file_tree.column('Spotify', width=60)
        
        scrollbar = ttk.Scrollbar(file_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botones con funciones de Spotify
        btn_frame = tk.Frame(file_frame, bg='#21262d')
        btn_frame.pack(fill='x', pady=10)
        
        tk.Button(btn_frame, text="🔄 Rescan", command=self.scan_audio_files,
                 bg='#0969da', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=1)
        tk.Button(btn_frame, text="📁 Browse", command=self.browse_folder,
                 bg='#6f42c1', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=1)
        tk.Button(btn_frame, text="▶️ Load", command=self.load_selected_file,
                 bg='#238636', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=1)
        tk.Button(btn_frame, text="🎵 Spotify", command=self.enhance_with_spotify,
                 bg='#1db954', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=1)
        
        self.file_tree.bind('<ButtonRelease-1>', self.on_file_select)
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        
    def create_control_panel(self, parent):
        control_frame = tk.LabelFrame(
            parent,
            text="🎛️ DJ Controls",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        control_frame.pack(side='left', fill='y', padx=5)
        control_frame.configure(width=380)
        control_frame.pack_propagate(False)
        
        # Información del archivo actual con datos de Spotify
        self.create_current_file_info(control_frame)
        
        # Controles de reproducción
        self.create_playback_controls(control_frame)
        
        # Creador de cue points con sugerencias de Spotify
        self.create_cue_creator(control_frame)
        
        # Panel de análisis de Spotify
        self.create_spotify_analysis_panel(control_frame)
        
    def create_current_file_info(self, parent):
        info_frame = tk.LabelFrame(parent, text="🎵 Current Track", bg='#21262d', fg='#f0f6fc')
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.current_file_label = tk.Label(
            info_frame,
            text="No file loaded",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 9),
            wraplength=340,
            justify='left'
        )
        self.current_file_label.pack(padx=10, pady=10)
        
    def create_playback_controls(self, parent):
        playback_frame = tk.LabelFrame(parent, text="▶️ Playback", bg='#21262d', fg='#f0f6fc')
        playback_frame.pack(fill='x', pady=(0, 10))
        
        self.position_var = tk.StringVar(value="0:00 / 0:00")
        tk.Label(
            playback_frame,
            textvariable=self.position_var,
            font=('Courier', 14, 'bold'),
            bg='#0d1117',
            fg='#f85149',
            relief='sunken',
            bd=2,
            padx=10,
            pady=6
        ).pack(fill='x', padx=5, pady=5)
        
        self.position_scale = tk.Scale(
            playback_frame,
            from_=0,
            to=300,
            orient='horizontal',
            bg='#21262d',
            fg='#f0f6fc',
            command=self.on_position_change,
            length=320
        )
        self.position_scale.pack(fill='x', padx=5, pady=5)
        
        # Botones de control
        btn_frame = tk.Frame(playback_frame, bg='#21262d')
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        self.play_button = tk.Button(
            btn_frame, text="▶️", command=self.toggle_play,
            bg='#238636', fg='white', font=('Arial', 14, 'bold'), width=3
        )
        self.play_button.pack(side='left', padx=2)
        
        tk.Button(btn_frame, text="⏹️", command=self.stop_playback,
                 bg='#da3633', fg='white', font=('Arial', 14, 'bold'), width=3).pack(side='left', padx=2)
        tk.Button(btn_frame, text="🎧", command=self.open_in_system_player,
                 bg='#6f42c1', fg='white', font=('Arial', 14, 'bold'), width=3).pack(side='left', padx=2)
        
    def create_cue_creator(self, parent):
        cue_creator_frame = tk.LabelFrame(parent, text="🎯 Cue Creator", bg='#21262d', fg='#f0f6fc')
        cue_creator_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(cue_creator_frame, text="Name:", bg='#21262d', fg='#f0f6fc', font=('Arial', 9, 'bold')).pack(anchor='w', padx=5)
        
        self.cue_name_var = tk.StringVar()
        tk.Entry(cue_creator_frame, textvariable=self.cue_name_var, bg='#0d1117', fg='#f0f6fc').pack(fill='x', padx=5, pady=2)
        
        tk.Label(cue_creator_frame, text="Color:", bg='#21262d', fg='#f0f6fc', font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=(8, 0))
        
        self.color_var = tk.StringVar(value='Hot Red')
        ttk.Combobox(cue_creator_frame, textvariable=self.color_var, values=list(self.dj_colors.keys()), state='readonly').pack(fill='x', padx=5, pady=2)
        
        tk.Label(cue_creator_frame, text="Energy Level:", bg='#21262d', fg='#f0f6fc', font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=(8, 0))
        
        self.energy_var = tk.IntVar(value=5)
        tk.Scale(cue_creator_frame, variable=self.energy_var, from_=1, to=10, orient='horizontal', bg='#21262d', fg='#f0f6fc').pack(fill='x', padx=5, pady=2)
        
        tk.Button(cue_creator_frame, text="➕ Add Cue Point", command=self.add_cue_point,
                 bg='#238636', fg='white', font=('Arial', 10, 'bold')).pack(fill='x', padx=5, pady=8)
        
    def create_spotify_analysis_panel(self, parent):
        spotify_frame = tk.LabelFrame(parent, text="🎵 Spotify Analysis", bg='#21262d', fg='#f0f6fc')
        spotify_frame.pack(fill='x', pady=(0, 10))
        
        # Botones de análisis
        btn_frame1 = tk.Frame(spotify_frame, bg='#21262d')
        btn_frame1.pack(fill='x', padx=5, pady=5)
        
        tk.Button(btn_frame1, text="🎯 Auto Cues", command=self.suggest_cues_from_spotify,
                 bg='#1db954', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=2, fill='x', expand=True)
        tk.Button(btn_frame1, text="📊 Analysis", command=self.show_spotify_analysis,
                 bg='#fd7e14', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=2, fill='x', expand=True)

        # Botón para leer cue points embebidos
        btn_frame2 = tk.Frame(spotify_frame, bg='#21262d')
        btn_frame2.pack(fill='x', padx=5, pady=5)

        tk.Button(btn_frame2, text="🎵 Read Embedded", command=self.read_embedded_cues,
                 bg='#6f42c1', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=2, fill='x', expand=True)
        tk.Button(btn_frame2, text="🔄 Auto-Load", command=self.auto_load_all_cues,
                 bg='#238636', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=2, fill='x', expand=True)
        
        # Información de Spotify
        self.spotify_info_label = tk.Label(
            spotify_frame,
            text="Load a track to see Spotify data",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 8),
            wraplength=340,
            justify='left'
        )
        self.spotify_info_label.pack(padx=5, pady=5)

    def create_cue_panel(self, parent):
        cue_frame = tk.LabelFrame(
            parent,
            text="📋 Cue Points",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        cue_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Lista de cue points con información de origen
        columns = ('Time', 'Name', 'Energy', 'Hot', 'Source')
        self.cue_tree = ttk.Treeview(cue_frame, columns=columns, show='headings', height=12)

        for col in columns:
            self.cue_tree.heading(col, text=col)

        self.cue_tree.column('Time', width=60)
        self.cue_tree.column('Name', width=100)
        self.cue_tree.column('Energy', width=50)
        self.cue_tree.column('Hot', width=30)
        self.cue_tree.column('Source', width=60)

        cue_scrollbar = ttk.Scrollbar(cue_frame, orient='vertical', command=self.cue_tree.yview)
        self.cue_tree.configure(yscrollcommand=cue_scrollbar.set)

        self.cue_tree.pack(side='left', fill='both', expand=True)
        cue_scrollbar.pack(side='right', fill='y')

        # Botones de acción
        action_frame = tk.Frame(cue_frame, bg='#21262d')
        action_frame.pack(fill='x', pady=10)

        tk.Button(action_frame, text="🗑️ Delete", command=self.delete_selected_cue,
                 bg='#da3633', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=2)
        tk.Button(action_frame, text="💾 Save", command=self.save_cues_to_file,
                 bg='#238636', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=2)
        tk.Button(action_frame, text="📁 Load", command=self.load_cues_from_file,
                 bg='#6f42c1', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=2)
        tk.Button(action_frame, text="🧹 Clear", command=self.clear_all_cues,
                 bg='#fd7e14', fg='white', font=('Arial', 9, 'bold')).pack(side='left', padx=2)

        self.cue_tree.bind('<ButtonRelease-1>', self.on_cue_select)
        self.cue_tree.bind('<Double-1>', self.on_cue_double_click)

    def create_hotcue_panel(self):
        hotcue_frame = tk.Frame(self.root, bg='#0d1117')
        hotcue_frame.pack(fill='x', padx=5, pady=5)

        tk.Label(hotcue_frame, text="🔥 HOT CUES", font=('Arial', 16, 'bold'),
                bg='#0d1117', fg='#f85149').pack(pady=5)

        grid_frame = tk.Frame(hotcue_frame, bg='#0d1117')
        grid_frame.pack(pady=5)

        self.hotcue_buttons = {}
        for i in range(8):
            row = i // 4
            col = i % 4

            btn = tk.Button(
                grid_frame,
                text=f"{i+1}",
                width=12,
                height=3,
                command=lambda x=i+1: self.trigger_hotcue(x),
                bg='#30363d',
                fg='#8b949e',
                font=('Arial', 12, 'bold')
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
            self.hotcue_buttons[i+1] = btn

    def scan_audio_files(self):
        self.file_count_label.config(text="📁 Escaneando archivos...")
        self.root.update()

        def scan_thread():
            audio_folder = "/Volumes/KINGSTON/Audio"
            self.audio_files = AudioFileScanner.scan_audio_folder(audio_folder)
            self.root.after(0, self.update_file_list)

        threading.Thread(target=scan_thread, daemon=True).start()

    def update_file_list(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        for audio_file in self.audio_files:
            duration_str = self.format_time(audio_file.duration)
            spotify_status = "✅" if audio_file.spotify_metadata else "❌"

            self.file_tree.insert('', 'end', values=(
                audio_file.artist,
                audio_file.title,
                duration_str,
                audio_file.format,
                spotify_status
            ))

        self.file_count_label.config(text=f"📁 {len(self.audio_files)} archivos encontrados")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Audio Folder")
        if folder:
            self.file_count_label.config(text="📁 Escaneando carpeta personalizada...")
            self.root.update()

            def scan_custom_thread():
                self.audio_files = AudioFileScanner.scan_audio_folder(folder)
                self.root.after(0, self.update_file_list)

            threading.Thread(target=scan_custom_thread, daemon=True).start()

    def enhance_with_spotify(self):
        """Mejorar metadatos de todos los archivos con Spotify."""
        if not self.spotify_connected:
            messagebox.showwarning("Warning", "Spotify not connected")
            return

        self.show_notification("🎵 Enhancing library with Spotify data...")

        def enhance_thread():
            enhanced_count = 0
            for audio_file in self.audio_files:
                if not audio_file.spotify_metadata:
                    metadata = self.spotify.enhance_track_metadata(audio_file.artist, audio_file.title)
                    if metadata:
                        audio_file.spotify_metadata = metadata
                        enhanced_count += 1

                        # Actualizar UI cada 5 archivos
                        if enhanced_count % 5 == 0:
                            self.root.after(0, lambda: self.show_notification(f"🎵 Enhanced {enhanced_count} tracks..."))

                    time.sleep(0.2)  # Rate limiting

            self.root.after(0, lambda: self.show_notification(f"✅ Enhanced {enhanced_count} tracks with Spotify data"))
            self.root.after(0, self.update_file_list)

        threading.Thread(target=enhance_thread, daemon=True).start()

    def on_file_select(self, event):
        selection = self.file_tree.selection()
        if selection:
            item = selection[0]
            self.selected_file_index = self.file_tree.index(item)

    def on_file_double_click(self, event):
        self.load_selected_file()

    def load_selected_file(self):
        if self.selected_file_index >= 0 and self.selected_file_index < len(self.audio_files):
            self.current_file = self.audio_files[self.selected_file_index]
            self.current_position = 0.0
            self.cue_points.clear()

            self.update_current_file_display()
            self.update_position_controls()
            self.update_cue_list()
            self.update_hotcue_buttons()
            self.load_cues_for_current_file()
            self.update_spotify_info()

            # Mejorar con Spotify si no tiene metadatos
            if not self.current_file.spotify_metadata and self.spotify_connected:
                self.enhance_current_file_with_spotify()

            # Auto-cargar cue points embebidos
            self.auto_load_embedded_cues()

            self.show_notification(f"📁 Loaded: {self.current_file.artist} - {self.current_file.title}")
        else:
            messagebox.showwarning("Warning", "Please select a file first")

    def enhance_current_file_with_spotify(self):
        """Mejorar archivo actual con datos de Spotify."""
        def enhance_thread():
            metadata = self.spotify.enhance_track_metadata(self.current_file.artist, self.current_file.title)
            if metadata:
                self.current_file.spotify_metadata = metadata
                self.root.after(0, self.update_spotify_info)
                self.root.after(0, lambda: self.show_notification("🎵 Enhanced with Spotify data"))

        threading.Thread(target=enhance_thread, daemon=True).start()

    def update_current_file_display(self):
        if self.current_file:
            info_text = f"🎵 {self.current_file.artist}\n📀 {self.current_file.title}\n⏱️ {self.format_time(self.current_file.duration)}\n📊 {self.current_file.format} • {self.current_file.bitrate}"
            self.current_file_label.config(text=info_text, fg='#f0f6fc')
        else:
            self.current_file_label.config(text="No file loaded", fg='#8b949e')

    def update_spotify_info(self):
        """Actualizar información de Spotify del archivo actual."""
        if not self.current_file or not self.current_file.spotify_metadata:
            self.spotify_info_label.config(text="No Spotify data available", fg='#8b949e')
            return

        metadata = self.current_file.spotify_metadata
        info_text = f"🎵 Spotify Match: {metadata.get('spotify_name', 'N/A')}\n"

        if 'spotify_bpm' in metadata:
            info_text += f"🥁 BPM: {metadata['spotify_bpm']}\n"
        if 'spotify_key' in metadata:
            info_text += f"🎹 Key: {metadata['spotify_key']}\n"
        if 'spotify_energy' in metadata:
            info_text += f"⚡ Energy: {metadata['spotify_energy']}/10\n"
        if 'spotify_danceability' in metadata:
            info_text += f"💃 Danceability: {metadata['spotify_danceability']}/10"

        self.spotify_info_label.config(text=info_text, fg='#1db954')

    def suggest_cues_from_spotify(self):
        """Sugerir cue points usando análisis de Spotify."""
        if not self.current_file:
            messagebox.showwarning("Warning", "No file loaded")
            return

        if not self.spotify_connected:
            messagebox.showwarning("Warning", "Spotify not connected")
            return

        if not self.current_file.spotify_metadata or 'spotify_id' not in self.current_file.spotify_metadata:
            messagebox.showwarning("Warning", "No Spotify data for this track")
            return

        self.show_notification("🎯 Analyzing track with Spotify...")

        def suggest_thread():
            spotify_id = self.current_file.spotify_metadata['spotify_id']
            suggested_cues = self.spotify.suggest_cue_points_from_analysis(spotify_id)

            if suggested_cues:
                # Agregar cue points sugeridos
                for cue_data in suggested_cues:
                    # Buscar próximo hot cue disponible
                    hotcue_index = 0
                    for i in range(1, 9):
                        if not any(cue.hotcue_index == i for cue in self.cue_points):
                            hotcue_index = i
                            break

                    cue_point = CuePoint(
                        position=cue_data['position'],
                        type="cue",
                        color=cue_data['color'],
                        name=cue_data['name'],
                        hotcue_index=hotcue_index,
                        created_at=time.time(),
                        energy_level=cue_data['energy_level'],
                        source="spotify_analysis"
                    )

                    self.cue_points.append(cue_point)

                self.root.after(0, self.update_cue_list)
                self.root.after(0, self.update_hotcue_buttons)
                self.root.after(0, lambda: self.show_notification(f"🎯 Added {len(suggested_cues)} Spotify-suggested cue points"))
            else:
                self.root.after(0, lambda: self.show_notification("❌ No cue points could be suggested"))

        threading.Thread(target=suggest_thread, daemon=True).start()

    def show_spotify_analysis(self):
        """Mostrar análisis detallado de Spotify."""
        if not self.current_file or not self.current_file.spotify_metadata:
            messagebox.showwarning("Warning", "No Spotify data available")
            return

        metadata = self.current_file.spotify_metadata

        # Crear ventana de análisis
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("🎵 Spotify Analysis")
        analysis_window.geometry("500x600")
        analysis_window.configure(bg='#0d1117')
        analysis_window.resizable(False, False)

        # Título
        tk.Label(
            analysis_window,
            text=f"🎵 {metadata.get('spotify_name', 'Unknown')}",
            font=('Arial', 16, 'bold'),
            bg='#0d1117',
            fg='#1db954'
        ).pack(pady=10)

        tk.Label(
            analysis_window,
            text=f"by {metadata.get('spotify_artist', 'Unknown')}",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#8b949e'
        ).pack(pady=(0, 20))

        # Frame para datos
        data_frame = tk.Frame(analysis_window, bg='#21262d')
        data_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Información básica
        basic_info = [
            ("🎵 Track", metadata.get('spotify_name', 'N/A')),
            ("👨‍🎤 Artist", metadata.get('spotify_artist', 'N/A')),
            ("💿 Album", metadata.get('spotify_album', 'N/A')),
            ("📊 Popularity", f"{metadata.get('spotify_popularity', 0)}/100"),
            ("⏱️ Duration", f"{metadata.get('spotify_duration_ms', 0) / 1000:.1f}s"),
        ]

        for label, value in basic_info:
            row_frame = tk.Frame(data_frame, bg='#21262d')
            row_frame.pack(fill='x', pady=2)

            tk.Label(row_frame, text=label, bg='#21262d', fg='#f0f6fc',
                    font=('Arial', 10, 'bold'), width=15, anchor='w').pack(side='left')
            tk.Label(row_frame, text=value, bg='#21262d', fg='#8b949e',
                    font=('Arial', 10), anchor='w').pack(side='left', padx=(10, 0))

        # Separador
        tk.Frame(data_frame, height=2, bg='#30363d').pack(fill='x', pady=10)

        # Características de audio
        audio_features = [
            ("🥁 BPM", metadata.get('spotify_bpm', 'N/A')),
            ("🎹 Key", metadata.get('spotify_key', 'N/A')),
            ("⚡ Energy", f"{metadata.get('spotify_energy', 0)}/10"),
            ("💃 Danceability", f"{metadata.get('spotify_danceability', 0)}/10"),
            ("😊 Valence", f"{metadata.get('spotify_valence', 0)}/10"),
            ("🎤 Acousticness", f"{metadata.get('spotify_acousticness', 0)}/10"),
            ("🎼 Instrumentalness", f"{metadata.get('spotify_instrumentalness', 0)}/10"),
            ("🎵 Time Signature", f"{metadata.get('spotify_time_signature', 4)}/4"),
        ]

        for label, value in audio_features:
            row_frame = tk.Frame(data_frame, bg='#21262d')
            row_frame.pack(fill='x', pady=2)

            tk.Label(row_frame, text=label, bg='#21262d', fg='#f0f6fc',
                    font=('Arial', 10, 'bold'), width=15, anchor='w').pack(side='left')
            tk.Label(row_frame, text=str(value), bg='#21262d', fg='#8b949e',
                    font=('Arial', 10), anchor='w').pack(side='left', padx=(10, 0))

        # Botón cerrar
        tk.Button(
            analysis_window,
            text="Close",
            command=analysis_window.destroy,
            bg='#238636',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(pady=20)

    def read_embedded_cues(self):
        """Leer cue points embebidos del archivo actual."""
        if not self.current_file:
            messagebox.showwarning("Warning", "No file loaded")
            return

        self.show_notification("🔍 Reading embedded cue points...")

        def read_thread():
            try:
                metadata = self.metadata_reader.scan_file(self.current_file.path)
                embedded_cues = metadata.get('cue_points', [])

                if embedded_cues:
                    # Convertir EmbeddedCuePoint a CuePoint
                    for embedded_cue in embedded_cues:
                        # Buscar próximo hot cue disponible
                        hotcue_index = 0
                        for i in range(1, 9):
                            if not any(cue.hotcue_index == i for cue in self.cue_points):
                                hotcue_index = i
                                break

                        cue_point = CuePoint(
                            position=embedded_cue.position,
                            type=embedded_cue.type,
                            color=embedded_cue.color,
                            name=embedded_cue.name,
                            hotcue_index=hotcue_index,
                            created_at=embedded_cue.created_at,
                            energy_level=embedded_cue.energy_level,
                            source=f"embedded_{embedded_cue.software}"
                        )

                        self.cue_points.append(cue_point)

                    self.root.after(0, self.update_cue_list)
                    self.root.after(0, self.update_hotcue_buttons)
                    self.root.after(0, lambda: self.show_notification(f"🎵 Loaded {len(embedded_cues)} embedded cue points from {embedded_cues[0].software}"))
                else:
                    self.root.after(0, lambda: self.show_notification("❌ No embedded cue points found"))

            except Exception as e:
                self.root.after(0, lambda: self.show_notification(f"❌ Error reading embedded cues: {str(e)}"))

        threading.Thread(target=read_thread, daemon=True).start()

    def auto_load_all_cues(self):
        """Cargar automáticamente cue points de todas las fuentes."""
        if not self.current_file:
            messagebox.showwarning("Warning", "No file loaded")
            return

        self.show_notification("🔄 Auto-loading cue points from all sources...")

        def auto_load_thread():
            try:
                # 1. Leer cue points embebidos
                metadata = self.metadata_reader.scan_file(self.current_file.path)
                embedded_cues = metadata.get('cue_points', [])

                # 2. Leer cue points de archivos JSON
                self.root.after(0, self.load_cues_for_current_file)

                # 3. Agregar cue points embebidos si no hay conflictos
                if embedded_cues:
                    for embedded_cue in embedded_cues:
                        # Verificar si ya existe un cue point en posición similar
                        exists = any(abs(cue.position - embedded_cue.position) < 2.0 for cue in self.cue_points)

                        if not exists:
                            # Buscar próximo hot cue disponible
                            hotcue_index = 0
                            for i in range(1, 9):
                                if not any(cue.hotcue_index == i for cue in self.cue_points):
                                    hotcue_index = i
                                    break

                            cue_point = CuePoint(
                                position=embedded_cue.position,
                                type=embedded_cue.type,
                                color=embedded_cue.color,
                                name=embedded_cue.name,
                                hotcue_index=hotcue_index,
                                created_at=embedded_cue.created_at,
                                energy_level=embedded_cue.energy_level,
                                source=f"embedded_{embedded_cue.software}"
                            )

                            self.cue_points.append(cue_point)

                # 4. Sugerir cue points de Spotify si está conectado
                if self.spotify_connected and self.current_file.spotify_metadata and 'spotify_id' in self.current_file.spotify_metadata:
                    spotify_id = self.current_file.spotify_metadata['spotify_id']
                    suggested_cues = self.spotify.suggest_cue_points_from_analysis(spotify_id)

                    for cue_data in suggested_cues:
                        # Verificar si ya existe
                        exists = any(abs(cue.position - cue_data['position']) < 2.0 for cue in self.cue_points)

                        if not exists:
                            hotcue_index = 0
                            for i in range(1, 9):
                                if not any(cue.hotcue_index == i for cue in self.cue_points):
                                    hotcue_index = i
                                    break

                            cue_point = CuePoint(
                                position=cue_data['position'],
                                type="cue",
                                color=cue_data['color'],
                                name=cue_data['name'],
                                hotcue_index=hotcue_index,
                                created_at=time.time(),
                                energy_level=cue_data['energy_level'],
                                source="spotify_analysis"
                            )

                            self.cue_points.append(cue_point)

                self.root.after(0, self.update_cue_list)
                self.root.after(0, self.update_hotcue_buttons)

                total_cues = len(self.cue_points)
                embedded_count = len([c for c in self.cue_points if c.source.startswith('embedded')])
                spotify_count = len([c for c in self.cue_points if c.source == 'spotify_analysis'])
                json_count = len([c for c in self.cue_points if c.source == 'manual'])

                message = f"🔄 Auto-loaded {total_cues} total cue points"
                if embedded_count > 0:
                    message += f" ({embedded_count} embedded"
                if spotify_count > 0:
                    message += f", {spotify_count} Spotify"
                if json_count > 0:
                    message += f", {json_count} saved"
                if embedded_count > 0 or spotify_count > 0 or json_count > 0:
                    message += ")"

                self.root.after(0, lambda: self.show_notification(message))

            except Exception as e:
                self.root.after(0, lambda: self.show_notification(f"❌ Error in auto-load: {str(e)}"))

        threading.Thread(target=auto_load_thread, daemon=True).start()

    def auto_load_embedded_cues(self):
        """Auto-cargar cue points embebidos al cargar archivo."""
        if not self.current_file:
            return

        def load_thread():
            try:
                metadata = self.metadata_reader.scan_file(self.current_file.path)
                embedded_cues = metadata.get('cue_points', [])

                if embedded_cues:
                    print(f"🎵 Found {len(embedded_cues)} embedded cue points from {embedded_cues[0].software}")

                    # Agregar cue points embebidos (siempre, sin verificar si hay existentes)
                    for embedded_cue in embedded_cues:
                        # Verificar si ya existe un cue point en posición similar
                        exists = any(abs(cue.position - embedded_cue.position) < 2.0 for cue in self.cue_points)

                        if not exists:
                            hotcue_index = 0
                            for i in range(1, 9):
                                if not any(cue.hotcue_index == i for cue in self.cue_points):
                                    hotcue_index = i
                                    break

                            cue_point = CuePoint(
                                position=embedded_cue.position,
                                type=embedded_cue.type,
                                color=embedded_cue.color,
                                name=embedded_cue.name,
                                hotcue_index=hotcue_index,
                                created_at=embedded_cue.created_at,
                                energy_level=embedded_cue.energy_level,
                                source=f"embedded_{embedded_cue.software}"
                            )

                            self.cue_points.append(cue_point)

                    self.root.after(0, self.update_cue_list)
                    self.root.after(0, self.update_hotcue_buttons)

                    # Mostrar notificación visible
                    software = embedded_cues[0].software.title()
                    added_count = len([c for c in self.cue_points if c.source.startswith('embedded')])
                    self.root.after(0, lambda: self.show_notification(f"🎵 Auto-loaded {added_count} {software} cue points"))

            except Exception as e:
                print(f"❌ Error auto-loading embedded cues: {e}")

        threading.Thread(target=load_thread, daemon=True).start()

    def update_position_controls(self):
        if self.current_file:
            self.position_scale.config(to=self.current_file.duration)
            self.position_scale.set(0)
            self.update_position_display()
        else:
            self.position_scale.config(to=300)
            self.position_var.set("0:00 / 0:00")

    def update_position_display(self):
        if self.current_file:
            current_str = self.format_time(self.current_position)
            total_str = self.format_time(self.current_file.duration)
            self.position_var.set(f"{current_str} / {total_str}")
        else:
            self.position_var.set("0:00 / 0:00")

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def on_position_change(self, value):
        self.current_position = float(value)
        self.update_position_display()

    def toggle_play(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "No file loaded")
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_button.config(text="⏸️", bg='#fd7e14')
            self.simulate_playback()
        else:
            self.play_button.config(text="▶️", bg='#238636')

    def stop_playback(self):
        self.is_playing = False
        self.current_position = 0.0
        self.position_scale.set(0)
        self.update_position_display()
        self.play_button.config(text="▶️", bg='#238636')

    def simulate_playback(self):
        if self.is_playing and self.current_file and self.current_position < self.current_file.duration:
            self.current_position += 0.1
            self.position_scale.set(self.current_position)
            self.update_position_display()
            self.root.after(100, self.simulate_playback)
        elif self.current_position >= (self.current_file.duration if self.current_file else 0):
            self.stop_playback()

    def open_in_system_player(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "No file loaded")
            return

        try:
            if platform.system() == "Darwin":
                subprocess.run(["open", self.current_file.path])
            elif platform.system() == "Windows":
                os.startfile(self.current_file.path)
            else:
                subprocess.run(["xdg-open", self.current_file.path])

            self.show_notification(f"🎧 Opening: {self.current_file.title}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def add_cue_point(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "No file loaded")
            return

        name = self.cue_name_var.get().strip()
        if not name:
            name = f"Cue {len(self.cue_points) + 1}"

        color = self.dj_colors.get(self.color_var.get(), '#FF0000')
        energy = self.energy_var.get()

        hotcue_index = 0
        for i in range(1, 9):
            if not any(cue.hotcue_index == i for cue in self.cue_points):
                hotcue_index = i
                break

        cue_point = CuePoint(
            position=self.current_position,
            type="cue",
            color=color,
            name=name,
            hotcue_index=hotcue_index,
            created_at=time.time(),
            energy_level=energy,
            source="manual"
        )

        self.cue_points.append(cue_point)
        self.update_cue_list()
        self.update_hotcue_buttons()
        self.cue_name_var.set("")

        self.show_notification(f"✅ Added: {name} @ {self.format_time(self.current_position)}")

    def update_cue_list(self):
        for item in self.cue_tree.get_children():
            self.cue_tree.delete(item)

        sorted_cues = sorted(self.cue_points, key=lambda x: x.position)
        for cue in sorted_cues:
            hotcue_text = f"#{cue.hotcue_index}" if cue.hotcue_index > 0 else "-"
            energy_text = f"{cue.energy_level}/10"
            source_text = "🎵" if cue.source == "spotify_analysis" else "👤" if cue.source == "manual" else "🤖"

            self.cue_tree.insert('', 'end', values=(
                self.format_time(cue.position),
                cue.name,
                energy_text,
                hotcue_text,
                source_text
            ))

    def update_hotcue_buttons(self):
        for i in range(1, 9):
            self.hotcue_buttons[i].config(text=str(i), bg='#30363d', fg='#8b949e')

        for cue in self.cue_points:
            if 1 <= cue.hotcue_index <= 8:
                btn = self.hotcue_buttons[cue.hotcue_index]
                btn.config(
                    text=f"{cue.hotcue_index}\n{cue.name[:6]}",
                    bg=cue.color,
                    fg='#000000' if self.is_light_color(cue.color) else '#ffffff'
                )

    def is_light_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness > 128

    def trigger_hotcue(self, hotcue_num):
        for cue in self.cue_points:
            if cue.hotcue_index == hotcue_num:
                self.current_position = cue.position
                self.position_scale.set(self.current_position)
                self.update_position_display()
                self.show_notification(f"🔥 Hot Cue {hotcue_num}: {cue.name}")
                return

        self.show_notification(f"🔥 Hot Cue {hotcue_num}: Not assigned")

    def on_cue_select(self, event):
        pass

    def on_cue_double_click(self, event):
        selection = self.cue_tree.selection()
        if selection:
            item = selection[0]
            index = self.cue_tree.index(item)
            sorted_cues = sorted(self.cue_points, key=lambda x: x.position)

            if 0 <= index < len(sorted_cues):
                cue = sorted_cues[index]
                self.current_position = cue.position
                self.position_scale.set(self.current_position)
                self.update_position_display()
                self.show_notification(f"🎯 Jump to: {cue.name}")

    def delete_selected_cue(self):
        selection = self.cue_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a cue point to delete")
            return

        item = selection[0]
        index = self.cue_tree.index(item)
        sorted_cues = sorted(self.cue_points, key=lambda x: x.position)

        if 0 <= index < len(sorted_cues):
            cue_to_delete = sorted_cues[index]
            self.cue_points.remove(cue_to_delete)
            self.update_cue_list()
            self.update_hotcue_buttons()
            self.show_notification(f"🗑️ Deleted: {cue_to_delete.name}")

    def clear_all_cues(self):
        if not self.cue_points:
            messagebox.showinfo("Info", "No cue points to clear")
            return

        result = messagebox.askyesno("Confirm", f"Clear all {len(self.cue_points)} cue points?")
        if result:
            self.cue_points.clear()
            self.update_cue_list()
            self.update_hotcue_buttons()
            self.show_notification("🧹 All cue points cleared")

    def save_cues_to_file(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "No file loaded")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Cue Points",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialvalue=f"{self.current_file.artist} - {self.current_file.title}_cues.json"
        )

        if filename:
            try:
                data = {
                    'version': '2.1',
                    'file_info': asdict(self.current_file),
                    'cue_points': [asdict(cue) for cue in self.cue_points],
                    'spotify_enhanced': bool(self.current_file.spotify_metadata),
                    'created_at': time.time()
                }

                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

                self.show_notification(f"💾 Saved {len(self.cue_points)} cue points")

            except Exception as e:
                messagebox.showerror("Error", f"Error saving file: {e}")

    def load_cues_from_file(self):
        filename = filedialog.askopenfilename(
            title="Load Cue Points",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                self.cue_points = []
                for cue_data in data.get('cue_points', []):
                    if 'energy_level' not in cue_data:
                        cue_data['energy_level'] = 5
                    if 'source' not in cue_data:
                        cue_data['source'] = 'manual'

                    cue = CuePoint(**cue_data)
                    self.cue_points.append(cue)

                self.update_cue_list()
                self.update_hotcue_buttons()

                spotify_enhanced = data.get('spotify_enhanced', False)
                message = f"📁 Loaded {len(self.cue_points)} cue points"
                if spotify_enhanced:
                    message += " (Spotify enhanced)"

                self.show_notification(message)

            except Exception as e:
                messagebox.showerror("Error", f"Error loading file: {e}")

    def load_cues_for_current_file(self):
        """Cargar cue points automáticamente para el archivo actual con búsqueda mejorada."""
        if not self.current_file:
            return

        # Limpiar nombres para búsqueda
        artist_clean = self.clean_filename(self.current_file.artist)
        title_clean = self.clean_filename(self.current_file.title)

        # Múltiples patrones de búsqueda
        search_patterns = [
            f"{self.current_file.artist} - {self.current_file.title}_cues.json",
            f"{artist_clean} - {title_clean}_cues.json",
            f"{self.current_file.artist} - {self.current_file.title.split('(')[0].strip()}_cues.json",
            f"{artist_clean} - {title_clean.split('(')[0].strip()}_cues.json"
        ]

        # Buscar en múltiples ubicaciones
        search_paths = [
            ".",  # Directorio actual
            "/Volumes/KINGSTON/DjAlfin",  # Directorio del proyecto
            os.path.dirname(self.current_file.path) if self.current_file.path else "."  # Directorio del archivo
        ]

        print(f"🔍 Searching cue points for: {self.current_file.artist} - {self.current_file.title}")

        cue_file_found = None

        # Buscar archivo de cue points
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue

            for pattern in search_patterns:
                full_path = os.path.join(search_path, pattern)
                print(f"   Checking: {full_path}")

                if os.path.exists(full_path):
                    cue_file_found = full_path
                    print(f"✅ Found cue file: {full_path}")
                    break

            if cue_file_found:
                break

        if not cue_file_found:
            print(f"❌ No cue points found for: {self.current_file.artist} - {self.current_file.title}")
            return

        # Cargar archivo de cue points
        try:
            with open(cue_file_found, 'r') as f:
                data = json.load(f)

            self.cue_points = []
            cue_points_data = data.get('cue_points', [])

            for cue_data in cue_points_data:
                # Asegurar compatibilidad con versiones anteriores
                if 'energy_level' not in cue_data:
                    cue_data['energy_level'] = 5
                if 'source' not in cue_data:
                    cue_data['source'] = 'manual'

                cue = CuePoint(**cue_data)
                self.cue_points.append(cue)

            self.update_cue_list()
            self.update_hotcue_buttons()

            # Verificar si es archivo con datos de Spotify
            spotify_enhanced = data.get('spotify_enhanced', False)
            demo_file = data.get('demo_file', False)

            message = f"📁 Auto-loaded {len(self.cue_points)} cue points"
            if spotify_enhanced:
                message += " (🎵 Spotify enhanced)"
            if demo_file:
                message += " (🎯 Demo file)"

            self.show_notification(message)
            print(f"✅ Loaded {len(self.cue_points)} cue points from {os.path.basename(cue_file_found)}")

        except Exception as e:
            print(f"❌ Error auto-loading cues from {cue_file_found}: {e}")
            self.show_notification(f"❌ Error loading cue points: {str(e)}")

    def clean_filename(self, name):
        """Limpiar nombre de archivo para búsqueda."""
        # Remover caracteres problemáticos
        cleaned = name.replace("_PN", "").replace("_", " ")
        # Remover espacios extra
        cleaned = " ".join(cleaned.split())
        return cleaned.strip()

    def show_notification(self, message):
        notification = tk.Toplevel(self.root)
        notification.title("Notification")
        notification.geometry("450x100")
        notification.configure(bg='#0d1117')
        notification.resizable(False, False)

        notification.transient(self.root)
        notification.grab_set()

        tk.Label(
            notification,
            text=message,
            font=('Arial', 12, 'bold'),
            bg='#0d1117',
            fg='#58a6ff',
            wraplength=430
        ).pack(expand=True)

        self.root.after(3000, notification.destroy)

    def run(self):
        print("🎯 DjAlfin Desktop - Spotify Enhanced")
        print("🎵 Loading real audio files with Spotify integration")
        print("✨ Professional cue point management with AI suggestions")

        self.root.mainloop()

def main():
    try:
        app = DjAlfinDesktopSpotify()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
