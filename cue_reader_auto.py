#!/usr/bin/env python3
"""
🎯 DjAlfin - Lector Automático de Cue Points
Lee automáticamente /Volumes/KINGSTON/Audio y muestra solo archivos con cue points
"""

import tkinter as tk
from tkinter import scrolledtext
import os
import glob
import threading
from basic_metadata_reader import BasicMetadataReader

class AutoCueReader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Auto Cue Reader")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.metadata_reader = BasicMetadataReader()
        self.files_with_cues = []
        self.current_file = None
        self.current_cues = []
        self.scanning = False
        
        # Configurar UI
        self.setup_ui()
        
        # Iniciar escaneo automático
        self.root.after(500, self.start_auto_scan)
    
    def setup_ui(self):
        """Configurar interfaz de usuario."""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#0d1117', height=70)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎯 DjAlfin - Auto Cue Reader",
            font=('Arial', 18, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(side='left', padx=20, pady=20)
        
        self.status_label = tk.Label(
            header_frame,
            text="🔍 Starting automatic scan...",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#f85149'
        )
        self.status_label.pack(side='right', padx=20, pady=20)
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - Files with cues
        self.create_files_panel(main_frame)
        
        # Right panel - Cue points display
        self.create_cues_panel(main_frame)
        
        # Bottom panel - Hot cues
        self.create_hotcues_panel()
    
    def create_files_panel(self, parent):
        """Crear panel de archivos con cue points."""
        
        files_frame = tk.LabelFrame(
            parent,
            text="🎵 Files with Embedded Cue Points",
            font=('Arial', 14, 'bold'),
            bg='#21262d',
            fg='#58a6ff',
            padx=15,
            pady=15
        )
        files_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Info label
        self.files_info_label = tk.Label(
            files_frame,
            text="🔍 Scanning /Volumes/KINGSTON/Audio for files with cue points...",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 11),
            wraplength=400,
            justify='left'
        )
        self.files_info_label.pack(fill='x', pady=(0, 10))
        
        # Files listbox
        self.files_listbox = tk.Listbox(
            files_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            selectbackground='#58a6ff',
            font=('Arial', 10),
            height=25
        )
        self.files_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind selection
        self.files_listbox.bind('<ButtonRelease-1>', self.on_file_select)
        self.files_listbox.bind('<Double-1>', self.on_file_double_click)
        
        # Control buttons
        btn_frame = tk.Frame(files_frame, bg='#21262d')
        btn_frame.pack(fill='x', pady=10)
        
        tk.Button(
            btn_frame,
            text="🔄 Rescan",
            command=self.start_auto_scan,
            bg='#0969da',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=12
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="🎵 Load Selected",
            command=self.load_selected_file,
            bg='#238636',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=12
        ).pack(side='left', padx=5)
    
    def create_cues_panel(self, parent):
        """Crear panel de cue points."""
        
        cues_frame = tk.LabelFrame(
            parent,
            text="🎯 Cue Points Details",
            font=('Arial', 14, 'bold'),
            bg='#21262d',
            fg='#58a6ff',
            padx=15,
            pady=15
        )
        cues_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Current file info
        self.current_file_label = tk.Label(
            cues_frame,
            text="Select a file to view cue points",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 12, 'bold'),
            height=2
        )
        self.current_file_label.pack(fill='x', pady=(0, 10))
        
        # Cue points display
        self.cues_text = scrolledtext.ScrolledText(
            cues_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 10),
            wrap=tk.WORD,
            height=20
        )
        self.cues_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.cues_text.insert('1.0', "🎯 Select a file from the left panel to view its cue points")
        
        # Stats display
        self.stats_label = tk.Label(
            cues_frame,
            text="📊 No file selected",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 10),
            height=2
        )
        self.stats_label.pack(fill='x', pady=(10, 0))
    
    def create_hotcues_panel(self):
        """Crear panel de hot cues."""
        
        hotcues_frame = tk.Frame(self.root, bg='#0d1117', height=80)
        hotcues_frame.pack(fill='x', padx=5, pady=5)
        hotcues_frame.pack_propagate(False)
        
        tk.Label(
            hotcues_frame,
            text="🔥 HOT CUES",
            font=('Arial', 14, 'bold'),
            bg='#0d1117',
            fg='#f85149'
        ).pack(pady=5)
        
        # Hot cue buttons
        buttons_frame = tk.Frame(hotcues_frame, bg='#0d1117')
        buttons_frame.pack(pady=5)
        
        self.hotcue_buttons = {}
        for i in range(8):
            btn = tk.Label(
                buttons_frame,
                text=f"{i+1}",
                width=8,
                height=2,
                bg='#30363d',
                fg='#8b949e',
                font=('Arial', 10, 'bold'),
                relief='raised',
                bd=2
            )
            btn.pack(side='left', padx=2)
            self.hotcue_buttons[i+1] = btn
    
    def start_auto_scan(self):
        """Iniciar escaneo automático."""
        
        if self.scanning:
            return
        
        self.scanning = True
        self.status_label.config(text="🔍 Scanning for files with cue points...", fg='#f85149')
        self.files_info_label.config(text="🔍 Scanning /Volumes/KINGSTON/Audio...")
        
        # Limpiar lista
        self.files_listbox.delete(0, tk.END)
        self.files_with_cues = []
        
        # Iniciar thread de escaneo
        threading.Thread(target=self.scan_for_cues, daemon=True).start()
    
    def scan_for_cues(self):
        """Escanear archivos buscando cue points."""
        
        audio_folder = "/Volumes/KINGSTON/Audio"
        
        if not os.path.exists(audio_folder):
            self.root.after(0, lambda: self.status_label.config(
                text="❌ Audio folder not found", fg='#f85149'
            ))
            self.scanning = False
            return
        
        # Buscar archivos de audio
        extensions = ['*.mp3', '*.m4a', '*.flac', '*.wav']
        all_files = []
        
        for ext in extensions:
            pattern = os.path.join(audio_folder, ext)
            files = glob.glob(pattern)
            
            for file_path in files:
                filename = os.path.basename(file_path)
                if not filename.startswith('._'):
                    all_files.append(file_path)
        
        print(f"🔍 Found {len(all_files)} audio files to scan")
        
        # Escanear cada archivo
        files_with_cues = []
        total_cues = 0
        
        for i, file_path in enumerate(all_files):
            filename = os.path.basename(file_path)
            
            # Actualizar status
            self.root.after(0, lambda f=filename, i=i, t=len(all_files): 
                self.status_label.config(text=f"🔍 Scanning {i+1}/{t}: {f[:30]}...")
            )
            
            try:
                # Leer metadatos
                metadata = self.metadata_reader.scan_file(file_path)
                cue_points = metadata.get('cue_points', [])
                
                if cue_points:
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    software = cue_points[0].software.title()
                    
                    file_info = {
                        'path': file_path,
                        'filename': filename,
                        'size_mb': file_size,
                        'cue_count': len(cue_points),
                        'software': software,
                        'cue_points': cue_points
                    }
                    
                    files_with_cues.append(file_info)
                    total_cues += len(cue_points)
                    
                    # Actualizar lista en tiempo real
                    display_text = f"🎵 {filename} ({len(cue_points)} cues - {software})"
                    self.root.after(0, lambda text=display_text: 
                        self.files_listbox.insert(tk.END, text)
                    )
                    
                    print(f"✅ {filename}: {len(cue_points)} cue points from {software}")
                
            except Exception as e:
                print(f"❌ Error scanning {filename}: {e}")
        
        # Guardar resultados
        self.files_with_cues = files_with_cues
        
        # Actualizar UI final
        self.root.after(0, self.finish_scan, len(files_with_cues), total_cues, len(all_files))
    
    def finish_scan(self, files_found, total_cues, total_files):
        """Finalizar escaneo y actualizar UI."""
        
        self.scanning = False
        
        if files_found > 0:
            status_text = f"✅ Found {files_found} files with {total_cues} cue points"
            status_color = '#238636'
            
            info_text = f"✅ Scan complete: {files_found} files with embedded cue points found\n"
            info_text += f"📊 Total: {total_cues} cue points from {total_files} files scanned"
            
        else:
            status_text = f"❌ No files with cue points found ({total_files} scanned)"
            status_color = '#f85149'
            
            info_text = f"❌ No files with embedded cue points found\n"
            info_text += f"📊 Scanned {total_files} files - no cue points detected"
        
        self.status_label.config(text=status_text, fg=status_color)
        self.files_info_label.config(text=info_text)
        
        print(f"📊 Scan complete: {files_found} files with {total_cues} cue points")
    
    def on_file_select(self, event):
        """Manejar selección de archivo."""
        pass
    
    def on_file_double_click(self, event):
        """Manejar doble clic."""
        self.load_selected_file()
    
    def load_selected_file(self):
        """Cargar archivo seleccionado."""
        
        selection = self.files_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if 0 <= index < len(self.files_with_cues):
            self.current_file = self.files_with_cues[index]
            self.current_cues = self.current_file['cue_points']
            
            # Actualizar display
            self.update_file_display()
            self.update_cues_display()
            self.update_hotcues_display()
            
            filename = self.current_file['filename']
            print(f"📁 Loaded: {filename}")
    
    def update_file_display(self):
        """Actualizar display del archivo actual."""
        
        if not self.current_file:
            return
        
        filename = self.current_file['filename']
        size_mb = self.current_file['size_mb']
        cue_count = self.current_file['cue_count']
        software = self.current_file['software']
        
        display_text = f"🎵 {filename}"
        self.current_file_label.config(text=display_text, fg='#58a6ff')
        
        stats_text = f"📊 {size_mb:.1f} MB • {cue_count} cue points • {software}"
        self.stats_label.config(text=stats_text, fg='#f0f6fc')
    
    def update_cues_display(self):
        """Actualizar display de cue points."""
        
        self.cues_text.delete('1.0', tk.END)
        
        if not self.current_cues:
            self.cues_text.insert('1.0', "No cue points found")
            return
        
        # Header
        filename = self.current_file['filename']
        software = self.current_file['software']
        
        display_text = f"🎯 CUE POINTS - {filename}\n"
        display_text += f"🎛️ Software: {software}\n"
        display_text += "=" * 60 + "\n\n"
        
        # Cue points
        for i, cue in enumerate(self.current_cues):
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            
            display_text += f"{i+1:2d}. {cue.name}\n"
            display_text += f"    ⏰ Time: {minutes}:{seconds:02d} ({cue.position:.1f}s)\n"
            display_text += f"    🎨 Color: {cue.color}\n"
            display_text += f"    🔥 Hot Cue: #{cue.hotcue_index}\n"
            display_text += f"    ⚡ Energy: {cue.energy_level}/10\n"
            display_text += "\n"
        
        # Summary
        display_text += "=" * 60 + "\n"
        display_text += f"📊 SUMMARY:\n"
        display_text += f"   Total cue points: {len(self.current_cues)}\n"
        display_text += f"   Software: {software}\n"
        display_text += f"   Hot cues assigned: {len([c for c in self.current_cues if c.hotcue_index > 0])}\n"
        display_text += f"   File size: {self.current_file['size_mb']:.1f} MB\n"
        
        self.cues_text.insert('1.0', display_text)
    
    def update_hotcues_display(self):
        """Actualizar display de hot cues."""
        
        # Reset hot cues
        for i in range(1, 9):
            self.hotcue_buttons[i].config(
                text=str(i),
                bg='#30363d',
                fg='#8b949e'
            )
        
        # Set active hot cues
        if self.current_cues:
            for cue in self.current_cues:
                if 1 <= cue.hotcue_index <= 8:
                    btn = self.hotcue_buttons[cue.hotcue_index]
                    btn.config(
                        text=f"{cue.hotcue_index}\n{cue.name[:6]}",
                        bg=cue.color,
                        fg='#000000' if self.is_light_color(cue.color) else '#ffffff'
                    )
    
    def is_light_color(self, hex_color):
        """Determinar si un color es claro."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness > 128
        except:
            return False
    
    def run(self):
        """Ejecutar la aplicación."""
        print("🎯 DjAlfin Auto Cue Reader")
        print("Automatically scanning /Volumes/KINGSTON/Audio for files with cue points")
        self.root.mainloop()

def main():
    """Función principal."""
    try:
        app = AutoCueReader()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
