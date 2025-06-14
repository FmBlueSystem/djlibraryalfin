#!/usr/bin/env python3
"""
🎯 DjAlfin - Interfaz de Usuario Mejorada para Cue Points
Prototipo con interfaz profesional estilo DJ software comercial
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json
import os
import time
import math
import random
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

@dataclass
class CuePoint:
    """Estructura de cue point mejorada."""
    position: float
    type: str
    color: str
    name: str
    hotcue_index: int
    created_at: float
    energy_level: int = 5  # 1-10
    
class DjAlfinCuePointUI:
    """Interfaz de usuario mejorada para cue points."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin Pro - Cue Points Studio")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(True, True)
        
        # Configurar estilo
        self.setup_styles()
        
        # Variables del estado
        self.cue_points: List[CuePoint] = []
        self.current_position = 0.0
        self.track_duration = 300.0  # 5 minutos
        self.is_playing = False
        self.bpm = 128
        self.key = "A minor"
        self.track_name = "Demo Track - Progressive House"
        self.waveform_data = self.generate_waveform_data()
        
        # Colores profesionales
        self.dj_colors = {
            'Hot Red': '#FF0000',
            'Electric Orange': '#FF6600', 
            'Neon Yellow': '#FFFF00',
            'Laser Green': '#00FF00',
            'Cyber Cyan': '#00FFFF',
            'Electric Blue': '#0066FF',
            'Neon Purple': '#9900FF',
            'Hot Pink': '#FF00CC',
            'White': '#FFFFFF',
            'Silver': '#C0C0C0'
        }
        
        self.setup_ui()
        self.load_demo_data()
        self.start_animations()
        
    def setup_styles(self):
        """Configurar estilos profesionales."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores oscuros
        style.configure('Dark.TFrame', background='#2a2a2a')
        style.configure('Dark.TLabel', background='#2a2a2a', foreground='#ffffff')
        style.configure('Dark.TButton', background='#3a3a3a', foreground='#ffffff')
        
    def setup_ui(self):
        """Configurar interfaz de usuario mejorada."""
        
        # Header principal
        self.create_header()
        
        # Frame principal con tres columnas
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Columna izquierda - Controles
        self.create_control_panel(main_frame)
        
        # Columna central - Waveform y timeline
        self.create_waveform_panel(main_frame)
        
        # Columna derecha - Lista y propiedades
        self.create_info_panel(main_frame)
        
        # Footer con hot cues
        self.create_hotcue_panel()
        
    def create_header(self):
        """Crear header profesional."""
        header_frame = tk.Frame(self.root, bg='#0d1117', height=80)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        # Logo y título
        title_frame = tk.Frame(header_frame, bg='#0d1117')
        title_frame.pack(side='left', fill='y', padx=20)
        
        title_label = tk.Label(
            title_frame,
            text="🎯 DjAlfin Pro",
            font=('Arial', 24, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        )
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(
            title_frame,
            text="Professional Cue Point Studio",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#8b949e'
        )
        subtitle_label.pack(anchor='w')
        
        # Información del track
        track_frame = tk.Frame(header_frame, bg='#0d1117')
        track_frame.pack(side='right', fill='y', padx=20)
        
        self.track_info_label = tk.Label(
            track_frame,
            text=f"🎵 {self.track_name}",
            font=('Arial', 14, 'bold'),
            bg='#0d1117',
            fg='#f0f6fc'
        )
        self.track_info_label.pack(anchor='e')
        
        self.track_details_label = tk.Label(
            track_frame,
            text=f"🥁 {self.bpm} BPM • 🎹 {self.key} • ⏱️ {self.format_time(self.track_duration)}",
            font=('Arial', 10),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.track_details_label.pack(anchor='e')
        
    def create_control_panel(self, parent):
        """Crear panel de controles."""
        control_frame = tk.Frame(parent, bg='#21262d', relief='raised', bd=2)
        control_frame.pack(side='left', fill='y', padx=(0, 5))
        control_frame.configure(width=300)
        control_frame.pack_propagate(False)
        
        # Título del panel
        tk.Label(
            control_frame,
            text="🎛️ CONTROL PANEL",
            font=('Arial', 14, 'bold'),
            bg='#21262d',
            fg='#58a6ff'
        ).pack(pady=10)
        
        # Controles de reproducción
        self.create_playback_controls(control_frame)
        
        # Controles de cue points
        self.create_cue_controls(control_frame)
        
        # Análisis automático
        self.create_analysis_controls(control_frame)
        
    def create_playback_controls(self, parent):
        """Crear controles de reproducción."""
        playback_frame = tk.LabelFrame(
            parent,
            text="▶️ Playback",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        playback_frame.pack(fill='x', padx=10, pady=5)
        
        # Display de posición
        position_frame = tk.Frame(playback_frame, bg='#21262d')
        position_frame.pack(fill='x', pady=5)
        
        self.position_var = tk.StringVar(value="0:00")
        position_display = tk.Label(
            position_frame,
            textvariable=self.position_var,
            font=('Courier', 20, 'bold'),
            bg='#0d1117',
            fg='#f85149',
            relief='sunken',
            bd=2,
            padx=10,
            pady=5
        )
        position_display.pack(fill='x')
        
        # Slider de posición
        self.position_scale = tk.Scale(
            playback_frame,
            from_=0,
            to=self.track_duration,
            orient='horizontal',
            bg='#21262d',
            fg='#f0f6fc',
            highlightbackground='#21262d',
            troughcolor='#0d1117',
            activebackground='#58a6ff',
            command=self.on_position_change,
            length=250
        )
        self.position_scale.pack(fill='x', pady=5)
        
        # Botones de control
        button_frame = tk.Frame(playback_frame, bg='#21262d')
        button_frame.pack(fill='x', pady=5)
        
        self.play_button = tk.Button(
            button_frame,
            text="▶️",
            command=self.toggle_play,
            bg='#238636',
            fg='white',
            font=('Arial', 16, 'bold'),
            width=3,
            relief='raised',
            bd=3
        )
        self.play_button.pack(side='left', padx=2)
        
        tk.Button(
            button_frame,
            text="⏹️",
            command=self.stop_playback,
            bg='#da3633',
            fg='white',
            font=('Arial', 16, 'bold'),
            width=3,
            relief='raised',
            bd=3
        ).pack(side='left', padx=2)
        
        tk.Button(
            button_frame,
            text="⏮️",
            command=self.previous_cue,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 16, 'bold'),
            width=3,
            relief='raised',
            bd=3
        ).pack(side='left', padx=2)
        
        tk.Button(
            button_frame,
            text="⏭️",
            command=self.next_cue,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 16, 'bold'),
            width=3,
            relief='raised',
            bd=3
        ).pack(side='left', padx=2)
        
    def create_cue_controls(self, parent):
        """Crear controles de cue points."""
        cue_frame = tk.LabelFrame(
            parent,
            text="🎯 Cue Point Creator",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        cue_frame.pack(fill='x', padx=10, pady=5)
        
        # Nombre del cue
        tk.Label(
            cue_frame,
            text="Name:",
            bg='#21262d',
            fg='#f0f6fc',
            font=('Arial', 10, 'bold')
        ).pack(anchor='w')
        
        self.cue_name_var = tk.StringVar()
        name_entry = tk.Entry(
            cue_frame,
            textvariable=self.cue_name_var,
            bg='#0d1117',
            fg='#f0f6fc',
            insertbackground='#f0f6fc',
            font=('Arial', 11)
        )
        name_entry.pack(fill='x', pady=2)
        
        # Selector de color
        color_frame = tk.Frame(cue_frame, bg='#21262d')
        color_frame.pack(fill='x', pady=5)
        
        tk.Label(
            color_frame,
            text="Color:",
            bg='#21262d',
            fg='#f0f6fc',
            font=('Arial', 10, 'bold')
        ).pack(side='left')
        
        self.color_var = tk.StringVar(value='Hot Red')
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_var,
            values=list(self.dj_colors.keys()),
            state='readonly',
            width=12
        )
        color_combo.pack(side='left', padx=(5, 0))
        
        tk.Button(
            color_frame,
            text="🎨",
            command=self.choose_custom_color,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=3
        ).pack(side='right')
        
        # Nivel de energía
        energy_frame = tk.Frame(cue_frame, bg='#21262d')
        energy_frame.pack(fill='x', pady=5)
        
        tk.Label(
            energy_frame,
            text="Energy:",
            bg='#21262d',
            fg='#f0f6fc',
            font=('Arial', 10, 'bold')
        ).pack(side='left')
        
        self.energy_var = tk.IntVar(value=5)
        energy_scale = tk.Scale(
            energy_frame,
            variable=self.energy_var,
            from_=1,
            to=10,
            orient='horizontal',
            bg='#21262d',
            fg='#f0f6fc',
            highlightbackground='#21262d',
            length=150
        )
        energy_scale.pack(side='right')
        
        # Botón agregar
        tk.Button(
            cue_frame,
            text="➕ Add Cue Point",
            command=self.add_cue_point,
            bg='#238636',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=3
        ).pack(fill='x', pady=10)
        
    def create_analysis_controls(self, parent):
        """Crear controles de análisis."""
        analysis_frame = tk.LabelFrame(
            parent,
            text="🤖 Auto Analysis",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        analysis_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(
            analysis_frame,
            text="🔍 Detect Cue Points",
            command=self.auto_detect_cues,
            bg='#0969da',
            fg='white',
            font=('Arial', 11, 'bold')
        ).pack(fill='x', pady=2)
        
        tk.Button(
            analysis_frame,
            text="🎵 Analyze Energy",
            command=self.analyze_energy,
            bg='#0969da',
            fg='white',
            font=('Arial', 11, 'bold')
        ).pack(fill='x', pady=2)
        
        tk.Button(
            analysis_frame,
            text="🥁 Find Beat Grid",
            command=self.find_beat_grid,
            bg='#0969da',
            fg='white',
            font=('Arial', 11, 'bold')
        ).pack(fill='x', pady=2)
        
        tk.Button(
            analysis_frame,
            text="🎹 Detect Key",
            command=self.detect_key,
            bg='#0969da',
            fg='white',
            font=('Arial', 11, 'bold')
        ).pack(fill='x', pady=2)
        
    def create_waveform_panel(self, parent):
        """Crear panel de waveform principal."""
        waveform_frame = tk.Frame(parent, bg='#0d1117', relief='raised', bd=2)
        waveform_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # Título
        tk.Label(
            waveform_frame,
            text="🌊 WAVEFORM STUDIO",
            font=('Arial', 14, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(pady=10)
        
        # Canvas principal para waveform
        self.waveform_canvas = tk.Canvas(
            waveform_frame,
            bg='#000000',
            height=200,
            highlightthickness=2,
            highlightbackground='#30363d'
        )
        self.waveform_canvas.pack(fill='x', padx=10, pady=5)
        
        # Timeline
        self.timeline_canvas = tk.Canvas(
            waveform_frame,
            bg='#161b22',
            height=40,
            highlightthickness=1,
            highlightbackground='#30363d'
        )
        self.timeline_canvas.pack(fill='x', padx=10, pady=5)
        
        # Zoom controls
        zoom_frame = tk.Frame(waveform_frame, bg='#0d1117')
        zoom_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            zoom_frame,
            text="🔍 Zoom:",
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Arial', 10, 'bold')
        ).pack(side='left')
        
        self.zoom_var = tk.DoubleVar(value=1.0)
        zoom_scale = tk.Scale(
            zoom_frame,
            variable=self.zoom_var,
            from_=0.5,
            to=5.0,
            resolution=0.1,
            orient='horizontal',
            bg='#0d1117',
            fg='#f0f6fc',
            command=self.on_zoom_change,
            length=200
        )
        zoom_scale.pack(side='left', padx=10)
        
        # Bind eventos
        self.waveform_canvas.bind('<Button-1>', self.on_waveform_click)
        self.waveform_canvas.bind('<B1-Motion>', self.on_waveform_drag)
        
    def create_info_panel(self, parent):
        """Crear panel de información."""
        info_frame = tk.Frame(parent, bg='#21262d', relief='raised', bd=2)
        info_frame.pack(side='right', fill='y', padx=(5, 0))
        info_frame.configure(width=350)
        info_frame.pack_propagate(False)
        
        # Título
        tk.Label(
            info_frame,
            text="📋 CUE POINT LIST",
            font=('Arial', 14, 'bold'),
            bg='#21262d',
            fg='#58a6ff'
        ).pack(pady=10)
        
        # Lista de cue points
        list_frame = tk.Frame(info_frame, bg='#21262d')
        list_frame.pack(fill='both', expand=True, padx=10)
        
        # Treeview con estilo
        columns = ('Time', 'Name', 'Energy', 'Hot')
        self.cue_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=12
        )
        
        # Configurar columnas
        self.cue_tree.heading('Time', text='Time')
        self.cue_tree.heading('Name', text='Name')
        self.cue_tree.heading('Energy', text='Energy')
        self.cue_tree.heading('Hot', text='Hot')
        
        self.cue_tree.column('Time', width=60)
        self.cue_tree.column('Name', width=120)
        self.cue_tree.column('Energy', width=60)
        self.cue_tree.column('Hot', width=40)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.cue_tree.yview)
        self.cue_tree.configure(yscrollcommand=scrollbar.set)
        
        self.cue_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botones de acción
        action_frame = tk.Frame(info_frame, bg='#21262d')
        action_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(
            action_frame,
            text="🗑️ Delete",
            command=self.delete_selected_cue,
            bg='#da3633',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            action_frame,
            text="📁 Load",
            command=self.load_cues_from_file,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            action_frame,
            text="💾 Save",
            command=self.save_cues_to_file,
            bg='#238636',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        # Propiedades del cue seleccionado
        props_frame = tk.LabelFrame(
            info_frame,
            text="🎯 Cue Properties",
            font=('Arial', 11, 'bold'),
            bg='#21262d',
            fg='#f0f6fc'
        )
        props_frame.pack(fill='x', padx=10, pady=5)
        
        self.props_text = tk.Text(
            props_frame,
            height=6,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 9),
            wrap='word'
        )
        self.props_text.pack(fill='x', padx=5, pady=5)
        
        # Bind eventos
        self.cue_tree.bind('<ButtonRelease-1>', self.on_cue_select)
        self.cue_tree.bind('<Double-1>', self.on_cue_double_click)
        
    def create_hotcue_panel(self):
        """Crear panel de hot cues."""
        hotcue_frame = tk.Frame(self.root, bg='#0d1117', relief='raised', bd=2)
        hotcue_frame.pack(fill='x', padx=5, pady=5)
        
        # Título
        tk.Label(
            hotcue_frame,
            text="🔥 HOT CUES",
            font=('Arial', 16, 'bold'),
            bg='#0d1117',
            fg='#f85149'
        ).pack(pady=5)
        
        # Grid de hot cues
        grid_frame = tk.Frame(hotcue_frame, bg='#0d1117')
        grid_frame.pack(pady=10)
        
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
                font=('Arial', 14, 'bold'),
                relief='raised',
                bd=3
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
            self.hotcue_buttons[i+1] = btn
        
        # Configurar grid
        for i in range(4):
            grid_frame.columnconfigure(i, weight=1)

    def generate_waveform_data(self):
        """Generar datos de waveform realistas."""
        data = []
        for i in range(1000):
            # Simular diferentes secciones de la canción
            pos = i / 1000.0

            if pos < 0.1:  # Intro
                intensity = 0.3 + 0.2 * math.sin(pos * 20)
            elif pos < 0.25:  # Build up
                intensity = 0.3 + pos * 2
            elif pos < 0.5:  # Main section
                intensity = 0.8 + 0.2 * math.sin(pos * 50)
            elif pos < 0.75:  # Breakdown
                intensity = 0.4 + 0.3 * math.sin(pos * 30)
            else:  # Outro
                intensity = 0.8 - (pos - 0.75) * 2

            # Agregar ruido
            intensity += random.uniform(-0.1, 0.1)
            intensity = max(0, min(1, intensity))
            data.append(intensity)

        return data

    def load_demo_data(self):
        """Cargar datos de demostración."""
        demo_cues = [
            CuePoint(15.5, "cue", "#FF0000", "Intro Drop", 1, time.time(), 7),
            CuePoint(45.2, "cue", "#FF6600", "Verse Start", 2, time.time(), 5),
            CuePoint(75.8, "cue", "#FFFF00", "Pre-Chorus", 3, time.time(), 6),
            CuePoint(105.3, "cue", "#00FF00", "Main Drop", 4, time.time(), 9),
            CuePoint(135.7, "cue", "#00FFFF", "Breakdown", 5, time.time(), 3),
            CuePoint(165.1, "cue", "#0066FF", "Build Up", 6, time.time(), 7),
            CuePoint(195.4, "cue", "#9900FF", "Final Drop", 7, time.time(), 10),
            CuePoint(225.8, "cue", "#FF00CC", "Outro", 8, time.time(), 4),
        ]

        self.cue_points = demo_cues
        self.update_displays()

    def start_animations(self):
        """Iniciar animaciones y actualizaciones."""
        self.update_waveform()
        self.update_timeline()
        self.root.after(50, self.animation_loop)

    def animation_loop(self):
        """Loop principal de animación."""
        if self.is_playing:
            self.current_position += 0.05
            if self.current_position >= self.track_duration:
                self.stop_playback()
            else:
                self.position_scale.set(self.current_position)
                self.update_position_display()
                self.update_waveform()

        self.root.after(50, self.animation_loop)

    def update_displays(self):
        """Actualizar todas las pantallas."""
        self.update_cue_list()
        self.update_hotcue_buttons()
        self.update_waveform()
        self.update_timeline()

    def update_waveform(self):
        """Actualizar visualización del waveform."""
        self.waveform_canvas.delete("all")

        width = self.waveform_canvas.winfo_width()
        height = self.waveform_canvas.winfo_height()

        if width <= 1:
            self.root.after(100, self.update_waveform)
            return

        # Calcular zoom y offset
        zoom = self.zoom_var.get()
        samples_per_pixel = len(self.waveform_data) / (width * zoom)
        start_sample = int((self.current_position / self.track_duration) * len(self.waveform_data))

        # Dibujar waveform
        for x in range(width):
            sample_idx = int(start_sample + x * samples_per_pixel)
            if 0 <= sample_idx < len(self.waveform_data):
                intensity = self.waveform_data[sample_idx]
                bar_height = int(intensity * height * 0.8)

                y1 = (height - bar_height) // 2
                y2 = y1 + bar_height

                # Color basado en intensidad
                if intensity > 0.7:
                    color = '#ff4444'
                elif intensity > 0.4:
                    color = '#ffaa00'
                else:
                    color = '#4488ff'

                self.waveform_canvas.create_rectangle(
                    x, y1, x + 1, y2,
                    fill=color, outline=color
                )

        # Dibujar línea de posición
        pos_x = width // 2
        self.waveform_canvas.create_line(
            pos_x, 0, pos_x, height,
            fill='#ffffff', width=2
        )

        # Dibujar marcadores de cue points
        for cue in self.cue_points:
            cue_time = cue.position
            relative_pos = (cue_time - (self.current_position - self.track_duration * zoom / 2)) / (self.track_duration * zoom)

            if 0 <= relative_pos <= 1:
                cue_x = int(relative_pos * width)
                self.waveform_canvas.create_line(
                    cue_x, 0, cue_x, height,
                    fill=cue.color, width=3
                )

                # Etiqueta
                self.waveform_canvas.create_text(
                    cue_x, 15,
                    text=cue.name[:8],
                    fill=cue.color,
                    font=('Arial', 8, 'bold'),
                    anchor='n'
                )

    def update_timeline(self):
        """Actualizar timeline."""
        self.timeline_canvas.delete("all")

        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()

        if width <= 1:
            return

        # Dibujar marcas de tiempo
        zoom = self.zoom_var.get()
        time_range = self.track_duration * zoom
        start_time = self.current_position - time_range / 2

        for i in range(int(time_range) + 1):
            time_pos = start_time + i
            if 0 <= time_pos <= self.track_duration:
                x = int((i / time_range) * width)

                # Línea de marca
                self.timeline_canvas.create_line(
                    x, height - 10, x, height,
                    fill='#8b949e', width=1
                )

                # Etiqueta de tiempo
                if i % 10 == 0:  # Solo cada 10 segundos
                    self.timeline_canvas.create_text(
                        x, height - 15,
                        text=self.format_time(time_pos),
                        fill='#f0f6fc',
                        font=('Arial', 8),
                        anchor='s'
                    )

    def update_cue_list(self):
        """Actualizar lista de cue points."""
        # Limpiar lista
        for item in self.cue_tree.get_children():
            self.cue_tree.delete(item)

        # Agregar cue points ordenados por posición
        sorted_cues = sorted(self.cue_points, key=lambda x: x.position)
        for cue in sorted_cues:
            hotcue_text = f"#{cue.hotcue_index}" if cue.hotcue_index > 0 else "-"
            energy_text = f"{cue.energy_level}/10"

            item = self.cue_tree.insert('', 'end', values=(
                self.format_time(cue.position),
                cue.name,
                energy_text,
                hotcue_text
            ))

            # Colorear según el color del cue
            self.cue_tree.set(item, 'Time', self.format_time(cue.position))

    def update_hotcue_buttons(self):
        """Actualizar botones de hot cue."""
        # Resetear todos los botones
        for i in range(1, 9):
            self.hotcue_buttons[i].config(
                text=str(i),
                bg='#30363d',
                fg='#8b949e'
            )

        # Configurar botones asignados
        for cue in self.cue_points:
            if 1 <= cue.hotcue_index <= 8:
                btn = self.hotcue_buttons[cue.hotcue_index]
                btn.config(
                    text=f"{cue.hotcue_index}\n{cue.name[:8]}",
                    bg=cue.color,
                    fg='#000000' if self.is_light_color(cue.color) else '#ffffff'
                )

    def is_light_color(self, hex_color):
        """Determinar si un color es claro."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness > 128

    def format_time(self, seconds):
        """Formatear tiempo en MM:SS."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def update_position_display(self):
        """Actualizar display de posición."""
        self.position_var.set(self.format_time(self.current_position))

    # Event handlers
    def on_position_change(self, value):
        """Manejar cambio de posición."""
        self.current_position = float(value)
        self.update_position_display()
        self.update_waveform()

    def on_zoom_change(self, value):
        """Manejar cambio de zoom."""
        self.update_waveform()
        self.update_timeline()

    def on_waveform_click(self, event):
        """Manejar clic en waveform."""
        width = self.waveform_canvas.winfo_width()
        zoom = self.zoom_var.get()
        time_range = self.track_duration * zoom
        start_time = self.current_position - time_range / 2

        click_ratio = event.x / width
        new_time = start_time + click_ratio * time_range

        if 0 <= new_time <= self.track_duration:
            self.current_position = new_time
            self.position_scale.set(self.current_position)
            self.update_position_display()
            self.update_waveform()

    def on_waveform_drag(self, event):
        """Manejar arrastre en waveform."""
        self.on_waveform_click(event)

    def on_cue_select(self, event):
        """Manejar selección de cue point."""
        selection = self.cue_tree.selection()
        if selection:
            item = selection[0]
            index = self.cue_tree.index(item)
            sorted_cues = sorted(self.cue_points, key=lambda x: x.position)

            if 0 <= index < len(sorted_cues):
                cue = sorted_cues[index]
                self.show_cue_properties(cue)

    def on_cue_double_click(self, event):
        """Manejar doble clic en cue point."""
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
                self.update_waveform()

    def show_cue_properties(self, cue):
        """Mostrar propiedades del cue point."""
        self.props_text.delete(1.0, tk.END)

        props = f"""Name: {cue.name}
