#!/usr/bin/env python3
"""
DjAlfin - GUI Instantánea
Versión que muestra archivos inmediatamente sin demoras
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

# Configuración para macOS
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class DjAlfinInstant:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_interface()
        self.show_welcome()
        
    def setup_window(self):
        """Configurar ventana principal."""
        self.root.title("🎵 DjAlfin - Biblioteca Musical Instantánea")
        self.root.geometry("800x500")
        self.root.configure(bg='#f0f0f0')
        
        # Configurar para visibilidad máxima
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
        width = 800
        height = 500
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_interface(self):
        """Crear interfaz principal."""
        # === HEADER ===
        header = tk.Frame(self.root, bg='#2c3e50', height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_label = tk.Label(
            header,
            text="🎵 DjAlfin - Explorador de Música",
            font=("Arial", 14, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=12)
        
        # Botones de acción
        btn_frame = tk.Frame(header, bg='#2c3e50')
        btn_frame.pack(side=tk.RIGHT, padx=15, pady=8)
        
        scan_btn = tk.Button(
            btn_frame,
            text="📁 Escanear",
            font=("Arial", 10, "bold"),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.scan_folder
        )
        scan_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        quick_scan_btn = tk.Button(
            btn_frame,
            text="⚡ Escaneo Rápido",
            font=("Arial", 10, "bold"),
            bg='#2ecc71',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.quick_scan
        )
        quick_scan_btn.pack(side=tk.LEFT)
        
        # === CONTENIDO PRINCIPAL ===
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # === LISTA DE ARCHIVOS ===
        list_frame = tk.LabelFrame(
            main_frame,
            text="📀 Archivos de Música",
            font=("Arial", 12, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame interno para lista con scroll
        inner_frame = tk.Frame(list_frame, bg='white')
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(inner_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.files_listbox = tk.Listbox(
            inner_frame,
            font=("Arial", 10),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            bg='white',
            fg='#2c3e50'
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # Bind para selección
        self.files_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # === INFORMACIÓN ===
        info_frame = tk.LabelFrame(
            main_frame,
            text="ℹ️ Información",
            font=("Arial", 11, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50',
            padx=10,
            pady=5
        )
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.info_var = tk.StringVar()
        self.info_var.set("Usa los botones de arriba para escanear archivos de música")
        
        info_label = tk.Label(
            info_frame,
            textvariable=self.info_var,
            font=("Arial", 10),
            bg='#f0f0f0',
            fg='#34495e',
            wraplength=700,
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)
        
        # === FOOTER ===
        footer = tk.Frame(self.root, bg='#34495e', height=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        self.status_var = tk.StringVar()
        self.status_var.set("✅ Listo - Selecciona una opción de escaneo")
        
        status_label = tk.Label(
            footer,
            textvariable=self.status_var,
            font=("Arial", 9),
            bg='#34495e',
            fg='#ecf0f1'
        )
        status_label.pack(expand=True, pady=3)
        
        # Cargar archivos de ejemplo inmediatamente
        self.load_sample_files()
        
    def load_sample_files(self):
        """Cargar archivos de ejemplo para mostrar inmediatamente."""
        sample_files = [
            "🎵 Ricky Martin - Livin' La Vida Loca.mp3",
            "🎵 Spice Girls - Who Do You Think You Are.mp3",
            "🎵 Steps - One For Sorrow.mp3",
            "🎵 Whitney Houston - I Will Always Love You.mp3",
            "🎵 Ed Sheeran - Bad Heartbroken Habits.mp3",
            "🎵 Coldplay - A Sky Full Of Stars.mp3",
            "🎵 The Chainsmokers - Something Just Like This.mp3",
            "🎵 Sean Paul - Get Busy.mp3",
            "🎵 Oasis - She's Electric.mp3",
            "🎵 Rolling Stones - Sympathy For the Devil.mp3",
            "🎵 Alice Cooper - School's Out.mp3",
            "🎵 Status Quo - Rockin' All Over the World.mp3",
            "🎵 Blue Öyster Cult - The Reaper.mp3",
            "🎵 Dolly Parton - 9 to 5.mp3",
            "🎵 Apache Indian - Boom Shack-a-lak.mp3",
            "🎵 Rihanna Feat. Drake - Work.mp3"
        ]
        
        for file in sample_files:
            self.files_listbox.insert(tk.END, file)
            
        self.info_var.set(f"📀 Mostrando {len(sample_files)} archivos de ejemplo. Usa 'Escanear' para buscar archivos reales.")
        self.status_var.set(f"✅ {len(sample_files)} archivos de ejemplo cargados")
        
    def quick_scan(self):
        """Escaneo rápido de ubicaciones comunes."""
        self.status_var.set("⚡ Ejecutando escaneo rápido...")
        self.root.update()
        
        # Limpiar lista
        self.files_listbox.delete(0, tk.END)
        
        # Ubicaciones a escanear
        locations = [
            "/Volumes/KINGSTON/Audio",
            "/Volumes/KINGSTON/DjAlfin",
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Desktop")
        ]
        
        found_files = []
        scanned_locations = []
        
        for location in locations:
            if os.path.exists(location):
                scanned_locations.append(location)
                self.status_var.set(f"⚡ Escaneando: {os.path.basename(location)}")
                self.root.update()
                
                try:
                    # Escaneo simple y rápido
                    for item in os.listdir(location):
                        if item.lower().endswith(('.mp3', '.m4a', '.flac', '.wav', '.aac')):
                            found_files.append(os.path.join(location, item))
                            self.files_listbox.insert(tk.END, f"🎵 {item}")
                            
                            # Actualizar cada 5 archivos para mostrar progreso
                            if len(found_files) % 5 == 0:
                                self.root.update()
                                
                            # Limitar para rendimiento
                            if len(found_files) >= 50:
                                break
                                
                except Exception as e:
                    print(f"Error escaneando {location}: {e}")
                    
                if len(found_files) >= 50:
                    break
        
        # Actualizar información
        if found_files:
            self.info_var.set(
                f"✅ Escaneo rápido completado!\n"
                f"📁 Ubicaciones: {', '.join([os.path.basename(loc) for loc in scanned_locations])}\n"
                f"🎵 Archivos encontrados: {len(found_files)}"
            )
            self.status_var.set(f"✅ {len(found_files)} archivos encontrados")
            
            # Mostrar mensaje de éxito
            messagebox.showinfo(
                "Escaneo Rápido Completado",
                f"✅ Escaneo completado!\n\n"
                f"🎵 Archivos encontrados: {len(found_files)}\n"
                f"📁 Ubicaciones escaneadas: {len(scanned_locations)}\n"
                f"⚡ Tiempo: Menos de 5 segundos"
            )
        else:
            self.info_var.set("❌ No se encontraron archivos en las ubicaciones comunes")
            self.status_var.set("❌ Sin archivos encontrados")
            
            # Recargar archivos de ejemplo
            self.load_sample_files()
            
            messagebox.showwarning(
                "Sin Archivos",
                "No se encontraron archivos de música en las ubicaciones comunes.\n\n"
                "Prueba con 'Escanear' para seleccionar una carpeta específica."
            )
            
    def scan_folder(self):
        """Escanear carpeta seleccionada."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de música")
        if not folder:
            return
            
        self.status_var.set("📁 Escaneando carpeta seleccionada...")
        self.root.update()
        
        # Limpiar lista
        self.files_listbox.delete(0, tk.END)
        
        found_files = []
        
        try:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg')):
                        file_path = os.path.join(root, file)
                        found_files.append(file_path)
                        self.files_listbox.insert(tk.END, f"🎵 {file}")
                        
                        # Actualizar cada 10 archivos
                        if len(found_files) % 10 == 0:
                            self.status_var.set(f"📁 Encontrados: {len(found_files)} archivos...")
                            self.root.update()
                            
                        # Limitar para rendimiento
                        if len(found_files) >= 100:
                            break
                            
                if len(found_files) >= 100:
                    break
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error escaneando carpeta:\n{e}")
            return
        
        # Actualizar información
        if found_files:
            self.info_var.set(
                f"✅ Escaneo de carpeta completado!\n"
                f"📁 Carpeta: {os.path.basename(folder)}\n"
                f"🎵 Archivos encontrados: {len(found_files)}"
            )
            self.status_var.set(f"✅ {len(found_files)} archivos en carpeta")
            
            messagebox.showinfo(
                "Escaneo Completado",
                f"✅ Escaneo completado!\n\n"
                f"📁 Carpeta: {os.path.basename(folder)}\n"
                f"🎵 Archivos encontrados: {len(found_files)}\n"
                f"📊 Formatos: MP3, M4A, FLAC, WAV, AAC, OGG"
            )
        else:
            self.info_var.set(f"❌ No se encontraron archivos en: {os.path.basename(folder)}")
            self.status_var.set("❌ Sin archivos en carpeta")
            
            messagebox.showwarning(
                "Sin Archivos",
                f"No se encontraron archivos de música en:\n{folder}"
            )
            
    def on_file_select(self, event):
        """Manejar selección de archivo."""
        selection = self.files_listbox.curselection()
        if not selection:
            return
            
        filename = self.files_listbox.get(selection[0])
        
        # Extraer información del nombre
        clean_name = filename.replace("🎵 ", "")
        
        if " - " in clean_name:
            parts = clean_name.split(" - ", 1)
            artist = parts[0].strip()
            title = parts[1].replace(".mp3", "").replace(".m4a", "").replace(".flac", "").strip()
        else:
            artist = "Desconocido"
            title = clean_name.replace(".mp3", "").replace(".m4a", "").replace(".flac", "").strip()
        
        info_text = f"🎤 Artista: {artist}\n🎵 Título: {title}\n📁 Archivo: {clean_name}"
        self.info_var.set(info_text)
        
    def show_welcome(self):
        """Mostrar mensaje de bienvenida."""
        self.root.after(1000, lambda: messagebox.showinfo(
            "🎵 DjAlfin - Explorador de Música",
            "¡Bienvenido a DjAlfin!\n\n"
            "✨ Explorador de archivos de música\n"
            "⚡ Escaneo rápido disponible\n"
            "📁 Selección manual de carpetas\n"
            "🎵 Visualización instantánea\n\n"
            "Usa los botones de arriba para empezar."
        ))
        
    def run(self):
        """Ejecutar aplicación."""
        print("🎵 Iniciando DjAlfin Instantáneo...")
        try:
            self.root.mainloop()
            print("🎵 DjAlfin cerrado correctamente")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Función principal."""
    try:
        app = DjAlfinInstant()
        app.run()
    except Exception as e:
        print(f"❌ Error ejecutando DjAlfin: {e}")

if __name__ == "__main__":
    main()
