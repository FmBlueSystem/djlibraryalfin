#!/usr/bin/env python3
"""
🎯 DjAlfin - Desktop Completo con Archivos Reales
Versión completa que funciona con archivos de audio reales de /Volumes/KINGSTON/Audio
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
from typing import List, Optional

@dataclass
class CuePoint:
    position: float
    type: str
    color: str
    name: str
    hotcue_index: int
    created_at: float
    energy_level: int = 5
    source: str = "manual"

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

class DjAlfinDesktopComplete:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin Desktop - Real Audio Files")
        self.root.geometry("1400x900")
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
        # Header
        header_frame = tk.Frame(self.root, bg='#0d1117', height=70)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎯 DjAlfin Desktop - Real Audio Files",
            font=('Arial', 20, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(side='left', padx=20, pady=20)
        
        self.file_count_label = tk.Label(
            header_frame,
            text="📁 Escaneando archivos...",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.file_count_label.pack(side='right', padx=20, pady=20)
        
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
        
        # Lista de archivos
        columns = ('Artist', 'Title', 'Duration', 'Format')
        self.file_tree = ttk.Treeview(
            file_frame,
            columns=columns,
            show='headings',
            height=20
        )
        
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(file_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botones
        btn_frame = tk.Frame(file_frame, bg='#21262d')
        btn_frame.pack(fill='x', pady=10)
        
        tk.Button(btn_frame, text="🔄 Rescan", command=self.scan_audio_files,
                 bg='#0969da', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=2)
        tk.Button(btn_frame, text="📁 Browse", command=self.browse_folder,
                 bg='#6f42c1', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=2)
        tk.Button(btn_frame, text="▶️ Load", command=self.load_selected_file,
                 bg='#238636', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=2)
        
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
        control_frame.configure(width=350)
        control_frame.pack_propagate(False)
        
        # Información del archivo actual
        info_frame = tk.LabelFrame(control_frame, text="🎵 Current Track", bg='#21262d', fg='#f0f6fc')
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.current_file_label = tk.Label(
            info_frame,
            text="No file loaded",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 10),
            wraplength=300,
            justify='left'
        )
        self.current_file_label.pack(padx=10, pady=10)
        
        # Controles de reproducción
        playback_frame = tk.LabelFrame(control_frame, text="▶️ Playback", bg='#21262d', fg='#f0f6fc')
        playback_frame.pack(fill='x', pady=(0, 10))
        
        self.position_var = tk.StringVar(value="0:00 / 0:00")
        tk.Label(
            playback_frame,
            textvariable=self.position_var,
            font=('Courier', 16, 'bold'),
            bg='#0d1117',
            fg='#f85149',
            relief='sunken',
            bd=2,
            padx=10,
            pady=8
        ).pack(fill='x', padx=5, pady=5)
        
        self.position_scale = tk.Scale(
            playback_frame,
            from_=0,
            to=300,
            orient='horizontal',
            bg='#21262d',
            fg='#f0f6fc',
            command=self.on_position_change,
            length=300
        )
        self.position_scale.pack(fill='x', padx=5, pady=5)
        
        # Botones de control
        btn_frame = tk.Frame(playback_frame, bg='#21262d')
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        self.play_button = tk.Button(
            btn_frame, text="▶️", command=self.toggle_play,
            bg='#238636', fg='white', font=('Arial', 16, 'bold'), width=4
        )
        self.play_button.pack(side='left', padx=2)
        
        tk.Button(btn_frame, text="⏹️", command=self.stop_playback,
                 bg='#da3633', fg='white', font=('Arial', 16, 'bold'), width=4).pack(side='left', padx=2)
        tk.Button(btn_frame, text="🎧", command=self.open_in_system_player,
                 bg='#6f42c1', fg='white', font=('Arial', 16, 'bold'), width=4).pack(side='left', padx=2)
        
        # Creador de cue points
        cue_creator_frame = tk.LabelFrame(control_frame, text="🎯 Cue Creator", bg='#21262d', fg='#f0f6fc')
        cue_creator_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(cue_creator_frame, text="Name:", bg='#21262d', fg='#f0f6fc', font=('Arial', 10, 'bold')).pack(anchor='w', padx=5)
        
        self.cue_name_var = tk.StringVar()
        tk.Entry(cue_creator_frame, textvariable=self.cue_name_var, bg='#0d1117', fg='#f0f6fc').pack(fill='x', padx=5, pady=2)
        
        tk.Label(cue_creator_frame, text="Color:", bg='#21262d', fg='#f0f6fc', font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=(10, 0))
        
        self.color_var = tk.StringVar(value='Hot Red')
        ttk.Combobox(cue_creator_frame, textvariable=self.color_var, values=list(self.dj_colors.keys()), state='readonly').pack(fill='x', padx=5, pady=2)
        
        tk.Label(cue_creator_frame, text="Energy Level:", bg='#21262d', fg='#f0f6fc', font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=(10, 0))
        
        self.energy_var = tk.IntVar(value=5)
        tk.Scale(cue_creator_frame, variable=self.energy_var, from_=1, to=10, orient='horizontal', bg='#21262d', fg='#f0f6fc').pack(fill='x', padx=5, pady=2)
        
        tk.Button(cue_creator_frame, text="➕ Add Cue Point", command=self.add_cue_point,
                 bg='#238636', fg='white', font=('Arial', 12, 'bold')).pack(fill='x', padx=5, pady=10)

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

        # Lista de cue points
        columns = ('Time', 'Name', 'Energy', 'Hot')
        self.cue_tree = ttk.Treeview(cue_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.cue_tree.heading(col, text=col)
            self.cue_tree.column(col, width=80)

        cue_scrollbar = ttk.Scrollbar(cue_frame, orient='vertical', command=self.cue_tree.yview)
        self.cue_tree.configure(yscrollcommand=cue_scrollbar.set)

        self.cue_tree.pack(side='left', fill='both', expand=True)
        cue_scrollbar.pack(side='right', fill='y')

        # Botones de acción
        action_frame = tk.Frame(cue_frame, bg='#21262d')
        action_frame.pack(fill='x', pady=10)

        tk.Button(action_frame, text="🗑️ Delete", command=self.delete_selected_cue,
                 bg='#da3633', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=2)
        tk.Button(action_frame, text="💾 Save", command=self.save_cues_to_file,
                 bg='#238636', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=2)
        tk.Button(action_frame, text="📁 Load", command=self.load_cues_from_file,
                 bg='#6f42c1', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=2)

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
                font=('Arial', 14, 'bold')
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

            self.file_tree.insert('', 'end', values=(
                audio_file.artist,
                audio_file.title,
                duration_str,
                audio_file.format
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

            self.show_notification(f"📁 Loaded: {self.current_file.artist} - {self.current_file.title}")
        else:
            messagebox.showwarning("Warning", "Please select a file first")

    def update_current_file_display(self):
        if self.current_file:
            info_text = f"🎵 {self.current_file.artist}\n📀 {self.current_file.title}\n⏱️ {self.format_time(self.current_file.duration)}\n📊 {self.current_file.format} • {self.current_file.bitrate}"
            self.current_file_label.config(text=info_text, fg='#f0f6fc')
        else:
            self.current_file_label.config(text="No file loaded", fg='#8b949e')

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

            self.cue_tree.insert('', 'end', values=(
                self.format_time(cue.position),
                cue.name,
                energy_text,
                hotcue_text
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
                    'version': '2.0',
                    'file_info': asdict(self.current_file),
                    'cue_points': [asdict(cue) for cue in self.cue_points],
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

                    cue = CuePoint(**cue_data)
                    self.cue_points.append(cue)

                self.update_cue_list()
                self.update_hotcue_buttons()

                self.show_notification(f"📁 Loaded {len(self.cue_points)} cue points")

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
        notification.geometry("400x100")
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
            wraplength=380
        ).pack(expand=True)

        self.root.after(2500, notification.destroy)

    def run(self):
        print("🎯 DjAlfin Desktop - Real Audio Files")
        print("🎵 Loading real audio files from /Volumes/KINGSTON/Audio")
        print("✨ Professional cue point management with real files")

        self.root.mainloop()

def main():
    try:
        app = DjAlfinDesktopComplete()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
