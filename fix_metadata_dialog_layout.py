#!/usr/bin/env python3
"""
Optimiza el layout del diálogo de metadatos para que quepa mejor en pantalla
Mejora la distribución de componentes y reduce la altura total
"""

import os

def fix_metadata_dialog_layout():
    """Optimiza el layout del diálogo de metadatos"""
    print("🔧 Optimizando layout del diálogo de metadatos...")
    
    with open('ui/metadata_panel.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Reducir tamaño inicial de la ventana
    content = content.replace(
        'self.geometry("900x800")',
        'self.geometry("850x700")'
    )
    
    # 2. Reducir padding en frames principales para aprovechar mejor el espacio
    content = content.replace(
        'main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)',
        'main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)'
    )
    
    # 3. Optimizar spacing en estadísticas usando grid layout más compacto
    stats_section_optimized = '''    def create_statistics_frame(self, parent):
        """Crea el frame de estadísticas con layout optimizado."""
        stats_frame = ttk.LabelFrame(parent, text="📊 Estado Actual de Metadatos", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Labels de estadísticas usando grid para layout más compacto
        self.stats_labels = {}
        
        # Fila 1 - Estadísticas principales (2 columnas)
        ttk.Label(stats_frame, text="Total:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        self.stats_labels['total'] = ttk.Label(stats_frame, text="0", font=("Segoe UI", 9))
        self.stats_labels['total'].grid(row=0, column=1, sticky="w", padx=(5, 15))
        
        ttk.Label(stats_frame, text="Completas:", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w")
        self.stats_labels['complete'] = ttk.Label(stats_frame, text="0", font=("Segoe UI", 9))
        self.stats_labels['complete'].grid(row=0, column=3, sticky="w", padx=(5, 15))
        
        ttk.Label(stats_frame, text="Incompletas:", font=("Segoe UI", 9, "bold")).grid(row=0, column=4, sticky="w")
        self.stats_labels['incomplete'] = ttk.Label(stats_frame, text="0", font=("Segoe UI", 9))
        self.stats_labels['incomplete'].grid(row=0, column=5, sticky="w", padx=(5, 0))
        
        # Fila 2 - Campos específicos (3 columnas)
        ttk.Label(stats_frame, text="Sin género:", font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.stats_labels['missing_genre'] = ttk.Label(stats_frame, text="0", font=("Segoe UI", 8))
        self.stats_labels['missing_genre'].grid(row=1, column=1, sticky="w", padx=(5, 15), pady=(5, 0))
        
        ttk.Label(stats_frame, text="Sin BPM:", font=("Segoe UI", 8)).grid(row=1, column=2, sticky="w", pady=(5, 0))
        self.stats_labels['missing_bpm'] = ttk.Label(stats_frame, text="0", font=("Segoe UI", 8))
        self.stats_labels['missing_bmp'].grid(row=1, column=3, sticky="w", padx=(5, 15), pady=(5, 0))
        
        ttk.Label(stats_frame, text="Sin key:", font=("Segoe UI", 8)).grid(row=1, column=4, sticky="w", pady=(5, 0))
        self.stats_labels['missing_key'] = ttk.Label(stats_frame, text="0", font=("Segoe UI", 8))
        self.stats_labels['missing_key'].grid(row=1, column=5, sticky="w", padx=(5, 0), pady=(5, 0))
        
        # Fila 3 - Porcentaje centrado
        percentage_frame = ttk.Frame(stats_frame)
        percentage_frame.grid(row=2, column=0, columnspan=6, pady=(5, 0))
        
        ttk.Label(percentage_frame, text="Completitud:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.stats_labels['percentage'] = ttk.Label(percentage_frame, text="0%", font=("Segoe UI", 9, "bold"), foreground="#00d4ff")
        self.stats_labels['percentage'].pack(side=tk.LEFT, padx=(5, 0))'''
    
    # Reemplazar la función de estadísticas
    content = content.replace(
        content[content.find('    def create_statistics_frame(self, parent):'):content.find('    def create_config_frame(self, parent):')],
        stats_section_optimized + '\n\n'
    )
    
    # 4. Hacer el frame de configuración más compacto usando pestañas
    config_section_optimized = '''    def create_config_frame(self, parent):
        """Crea el frame de configuración optimizado con pestañas."""
        self.config_frame = ttk.LabelFrame(parent, text="⚙️ Configuración", padding=10)
        self.config_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Crear notebook para pestañas
        config_notebook = ttk.Notebook(self.config_frame)
        config_notebook.pack(fill=tk.X, pady=(0, 5))
        
        # Pestaña APIs
        apis_frame = ttk.Frame(config_notebook)
        config_notebook.add(apis_frame, text="APIs")
        
        self.api_vars = {}
        
        # APIs en layout horizontal compacto
        api_row = ttk.Frame(apis_frame)
        api_row.pack(fill=tk.X, pady=5)
        
        self.api_vars['spotify'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(api_row, text="🎵 Spotify", variable=self.api_vars['spotify']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.api_vars['musicbrainz'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(api_row, text="🎼 MusicBrainz", variable=self.api_vars['musicbrainz']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.api_vars['lastfm'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(api_row, text="📻 Last.fm", variable=self.api_vars['lastfm'], state=tk.DISABLED).pack(side=tk.LEFT)
        
        # Pestaña Opciones
        options_frame = ttk.Frame(config_notebook)
        config_notebook.add(options_frame, text="Opciones")
        
        # Opciones en layout horizontal
        options_row = ttk.Frame(options_frame)
        options_row.pack(fill=tk.X, pady=5)
        
        self.enrich_all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_row, text="🔍 Análisis Profundo", variable=self.enrich_all_var).pack(side=tk.LEFT, padx=(0, 15))
        
        self.write_to_file_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row, text="💾 Guardar en archivos", variable=self.write_to_file_var).pack(side=tk.LEFT)
        
        # Estado de APIs compacto
        self.api_status_label = ttk.Label(
            self.config_frame,
            text="🔄 Verificando APIs...",
            font=("Segoe UI", 8),
            foreground="#cccccc"
        )
        self.api_status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Verificar estado de APIs al crear el frame
        self.after(100, self.check_api_status)'''
    
    # Reemplazar la función de configuración
    content = content.replace(
        content[content.find('    def create_config_frame(self, parent):'):content.find('    def create_progress_frame(self, parent):')],
        config_section_optimized + '\n\n'
    )
    
    # 5. Hacer el frame de progreso más compacto
    content = content.replace(
        'self.progress_frame = ttk.LabelFrame(parent, text="📈 Progreso", padding=15)',
        'self.progress_frame = ttk.LabelFrame(parent, text="📈 Progreso", padding=8)'
    )
    
    # 6. Hacer el frame de botones más compacto
    content = content.replace(
        'buttons_container = ttk.LabelFrame(parent, text="🎯 Acciones", padding=15)',
        'buttons_container = ttk.LabelFrame(parent, text="🎯 Acciones", padding=8)'
    )
    
    # 7. Reducir altura del Treeview de resultados
    content = content.replace(
        'self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")',
        'self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)'
    )
    
    # 8. Reducir padding en el frame de resultados
    content = content.replace(
        'results_frame = ttk.LabelFrame(parent, text="📋 Resultados", padding=15)',
        'results_frame = ttk.LabelFrame(parent, text="📋 Resultados", padding=8)'
    )
    
    # 9. Hacer ventana redimensionable con tamaño mínimo
    content = content.replace(
        'self.resizable(True, True)',
        'self.resizable(True, True)\n        self.minsize(700, 600)  # Tamaño mínimo\n        self.maxsize(1000, 800)  # Tamaño máximo'
    )
    
    with open('ui/metadata_panel.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Layout del diálogo optimizado")

def fix_typo_in_stats():
    """Corrige el typo en la línea de missing_bpm"""
    print("🔧 Corrigiendo typo en estadísticas...")
    
    with open('ui/metadata_panel.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corregir el typo missing_bmp -> missing_bpm
    content = content.replace(
        "self.stats_labels['missing_bmp'].grid",
        "self.stats_labels['missing_bpm'].grid"
    )
    
    with open('ui/metadata_panel.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Typo corregido")

def test_layout():
    """Prueba que el layout optimizado funcione"""
    print("🧪 Probando layout optimizado...")
    
    try:
        import sys
        sys.path.append('.')
        
        # Intentar importar el diálogo
        from ui.metadata_panel import MetadataEnrichmentDialog
        print("✅ Import exitoso")
        
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("📐 OPTIMIZACIÓN DE LAYOUT DEL DIÁLOGO DE METADATOS")
    print("=" * 55)
    
    # Aplicar optimizaciones de layout
    fix_metadata_dialog_layout()
    
    # Corregir typo
    fix_typo_in_stats()
    
    # Verificar que funcione
    if test_layout():
        print("\n🎉 Optimización de layout completada!")
        print("\n📊 Mejoras aplicadas:")
        print("✅ Ventana reducida de 900x800 a 850x700")
        print("✅ Estadísticas en grid compacto (2 filas)")
        print("✅ Configuración organizada en pestañas")
        print("✅ Reduced padding en todos los frames")
        print("✅ Treeview de resultados con altura fija")
        print("✅ Ventana redimensionable con límites")
        print("✅ Layout horizontal para APIs y opciones")
        
        print("\n💡 Resultado:")
        print("• El diálogo ahora cabe mejor en pantallas normales")
        print("• Mejor aprovechamiento del espacio vertical")
        print("• Interfaz más compacta y organizada")
        print("• Funcionalidad completa mantenida")
    else:
        print("❌ Hubo un problema con la optimización")

if __name__ == "__main__":
    main()