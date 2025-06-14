#!/usr/bin/env python3
"""
DjAlfin - GUI Simple que Muestra Archivos Reales
Versión enfocada en mostrar correctamente los archivos de música
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import glob

# Configuración para macOS
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class DjAlfinSimpleGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_interface()
        self.scan_for_music_files()
        
    def setup_window(self):
        """Configurar ventana principal."""
        self.root.title("🎵 DjAlfin - Biblioteca Musical")
        self.root.geometry("900x600")
        self.root.configure(bg='#f0f0f0')
        
        # Configurar para visibilidad en macOS
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.focus_force()
        
        # Centrar ventana
        self.center_window()
        
        # Quitar topmost después de 2 segundos
        self.root.after(2000, lambda: self.root.attributes('-topmost', False))
        
    def center_window(self):
        """Centrar ventana en pantalla."""
        self.root.update_idletasks()
        width = 900
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_interface(self):
        """Crear interfaz principal."""
        # === HEADER ===
        header = tk.Frame(self.root, bg='#2c3e50', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_label = tk.Label(
            header,
            text="🎵 DjAlfin - Archivos de Música",
            font=("Arial", 16, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Botón de escanear
        scan_btn = tk.Button(
            header,
            text="📁 Escanear Carpeta",
            font=("Arial", 11, "bold"),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self.scan_folder
        )
        scan_btn.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # === CONTENEDOR PRINCIPAL ===
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # === PANEL IZQUIERDO - LISTA DE ARCHIVOS ===
        left_panel = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Título de la lista
        list_title = tk.Label(
            left_panel,
            text="📀 Archivos Encontrados",
            font=("Arial", 12, "bold"),
            bg='#ecf0f1',
            fg='#2c3e50',
            pady=10
        )
        list_title.pack(fill=tk.X)
        
        # Frame para la lista con scroll
        list_frame = tk.Frame(left_panel, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Listbox con scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 10),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # Bind para selección
        self.files_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # === PANEL DERECHO - INFORMACIÓN ===
        right_panel = tk.Frame(main_frame, bg='#f8f9fa', relief=tk.RAISED, bd=1, width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        # Título del panel
        info_title = tk.Label(
            right_panel,
            text="🎵 Información del Archivo",
            font=("Arial", 12, "bold"),
            bg='#f8f9fa',
            fg='#2c3e50',
            pady=10
        )
        info_title.pack(fill=tk.X)
        
        # Información del archivo
        info_frame = tk.Frame(right_panel, bg='#f8f9fa')
        info_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.file_info_var = tk.StringVar()
        self.file_info_var.set("Selecciona un archivo para ver información")
        
        self.file_info_label = tk.Label(
            info_frame,
            textvariable=self.file_info_var,
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#34495e',
            justify=tk.LEFT,
            wraplength=250,
            anchor='nw'
        )
        self.file_info_label.pack(fill=tk.BOTH, expand=True)
        
        # Estadísticas
        stats_frame = tk.LabelFrame(
            right_panel,
            text="📊 Estadísticas",
            font=("Arial", 11, "bold"),
            bg='#f8f9fa',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        stats_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.stats_var = tk.StringVar()
        self.stats_var.set("📀 Total: 0 archivos")
        
        stats_label = tk.Label(
            stats_frame,
            textvariable=self.stats_var,
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#34495e',
            justify=tk.LEFT
        )
        stats_label.pack(anchor=tk.W)
        
        # === FOOTER ===
        footer = tk.Frame(self.root, bg='#34495e', height=30)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        self.status_var = tk.StringVar()
        self.status_var.set("✅ Listo para escanear archivos")
        
        status_label = tk.Label(
            footer,
            textvariable=self.status_var,
            font=("Arial", 9),
            bg='#34495e',
            fg='#ecf0f1'
        )
        status_label.pack(expand=True, pady=5)
        
    def scan_for_music_files(self):
        """Escanear automáticamente archivos de música."""
        self.status_var.set("🔍 Escaneando archivos de música...")
        self.root.update()
        
        # Limpiar lista
        self.files_listbox.delete(0, tk.END)
        
        # Carpetas a escanear
        folders_to_scan = [
            "/Volumes/KINGSTON/Audio",
            "/Volumes/KINGSTON/DjAlfin", 
            "/Volumes/KINGSTON/djlibraryalfin-main",
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Desktop")
        ]
        
        # Extensiones de audio
        audio_extensions = ['*.mp3', '*.m4a', '*.flac', '*.wav', '*.aac', '*.ogg']
        
        found_files = []
        
        print("🔍 Iniciando escaneo de archivos...")
        
        for folder in folders_to_scan:
            if os.path.exists(folder):
                print(f"📁 Escaneando: {folder}")
                self.status_var.set(f"🔍 Escaneando: {os.path.basename(folder)}")
                self.root.update()
                
                try:
                    for extension in audio_extensions:
                        pattern = os.path.join(folder, '**', extension)
                        files = glob.glob(pattern, recursive=True)
                        found_files.extend(files)
                        
                        # Limitar para rendimiento
                        if len(found_files) >= 100:
                            break
                    
                    if len(found_files) >= 100:
                        break
                        
                except Exception as e:
                    print(f"❌ Error escaneando {folder}: {e}")
        
        # Agregar archivos a la lista
        print(f"✅ Encontrados {len(found_files)} archivos")
        
        for file_path in found_files:
            filename = os.path.basename(file_path)
            self.files_listbox.insert(tk.END, filename)
            
        # Actualizar estadísticas
        self.update_stats(len(found_files))
        
        if found_files:
            self.status_var.set(f"✅ {len(found_files)} archivos encontrados")
            # Mostrar mensaje de éxito
            self.root.after(1000, lambda: messagebox.showinfo(
                "Escaneo Completado",
                f"✅ Escaneo completado!\n\n"
                f"🎵 Archivos encontrados: {len(found_files)}\n"
                f"📁 Carpetas escaneadas: {len([f for f in folders_to_scan if os.path.exists(f)])}\n"
                f"📊 Formatos: MP3, M4A, FLAC, WAV, AAC, OGG"
            ))
        else:
            self.status_var.set("❌ No se encontraron archivos de música")
            messagebox.showwarning(
                "Sin Archivos",
                "No se encontraron archivos de música.\n\n"
                "Usa el botón 'Escanear Carpeta' para\n"
                "seleccionar una carpeta específica."
            )
            
        # Guardar rutas para referencia
        self.file_paths = found_files
        
    def scan_folder(self):
        """Escanear carpeta seleccionada por el usuario."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de música")
        if not folder:
            return
            
        self.status_var.set("🔍 Escaneando carpeta seleccionada...")
        self.root.update()
        
        # Limpiar lista
        self.files_listbox.delete(0, tk.END)
        
        # Extensiones de audio
        audio_extensions = ['*.mp3', '*.m4a', '*.flac', '*.wav', '*.aac', '*.ogg']
        
        found_files = []
        
        print(f"🔍 Escaneando carpeta: {folder}")
        
        try:
            for extension in audio_extensions:
                pattern = os.path.join(folder, '**', extension)
                files = glob.glob(pattern, recursive=True)
                found_files.extend(files)
                
        except Exception as e:
            print(f"❌ Error escaneando {folder}: {e}")
            messagebox.showerror("Error", f"Error escaneando carpeta:\n{e}")
            return
        
        # Agregar archivos a la lista
        print(f"✅ Encontrados {len(found_files)} archivos en carpeta seleccionada")
        
        for file_path in found_files:
            filename = os.path.basename(file_path)
            self.files_listbox.insert(tk.END, filename)
            
        # Actualizar estadísticas
        self.update_stats(len(found_files))
        
        if found_files:
            self.status_var.set(f"✅ {len(found_files)} archivos encontrados en carpeta")
            messagebox.showinfo(
                "Escaneo Completado",
                f"✅ Escaneo completado!\n\n"
                f"📁 Carpeta: {os.path.basename(folder)}\n"
                f"🎵 Archivos encontrados: {len(found_files)}\n"
                f"📊 Formatos soportados encontrados"
            )
        else:
            self.status_var.set("❌ No se encontraron archivos en la carpeta")
            messagebox.showwarning(
                "Sin Archivos",
                f"No se encontraron archivos de música en:\n{folder}"
            )
            
        # Guardar rutas para referencia
        self.file_paths = found_files
        
    def update_stats(self, file_count):
        """Actualizar estadísticas."""
        if file_count == 0:
            self.stats_var.set("📀 Total: 0 archivos")
        else:
            # Calcular tipos de archivo
            extensions = {}
            for file_path in self.file_paths:
                ext = os.path.splitext(file_path)[1].lower()
                extensions[ext] = extensions.get(ext, 0) + 1
            
            stats_text = f"📀 Total: {file_count} archivos\n"
            for ext, count in extensions.items():
                stats_text += f"{ext.upper()}: {count}\n"
                
            self.stats_var.set(stats_text.strip())
        
    def on_file_select(self, event):
        """Manejar selección de archivo."""
        selection = self.files_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        filename = self.files_listbox.get(index)
        
        if hasattr(self, 'file_paths') and index < len(self.file_paths):
            file_path = self.file_paths[index]
            
            # Obtener información del archivo
            try:
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / (1024 * 1024)
                
                # Extraer información del nombre
                name_without_ext = os.path.splitext(filename)[0]
                if ' - ' in name_without_ext:
                    parts = name_without_ext.split(' - ', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                else:
                    artist = "Desconocido"
                    title = name_without_ext
                
                info_text = f"""📁 Archivo: {filename}

🎤 Artista: {artist}
🎵 Título: {title}
📂 Carpeta: {os.path.dirname(file_path)}
📊 Tamaño: {file_size_mb:.1f} MB
🔧 Formato: {os.path.splitext(filename)[1].upper()}

📍 Ruta completa:
{file_path}"""
                
                self.file_info_var.set(info_text)
                
            except Exception as e:
                self.file_info_var.set(f"❌ Error leyendo archivo:\n{e}")
        else:
            self.file_info_var.set(f"📁 Archivo: {filename}\n\n❌ Información no disponible")
            
    def run(self):
        """Ejecutar aplicación."""
        print("🎵 Iniciando DjAlfin GUI Simple...")
        try:
            self.root.mainloop()
            print("🎵 DjAlfin cerrado correctamente")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Función principal."""
    try:
        app = DjAlfinSimpleGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error ejecutando DjAlfin: {e}")

if __name__ == "__main__":
    main()
