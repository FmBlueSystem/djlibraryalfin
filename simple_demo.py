#!/usr/bin/env python3
"""
Demo Simplificado del Panel de Metadatos Mejorado
Versión que funciona mejor en macOS con Tkinter del sistema
"""

import tkinter as tk
from tkinter import ttk
import os

# Silenciar advertencias de deprecación
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class SimpleDemoPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()
    
    def setup_window(self):
        """Configurar la ventana principal."""
        self.root.title("🎵 DjAlfin - Panel de Metadatos Mejorado")
        self.root.geometry("450x600")
        self.root.configure(bg='#f0f0f0')
        
        # Centrar la ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"450x600+{x}+{y}")
    
    def create_widgets(self):
        """Crear todos los widgets del panel."""
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === TÍTULO ===
        title_label = tk.Label(
            main_frame,
            text="🎵 Metadatos",
            font=("Arial", 18, "bold"),
            bg='#f0f0f0',
            fg='#333333'
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_label = tk.Label(
            main_frame,
            text="Gestión Inteligente",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#666666'
        )
        subtitle_label.pack(pady=(0, 20))
        
        # === ESTADÍSTICAS ===
        self.create_stats_section(main_frame)
        
        # === ESTADO APIs ===
        self.create_api_section(main_frame)
        
        # === ACCIONES ===
        self.create_actions_section(main_frame)
        
        # === INFORMACIÓN ===
        info_frame = tk.Frame(main_frame, bg='#f0f0f0')
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        info_label = tk.Label(
            info_frame,
            text="✨ Panel de metadatos completamente renovado\ncon diseño moderno y funcionalidades mejoradas",
            font=("Arial", 10),
            bg='#f0f0f0',
            fg='#28a745',
            justify=tk.CENTER
        )
        info_label.pack()
    
    def create_stats_section(self, parent):
        """Crear sección de estadísticas."""
        # Frame con borde
        stats_frame = tk.LabelFrame(
            parent,
            text="📊 Estado Actual",
            font=("Arial", 12, "bold"),
            bg='#f0f0f0',
            fg='#333333',
            padx=15,
            pady=10
        )
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Estadísticas
        stats_text = """📀 Total: 1,247 pistas
✅ Completas: 1,089
❌ Incompletas: 158

🎭 Sin género: 45
🎵 Sin BPM: 89
🎹 Sin key: 67"""
        
        stats_label = tk.Label(
            stats_frame,
            text=stats_text,
            font=("Arial", 11),
            bg='#f0f0f0',
            fg='#333333',
            justify=tk.LEFT
        )
        stats_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Completitud
        completeness_frame = tk.Frame(stats_frame, bg='#f0f0f0')
        completeness_frame.pack(fill=tk.X)
        
        comp_label = tk.Label(
            completeness_frame,
            text="Completitud: 87.3% • Excelente",
            font=("Arial", 11, "bold"),
            bg='#f0f0f0',
            fg='#28a745'
        )
        comp_label.pack(anchor=tk.W)
        
        # Barra de progreso simulada
        progress_frame = tk.Frame(completeness_frame, bg='#28a745', height=8)
        progress_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Parte vacía de la barra
        empty_frame = tk.Frame(completeness_frame, bg='#e9ecef', height=8)
        empty_frame.place(relx=0.873, rely=1, relwidth=0.127, anchor='sw')
    
    def create_api_section(self, parent):
        """Crear sección de estado de APIs."""
        api_frame = tk.LabelFrame(
            parent,
            text="🔗 Estado APIs",
            font=("Arial", 12, "bold"),
            bg='#f0f0f0',
            fg='#333333',
            padx=15,
            pady=10
        )
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Estado general
        status_label = tk.Label(
            api_frame,
            text="✅ Todas las APIs operativas",
            font=("Arial", 11, "bold"),
            bg='#f0f0f0',
            fg='#28a745'
        )
        status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # APIs individuales
        apis_text = """🟢 Spotify ✓
🟢 MusicBrainz ✓"""
        
        apis_label = tk.Label(
            api_frame,
            text=apis_text,
            font=("Arial", 10),
            bg='#f0f0f0',
            fg='#333333',
            justify=tk.LEFT
        )
        apis_label.pack(anchor=tk.W)
    
    def create_actions_section(self, parent):
        """Crear sección de acciones."""
        actions_frame = tk.LabelFrame(
            parent,
            text="🚀 Acciones",
            font=("Arial", 12, "bold"),
            bg='#f0f0f0',
            fg='#333333',
            padx=15,
            pady=10
        )
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Botón principal
        main_btn = tk.Button(
            actions_frame,
            text="🔍 Enriquecer Metadatos",
            font=("Arial", 11, "bold"),
            bg='#007bff',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self.demo_action
        )
        main_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Botones secundarios
        secondary_frame = tk.Frame(actions_frame, bg='#f0f0f0')
        secondary_frame.pack(fill=tk.X)
        
        quick_btn = tk.Button(
            secondary_frame,
            text="⚡ Análisis Rápido",
            font=("Arial", 10),
            bg='#6c757d',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=self.demo_action
        )
        quick_btn.pack(fill=tk.X, pady=(0, 5))
        
        preview_btn = tk.Button(
            secondary_frame,
            text="👁️ Vista Previa",
            font=("Arial", 10),
            bg='#6c757d',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=6,
            command=self.demo_action
        )
        preview_btn.pack(fill=tk.X)
        
        # === ACCIONES RÁPIDAS ===
        quick_actions_frame = tk.LabelFrame(
            parent,
            text="⚡ Acciones Rápidas",
            font=("Arial", 12, "bold"),
            bg='#f0f0f0',
            fg='#333333',
            padx=15,
            pady=10
        )
        quick_actions_frame.pack(fill=tk.X)
        
        # Grid de botones
        btn_frame = tk.Frame(quick_actions_frame, bg='#f0f0f0')
        btn_frame.pack(fill=tk.X)
        
        # Fila 1
        row1_frame = tk.Frame(btn_frame, bg='#f0f0f0')
        row1_frame.pack(fill=tk.X, pady=(0, 5))
        
        refresh_btn = tk.Button(
            row1_frame,
            text="🔄 Actualizar",
            font=("Arial", 9),
            bg='#17a2b8',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.demo_action
        )
        refresh_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        validate_btn = tk.Button(
            row1_frame,
            text="✅ Validar",
            font=("Arial", 9),
            bg='#28a745',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.demo_action
        )
        validate_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        
        # Fila 2
        export_btn = tk.Button(
            btn_frame,
            text="📄 Exportar Reporte",
            font=("Arial", 9),
            bg='#ffc107',
            fg='black',
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.demo_action
        )
        export_btn.pack(fill=tk.X)
    
    def demo_action(self):
        """Acción de demostración."""
        print("🎵 Acción ejecutada en el panel de metadatos mejorado!")
        
        # Mostrar mensaje en la ventana
        msg_window = tk.Toplevel(self.root)
        msg_window.title("Acción Ejecutada")
        msg_window.geometry("300x100")
        msg_window.configure(bg='#f0f0f0')
        
        # Centrar ventana de mensaje
        msg_window.update_idletasks()
        x = (msg_window.winfo_screenwidth() // 2) - (300 // 2)
        y = (msg_window.winfo_screenheight() // 2) - (100 // 2)
        msg_window.geometry(f"300x100+{x}+{y}")
        
        msg_label = tk.Label(
            msg_window,
            text="🎵 Acción ejecutada correctamente!\n\nPanel de metadatos funcionando.",
            font=("Arial", 11),
            bg='#f0f0f0',
            fg='#28a745',
            justify=tk.CENTER
        )
        msg_label.pack(expand=True)
        
        # Cerrar automáticamente después de 2 segundos
        msg_window.after(2000, msg_window.destroy)
    
    def run(self):
        """Ejecutar la aplicación."""
        print("🎵 Iniciando demo del panel de metadatos mejorado...")
        print("✨ Ventana abierta. Cierra la ventana para terminar.")
        self.root.mainloop()
        print("🎵 Demo completada.")

def main():
    """Función principal."""
    try:
        demo = SimpleDemoPanel()
        demo.run()
    except Exception as e:
        print(f"❌ Error ejecutando la demo: {e}")
        print("💡 Intenta ejecutar: python3 simple_demo.py")

if __name__ == "__main__":
    main()
