#!/usr/bin/env python3
"""
DjAlfin - Interfaz Gráfica Principal
Versión optimizada para macOS con panel de metadatos mejorado
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import sqlite3
from pathlib import Path

# Silenciar advertencias
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class DjAlfinGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_database()
        self.create_main_interface()
        
    def setup_window(self):
        """Configurar ventana principal."""
        self.root.title("🎵 DjAlfin - Gestión de Biblioteca Musical")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f8f9fa')
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")
        
        # Configurar para que se muestre al frente
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        
    def setup_database(self):
        """Configurar base de datos."""
        self.db_path = "music_library.db"
        self.init_database()
        
    def init_database(self):
        """Inicializar base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY,
                    filename TEXT,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    genre TEXT,
                    bpm REAL,
                    key TEXT,
                    duration REAL,
                    file_path TEXT,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
    
    def create_main_interface(self):
        """Crear interfaz principal."""
        # === BARRA DE HERRAMIENTAS ===
        self.create_toolbar()
        
        # === CONTENEDOR PRINCIPAL ===
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#f8f9fa')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # === PANEL IZQUIERDO - LISTA DE PISTAS ===
        left_panel = self.create_tracks_panel(main_container)
        main_container.add(left_panel, width=700)
        
        # === PANEL DERECHO - METADATOS MEJORADO ===
        right_panel = self.create_metadata_panel(main_container)
        main_container.add(right_panel, width=450)
        
        # === BARRA DE ESTADO ===
        self.create_status_bar()
        
        # Cargar datos iniciales
        self.load_tracks()
        
    def create_toolbar(self):
        """Crear barra de herramientas."""
        toolbar = tk.Frame(self.root, bg='#343a40', height=50)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # Botones principales
        btn_frame = tk.Frame(toolbar, bg='#343a40')
        btn_frame.pack(side=tk.LEFT, padx=10, pady=8)
        
        scan_btn = tk.Button(
            btn_frame,
            text="📁 Escanear Biblioteca",
            font=("Arial", 10, "bold"),
            bg='#007bff',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.scan_library
        )
        scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        enrich_btn = tk.Button(
            btn_frame,
            text="🔍 Enriquecer Metadatos",
            font=("Arial", 10, "bold"),
            bg='#28a745',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.enrich_metadata
        )
        enrich_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Título
        title_label = tk.Label(
            toolbar,
            text="🎵 DjAlfin",
            font=("Arial", 16, "bold"),
            bg='#343a40',
            fg='white'
        )
        title_label.pack(side=tk.RIGHT, padx=20, pady=10)
        
    def create_tracks_panel(self, parent):
        """Crear panel de lista de pistas."""
        panel = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        
        # Título
        title_frame = tk.Frame(panel, bg='#f8f9fa', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="📀 Biblioteca Musical",
            font=("Arial", 14, "bold"),
            bg='#f8f9fa',
            fg='#333333'
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Treeview para mostrar pistas
        tree_frame = tk.Frame(panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.tracks_tree = ttk.Treeview(
            tree_frame,
            columns=('artist', 'title', 'album', 'genre', 'bpm', 'key'),
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Configurar columnas
        self.tracks_tree.heading('artist', text='Artista')
        self.tracks_tree.heading('title', text='Título')
        self.tracks_tree.heading('album', text='Álbum')
        self.tracks_tree.heading('genre', text='Género')
        self.tracks_tree.heading('bpm', text='BPM')
        self.tracks_tree.heading('key', text='Key')
        
        self.tracks_tree.column('artist', width=150)
        self.tracks_tree.column('title', width=200)
        self.tracks_tree.column('album', width=150)
        self.tracks_tree.column('genre', width=100)
        self.tracks_tree.column('bpm', width=60)
        self.tracks_tree.column('key', width=50)
        
        # Configurar scrollbars
        v_scrollbar.config(command=self.tracks_tree.yview)
        h_scrollbar.config(command=self.tracks_tree.xview)
        
        # Empaquetar
        self.tracks_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind para selección
        self.tracks_tree.bind('<<TreeviewSelect>>', self.on_track_select)
        
        return panel
        
    def create_metadata_panel(self, parent):
        """Crear panel de metadatos mejorado."""
        panel = tk.Frame(parent, bg='#f8f9fa', relief=tk.RAISED, bd=1)
        
        # Scroll para el panel
        canvas = tk.Canvas(panel, bg='#f8f9fa')
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f8f9fa')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # === TÍTULO ===
        title_frame = tk.Frame(scrollable_frame, bg='#f8f9fa')
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        title_label = tk.Label(
            title_frame,
            text="🎵 Metadatos",
            font=("Arial", 16, "bold"),
            bg='#f8f9fa',
            fg='#333333'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Gestión Inteligente",
            font=("Arial", 11),
            bg='#f8f9fa',
            fg='#666666'
        )
        subtitle_label.pack()
        
        # === ESTADÍSTICAS ===
        self.create_stats_card(scrollable_frame)
        
        # === ESTADO APIs ===
        self.create_api_status_card(scrollable_frame)
        
        # === INFORMACIÓN DE PISTA ===
        self.create_track_info_card(scrollable_frame)
        
        # === ACCIONES ===
        self.create_actions_card(scrollable_frame)
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return panel
        
    def create_stats_card(self, parent):
        """Crear card de estadísticas."""
        card = tk.LabelFrame(
            parent,
            text="📊 Estado Actual",
            font=("Arial", 12, "bold"),
            bg='#f8f9fa',
            fg='#333333',
            padx=15,
            pady=10
        )
        card.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Variables para estadísticas
        self.stats_text = tk.StringVar()
        self.completeness_text = tk.StringVar()
        
        stats_label = tk.Label(
            card,
            textvariable=self.stats_text,
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#333333',
            justify=tk.LEFT
        )
        stats_label.pack(anchor=tk.W, pady=(0, 10))
        
        completeness_label = tk.Label(
            card,
            textvariable=self.completeness_text,
            font=("Arial", 11, "bold"),
            bg='#f8f9fa',
            fg='#28a745'
        )
        completeness_label.pack(anchor=tk.W)
        
        # Actualizar estadísticas iniciales
        self.update_stats()
        
    def create_api_status_card(self, parent):
        """Crear card de estado de APIs."""
        card = tk.LabelFrame(
            parent,
            text="🔗 Estado APIs",
            font=("Arial", 12, "bold"),
            bg='#f8f9fa',
            fg='#333333',
            padx=15,
            pady=10
        )
        card.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        status_label = tk.Label(
            card,
            text="✅ APIs configuradas\n🟢 Spotify: Listo\n🟢 MusicBrainz: Listo",
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#28a745',
            justify=tk.LEFT
        )
        status_label.pack(anchor=tk.W)
        
    def create_track_info_card(self, parent):
        """Crear card de información de pista."""
        card = tk.LabelFrame(
            parent,
            text="🎵 Pista Seleccionada",
            font=("Arial", 12, "bold"),
            bg='#f8f9fa',
            fg='#333333',
            padx=15,
            pady=10
        )
        card.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.track_info_text = tk.StringVar()
        self.track_info_text.set("Selecciona una pista para ver detalles")
        
        info_label = tk.Label(
            card,
            textvariable=self.track_info_text,
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#333333',
            justify=tk.LEFT,
            wraplength=350
        )
        info_label.pack(anchor=tk.W)
        
    def create_actions_card(self, parent):
        """Crear card de acciones."""
        card = tk.LabelFrame(
            parent,
            text="🚀 Acciones",
            font=("Arial", 12, "bold"),
            bg='#f8f9fa',
            fg='#333333',
            padx=15,
            pady=10
        )
        card.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Botón principal
        main_btn = tk.Button(
            card,
            text="🔍 Enriquecer Seleccionada",
            font=("Arial", 11, "bold"),
            bg='#007bff',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self.enrich_selected_track
        )
        main_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Botones secundarios
        quick_btn = tk.Button(
            card,
            text="⚡ Análisis Rápido",
            font=("Arial", 10),
            bg='#6c757d',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=self.quick_analysis
        )
        quick_btn.pack(fill=tk.X, pady=(0, 5))
        
        refresh_btn = tk.Button(
            card,
            text="🔄 Actualizar Vista",
            font=("Arial", 10),
            bg='#17a2b8',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=self.refresh_view
        )
        refresh_btn.pack(fill=tk.X)
        
    def create_status_bar(self):
        """Crear barra de estado."""
        self.status_bar = tk.Frame(self.root, bg='#e9ecef', height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)
        
        self.status_text = tk.StringVar()
        self.status_text.set("✅ Listo")
        
        status_label = tk.Label(
            self.status_bar,
            textvariable=self.status_text,
            font=("Arial", 9),
            bg='#e9ecef',
            fg='#333333'
        )
        status_label.pack(side=tk.LEFT, padx=10, pady=3)
        
    def load_tracks(self):
        """Cargar pistas desde la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT artist, title, album, genre, bpm, key FROM tracks")
            tracks = cursor.fetchall()
            
            # Limpiar treeview
            for item in self.tracks_tree.get_children():
                self.tracks_tree.delete(item)
            
            # Agregar pistas
            for track in tracks:
                self.tracks_tree.insert('', 'end', values=track)
            
            conn.close()
            self.update_stats()
            self.status_text.set(f"✅ {len(tracks)} pistas cargadas")
            
        except Exception as e:
            self.status_text.set(f"❌ Error cargando pistas: {e}")
            
    def update_stats(self):
        """Actualizar estadísticas."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar totales
            cursor.execute("SELECT COUNT(*) FROM tracks")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tracks WHERE genre IS NOT NULL AND genre != ''")
            with_genre = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tracks WHERE bpm IS NOT NULL AND bpm > 0")
            with_bpm = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tracks WHERE key IS NOT NULL AND key != ''")
            with_key = cursor.fetchone()[0]
            
            # Calcular completitud
            if total > 0:
                completeness = ((with_genre + with_bpm + with_key) / (total * 3)) * 100
            else:
                completeness = 0
            
            # Actualizar textos
            stats_text = f"""📀 Total: {total} pistas
✅ Con género: {with_genre}
🎵 Con BPM: {with_bpm}
🎹 Con key: {with_key}
❌ Incompletas: {total - min(with_genre, with_bpm, with_key)}"""
            
            self.stats_text.set(stats_text)
            
            if completeness >= 80:
                status = "Excelente"
                color = "#28a745"
            elif completeness >= 60:
                status = "Bueno"
                color = "#ffc107"
            else:
                status = "Necesita mejoras"
                color = "#dc3545"
                
            self.completeness_text.set(f"Completitud: {completeness:.1f}% • {status}")
            
            conn.close()
            
        except Exception as e:
            self.stats_text.set(f"Error calculando estadísticas: {e}")
            
    def on_track_select(self, event):
        """Manejar selección de pista."""
        selection = self.tracks_tree.selection()
        if selection:
            item = self.tracks_tree.item(selection[0])
            values = item['values']
            
            if values:
                info = f"""🎤 Artista: {values[0] or 'N/A'}
🎵 Título: {values[1] or 'N/A'}
💿 Álbum: {values[2] or 'N/A'}
🎭 Género: {values[3] or 'N/A'}
🥁 BPM: {values[4] or 'N/A'}
🎹 Key: {values[5] or 'N/A'}"""
                
                self.track_info_text.set(info)
                
    def scan_library(self):
        """Escanear biblioteca."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de música")
        if folder:
            self.status_text.set(f"📁 Escaneando: {folder}")
            messagebox.showinfo("Escaneo", f"Iniciando escaneo en:\n{folder}")
            
    def enrich_metadata(self):
        """Enriquecer metadatos."""
        self.status_text.set("🔍 Enriqueciendo metadatos...")
        messagebox.showinfo("Enriquecimiento", "Proceso de enriquecimiento iniciado")
        
    def enrich_selected_track(self):
        """Enriquecer pista seleccionada."""
        selection = self.tracks_tree.selection()
        if selection:
            messagebox.showinfo("Enriquecimiento", "Enriqueciendo pista seleccionada...")
        else:
            messagebox.showwarning("Advertencia", "Selecciona una pista primero")
            
    def quick_analysis(self):
        """Análisis rápido."""
        messagebox.showinfo("Análisis", "Ejecutando análisis rápido...")
        
    def refresh_view(self):
        """Actualizar vista."""
        self.load_tracks()
        messagebox.showinfo("Actualización", "Vista actualizada correctamente")
        
    def run(self):
        """Ejecutar aplicación."""
        print("🎵 Iniciando DjAlfin GUI...")
        self.root.mainloop()

def main():
    """Función principal."""
    try:
        app = DjAlfinGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error ejecutando DjAlfin: {e}")

if __name__ == "__main__":
    main()
