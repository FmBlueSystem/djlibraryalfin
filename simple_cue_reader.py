#!/usr/bin/env python3
"""
🎯 DjAlfin - Lector Simple de Cue Points
Versión simplificada para probar la carga de cue points embebidos
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import glob
import threading
from basic_metadata_reader import BasicMetadataReader

class SimpleCueReader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Simple Cue Reader")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')
        
        self.metadata_reader = BasicMetadataReader()
        self.audio_files = []
        self.current_file = None
        self.cue_points = []
        
        self.setup_ui()
        self.scan_audio_files()
    
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#0d1117', height=60)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎯 DjAlfin - Simple Cue Reader",
            font=('Arial', 16, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(side='left', padx=20, pady=15)
        
        self.status_label = tk.Label(
            header_frame,
            text="📁 Scanning files...",
            font=('Arial', 10),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.status_label.pack(side='right', padx=20, pady=15)
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # File list
        self.create_file_list(main_frame)
        
        # Cue points display
        self.create_cue_display(main_frame)
        
        # Controls
        self.create_controls(main_frame)
    
    def create_file_list(self, parent):
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
        
        # Listbox for files
        self.file_listbox = tk.Listbox(
            file_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            selectbackground='#58a6ff',
            font=('Arial', 10),
            height=20
        )
        self.file_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind selection
        self.file_listbox.bind('<ButtonRelease-1>', self.on_file_select)
        self.file_listbox.bind('<Double-1>', self.on_file_double_click)
        
        # Buttons
        btn_frame = tk.Frame(file_frame, bg='#21262d')
        btn_frame.pack(fill='x', pady=5)
        
        tk.Button(
            btn_frame,
            text="🔄 Rescan",
            command=self.scan_audio_files,
            bg='#0969da',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            btn_frame,
            text="📁 Load",
            command=self.load_selected_file,
            bg='#238636',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
    
    def create_cue_display(self, parent):
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
        
        # Current file info
        self.file_info_label = tk.Label(
            cue_frame,
            text="No file loaded",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 10),
            wraplength=300,
            justify='left'
        )
        self.file_info_label.pack(fill='x', padx=5, pady=5)
        
        # Cue points list
        columns = ('Time', 'Name', 'Software')
        self.cue_tree = ttk.Treeview(
            cue_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        for col in columns:
            self.cue_tree.heading(col, text=col)
            self.cue_tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(cue_frame, orient='vertical', command=self.cue_tree.yview)
        self.cue_tree.configure(yscrollcommand=scrollbar.set)
        
        self.cue_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')
    
    def create_controls(self, parent):
        control_frame = tk.Frame(parent, bg='#1a1a1a')
        control_frame.pack(fill='x', pady=10)
        
        tk.Button(
            control_frame,
            text="🎵 Read Embedded Cues",
            command=self.read_embedded_cues,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2
        ).pack(side='left', padx=10, fill='x', expand=True)
        
        tk.Button(
            control_frame,
            text="🧹 Clear",
            command=self.clear_cues,
            bg='#da3633',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2
        ).pack(side='left', padx=10)
    
    def scan_audio_files(self):
        """Escanear archivos de audio."""
        self.status_label.config(text="📁 Scanning files...")
        self.root.update()
        
        def scan_thread():
            audio_folder = "/Volumes/KINGSTON/Audio"
            self.audio_files = []
            
            if os.path.exists(audio_folder):
                for ext in ['.mp3', '.m4a', '.flac', '.wav']:
                    pattern = os.path.join(audio_folder, f"*{ext}")
                    files = glob.glob(pattern)
                    
                    for file_path in files:
                        filename = os.path.basename(file_path)
                        # Filtrar archivos ocultos de macOS
                        if not filename.startswith('._'):
                            self.audio_files.append({
                                'path': file_path,
                                'filename': filename
                            })
            
            self.root.after(0, self.update_file_list)
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def update_file_list(self):
        """Actualizar lista de archivos."""
        self.file_listbox.delete(0, tk.END)
        
        for audio_file in self.audio_files:
            self.file_listbox.insert(tk.END, audio_file['filename'])
        
        self.status_label.config(text=f"📁 {len(self.audio_files)} files found")
    
    def on_file_select(self, event):
        """Manejar selección de archivo."""
        pass
    
    def on_file_double_click(self, event):
        """Manejar doble clic."""
        self.load_selected_file()
    
    def load_selected_file(self):
        """Cargar archivo seleccionado."""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        index = selection[0]
        if 0 <= index < len(self.audio_files):
            self.current_file = self.audio_files[index]
            self.cue_points = []
            
            # Actualizar info del archivo
            filename = self.current_file['filename']
            file_path = self.current_file['path']
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            info_text = f"📁 {filename}\n📊 {file_size:.1f} MB\n🎵 Ready to read cues"
            self.file_info_label.config(text=info_text, fg='#f0f6fc')
            
            # Limpiar lista de cue points
            for item in self.cue_tree.get_children():
                self.cue_tree.delete(item)
            
            self.show_message(f"📁 Loaded: {filename}")
    
    def read_embedded_cues(self):
        """Leer cue points embebidos."""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        self.show_message("🔍 Reading embedded cue points...")
        
        def read_thread():
            try:
                file_path = self.current_file['path']
                print(f"🔍 Reading cues from: {file_path}")
                
                metadata = self.metadata_reader.scan_file(file_path)
                embedded_cues = metadata.get('cue_points', [])
                
                print(f"📊 Found {len(embedded_cues)} cue points")
                
                if embedded_cues:
                    self.cue_points = embedded_cues
                    self.root.after(0, self.update_cue_list)
                    self.root.after(0, lambda: self.show_message(f"🎵 Found {len(embedded_cues)} embedded cue points from {embedded_cues[0].software}"))
                else:
                    self.root.after(0, lambda: self.show_message("❌ No embedded cue points found"))
                    
            except Exception as e:
                print(f"❌ Error reading cues: {e}")
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self.show_message(f"❌ Error: {str(e)}"))
        
        threading.Thread(target=read_thread, daemon=True).start()
    
    def update_cue_list(self):
        """Actualizar lista de cue points."""
        # Limpiar lista
        for item in self.cue_tree.get_children():
            self.cue_tree.delete(item)
        
        # Agregar cue points
        for cue in self.cue_points:
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            time_str = f"{minutes}:{seconds:02d}"
            
            self.cue_tree.insert('', 'end', values=(
                time_str,
                cue.name,
                cue.software.title()
            ))
        
        # Actualizar info del archivo
        if self.current_file and self.cue_points:
            filename = self.current_file['filename']
            file_path = self.current_file['path']
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            info_text = f"📁 {filename}\n📊 {file_size:.1f} MB\n🎯 {len(self.cue_points)} cue points\n🎛️ {self.cue_points[0].software.title()}"
            self.file_info_label.config(text=info_text, fg='#58a6ff')
    
    def clear_cues(self):
        """Limpiar cue points."""
        self.cue_points = []
        for item in self.cue_tree.get_children():
            self.cue_tree.delete(item)
        
        if self.current_file:
            filename = self.current_file['filename']
            file_path = self.current_file['path']
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            info_text = f"📁 {filename}\n📊 {file_size:.1f} MB\n🎵 Ready to read cues"
            self.file_info_label.config(text=info_text, fg='#f0f6fc')
        
        self.show_message("🧹 Cue points cleared")
    
    def show_message(self, message):
        """Mostrar mensaje en la consola y status."""
        print(message)
        self.status_label.config(text=message)
        
        # Auto-limpiar después de 3 segundos
        self.root.after(3000, lambda: self.status_label.config(text=f"📁 {len(self.audio_files)} files found"))
    
    def run(self):
        """Ejecutar la aplicación."""
        print("🎯 DjAlfin Simple Cue Reader")
        print("Testing embedded cue point reading")
        self.root.mainloop()

def main():
    """Función principal."""
    try:
        app = SimpleCueReader()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