Position: {self.format_time(cue.position)}
Type: {cue.type.title()}
Color: {cue.color}
Hot Cue: {cue.hotcue_index if cue.hotcue_index > 0 else 'None'}
Energy: {cue.energy_level}/10
Created: {time.strftime('%H:%M:%S', time.localtime(cue.created_at))}
"""

        self.props_text.insert(1.0, props)

    # Control functions
    def toggle_play(self):
        """Alternar reproducción."""
        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_button.config(text="⏸️", bg='#fd7e14')
        else:
            self.play_button.config(text="▶️", bg='#238636')

    def stop_playback(self):
        """Detener reproducción."""
        self.is_playing = False
        self.current_position = 0.0
        self.position_scale.set(0)
        self.update_position_display()
        self.play_button.config(text="▶️", bg='#238636')
        self.update_waveform()

    def previous_cue(self):
        """Ir al cue point anterior."""
        current_pos = self.current_position
        previous_cue = None

        for cue in sorted(self.cue_points, key=lambda x: x.position, reverse=True):
            if cue.position < current_pos - 1.0:  # Al menos 1 segundo antes
                previous_cue = cue
                break

        if previous_cue:
            self.current_position = previous_cue.position
            self.position_scale.set(self.current_position)
            self.update_position_display()
            self.update_waveform()
            self.show_notification(f"⏮️ {previous_cue.name}")

    def next_cue(self):
        """Ir al siguiente cue point."""
        current_pos = self.current_position
        next_cue = None

        for cue in sorted(self.cue_points, key=lambda x: x.position):
            if cue.position > current_pos + 1.0:  # Al menos 1 segundo después
                next_cue = cue
                break

        if next_cue:
            self.current_position = next_cue.position
            self.position_scale.set(self.current_position)
            self.update_position_display()
            self.update_waveform()
            self.show_notification(f"⏭️ {next_cue.name}")

    def add_cue_point(self):
        """Agregar nuevo cue point."""
        name = self.cue_name_var.get().strip()
        if not name:
            name = f"Cue {len(self.cue_points) + 1}"

        color = self.dj_colors.get(self.color_var.get(), '#FF0000')
        energy = self.energy_var.get()

        # Buscar próximo hot cue disponible
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
            energy_level=energy
        )

        self.cue_points.append(cue_point)
        self.update_displays()

        # Limpiar entrada
        self.cue_name_var.set("")

        self.show_notification(f"✅ Added: {name} @ {self.format_time(self.current_position)}")

    def delete_selected_cue(self):
        """Eliminar cue point seleccionado."""
        selection = self.cue_tree.selection()
        if not selection:
            self.show_notification("⚠️ Select a cue point to delete")
            return

        item = selection[0]
        index = self.cue_tree.index(item)
        sorted_cues = sorted(self.cue_points, key=lambda x: x.position)

        if 0 <= index < len(sorted_cues):
            cue_to_delete = sorted_cues[index]
            self.cue_points.remove(cue_to_delete)
            self.update_displays()
            self.show_notification(f"🗑️ Deleted: {cue_to_delete.name}")

    def trigger_hotcue(self, hotcue_num):
        """Activar hot cue."""
        for cue in self.cue_points:
            if cue.hotcue_index == hotcue_num:
                self.current_position = cue.position
                self.position_scale.set(self.current_position)
                self.update_position_display()
                self.update_waveform()
                self.show_notification(f"🔥 Hot Cue {hotcue_num}: {cue.name}")
                return

        self.show_notification(f"🔥 Hot Cue {hotcue_num}: Not assigned")

    def choose_custom_color(self):
        """Elegir color personalizado."""
        color = colorchooser.askcolor(title="Choose Cue Point Color")
        if color[1]:  # Si se seleccionó un color
            hex_color = color[1].upper()
            # Agregar a la lista temporal
            self.dj_colors['Custom'] = hex_color
            self.color_var.set('Custom')
            self.show_notification(f"🎨 Custom color: {hex_color}")

    # Analysis functions
    def auto_detect_cues(self):
        """Detectar cue points automáticamente."""
        self.show_notification("🔍 Analyzing track for cue points...")

        # Simular detección automática
        self.root.after(1000, self._complete_auto_detection)

    def _complete_auto_detection(self):
        """Completar detección automática."""
        # Generar cue points basados en análisis simulado
        auto_cues = []

        # Detectar cambios de energía
        for i in range(5):
            pos = random.uniform(20, self.track_duration - 20)
            energy = random.randint(6, 10)
            color = list(self.dj_colors.values())[i % len(self.dj_colors)]

            auto_cue = CuePoint(
                position=pos,
                type="cue",
                color=color,
                name=f"Auto {i+1}",
                hotcue_index=0,  # No asignar hot cue automáticamente
                created_at=time.time(),
                energy_level=energy
            )
            auto_cues.append(auto_cue)

        self.cue_points.extend(auto_cues)
        self.update_displays()
        self.show_notification(f"✅ Detected {len(auto_cues)} cue points automatically")

    def analyze_energy(self):
        """Analizar energía del track."""
        self.show_notification("🎵 Analyzing energy levels...")

        # Simular análisis de energía
        self.root.after(1500, lambda: self.show_notification("✅ Energy analysis complete"))

    def find_beat_grid(self):
        """Encontrar beat grid."""
        self.show_notification("🥁 Analyzing beat grid...")

        # Simular análisis de beats
        self.root.after(1200, lambda: self.show_notification(f"✅ Beat grid found: {self.bpm} BPM"))

    def detect_key(self):
        """Detectar tonalidad."""
        keys = ["C major", "G major", "D major", "A major", "E major", "B major",
                "F# major", "C# major", "A minor", "E minor", "B minor", "F# minor"]

        detected_key = random.choice(keys)
        self.key = detected_key

        # Actualizar display
        self.track_details_label.config(
            text=f"🥁 {self.bpm} BPM • 🎹 {self.key} • ⏱️ {self.format_time(self.track_duration)}"
        )

        self.show_notification(f"🎹 Key detected: {detected_key}")

    # File operations
    def save_cues_to_file(self):
        """Guardar cue points a archivo."""
        filename = filedialog.asksaveasfilename(
            title="Save Cue Points",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                data = {
                    'version': '2.0',
                    'track_name': self.track_name,
                    'track_duration': self.track_duration,
                    'bpm': self.bpm,
                    'key': self.key,
                    'cue_points': [asdict(cue) for cue in self.cue_points],
                    'created_at': time.time()
                }

                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

                self.show_notification(f"💾 Saved to {os.path.basename(filename)}")

            except Exception as e:
                messagebox.showerror("Error", f"Error saving file: {e}")

    def load_cues_from_file(self):
        """Cargar cue points desde archivo."""
        filename = filedialog.askopenfilename(
            title="Load Cue Points",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Cargar datos del track
                self.track_name = data.get('track_name', 'Loaded Track')
                self.track_duration = data.get('track_duration', 300.0)
                self.bpm = data.get('bpm', 128)
                self.key = data.get('key', 'Unknown')

                # Cargar cue points
                self.cue_points = []
                for cue_data in data.get('cue_points', []):
                    # Asegurar compatibilidad con versiones anteriores
                    if 'energy_level' not in cue_data:
                        cue_data['energy_level'] = 5

                    cue = CuePoint(**cue_data)
                    self.cue_points.append(cue)

                # Actualizar displays
                self.position_scale.config(to=self.track_duration)
                self.track_info_label.config(text=f"🎵 {self.track_name}")
                self.track_details_label.config(
                    text=f"🥁 {self.bpm} BPM • 🎹 {self.key} • ⏱️ {self.format_time(self.track_duration)}"
                )

                self.update_displays()

                self.show_notification(f"📁 Loaded {len(self.cue_points)} cue points")

            except Exception as e:
                messagebox.showerror("Error", f"Error loading file: {e}")

    def show_notification(self, message):
        """Mostrar notificación temporal."""
        # Crear ventana de notificación
        notification = tk.Toplevel(self.root)
        notification.title("Notification")
        notification.geometry("300x80")
        notification.configure(bg='#0d1117')
        notification.resizable(False, False)

        # Centrar en pantalla
        notification.transient(self.root)
        notification.grab_set()

        # Mensaje
        tk.Label(
            notification,
            text=message,
            font=('Arial', 12, 'bold'),
            bg='#0d1117',
            fg='#58a6ff',
            wraplength=280
        ).pack(expand=True)

        # Auto-cerrar después de 2 segundos
        self.root.after(2000, notification.destroy)

    def run(self):
        """Ejecutar la aplicación."""
        print("🎯 DjAlfin Pro - Cue Points Studio")
        print("🎧 Enhanced UI with professional features")
        print("✨ Ready for professional DJ use")

        self.root.mainloop()

def main():
    """Función principal."""
    try:
        app = DjAlfinCuePointUI()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
