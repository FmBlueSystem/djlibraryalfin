#!/usr/bin/env python3
"""
🎯 DjAlfin - Lector Directo de Cue Points
Versión que lee directamente /Volumes/KINGSTON/Audio sin problemas de threading
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import glob
from basic_metadata_reader import BasicMetadataReader

class DirectCueReader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 DjAlfin - Direct Cue Reader")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.metadata_reader = BasicMetadataReader()
        self.audio_files = []
        self.current_file = None
        self.current_cues = []
        
        # Configurar UI
        self.setup_ui()
        
        # Cargar archivos inmediatamente
        self.load_audio_files()
    
    def setup_ui(self):
        """Configurar interfaz de usuario."""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#0d1117', height=70)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎯 DjAlfin - Direct Cue Reader",
            font=('Arial', 18, 'bold'),
            bg='#0d1117',
            fg='#58a6ff'
        ).pack(side='left', padx=20, pady=20)
        
        self.status_label = tk.Label(
            header_frame,
            text="📁 Loading audio files...",
            font=('Arial', 12),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.status_label.pack(side='right', padx=20, pady=20)
        
        # Main container
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
            text="📁 Audio Files (/Volumes/KINGSTON/Audio)",
            font=('Arial', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            padx=10,
            pady=10
        )
        file_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Treeview para archivos
        columns = ('Filename', 'Size', 'Format', 'Cues')
        self.file_tree = ttk.Treeview(
            file_frame,
            columns=columns,
            show='headings',
            height=25
        )
        
        # Configurar columnas
        self.file_tree.heading('Filename', text='Filename')
        self.file_tree.heading('Size', text='Size (MB)')
        self.file_tree.heading('Format', text='Format')
        self.file_tree.heading('Cues', text='Cues')
        
        self.file_tree.column('Filename', width=300)
        self.file_tree.column('Size', width=80)
        self.file_tree.column('Format', width=60)
        self.file_tree.column('Cues', width=50)
        
        # Scrollbar
        file_scrollbar = ttk.Scrollbar(file_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        file_scrollbar.pack(side='right', fill='y')
        
        # Bind events
        self.file_tree.bind('<ButtonRelease-1>', self.on_file_select)
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        
        # Buttons
        btn_frame = tk.Frame(file_frame, bg='#21262d')
        btn_frame.pack(fill='x', pady=10)
        
        tk.Button(
            btn_frame,
            text="🔄 Reload",
            command=self.load_audio_files,
            bg='#0969da',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            btn_frame,
            text="🎵 Load File",
            command=self.load_selected_file,
            bg='#238636',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=2)
        
        tk.Button(
            btn_frame,
            text="🔍 Scan All Cues",
            command=self.scan_all_cues,
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
        self.file_info_label = tk.Label(
            cue_frame,
            text="Select a file to view cue points",
            bg='#21262d',
            fg='#8b949e',
            font=('Arial', 11),
            wraplength=400,
            justify='left',
            height=3
        )
        self.file_info_label.pack(fill='x', padx=5, pady=5)
        
        # Cue points tree
        cue_columns = ('Time', 'Name', 'Color', 'Software', 'Hot')
        self.cue_tree = ttk.Treeview(
            cue_frame,
            columns=cue_columns,
            show='headings',
            height=20
        )
        
        # Configure cue columns
        self.cue_tree.heading('Time', text='Time')
        self.cue_tree.heading('Name', text='Name')
        self.cue_tree.heading('Color', text='Color')
        self.cue_tree.heading('Software', text='Software')
        self.cue_tree.heading('Hot', text='Hot')
        
        self.cue_tree.column('Time', width=60)
        self.cue_tree.column('Name', width=120)
        self.cue_tree.column('Color', width=80)
        self.cue_tree.column('Software', width=80)
        self.cue_tree.column('Hot', width=40)
        
        # Cue scrollbar
        cue_scrollbar = ttk.Scrollbar(cue_frame, orient='vertical', command=self.cue_tree.yview)
        self.cue_tree.configure(yscrollcommand=cue_scrollbar.set)
        
        self.cue_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        cue_scrollbar.pack(side='right', fill='y')
    
    def create_control_panel(self):
        """Crear panel de controles."""
        
        control_frame = tk.Frame(self.root, bg='#0d1117', height=80)
        control_frame.pack(fill='x', padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Hot cues display
        tk.Label(
            control_frame,
            text="🔥 HOT CUES",
            font=('Arial', 14, 'bold'),
            bg='#0d1117',
            fg='#f85149'
        ).pack(pady=5)
        
        hotcue_frame = tk.Frame(control_frame, bg='#0d1117')
        hotcue_frame.pack(pady=5)
        
        self.hotcue_buttons = {}
        for i in range(8):
            btn = tk.Button(
                hotcue_frame,
                text=f"{i+1}",
                width=8,
                height=2,
                bg='#30363d',
                fg='#8b949e',
                font=('Arial', 10, 'bold')
            )
            btn.pack(side='left', padx=2)
            self.hotcue_buttons[i+1] = btn
    
    def load_audio_files(self):
        """Cargar archivos de audio directamente."""
        
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
                
                # Filtrar archivos ocultos de macOS
                if not filename.startswith('._'):
                    try:
                        file_size = os.path.getsize(file_path) / (1024 * 1024)
                        _, file_ext = os.path.splitext(filename)
                        format_name = file_ext.upper().replace('.', '')
                        
                        self.audio_files.append({
                            'path': file_path,
                            'filename': filename,
                            'size_mb': file_size,
                            'format': format_name,
                            'cue_count': 0  # Se actualizará después
                        })
                    except Exception as e:
                        print(f"❌ Error processing {filename}: {e}")
        
        # Actualizar lista
        self.update_file_list()
        
        print(f"✅ Loaded {len(self.audio_files)} audio files")
        self.status_label.config(text=f"📁 {len(self.audio_files)} audio files loaded")
    
    def update_file_list(self):
        """Actualizar lista de archivos en la UI."""
        
        # Limpiar lista
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Agregar archivos
        for audio_file in self.audio_files:
            self.file_tree.insert('', 'end', values=(
                audio_file['filename'],
                f"{audio_file['size_mb']:.1f}",
                audio_file['format'],
                audio_file['cue_count']
            ))
    
    def on_file_select(self, event):
        """Manejar selección de archivo."""
        pass
    
    def on_file_double_click(self, event):
        """Manejar doble clic en archivo."""
        self.load_selected_file()
    
    def load_selected_file(self):
        """Cargar archivo seleccionado."""
        
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        # Obtener índice del archivo seleccionado
        item = selection[0]
        index = self.file_tree.index(item)
        
        if 0 <= index < len(self.audio_files):
            self.current_file = self.audio_files[index]
            
            # Actualizar info del archivo
            filename = self.current_file['filename']
            size_mb = self.current_file['size_mb']
            format_name = self.current_file['format']
            
            info_text = f"📁 {filename}\n📊 {size_mb:.1f} MB • {format_name}\n🔍 Reading embedded cue points..."
            self.file_info_label.config(text=info_text, fg='#f0f6fc')
            
            # Leer cue points inmediatamente
            self.read_cue_points()
            
            print(f"📁 Loaded: {filename}")
    
    def read_cue_points(self):
        """Leer cue points del archivo actual."""
        
        if not self.current_file:
            return
        
        file_path = self.current_file['path']
        filename = self.current_file['filename']
        
        print(f"🔍 Reading cues from: {filename}")
        
        try:
            # Leer metadatos
            metadata = self.metadata_reader.scan_file(file_path)
            self.current_cues = metadata.get('cue_points', [])
            
            # Actualizar info del archivo
            size_mb = self.current_file['size_mb']
            format_name = self.current_file['format']
            cue_count = len(self.current_cues)
            
            if self.current_cues:
                software = self.current_cues[0].software.title()
                info_text = f"📁 {filename}\n📊 {size_mb:.1f} MB • {format_name}\n🎯 {cue_count} cue points from {software}"
                self.file_info_label.config(text=info_text, fg='#58a6ff')
                
                print(f"✅ Found {cue_count} cue points from {software}")
            else:
                info_text = f"📁 {filename}\n📊 {size_mb:.1f} MB • {format_name}\n❌ No embedded cue points found"
                self.file_info_label.config(text=info_text, fg='#f85149')
                
                print(f"❌ No cue points found")
            
            # Actualizar lista de cue points
            self.update_cue_list()
            
            # Actualizar hot cues
            self.update_hotcue_buttons()
            
            # Actualizar contador en la lista de archivos
            self.current_file['cue_count'] = cue_count
            self.update_file_list()
            
        except Exception as e:
            error_msg = f"❌ Error reading cues: {str(e)}"
            print(error_msg)
            
            info_text = f"📁 {filename}\n📊 {size_mb:.1f} MB • {format_name}\n{error_msg}"
            self.file_info_label.config(text=info_text, fg='#f85149')
    
    def update_cue_list(self):
        """Actualizar lista de cue points."""
        
        # Limpiar lista
        for item in self.cue_tree.get_children():
            self.cue_tree.delete(item)
        
        # Agregar cue points
        for i, cue in enumerate(self.current_cues):
            minutes = int(cue.position // 60)
            seconds = int(cue.position % 60)
            time_str = f"{minutes}:{seconds:02d}"
            
            self.cue_tree.insert('', 'end', values=(
                time_str,
                cue.name,
                cue.color,
                cue.software.title(),
                f"#{cue.hotcue_index}" if cue.hotcue_index > 0 else "-"
            ))
    
    def update_hotcue_buttons(self):
        """Actualizar botones de hot cues."""
        
        # Resetear botones
        for i in range(1, 9):
            self.hotcue_buttons[i].config(
                text=str(i),
                bg='#30363d',
                fg='#8b949e'
            )
        
        # Configurar hot cues activos
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
    
    def scan_all_cues(self):
        """Escanear cue points en todos los archivos."""
        
        if not self.audio_files:
            messagebox.showwarning("Warning", "No audio files loaded")
            return
        
        self.status_label.config(text="🔍 Scanning all files for cue points...")
        self.root.update()
        
        total_cues = 0
        files_with_cues = 0
        
        for i, audio_file in enumerate(self.audio_files):
            filename = audio_file['filename']
            file_path = audio_file['path']
            
            # Actualizar status
            self.status_label.config(text=f"🔍 Scanning {i+1}/{len(self.audio_files)}: {filename[:30]}...")
            self.root.update()
            
            try:
                metadata = self.metadata_reader.scan_file(file_path)
                cue_points = metadata.get('cue_points', [])
                
                audio_file['cue_count'] = len(cue_points)
                
                if cue_points:
                    files_with_cues += 1
                    total_cues += len(cue_points)
                    print(f"✅ {filename}: {len(cue_points)} cue points")
                
            except Exception as e:
                print(f"❌ Error scanning {filename}: {e}")
                audio_file['cue_count'] = 0
        
        # Actualizar lista
        self.update_file_list()
        
        # Mostrar resultados
        result_msg = f"📊 Scan complete: {files_with_cues} files with {total_cues} total cue points"
        self.status_label.config(text=result_msg)
        
        print(f"📊 Scan Results:")
        print(f"   Files scanned: {len(self.audio_files)}")
        print(f"   Files with cues: {files_with_cues}")
        print(f"   Total cue points: {total_cues}")
        
        messagebox.showinfo("Scan Complete", result_msg)
    
    def run(self):
        """Ejecutar la aplicación."""
        print("🎯 DjAlfin Direct Cue Reader")
        print("Reading embedded cue points from /Volumes/KINGSTON/Audio")
        self.root.mainloop()

def main():
    """Función principal."""
    try:
        app = DirectCueReader()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
