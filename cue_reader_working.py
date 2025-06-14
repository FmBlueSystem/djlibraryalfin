#!/usr/bin/env python3
"""
🎯 DjAlfin - Lector de Cue Points (Versión que Funciona)
Versión simplificada y estable para leer cue points embebidos
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import glob
from basic_metadata_reader import BasicMetadataReader

class WorkingCueReader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Working Cue Reader")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.metadata_reader = BasicMetadataReader()
        self.audio_files = []
        self.current_file = None
        self.current_cues = []
        
        # Configurar UI
        self.setup_ui()
        
        # Cargar archivos
        self.root.after(100, self.load_audio_files)
    
    def setup_ui(self):
        """Configurar interfaz de usuario."""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#0d1117', height=60)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎯 DjAlfin - Working Cue Reader",
            font=('Arial', 16, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(side='left', padx=20, pady=15)
        
        self.status_label = tk.Label(
            header_frame,
            text="📁 Ready to load files...",
            font=('Arial', 10),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.status_label.pack(side='right', padx=20, pady=15)
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - File list
        self.create_file_panel(main_frame)
        
        # Right panel - Cue points
        self.create_cue_panel(main_frame)
        
        # Bottom panel - Controls
        self.create_control_panel()
    
    def create_file_panel(self, parent):
        """Crear panel de archivos."""
        
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
        
        # Listbox para archivos
        self.file_listbox = tk.Listbox(
            file_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            selectbackground='#58a6ff',
            font=('Arial', 9),
            height=25
        )
        self.file_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind events
        self.file_listbox.bind('<ButtonRelease-1>', self.on_file_select)
        self.file_listbox.bind('<Double-1>', self.on_file_double_click)
        
        # Buttons
        btn_frame = tk.Frame(file_frame, bg='#21262d')
        btn_frame.pack(fill='x', pady=5)
        
        tk.Button(
            btn_frame,
            text="🔄 Load Files",
            command=self.load_audio_files,
            bg='#0969da',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            btn_frame,
            text="🎵 Read Cues",
            command=self.read_selected_file,
            bg='#238636',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            btn_frame,
            text="🔍 Scan All",
            command=self.scan_all_files,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
    
    def create_cue_panel(self, parent):
        """Crear panel de cue points."""
        
        cue_frame = tk.LabelFrame(
            parent,
            text="🎯 Cue Points",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        cue_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # File info
        self.file_info_text = scrolledtext.ScrolledText(
            cue_frame,
            height=6,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Arial', 10),
            wrap=tk.WORD
        )
        self.file_info_text.pack(fill='x', padx=5, pady=5)
        self.file_info_text.insert('1.0', "Select a file to view information and cue points")
        
        # Cue points display
        self.cue_text = scrolledtext.ScrolledText(
            cue_frame,
            height=15,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Courier', 9),
            wrap=tk.WORD
        )
        self.cue_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.cue_text.insert('1.0', "No cue points loaded")
    
    def create_control_panel(self):
        """Crear panel de controles."""
        
        control_frame = tk.Frame(self.root, bg='#0d1117', height=60)
        control_frame.pack(fill='x', padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Hot cues display
        tk.Label(
            control_frame,
            text="🔥 HOT CUES:",
            font=('Arial', 12, 'bold'),
            bg='#0d1117',
            fg='#f85149'
        ).pack(side='left', padx=10, pady=15)
        
        self.hotcue_frame = tk.Frame(control_frame, bg='#0d1117')
        self.hotcue_frame.pack(side='left', pady=15)
        
        self.hotcue_labels = {}
        for i in range(8):
            label = tk.Label(
                self.hotcue_frame,
                text=f"{i+1}",
                width=6,
                height=2,
                bg='#30363d',
                fg='#8b949e',
                font=('Arial', 9, 'bold'),
                relief='raised'
            )
            label.pack(side='left', padx=1)
            self.hotcue_labels[i+1] = label
    
    def load_audio_files(self):
        """Cargar archivos de audio."""
        
        self.status_label.config(text="📁 Loading audio files...")
        self.root.update()
        
        audio_folder = "/Volumes/KINGSTON/Audio"
        self.audio_files = []
        
        print(f"🔍 Scanning: {audio_folder}")
        
        if not os.path.exists(audio_folder):
            self.status_label.config(text="❌ Audio folder not found")
            messagebox.showerror("Error", f"Folder not found: {audio_folder}")
            return
        
        # Buscar archivos de audio
        extensions = ['*.mp3', '*.m4a', '*.flac', '*.wav']
        
        for ext in extensions:
            pattern = os.path.join(audio_folder, ext)
            files = glob.glob(pattern)
            
            for file_path in files:
                filename = os.path.basename(file_path)
                
                # Filtrar archivos ocultos
                if not filename.startswith('._'):
                    try:
                        file_size = os.path.getsize(file_path) / (1024 * 1024)
                        
                        self.audio_files.append({
                            'path': file_path,
                            'filename': filename,
                            'size_mb': file_size
                        })
                    except Exception as e:
                        print(f"❌ Error processing {filename}: {e}")
        
        # Actualizar lista
        self.update_file_list()
        
        print(f"✅ Loaded {len(self.audio_files)} audio files")
        self.status_label.config(text=f"📁 {len(self.audio_files)} files loaded")
    
    def update_file_list(self):
        """Actualizar lista de archivos."""
        
        self.file_listbox.delete(0, tk.END)
        
        for audio_file in self.audio_files:
            display_text = f"{audio_file['filename']} ({audio_file['size_mb']:.1f} MB)"
            self.file_listbox.insert(tk.END, display_text)
    
    def on_file_select(self, event):
        """Manejar selección de archivo."""
        pass
    
    def on_file_double_click(self, event):
        """Manejar doble clic."""
        self.read_selected_file()
    
    def read_selected_file(self):
        """Leer archivo seleccionado."""
        
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        index = selection[0]
        if 0 <= index < len(self.audio_files):
            self.current_file = self.audio_files[index]
            
            filename = self.current_file['filename']
            file_path = self.current_file['path']
            size_mb = self.current_file['size_mb']
            
            # Actualizar info del archivo
            info_text = f"📁 File: {filename}\n"
            info_text += f"📊 Size: {size_mb:.1f} MB\n"
            info_text += f"📍 Path: {file_path}\n"
            info_text += f"🔍 Reading embedded cue points...\n"
            
            self.file_info_text.delete('1.0', tk.END)
            self.file_info_text.insert('1.0', info_text)
            
            # Leer cue points
            self.read_cue_points()
            
            print(f"📁 Reading: {filename}")
    
    def read_cue_points(self):
        """Leer cue points del archivo actual."""
        
        if not self.current_file:
            return
        
        file_path = self.current_file['path']
        filename = self.current_file['filename']
        
        try:
            # Leer metadatos
            metadata = self.metadata_reader.scan_file(file_path)
            self.current_cues = metadata.get('cue_points', [])
            
            # Actualizar info del archivo
            size_mb = self.current_file['size_mb']
            cue_count = len(self.current_cues)
            
            info_text = f"📁 File: {filename}\n"
            info_text += f"📊 Size: {size_mb:.1f} MB\n"
            info_text += f"🎯 Cue Points: {cue_count}\n"
            
            if self.current_cues:
                software = self.current_cues[0].software.title()
                info_text += f"🎛️ Software: {software}\n"
                info_text += f"✅ Status: Cue points found!\n"
                
                print(f"✅ Found {cue_count} cue points from {software}")
            else:
                info_text += f"❌ Status: No cue points found\n"
                print(f"❌ No cue points found")
            
            self.file_info_text.delete('1.0', tk.END)
            self.file_info_text.insert('1.0', info_text)
            
            # Actualizar display de cue points
            self.update_cue_display()
            
            # Actualizar hot cues
            self.update_hotcue_display()
            
        except Exception as e:
            error_msg = f"❌ Error reading cues: {str(e)}"
            print(error_msg)
            
            info_text = f"📁 File: {filename}\n"
            info_text += f"📊 Size: {size_mb:.1f} MB\n"
            info_text += f"{error_msg}\n"
            
            self.file_info_text.delete('1.0', tk.END)
            self.file_info_text.insert('1.0', info_text)
    
    def update_cue_display(self):
        """Actualizar display de cue points."""
        
        self.cue_text.delete('1.0', tk.END)
        
        if not self.current_cues:
            self.cue_text.insert('1.0', "No cue points found in this file")
            return
        
        # Header
        display_text = f"🎯 CUE POINTS ({len(self.current_cues)} found)\n"
        display_text += "=" * 50 + "\n\n"
        
        # Cue points
        for i, cue in enumerate(self.current_cues):
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            
            display_text += f"{i+1:2d}. {cue.name}\n"
            display_text += f"    Time: {minutes}:{seconds:02d} ({cue.position:.1f}s)\n"
            display_text += f"    Color: {cue.color}\n"
            display_text += f"    Hot Cue: #{cue.hotcue_index}\n"
            display_text += f"    Software: {cue.software.title()}\n"
            display_text += f"    Energy: {cue.energy_level}/10\n"
            display_text += "\n"
        
        # Summary
        display_text += "=" * 50 + "\n"
        display_text += f"📊 Summary:\n"
        display_text += f"   Total cue points: {len(self.current_cues)}\n"
        display_text += f"   Software: {self.current_cues[0].software.title()}\n"
        display_text += f"   Hot cues assigned: {len([c for c in self.current_cues if c.hotcue_index > 0])}\n"
        
        self.cue_text.insert('1.0', display_text)
    
    def update_hotcue_display(self):
        """Actualizar display de hot cues."""
        
        # Resetear hot cues
        for i in range(1, 9):
            self.hotcue_labels[i].config(
                text=str(i),
                bg='#30363d',
                fg='#8b949e'
            )
        
        # Configurar hot cues activos
        for cue in self.current_cues:
            if 1 <= cue.hotcue_index <= 8:
                label = self.hotcue_labels[cue.hotcue_index]
                label.config(
                    text=f"{cue.hotcue_index}\n{cue.name[:4]}",
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
    
    def scan_all_files(self):
        """Escanear todos los archivos."""
        
        if not self.audio_files:
            messagebox.showwarning("Warning", "No audio files loaded")
            return
        
        self.status_label.config(text="🔍 Scanning all files...")
        
        total_cues = 0
        files_with_cues = 0
        
        scan_results = "🔍 SCAN RESULTS\n"
        scan_results += "=" * 50 + "\n\n"
        
        for i, audio_file in enumerate(self.audio_files):
            filename = audio_file['filename']
            file_path = audio_file['path']
            
            # Actualizar status
            self.status_label.config(text=f"🔍 Scanning {i+1}/{len(self.audio_files)}")
            self.root.update()
            
            try:
                metadata = self.metadata_reader.scan_file(file_path)
                cue_points = metadata.get('cue_points', [])
                
                if cue_points:
                    files_with_cues += 1
                    total_cues += len(cue_points)
                    software = cue_points[0].software.title()
                    
                    scan_results += f"✅ {filename}\n"
                    scan_results += f"   {len(cue_points)} cue points from {software}\n\n"
                    
                    print(f"✅ {filename}: {len(cue_points)} cue points")
                else:
                    scan_results += f"❌ {filename}\n"
                    scan_results += f"   No cue points found\n\n"
                
            except Exception as e:
                scan_results += f"❌ {filename}\n"
                scan_results += f"   Error: {str(e)}\n\n"
                print(f"❌ Error scanning {filename}: {e}")
        
        # Summary
        scan_results += "=" * 50 + "\n"
        scan_results += f"📊 SUMMARY:\n"
        scan_results += f"   Files scanned: {len(self.audio_files)}\n"
        scan_results += f"   Files with cues: {files_with_cues}\n"
        scan_results += f"   Total cue points: {total_cues}\n"
        scan_results += f"   Success rate: {(files_with_cues/len(self.audio_files)*100):.1f}%\n"
        
        # Mostrar resultados
        self.cue_text.delete('1.0', tk.END)
        self.cue_text.insert('1.0', scan_results)
        
        result_msg = f"📊 Scan complete: {files_with_cues} files with {total_cues} total cue points"
        self.status_label.config(text=result_msg)
        
        print(f"📊 Scan Results: {files_with_cues}/{len(self.audio_files)} files with {total_cues} cue points")
        
        messagebox.showinfo("Scan Complete", result_msg)
    
    def run(self):
        """Ejecutar la aplicación."""
        print("🎯 DjAlfin Working Cue Reader")
        print("Stable version for reading embedded cue points")
        self.root.mainloop()

def main():
    """Función principal."""
    try:
        app = WorkingCueReader()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
