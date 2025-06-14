#!/usr/bin/env python3
"""
Demo del Panel de Metadatos Mejorado
Muestra las mejoras visuales implementadas en el panel lateral
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.theme import MacOSTheme

class MockMetadataEnricher:
    """Mock del MetadataEnricher para la demo."""
    
    def __init__(self, db_path=None):
        self.clients = {}
    
    def get_enrichment_statistics(self):
        """Retorna estadísticas de ejemplo."""
        return {
            'total_tracks': 1247,
            'complete_tracks': 1089,
            'incomplete_tracks': 158,
            'missing_genre': 45,
            'missing_bpm': 89,
            'missing_key': 67,
            'completion_percentage': 87.3
        }

class DemoMetadataPanel(ttk.Frame):
    """Panel de metadatos mejorado para demostración."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.enricher = MockMetadataEnricher()
        
        self.setup_panel()
        self.load_quick_stats()
        
        # Auto-actualizar estadísticas cada 10 segundos para la demo
        self.after(10000, self.auto_refresh_stats)
    
    def setup_panel(self):
        """Configura el panel con el nuevo diseño."""
        # Título con estilo consistente
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, MacOSTheme.PADDING_LARGE))
        
        title_label = ttk.Label(
            title_frame,
            text="🎵 Metadatos",
            style="Title.TLabel"
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Gestión Inteligente",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack()
        
        # Frame de estadísticas mejorado
        self.create_stats_section()
        
        # Frame de estado de APIs
        self.create_api_status_section()
        
        # Frame de acciones principales
        self.create_actions_section()
        
        # Frame de acciones rápidas
        self.create_quick_actions_section()
    
    def create_stats_section(self):
        """Crea la sección de estadísticas con diseño moderno y elegante."""
        # === FRAME PRINCIPAL CON ESTILO MEJORADO ===
        stats_frame = ttk.LabelFrame(
            self, 
            text="📊 Estado Actual", 
            padding=MacOSTheme.PADDING_MEDIUM,
            style="ModernCard.TFrame"
        )
        stats_frame.pack(fill=tk.X, pady=(0, MacOSTheme.PADDING_MEDIUM))
        
        # === ESTADÍSTICAS PRINCIPALES CON MEJOR FORMATO ===
        self.quick_stats_label = ttk.Label(
            stats_frame,
            text="🔄 Cargando estadísticas...",
            justify=tk.LEFT,
            font=(MacOSTheme.FONT_FAMILY_UI, MacOSTheme.FONT_SIZE_BODY),
            foreground=MacOSTheme.FG_SECONDARY
        )
        self.quick_stats_label.pack(anchor=tk.W, pady=(0, MacOSTheme.PADDING_SMALL))
        
        # === SECCIÓN DE COMPLETITUD MEJORADA ===
        completeness_section = ttk.Frame(stats_frame)
        completeness_section.pack(fill=tk.X, pady=(MacOSTheme.PADDING_SMALL, 0))
        
        # Header de completitud
        completeness_header = ttk.Frame(completeness_section)
        completeness_header.pack(fill=tk.X, pady=(0, 4))
        
        completeness_title = ttk.Label(
            completeness_header,
            text="Completitud:",
            font=(MacOSTheme.FONT_FAMILY_UI, MacOSTheme.FONT_SIZE_SMALL, "bold"),
            foreground=MacOSTheme.FG_PRIMARY
        )
        completeness_title.pack(side=tk.LEFT)
        
        self.completion_label = ttk.Label(
            completeness_header,
            text="0%",
            font=(MacOSTheme.FONT_FAMILY, MacOSTheme.FONT_SIZE_BODY, "bold"),
            foreground=MacOSTheme.ACCENT_BLUE
        )
        self.completion_label.pack(side=tk.RIGHT)
        
        # Barra de progreso moderna y más grande
        self.completion_progress = ttk.Progressbar(
            completeness_section,
            mode='determinate',
            style="TProgressbar"
        )
        self.completion_progress.pack(fill=tk.X, pady=(0, 4))
        
        # Indicador de estado textual
        self.completion_status_label = ttk.Label(
            completeness_section,
            text="",
            font=(MacOSTheme.FONT_FAMILY_UI, MacOSTheme.FONT_SIZE_SMALL),
            foreground=MacOSTheme.FG_SECONDARY
        )
        self.completion_status_label.pack(anchor=tk.W)
    
    def create_api_status_section(self):
        """Crea la sección de estado de APIs con diseño moderno."""
        # === FRAME PRINCIPAL ===
        api_frame = ttk.LabelFrame(
            self, 
            text="🔗 Estado APIs", 
            padding=MacOSTheme.PADDING_MEDIUM,
            style="ModernCard.TFrame"
        )
        api_frame.pack(fill=tk.X, pady=(0, MacOSTheme.PADDING_MEDIUM))
        
        # === INDICADOR PRINCIPAL DE ESTADO ===
        status_container = ttk.Frame(api_frame)
        status_container.pack(fill=tk.X, pady=(0, MacOSTheme.PADDING_SMALL))
        
        self.api_status_label = ttk.Label(
            status_container,
            text="✅ Todas las APIs operativas",
            font=(MacOSTheme.FONT_FAMILY_UI, MacOSTheme.FONT_SIZE_BODY),
            foreground=MacOSTheme.SUCCESS_COLOR,
            justify=tk.LEFT
        )
        self.api_status_label.pack(side=tk.LEFT)
        
        # === INDICADORES INDIVIDUALES DE APIs ===
        apis_detail_frame = ttk.Frame(api_frame)
        apis_detail_frame.pack(fill=tk.X, pady=(MacOSTheme.PADDING_SMALL, 0))
        
        # Spotify status
        spotify_frame = ttk.Frame(apis_detail_frame)
        spotify_frame.pack(fill=tk.X, pady=(0, 2))
        
        self.spotify_status_icon = ttk.Label(
            spotify_frame,
            text="🟢",
            font=(MacOSTheme.FONT_FAMILY, 12),
            foreground=MacOSTheme.SUCCESS_COLOR
        )
        self.spotify_status_icon.pack(side=tk.LEFT)
        
        self.spotify_status_text = ttk.Label(
            spotify_frame,
            text="Spotify",
            font=(MacOSTheme.FONT_FAMILY_UI, MacOSTheme.FONT_SIZE_SMALL),
            foreground=MacOSTheme.SUCCESS_COLOR
        )
        self.spotify_status_text.pack(side=tk.LEFT, padx=(4, 0))
        
        # MusicBrainz status
        mb_frame = ttk.Frame(apis_detail_frame)
        mb_frame.pack(fill=tk.X, pady=(0, 2))
        
        self.mb_status_icon = ttk.Label(
            mb_frame,
            text="🟢",
            font=(MacOSTheme.FONT_FAMILY, 12),
            foreground=MacOSTheme.SUCCESS_COLOR
        )
        self.mb_status_icon.pack(side=tk.LEFT)
        
        self.mb_status_text = ttk.Label(
            mb_frame,
            text="MusicBrainz",
            font=(MacOSTheme.FONT_FAMILY_UI, MacOSTheme.FONT_SIZE_SMALL),
            foreground=MacOSTheme.SUCCESS_COLOR
        )
        self.mb_status_text.pack(side=tk.LEFT, padx=(4, 0))
    
    def create_actions_section(self):
        """Crea la sección de acciones principales con diseño moderno."""
        # === FRAME PRINCIPAL ===
        actions_frame = ttk.LabelFrame(
            self, 
            text="🚀 Acciones", 
            padding=MacOSTheme.PADDING_MEDIUM,
            style="ModernCard.TFrame"
        )
        actions_frame.pack(fill=tk.X, pady=(0, MacOSTheme.PADDING_MEDIUM))
        
        # === BOTÓN PRINCIPAL DESTACADO ===
        main_btn_container = ttk.Frame(actions_frame)
        main_btn_container.pack(fill=tk.X, pady=(0, MacOSTheme.PADDING_SMALL))
        
        self.main_action_btn = ttk.Button(
            main_btn_container,
            text="🔍 Enriquecer Metadatos",
            command=self.demo_action,
            style="Accent.TButton"
        )
        self.main_action_btn.pack(fill=tk.X)
        
        # === SEPARADOR VISUAL ===
        separator = ttk.Separator(actions_frame, orient="horizontal")
        separator.pack(fill=tk.X, pady=MacOSTheme.PADDING_SMALL)
        
        # === ACCIONES SECUNDARIAS ===
        secondary_actions = ttk.Frame(actions_frame)
        secondary_actions.pack(fill=tk.X)
        
        # Botón de análisis rápido con icono mejorado
        self.quick_analysis_btn = ttk.Button(
            secondary_actions,
            text="⚡ Análisis Rápido",
            command=self.demo_action,
            style="Secondary.TButton"
        )
        self.quick_analysis_btn.pack(fill=tk.X, pady=(0, MacOSTheme.PADDING_SMALL))
        
        # Botón de vista previa con mejor descripción
        self.preview_btn = ttk.Button(
            secondary_actions,
            text="👁️ Vista Previa",
            command=self.demo_action,
            style="Secondary.TButton"
        )
        self.preview_btn.pack(fill=tk.X)
    
    def create_quick_actions_section(self):
        """Crea la sección de acciones rápidas con diseño moderno."""
        # === FRAME PRINCIPAL ===
        quick_frame = ttk.LabelFrame(
            self, 
            text="⚡ Acciones Rápidas", 
            padding=MacOSTheme.PADDING_MEDIUM,
            style="ModernCard.TFrame"
        )
        quick_frame.pack(fill=tk.X, pady=(0, MacOSTheme.PADDING_MEDIUM))
        
        # === GRID DE ACCIONES RÁPIDAS ===
        # Configurar grid de 2 columnas para mejor aprovechamiento del espacio
        quick_frame.columnconfigure(0, weight=1)
        quick_frame.columnconfigure(1, weight=1)
        
        # Fila 1: Actualizar y Validar
        refresh_btn = ttk.Button(
            quick_frame,
            text="🔄 Actualizar",
            command=self.load_quick_stats,
            style="Compact.TButton"
        )
        refresh_btn.grid(row=0, column=0, sticky="ew", padx=(0, 2), pady=(0, 4))
        
        validate_btn = ttk.Button(
            quick_frame,
            text="✅ Validar",
            command=self.demo_action,
            style="Compact.TButton"
        )
        validate_btn.grid(row=0, column=1, sticky="ew", padx=(2, 0), pady=(0, 4))
        
        # Fila 2: Exportar (span completo)
        export_btn = ttk.Button(
            quick_frame,
            text="📄 Exportar Reporte",
            command=self.demo_action,
            style="Compact.TButton"
        )
        export_btn.grid(row=1, column=0, columnspan=2, sticky="ew")
    
    def load_quick_stats(self):
        """Carga estadísticas rápidas con diseño mejorado y más información."""
        try:
            stats = self.enricher.get_enrichment_statistics()
            
            # === TEXTO DE ESTADÍSTICAS MEJORADO ===
            stats_lines = [
                f"📀 Total: {stats['total_tracks']} pistas",
                f"✅ Completas: {stats['complete_tracks']}",
                f"❌ Incompletas: {stats['incomplete_tracks']}"
            ]
            
            # Agregar detalles de campos faltantes solo si hay datos
            if stats['missing_genre'] > 0 or stats['missing_bpm'] > 0 or stats['missing_key'] > 0:
                stats_lines.append("") # Línea en blanco para separar
                if stats['missing_genre'] > 0:
                    stats_lines.append(f"🎭 Sin género: {stats['missing_genre']}")
                if stats['missing_bpm'] > 0:
                    stats_lines.append(f"🎵 Sin BPM: {stats['missing_bpm']}")
                if stats['missing_key'] > 0:
                    stats_lines.append(f"🎹 Sin key: {stats['missing_key']}")
            
            stats_text = "\n".join(stats_lines)
            self.quick_stats_label.config(text=stats_text)
            
            # === ACTUALIZAR BARRA DE PROGRESO ===
            completion_pct = stats['completion_percentage']
            self.completion_progress['value'] = completion_pct
            
            # Actualizar porcentaje con color dinámico
            if completion_pct >= 80:
                percentage_color = MacOSTheme.SUCCESS_COLOR
                status_text = "Excelente"
            elif completion_pct >= 50:
                percentage_color = MacOSTheme.WARNING_COLOR
                status_text = "Bueno"
            else:
                percentage_color = MacOSTheme.ERROR_COLOR
                status_text = "Necesita mejoras"
            
            self.completion_label.config(
                text=f"{completion_pct:.1f}%",
                foreground=percentage_color
            )
            
            # Actualizar indicador de estado
            self.completion_status_label.config(
                text=f"• {status_text}",
                foreground=percentage_color
            )
            
        except Exception as e:
            # === MANEJO DE ERRORES MEJORADO ===
            error_msg = f"❌ Error cargando datos: {str(e)[:25]}..."
            self.quick_stats_label.config(
                text=error_msg,
                foreground=MacOSTheme.ERROR_COLOR
            )
            self.completion_progress['value'] = 0
            self.completion_label.config(
                text="--",
                foreground=MacOSTheme.ERROR_COLOR
            )
            
            self.completion_status_label.config(
                text="• Error",
                foreground=MacOSTheme.ERROR_COLOR
            )
    
    def auto_refresh_stats(self):
        """Auto-actualiza las estadísticas cada 10 segundos para la demo."""
        self.load_quick_stats()
        self.after(10000, self.auto_refresh_stats)
    
    def demo_action(self):
        """Acción de demostración."""
        print("🎵 Acción ejecutada en el panel de metadatos mejorado!")

def main():
    """Función principal para ejecutar la demo."""
    root = tk.Tk()
    root.title("🎵 Demo: Panel de Metadatos Mejorado - DjAlfin")
    root.geometry("400x700")
    root.resizable(True, True)
    
    # Aplicar tema
    style = MacOSTheme.apply_theme(root)
    
    # Crear frame principal
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Título de la demo
    title_label = ttk.Label(
        main_frame,
        text="🎵 Panel de Metadatos Mejorado",
        style="Title.TLabel"
    )
    title_label.pack(pady=(0, 10))
    
    subtitle_label = ttk.Label(
        main_frame,
        text="Diseño moderno y elegante para macOS",
        style="Subtitle.TLabel"
    )
    subtitle_label.pack(pady=(0, 20))
    
    # Crear el panel de metadatos mejorado
    metadata_panel = DemoMetadataPanel(main_frame)
    metadata_panel.pack(fill=tk.BOTH, expand=True)
    
    # Información adicional
    info_frame = ttk.Frame(main_frame)
    info_frame.pack(fill=tk.X, pady=(20, 0))
    
    info_label = ttk.Label(
        info_frame,
        text="✨ Mejoras implementadas:\n• Diseño moderno con cards\n• Indicadores visuales mejorados\n• Mejor jerarquía de información\n• Colores dinámicos según estado\n• Layout optimizado para macOS",
        style="Caption.TLabel",
        justify=tk.LEFT
    )
    info_label.pack(anchor=tk.W)
    
    root.mainloop()

if __name__ == "__main__":
    main()
