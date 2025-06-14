#!/usr/bin/env python3
"""
🎯 DjAlfin - Prototipo Aislado de Cue Points
Prototipo independiente para probar el sistema de cue points sin afectar la app principal
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

@dataclass
class CuePoint:
    """Estructura de cue point para el prototipo."""
    position: float
    type: str
    color: str
    name: str
    hotcue_index: int
    created_at: float

class CuePointPrototype:
    """Prototipo aislado del sistema de cue points."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Prototipo Cue Points")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        
        # Datos del prototipo
        self.cue_points: List[CuePoint] = []
        self.current_position = 0.0
        self.track_duration = 240.0  # 4 minutos de ejemplo
        self.is_playing = False
        self.current_file = None
        
        # Colores predefinidos
        self.colors = {
            'Red': '#FF0000',
            'Orange': '#FF8000',
            'Yellow': '#FFFF00',
            'Green': '#00FF00',
            'Cyan': '#00FFFF',
            'Blue': '#0000FF',
            'Purple': '#8000FF',
            'Pink': '#FF00FF'
        }
        
        self.setup_ui()
        self.load_demo_cues()
        
    def setup_ui(self):
        """Configurar la interfaz de usuario."""
        
        # Título principal
        title_frame = tk.Frame(self.root, bg='#2c3e50')
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = tk.Label(
            title_frame,
            text="🎯 DjAlfin - Prototipo de Cue Points",
            font=('Arial', 16, 'bold'),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Sistema independiente para probar funcionalidades de cue points",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='#bdc3c7'
        )
        subtitle_label.pack()
        
        # Frame principal dividido
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Panel izquierdo - Controles
        self.setup_control_panel(main_frame)
        
        # Panel derecho - Lista de cue points
        self.setup_cue_list_panel(main_frame)
        
        # Panel inferior - Waveform simulado
        self.setup_waveform_panel()
        
    def setup_control_panel(self, parent):
        """Configurar panel de controles."""
        control_frame = tk.LabelFrame(
            parent,
            text="🎛️ Controles",
            font=('Arial', 12, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            padx=10,
            pady=10
        )
        control_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Información del track
        info_frame = tk.Frame(control_frame, bg='#34495e')
        info_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            info_frame,
            text="📁 Track: Demo Track.mp3",
            font=('Arial', 10, 'bold'),
            bg='#34495e',
            fg='#3498db'
        ).pack(anchor='w')
        
        tk.Label(
            info_frame,
            text="⏱️ Duración: 4:00",
            font=('Arial', 9),
            bg='#34495e',
            fg='#95a5a6'
        ).pack(anchor='w')
        
        # Controles de reproducción
        playback_frame = tk.LabelFrame(
            control_frame,
            text="▶️ Reproducción",
            bg='#34495e',
            fg='#ecf0f1'
        )
        playback_frame.pack(fill='x', pady=(0, 10))
        
        # Posición actual
        position_frame = tk.Frame(playback_frame, bg='#34495e')
        position_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(
            position_frame,
            text="Posición:",
            bg='#34495e',
            fg='#ecf0f1'
        ).pack(side='left')
        
        self.position_var = tk.StringVar(value="0:00")
        self.position_label = tk.Label(
            position_frame,
            textvariable=self.position_var,
            font=('Arial', 12, 'bold'),
            bg='#34495e',
            fg='#e74c3c'
        )
        self.position_label.pack(side='right')
        
        # Slider de posición
        self.position_scale = tk.Scale(
            playback_frame,
            from_=0,
            to=self.track_duration,
            orient='horizontal',
            bg='#34495e',
            fg='#ecf0f1',
            highlightbackground='#34495e',
            command=self.on_position_change
        )
        self.position_scale.pack(fill='x', padx=5, pady=5)
        
        # Botones de reproducción
        button_frame = tk.Frame(playback_frame, bg='#34495e')
        button_frame.pack(fill='x', padx=5, pady=5)
        
        self.play_button = tk.Button(
            button_frame,
            text="▶️ Play",
            command=self.toggle_play,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        self.play_button.pack(side='left', padx=(0, 5))
        
        tk.Button(
            button_frame,
            text="⏹️ Stop",
            command=self.stop_playback,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=(0, 5))
        
        # Controles de cue points
        cue_control_frame = tk.LabelFrame(
            control_frame,
            text="🎯 Cue Points",
            bg='#34495e',
            fg='#ecf0f1'
        )
        cue_control_frame.pack(fill='x', pady=(0, 10))
        
        # Agregar cue point
        add_frame = tk.Frame(cue_control_frame, bg='#34495e')
        add_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(
            add_frame,
            text="Nombre:",
            bg='#34495e',
            fg='#ecf0f1'
        ).pack(side='left')
        
        self.cue_name_var = tk.StringVar()
        self.cue_name_entry = tk.Entry(
            add_frame,
            textvariable=self.cue_name_var,
            width=15
        )
        self.cue_name_entry.pack(side='left', padx=(5, 0))
        
        # Color selector
        color_frame = tk.Frame(cue_control_frame, bg='#34495e')
        color_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(
            color_frame,
            text="Color:",
            bg='#34495e',
            fg='#ecf0f1'
        ).pack(side='left')
        
        self.color_var = tk.StringVar(value='Red')
        self.color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_var,
            values=list(self.colors.keys()),
            state='readonly',
            width=12
        )
        self.color_combo.pack(side='left', padx=(5, 0))
        
        # Botón agregar
        tk.Button(
            cue_control_frame,
            text="➕ Agregar Cue Point",
            command=self.add_cue_point,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(fill='x', padx=5, pady=5)
        
        # Hot Cues
        hotcue_frame = tk.LabelFrame(
            control_frame,
            text="🔥 Hot Cues",
            bg='#34495e',
            fg='#ecf0f1'
        )
        hotcue_frame.pack(fill='both', expand=True)
        
        # Grid de hot cues
        self.hotcue_buttons = {}
        for i in range(8):
            row = i // 4
            col = i % 4
            
            btn = tk.Button(
                hotcue_frame,
                text=f"{i+1}",
                width=8,
                height=2,
                command=lambda x=i+1: self.trigger_hotcue(x),
                bg='#7f8c8d',
                fg='white',
                font=('Arial', 12, 'bold')
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
            self.hotcue_buttons[i+1] = btn
        
        # Configurar grid
        for i in range(4):
            hotcue_frame.columnconfigure(i, weight=1)
        for i in range(2):
            hotcue_frame.rowconfigure(i, weight=1)
    
    def setup_cue_list_panel(self, parent):
        """Configurar panel de lista de cue points."""
        list_frame = tk.LabelFrame(
            parent,
            text="📋 Lista de Cue Points",
            font=('Arial', 12, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            padx=10,
            pady=10
        )
        list_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Treeview para lista
        columns = ('Position', 'Name', 'Type', 'Color', 'HotCue')
        self.cue_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.cue_tree.heading('Position', text='Posición')
        self.cue_tree.heading('Name', text='Nombre')
        self.cue_tree.heading('Type', text='Tipo')
        self.cue_tree.heading('Color', text='Color')
        self.cue_tree.heading('HotCue', text='Hot Cue')
        
        self.cue_tree.column('Position', width=80)
        self.cue_tree.column('Name', width=120)
        self.cue_tree.column('Type', width=80)
        self.cue_tree.column('Color', width=80)
        self.cue_tree.column('HotCue', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.cue_tree.yview)
        self.cue_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview y scrollbar
        self.cue_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botones de acción
        action_frame = tk.Frame(list_frame, bg='#34495e')
        action_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(
            action_frame,
            text="🗑️ Eliminar",
            command=self.delete_selected_cue,
            bg='#e74c3c',
            fg='white'
        ).pack(side='left', padx=(0, 5))
        
        tk.Button(
            action_frame,
            text="📁 Cargar",
            command=self.load_cues_from_file,
            bg='#f39c12',
            fg='white'
        ).pack(side='left', padx=(0, 5))
        
        tk.Button(
            action_frame,
            text="💾 Guardar",
            command=self.save_cues_to_file,
            bg='#27ae60',
            fg='white'
        ).pack(side='left')
        
        # Bind eventos
        self.cue_tree.bind('<Double-1>', self.on_cue_double_click)
    
    def setup_waveform_panel(self):
        """Configurar panel de waveform simulado."""
        waveform_frame = tk.LabelFrame(
            self.root,
            text="🌊 Waveform (Simulado)",
            font=('Arial', 12, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            padx=10,
            pady=10
        )
        waveform_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        # Canvas para waveform
        self.waveform_canvas = tk.Canvas(
            waveform_frame,
            height=80,
            bg='#2c3e50',
            highlightthickness=0
        )
        self.waveform_canvas.pack(fill='x', padx=5, pady=5)
        
        # Dibujar waveform inicial
        self.draw_waveform()
    
    def draw_waveform(self):
        """Dibujar waveform simulado."""
        self.waveform_canvas.delete("all")
        
        width = self.waveform_canvas.winfo_width()
        height = self.waveform_canvas.winfo_height()
        
        if width <= 1:  # Canvas no inicializado
            self.root.after(100, self.draw_waveform)
            return
        
        # Dibujar barras de waveform simulado
        import random
        bar_width = 2
        num_bars = width // bar_width
        
        for i in range(num_bars):
            x = i * bar_width
            bar_height = random.randint(10, height - 10)
            y1 = (height - bar_height) // 2
            y2 = y1 + bar_height
            
            # Color basado en la intensidad
            intensity = bar_height / height
            if intensity > 0.7:
                color = '#e74c3c'  # Rojo para alta intensidad
            elif intensity > 0.4:
                color = '#f39c12'  # Naranja para media intensidad
            else:
                color = '#3498db'  # Azul para baja intensidad
            
            self.waveform_canvas.create_rectangle(
                x, y1, x + bar_width - 1, y2,
                fill=color, outline=color
            )
        
        # Dibujar línea de posición actual
        pos_x = (self.current_position / self.track_duration) * width
        self.waveform_canvas.create_line(
            pos_x, 0, pos_x, height,
            fill='#ecf0f1', width=2
        )
        
        # Dibujar marcadores de cue points
        for cue in self.cue_points:
            cue_x = (cue.position / self.track_duration) * width
            self.waveform_canvas.create_line(
                cue_x, 0, cue_x, height,
                fill=cue.color, width=3
            )
            
            # Etiqueta del cue
            self.waveform_canvas.create_text(
                cue_x, 10,
                text=cue.name[:8],
                fill=cue.color,
                font=('Arial', 8, 'bold'),
                anchor='n'
            )
    
    def load_demo_cues(self):
        """Cargar cue points de demostración."""
        demo_cues = [
            CuePoint(16.5, "cue", "#FF0000", "Intro", 1, time.time()),
            CuePoint(48.2, "cue", "#FF8000", "Verse", 2, time.time()),
            CuePoint(80.7, "cue", "#FFFF00", "Chorus", 3, time.time()),
            CuePoint(112.3, "cue", "#00FF00", "Bridge", 4, time.time()),
            CuePoint(144.8, "cue", "#00FFFF", "Drop", 5, time.time()),
            CuePoint(176.1, "cue", "#0000FF", "Outro", 6, time.time()),
        ]
        
        self.cue_points = demo_cues
        self.update_cue_list()
        self.update_hotcue_buttons()
        self.draw_waveform()
    
    def add_cue_point(self):
        """Agregar nuevo cue point."""
        name = self.cue_name_var.get().strip()
        if not name:
            name = f"Cue {len(self.cue_points) + 1}"
        
        color = self.colors[self.color_var.get()]
        
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
            created_at=time.time()
        )
        
        self.cue_points.append(cue_point)
        self.cue_points.sort(key=lambda x: x.position)
        
        self.update_cue_list()
        self.update_hotcue_buttons()
        self.draw_waveform()
        
        # Limpiar entrada
        self.cue_name_var.set("")
        
        messagebox.showinfo("Éxito", f"Cue point '{name}' agregado en {self.format_time(self.current_position)}")
    
    def delete_selected_cue(self):
        """Eliminar cue point seleccionado."""
        selection = self.cue_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un cue point para eliminar")
            return
        
        item = selection[0]
        index = self.cue_tree.index(item)
        
        if 0 <= index < len(self.cue_points):
            cue_name = self.cue_points[index].name
            del self.cue_points[index]
            
            self.update_cue_list()
            self.update_hotcue_buttons()
            self.draw_waveform()
            
            messagebox.showinfo("Éxito", f"Cue point '{cue_name}' eliminado")
    
    def trigger_hotcue(self, hotcue_num):
        """Activar hot cue."""
        for cue in self.cue_points:
            if cue.hotcue_index == hotcue_num:
                self.current_position = cue.position
                self.position_scale.set(self.current_position)
                self.update_position_display()
                self.draw_waveform()
                messagebox.showinfo("Hot Cue", f"Saltando a {cue.name} ({self.format_time(cue.position)})")
                return
        
        messagebox.showinfo("Hot Cue", f"Hot Cue {hotcue_num} no asignado")
    
    def on_cue_double_click(self, event):
        """Manejar doble clic en cue point."""
        selection = self.cue_tree.selection()
        if selection:
            item = selection[0]
            index = self.cue_tree.index(item)
            
            if 0 <= index < len(self.cue_points):
                cue = self.cue_points[index]
                self.current_position = cue.position
                self.position_scale.set(self.current_position)
                self.update_position_display()
                self.draw_waveform()
    
    def toggle_play(self):
        """Alternar reproducción."""
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_button.config(text="⏸️ Pause", bg='#f39c12')
            self.simulate_playback()
        else:
            self.play_button.config(text="▶️ Play", bg='#27ae60')
    
    def stop_playback(self):
        """Detener reproducción."""
        self.is_playing = False
        self.current_position = 0.0
        self.position_scale.set(0)
        self.update_position_display()
        self.play_button.config(text="▶️ Play", bg='#27ae60')
        self.draw_waveform()
    
    def simulate_playback(self):
        """Simular reproducción."""
        if self.is_playing and self.current_position < self.track_duration:
            self.current_position += 0.1
            self.position_scale.set(self.current_position)
            self.update_position_display()
            self.draw_waveform()
            self.root.after(100, self.simulate_playback)
        elif self.current_position >= self.track_duration:
            self.stop_playback()
    
    def on_position_change(self, value):
        """Manejar cambio de posición."""
        self.current_position = float(value)
        self.update_position_display()
        self.draw_waveform()
    
    def update_position_display(self):
        """Actualizar display de posición."""
        self.position_var.set(self.format_time(self.current_position))
    
    def format_time(self, seconds):
        """Formatear tiempo en MM:SS."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def update_cue_list(self):
        """Actualizar lista de cue points."""
        # Limpiar lista
        for item in self.cue_tree.get_children():
            self.cue_tree.delete(item)
        
        # Agregar cue points
        for cue in self.cue_points:
            hotcue_text = f"Hot {cue.hotcue_index}" if cue.hotcue_index > 0 else "-"
            self.cue_tree.insert('', 'end', values=(
                self.format_time(cue.position),
                cue.name,
                cue.type.title(),
                cue.color,
                hotcue_text
            ))
    
    def update_hotcue_buttons(self):
        """Actualizar botones de hot cue."""
        # Resetear todos los botones
        for i in range(1, 9):
            self.hotcue_buttons[i].config(
                text=str(i),
                bg='#7f8c8d'
            )
        
        # Configurar botones asignados
        for cue in self.cue_points:
            if 1 <= cue.hotcue_index <= 8:
                self.hotcue_buttons[cue.hotcue_index].config(
                    text=f"{cue.hotcue_index}\n{cue.name[:6]}",
                    bg=cue.color
                )
    
    def save_cues_to_file(self):
        """Guardar cue points a archivo."""
        filename = filedialog.asksaveasfilename(
            title="Guardar Cue Points",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                data = {
                    'version': '1.0',
                    'track_duration': self.track_duration,
                    'cue_points': [asdict(cue) for cue in self.cue_points]
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                messagebox.showinfo("Éxito", f"Cue points guardados en {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error guardando archivo: {e}")
    
    def load_cues_from_file(self):
        """Cargar cue points desde archivo."""
        filename = filedialog.askopenfilename(
            title="Cargar Cue Points",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                self.cue_points = []
                for cue_data in data.get('cue_points', []):
                    cue = CuePoint(**cue_data)
                    self.cue_points.append(cue)
                
                self.track_duration = data.get('track_duration', 240.0)
                self.position_scale.config(to=self.track_duration)
                
                self.update_cue_list()
                self.update_hotcue_buttons()
                self.draw_waveform()
                
                messagebox.showinfo("Éxito", f"Cue points cargados desde {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error cargando archivo: {e}")
    
    def run(self):
        """Ejecutar el prototipo."""
        print("🎯 Iniciando prototipo de Cue Points...")
        print("✨ Prototipo aislado - No afecta la aplicación principal")
        self.root.mainloop()

def main():
    """Función principal."""
    print("🎯 DjAlfin - Prototipo Aislado de Cue Points")
    print("=" * 50)
    print("🔧 Características del prototipo:")
    print("  • Interfaz gráfica completa")
    print("  • Hot Cues 1-8 funcionales")
    print("  • Waveform visual simulado")
    print("  • Guardar/Cargar cue points")
    print("  • Simulación de reproducción")
    print("  • Completamente aislado")
    print("=" * 50)
    
    try:
        prototype = CuePointPrototype()
        prototype.run()
    except Exception as e:
        print(f"❌ Error ejecutando prototipo: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
