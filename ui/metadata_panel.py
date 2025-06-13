"""
Panel de gestión de metadatos faltantes para DjAlfin
Interfaz para buscar y completar metadatos usando múltiples APIs
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, Dict, Any
import os

from core.metadata_enricher import MetadataEnricher, MetadataSource


# Importar tema de la aplicación principal
class MixedInKeyTheme:
    """Constantes de colores inspiradas en Mixed In Key Pro."""
    BG_MAIN = "#1a1a1a"          # Fondo principal negro profundo
    BG_PANEL = "#2a2a2a"         # Paneles secundarios gris oscuro
    BG_WIDGET = "#333333"        # Widgets gris medio
    FG_PRIMARY = "#ffffff"       # Texto principal blanco
    FG_SECONDARY = "#cccccc"     # Texto secundario gris claro
    ACCENT_BLUE = "#00d4ff"      # Azul brillante para acentos
    ACCENT_GREEN = "#00ff88"     # Verde para elementos activos
    SELECT_BG = "#0066cc"        # Selección azul oscuro


class MetadataEnrichmentDialog(tk.Toplevel):
    """Diálogo para enriquecimiento de metadatos."""
    
    def __init__(self, parent, db_path: str = None):
        super().__init__(parent)
        # Si no se proporciona db_path, usar None para que MetadataEnricher use la ruta correcta
        self.db_path = db_path
        self.enricher = MetadataEnricher(db_path)
        self.enrichment_thread: Optional[threading.Thread] = None
        self.is_enriching = False
        
        self.setup_dialog()
        self.load_statistics()
    
    def setup_dialog(self):
        """Configura la interfaz del diálogo."""
        self.title("🔍 Búsqueda de Metadatos Faltantes")
        self.geometry("900x800")  # Aumentar tamaño para asegurar visibilidad
        self.resizable(True, True)
        
        # Configurar colores del tema
        self.configure(bg=MixedInKeyTheme.BG_MAIN)
        
        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="🔍 Búsqueda de Metadatos Faltantes",
            style="Title.TLabel"
        )
        title_label.pack(pady=(0, 20))
        
        # Frame de estadísticas
        self.create_statistics_frame(main_frame)
        
        # Frame de configuración
        self.create_config_frame(main_frame)
        
        # Frame de progreso
        self.create_progress_frame(main_frame)
        
        # Frame de botones
        self.create_buttons_frame(main_frame)
        
        # Frame de resultados
        self.create_results_frame(main_frame)
    
    def create_statistics_frame(self, parent):
        """Crea el frame de estadísticas."""
        stats_frame = ttk.LabelFrame(parent, text="📊 Estado Actual de Metadatos", padding=15)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Labels de estadísticas usando pack en lugar de grid
        self.stats_labels = {}
        
        # Fila 1 - Estadísticas principales
        row1_frame = ttk.Frame(stats_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row1_frame, text="Total de pistas:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.stats_labels['total'] = ttk.Label(row1_frame, text="0", font=("Segoe UI", 10))
        self.stats_labels['total'].pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row1_frame, text="Completas:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.stats_labels['complete'] = ttk.Label(row1_frame, text="0", font=("Segoe UI", 10))
        self.stats_labels['complete'].pack(side=tk.LEFT, padx=(5, 0))
        
        # Fila 2 - Estadísticas secundarias
        row2_frame = ttk.Frame(stats_frame)
        row2_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row2_frame, text="Incompletas:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.stats_labels['incomplete'] = ttk.Label(row2_frame, text="0", font=("Segoe UI", 10))
        self.stats_labels['incomplete'].pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row2_frame, text="% Completado:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.stats_labels['percentage'] = ttk.Label(row2_frame, text="0%", font=("Segoe UI", 10))
        self.stats_labels['percentage'].pack(side=tk.LEFT, padx=(5, 0))
        
        # Separador
        separator = ttk.Separator(stats_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)
        
        # Fila 3 - Campos específicos faltantes
        row3_frame = ttk.Frame(stats_frame)
        row3_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row3_frame, text="Sin género:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.stats_labels['missing_genre'] = ttk.Label(row3_frame, text="0", font=("Segoe UI", 9))
        self.stats_labels['missing_genre'].pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row3_frame, text="Sin BPM:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.stats_labels['missing_bpm'] = ttk.Label(row3_frame, text="0", font=("Segoe UI", 9))
        self.stats_labels['missing_bpm'].pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(row3_frame, text="Sin key:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.stats_labels['missing_key'] = ttk.Label(row3_frame, text="0", font=("Segoe UI", 9))
        self.stats_labels['missing_key'].pack(side=tk.LEFT, padx=(5, 0))
    
    def create_config_frame(self, parent):
        """Crea el frame de configuración."""
        self.config_frame = ttk.LabelFrame(parent, text="⚙️ Configuración de Búsqueda", padding=15)
        self.config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # APIs disponibles
        apis_title = ttk.Label(self.config_frame, text="APIs disponibles:", font=("Segoe UI", 10, "bold"))
        apis_title.pack(anchor=tk.W, pady=(0, 5))
        
        apis_frame = ttk.Frame(self.config_frame)
        apis_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.api_vars = {}
        
        # Spotify
        self.api_vars['spotify'] = tk.BooleanVar(value=True)
        spotify_cb = ttk.Checkbutton(
            apis_frame,
            text="🎵 Spotify (Géneros, popularidad)",
            variable=self.api_vars['spotify']
        )
        spotify_cb.pack(anchor=tk.W, pady=2)
        
        # MusicBrainz
        self.api_vars['musicbrainz'] = tk.BooleanVar(value=True)
        mb_cb = ttk.Checkbutton(
            apis_frame,
            text="🎼 MusicBrainz (Metadatos detallados)",
            variable=self.api_vars['musicbrainz']
        )
        mb_cb.pack(anchor=tk.W, pady=2)
        
        # Last.fm (deshabilitado por ahora)
        self.api_vars['lastfm'] = tk.BooleanVar(value=False)
        lastfm_cb = ttk.Checkbutton(
            apis_frame,
            text="📻 Last.fm (Próximamente)",
            variable=self.api_vars['lastfm'],
            state=tk.DISABLED
        )
        lastfm_cb.pack(anchor=tk.W, pady=2)
        
        # Discogs (deshabilitado por ahora)
        self.api_vars['discogs'] = tk.BooleanVar(value=False)
        discogs_cb = ttk.Checkbutton(
            apis_frame,
            text="💿 Discogs (Próximamente)",
            variable=self.api_vars['discogs'],
            state=tk.DISABLED
        )
        discogs_cb.pack(anchor=tk.W, pady=2)

        # Separador
        separator = ttk.Separator(self.config_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)

        # Opciones de enriquecimiento
        options_title = ttk.Label(self.config_frame, text="Opciones de Análisis:", font=("Segoe UI", 10, "bold"))
        options_title.pack(anchor=tk.W, pady=(0, 5))
        
        options_frame = ttk.Frame(self.config_frame)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        self.enrich_all_var = tk.BooleanVar(value=False)
        enrich_all_check = ttk.Checkbutton(
            options_frame,
            text="🔍 Análisis Profundo (mejorar todas las pistas, más lento)",
            variable=self.enrich_all_var
        )
        enrich_all_check.pack(anchor=tk.W, pady=2)

        self.write_to_file_var = tk.BooleanVar(value=True)
        write_to_file_check = ttk.Checkbutton(
            options_frame,
            text="💾 Guardar cambios directamente en los archivos de audio",
            variable=self.write_to_file_var
        )
        write_to_file_check.pack(anchor=tk.W, pady=2)
        
        # Frame de estado de APIs
        self.api_status_frame = ttk.Frame(self.config_frame)
        self.api_status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.api_status_label = ttk.Label(
            self.api_status_frame,
            text="🔄 Verificando estado de APIs...",
            font=("Segoe UI", 9),
            foreground="#888888"
        )
        self.api_status_label.pack(anchor=tk.W)
        
        # Verificar estado de APIs al crear el frame
        self.after(100, self.check_api_status)
    
    def create_progress_frame(self, parent):
        """Crea el frame de progreso."""
        self.progress_frame = ttk.LabelFrame(parent, text="📈 Progreso", padding=15)
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Label de estado
        self.status_label = ttk.Label(
            self.progress_frame,
            text="Listo para comenzar",
            font=("Segoe UI", 9)
        )
        self.status_label.pack(anchor=tk.W)
        
        # Label de progreso detallado
        self.progress_detail_label = ttk.Label(
            self.progress_frame,
            text="",
            font=("Segoe UI", 8)
        )
        self.progress_detail_label.pack(anchor=tk.W)
    
    def create_buttons_frame(self, parent):
        """Crea el frame de botones."""
        # Frame contenedor con borde visible para depuración
        buttons_container = ttk.LabelFrame(parent, text="🎯 Acciones", padding=15)
        buttons_container.pack(fill=tk.X, pady=(10, 15))
        
        buttons_frame = ttk.Frame(buttons_container)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        # Botón de vista previa
        self.preview_button = ttk.Button(
            buttons_frame,
            text="👁️ Vista Previa",
            command=self.show_preview,
            style="TButton"
        )
        self.preview_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        # Botón de inicio directo (sin vista previa) - MÁS PROMINENTE
        self.start_button = ttk.Button(
            buttons_frame,
            text="🚀 INICIAR ENRIQUECIMIENTO",
            command=self.start_enrichment_direct,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))

        # Botón de detener
        self.stop_button = ttk.Button(
            buttons_frame,
            text="⏹ Detener",
            command=self.stop_enrichment,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        
        # Añadir información adicional
        info_label = ttk.Label(
            buttons_container,
            text="💡 Usa 'Vista Previa' para ver qué se procesará antes de iniciar",
            font=("Segoe UI", 8),
            foreground="#888888"
        )
        info_label.pack(pady=(5, 0))
    
    def create_results_frame(self, parent):
        """Crea el frame de resultados."""
        results_frame = ttk.LabelFrame(parent, text="📋 Resultados", padding=15)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("status", "track", "message")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        self.results_tree.heading("status", text="Estado")
        self.results_tree.heading("track", text="Pista")
        self.results_tree.heading("message", text="Resultado")

        self.results_tree.column("status", width=60, anchor="center")
        self.results_tree.column("track", width=250)
        
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        self.final_results = []
    
    def load_statistics(self):
        """Carga las estadísticas actuales."""
        try:
            stats = self.enricher.get_enrichment_statistics()
            
            self.stats_labels['total'].config(text=str(stats['total_tracks']))
            self.stats_labels['complete'].config(text=str(stats['complete_tracks']))
            self.stats_labels['incomplete'].config(text=str(stats['incomplete_tracks']))
            self.stats_labels['percentage'].config(text=f"{stats['completion_percentage']:.1f}%")
            self.stats_labels['missing_genre'].config(text=str(stats['missing_genre']))
            self.stats_labels['missing_bpm'].config(text=str(stats['missing_bpm']))
            self.stats_labels['missing_key'].config(text=str(stats['missing_key']))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar estadísticas: {e}")
    
    def start_enrichment_direct(self):
        """Inicia el enriquecimiento directamente después de validar."""
        if not self.validate_before_start():
            return
        self.start_enrichment()
    
    def start_enrichment(self):
        """Inicia el proceso de enriquecimiento."""
        if self.is_enriching:
            return
        
        self.is_enriching = True
        self.start_button.config(state=tk.DISABLED, text="⏳ PROCESANDO...")
        self.preview_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.results_tree.delete(*self.results_tree.get_children())
        self.final_results = []
        
        enrich_all = self.enrich_all_var.get()
        write_to_file = self.write_to_file_var.get()

        self.enrichment_thread = threading.Thread(
            target=self._enrich_in_background,
            args=(enrich_all, write_to_file),
            daemon=True
        )
        self.enrichment_thread.start()
    
    def stop_enrichment(self):
        """Detiene el proceso de enriquecimiento."""
        if not self.is_enriching:
            return
        self.is_enriching = False
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL, text="🚀 INICIAR ENRIQUECIMIENTO")
        self.preview_button.config(state=tk.NORMAL)
        self.status_label.config(text="Detenido por el usuario.")
    
    def _enrich_in_background(self, enrich_all: bool, write_to_file: bool):
        """Lógica de enriquecimiento que se ejecuta en segundo plano."""
        try:
            # La función de enriquecimiento ahora llamará a update_progress
            self.enricher.enrich_library(
                enrich_all=enrich_all,
                write_to_file=write_to_file,
                update_callback=lambda p, m, r: self.after(0, self.update_progress, p, m, r)
            )
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: messagebox.showerror("Error Crítico", f"Ha ocurrido un error irrecuperable: {msg}"))
        finally:
            self.is_enriching = False
            self.after(0, self._enrichment_finished)
            
    def _enrichment_finished(self):
        """Se llama cuando el proceso de enriquecimiento ha finalizado."""
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL, text="🚀 INICIAR ENRIQUECIMIENTO")
        self.preview_button.config(state=tk.NORMAL)
        self.status_label.config(text="¡Proceso completado!")
        self.progress_bar['value'] = 100
        
        # Mostrar notificación de finalización
        if hasattr(self, 'final_results') and self.final_results:
            successful = sum(1 for _, success, _ in self.final_results if success)
            total = len(self.final_results)
            messagebox.showinfo(
                "Proceso Completado",
                f"Enriquecimiento finalizado:\n\n"
                f"✅ Exitosos: {successful}\n"
                f"❌ Fallidos: {total - successful}\n"
                f"📊 Total procesado: {total}"
            )
        
        # Cargar estadísticas finales
        self.load_statistics()

    def update_progress(self, progress: float, message: str, results: list):
        """Actualiza la UI con el progreso desde el hilo de trabajo."""
        if not self.is_enriching or not hasattr(self, 'progress_bar'):
            return
            
        self.progress_bar['value'] = progress
        self.status_label.config(text=message)
        
        # Calcular estadísticas en tiempo real
        if results:
            successful = sum(1 for _, success, _ in results if success)
            failed = len(results) - successful
            
            # Actualizar label de progreso detallado
            detail_text = f"✅ Exitosos: {successful} | ❌ Fallidos: {failed} | 📊 Total: {len(results)}"
            if progress > 0:
                # Calcular velocidad aproximada
                tracks_per_minute = len(results) / (progress / 100) * 60 if progress > 0 else 0
                if tracks_per_minute > 0:
                    detail_text += f" | ⚡ Velocidad: {tracks_per_minute:.1f} pistas/min"
            
            self.progress_detail_label.config(text=detail_text)
        
        # Actualizar el árbol de resultados en tiempo real
        self.results_tree.delete(*self.results_tree.get_children())
        
        # Mostrar solo los últimos 50 resultados para mejor rendimiento
        display_results = results[-50:] if len(results) > 50 else results
        
        for file_path, success, msg in display_results:
            status_icon = "✅" if success else "❌"
            # Obtener solo el nombre del archivo para mejor legibilidad
            filename = os.path.basename(file_path)
            # Limitar la longitud del mensaje para que no desborde la columna
            truncated_msg = (msg[:60] + '...') if len(msg) > 60 else msg
            
            # Usar colores diferentes según el resultado
            tags = ("success",) if success else ("error",)
            item = self.results_tree.insert("", "end", values=(status_icon, filename, truncated_msg), tags=tags)
        
        # Configurar colores para los tags usando el tema
        if not hasattr(self, '_tags_configured'):
            self.results_tree.tag_configure("success", foreground=MixedInKeyTheme.ACCENT_GREEN)
            self.results_tree.tag_configure("error", foreground="#ff6666")
            self._tags_configured = True
        
        # Auto-scroll hacia el final
        if self.results_tree.get_children():
            self.results_tree.yview_moveto(1)
        
        # Guardar resultados para el resumen final
        self.final_results = results

    def on_close(self):
        """Maneja el cierre de la ventana."""
        self.destroy()

    def check_api_status(self):
        """Verifica el estado de las APIs configuradas."""
        try:
            # Verificar configuración de APIs
            spotify_configured = self.enricher.clients.get(MetadataSource.SPOTIFY) is not None
            musicbrainz_configured = self.enricher.clients.get(MetadataSource.MUSICBRAINZ) is not None
            
            status_parts = []
            if spotify_configured:
                status_parts.append("✅ Spotify")
            else:
                status_parts.append("❌ Spotify")
                
            if musicbrainz_configured:
                status_parts.append("✅ MusicBrainz")
            else:
                status_parts.append("❌ MusicBrainz")
            
            status_text = " | ".join(status_parts)
            
            if spotify_configured or musicbrainz_configured:
                self.api_status_label.config(
                    text=f"Estado APIs: {status_text}",
                    foreground=MixedInKeyTheme.ACCENT_GREEN
                )
            else:
                self.api_status_label.config(
                    text=f"⚠️ APIs no configuradas: {status_text}",
                    foreground="#ffaa00"
                )
                
        except Exception as e:
            self.api_status_label.config(
                text=f"❌ Error verificando APIs: {str(e)[:50]}...",
                foreground="#ff4444"
            )
    
    def show_preview(self):
        """Muestra una vista previa de lo que se va a procesar."""
        try:
            enrich_all = self.enrich_all_var.get()
            
            if enrich_all:
                tracks_to_process = self.enricher.get_all_tracks()
                preview_title = "Vista Previa - Análisis Profundo"
                preview_msg = f"Se analizarán TODAS las {len(tracks_to_process)} pistas de tu biblioteca.\n"
                preview_msg += "Esto puede tomar mucho tiempo pero mejorará todos los metadatos."
            else:
                tracks_to_process = self.enricher.get_tracks_with_missing_metadata()
                preview_title = "Vista Previa - Análisis Rápido"
                preview_msg = f"Se analizarán {len(tracks_to_process)} pistas con metadatos faltantes.\n"
                preview_msg += "Solo se procesarán las pistas que necesiten mejoras."
            
            if not tracks_to_process:
                messagebox.showinfo(
                    "Sin pistas para procesar",
                    "No hay pistas que necesiten enriquecimiento en este momento."
                )
                return
            
            # Calcular estimación de tiempo
            estimated_minutes = len(tracks_to_process) * 0.5  # ~30 segundos por pista
            time_str = f"{estimated_minutes:.0f} minutos" if estimated_minutes >= 1 else "menos de 1 minuto"
            
            preview_msg += f"\n⏱️ Tiempo estimado: {time_str}"
            preview_msg += f"\n💾 Guardar en archivos: {'Sí' if self.write_to_file_var.get() else 'No'}"
            
            # Mostrar algunas pistas de ejemplo
            preview_msg += "\n\n📋 Ejemplos de pistas a procesar:"
            for i, track in enumerate(tracks_to_process[:5]):
                missing = track.missing_fields() if not enrich_all else ["mejora general"]
                preview_msg += f"\n  • {track.title or 'Sin título'} - {track.artist or 'Sin artista'}"
                if missing:
                    preview_msg += f" (falta: {', '.join(missing[:3])})"
            
            if len(tracks_to_process) > 5:
                preview_msg += f"\n  ... y {len(tracks_to_process) - 5} pistas más"
            
            result = messagebox.askyesno(
                preview_title,
                preview_msg + "\n\n¿Continuar con el proceso?",
                icon="question"
            )
            
            if result:
                self.start_enrichment()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar vista previa: {e}")
    
    def validate_before_start(self) -> bool:
        """Valida la configuración antes de iniciar el proceso."""
        # Verificar que al menos una API esté seleccionada y configurada
        selected_apis = [api for api, var in self.api_vars.items() if var.get()]
        
        if not selected_apis:
            messagebox.showwarning(
                "APIs no seleccionadas",
                "Selecciona al menos una API para la búsqueda."
            )
            return False
        
        # Verificar que las APIs seleccionadas estén configuradas
        configured_apis = []
        if 'spotify' in selected_apis and self.enricher.clients.get(MetadataSource.SPOTIFY):
            configured_apis.append('Spotify')
        if 'musicbrainz' in selected_apis and self.enricher.clients.get(MetadataSource.MUSICBRAINZ):
            configured_apis.append('MusicBrainz')
        
        if not configured_apis:
            messagebox.showerror(
                "APIs no configuradas",
                "Las APIs seleccionadas no están configuradas correctamente.\n\n"
                "Verifica tu archivo config/api_keys.json y reinicia la aplicación."
            )
            return False
        
        return True


class MetadataPanel(ttk.Frame):
    """Panel integrado para gestión de metadatos en la aplicación principal."""
    
    def __init__(self, parent, db_path: str = None):
        super().__init__(parent)
        # Si no se proporciona db_path, usar None para que MetadataEnricher use la ruta correcta
        self.db_path = db_path
        self.enricher = MetadataEnricher(db_path)
        
        self.setup_panel()
        self.load_quick_stats()
        
        # Auto-actualizar estadísticas cada 30 segundos
        self.after(30000, self.auto_refresh_stats)
    
    def setup_panel(self):
        """Configura el panel."""
        # Título con estilo consistente
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
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
        """Crea la sección de estadísticas."""
        stats_frame = ttk.LabelFrame(self, text="📊 Estado Actual", padding=10, style="Card.TFrame")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Estadísticas principales
        self.quick_stats_label = ttk.Label(
            stats_frame,
            text="Cargando estadísticas...",
            justify=tk.LEFT
        )
        self.quick_stats_label.pack(anchor=tk.W)
        
        # Barra de progreso visual
        progress_frame = ttk.Frame(stats_frame)
        progress_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(progress_frame, text="Completitud:", font=("Segoe UI", 8)).pack(anchor=tk.W)
        
        self.completion_progress = ttk.Progressbar(
            progress_frame,
            length=150,
            mode='determinate'
        )
        self.completion_progress.pack(fill=tk.X, pady=(2, 0))
        
        self.completion_label = ttk.Label(
            progress_frame,
            text="0%",
            font=("Segoe UI", 8)
        )
        self.completion_label.pack(anchor=tk.E)
    
    def create_api_status_section(self):
        """Crea la sección de estado de APIs."""
        api_frame = ttk.LabelFrame(self, text="🔗 Estado APIs", padding=8, style="Card.TFrame")
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.api_status_label = ttk.Label(
            api_frame,
            text="🔄 Verificando...",
            font=("Segoe UI", 8),
            justify=tk.LEFT
        )
        self.api_status_label.pack(anchor=tk.W)
        
        # Verificar estado después de un momento
        self.after(500, self.check_api_status_quick)
    
    def create_actions_section(self):
        """Crea la sección de acciones principales."""
        actions_frame = ttk.LabelFrame(self, text="🚀 Acciones", padding=8, style="Card.TFrame")
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botón principal mejorado
        self.main_action_btn = ttk.Button(
            actions_frame,
            text="🔍 Enriquecer Metadatos",
            command=self.open_enrichment_dialog,
            style="Accent.TButton"
        )
        self.main_action_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Botón de análisis rápido
        self.quick_analysis_btn = ttk.Button(
            actions_frame,
            text="⚡ Análisis Rápido",
            command=self.quick_enrichment
        )
        self.quick_analysis_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Botón de vista previa
        self.preview_btn = ttk.Button(
            actions_frame,
            text="👁️ Vista Previa",
            command=self.show_preview_from_panel
        )
        self.preview_btn.pack(fill=tk.X)
    
    def create_quick_actions_section(self):
        """Crea la sección de acciones rápidas."""
        quick_frame = ttk.LabelFrame(self, text="⚡ Acciones Rápidas", padding=8, style="Card.TFrame")
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botón de actualizar estadísticas
        refresh_btn = ttk.Button(
            quick_frame,
            text="🔄 Actualizar Stats",
            command=self.load_quick_stats
        )
        refresh_btn.pack(fill=tk.X, pady=(0, 3))
        
        # Botón para validar metadatos
        validate_btn = ttk.Button(
            quick_frame,
            text="✅ Validar Datos",
            command=self.validate_metadata
        )
        validate_btn.pack(fill=tk.X, pady=(0, 3))
        
        # Botón para exportar reporte
        export_btn = ttk.Button(
            quick_frame,
            text="📄 Exportar Reporte",
            command=self.export_metadata_report
        )
        export_btn.pack(fill=tk.X)
    
    def check_api_status_quick(self):
        """Verifica rápidamente el estado de las APIs."""
        try:
            spotify_ok = self.enricher.clients.get(MetadataSource.SPOTIFY) is not None
            musicbrainz_ok = self.enricher.clients.get(MetadataSource.MUSICBRAINZ) is not None
            
            if spotify_ok and musicbrainz_ok:
                status_text = "✅ Todas las APIs configuradas"
                color = MixedInKeyTheme.ACCENT_GREEN
            elif spotify_ok or musicbrainz_ok:
                status_text = "⚠️ Algunas APIs configuradas"
                color = "#ffaa00"  # Amarillo para advertencia
            else:
                status_text = "❌ APIs no configuradas"
                color = "#ff4444"  # Rojo para error
            
            self.api_status_label.config(text=status_text, foreground=color)
            
        except Exception as e:
            self.api_status_label.config(
                text="❌ Error verificando APIs",
                foreground="#ff4444"
            )
    
    def load_quick_stats(self):
        """Carga estadísticas rápidas mejoradas."""
        try:
            stats = self.enricher.get_enrichment_statistics()
            
            # Texto de estadísticas más detallado
            stats_text = f"""📀 Total: {stats['total_tracks']} pistas
✅ Completas: {stats['complete_tracks']}
❌ Incompletas: {stats['incomplete_tracks']}
🎭 Sin género: {stats['missing_genre']}
🎵 Sin BPM: {stats['missing_bpm']}
🎹 Sin key: {stats['missing_key']}"""
            
            self.quick_stats_label.config(text=stats_text)
            
            # Actualizar barra de progreso
            completion_pct = stats['completion_percentage']
            self.completion_progress['value'] = completion_pct
            self.completion_label.config(text=f"{completion_pct:.1f}%")
            
            # Cambiar color de la barra según el porcentaje usando colores del tema
            if completion_pct >= 80:
                style_name = "Green.Horizontal.TProgressbar"
                color = MixedInKeyTheme.ACCENT_GREEN
            elif completion_pct >= 50:
                style_name = "Yellow.Horizontal.TProgressbar"
                color = "#ffaa00"
            else:
                style_name = "Red.Horizontal.TProgressbar"
                color = "#ff4444"
            
            # Configurar estilos si no existen
            style = ttk.Style()
            if not hasattr(self, '_progress_styles_configured'):
                style.configure("Green.Horizontal.TProgressbar", background=MixedInKeyTheme.ACCENT_GREEN)
                style.configure("Yellow.Horizontal.TProgressbar", background="#ffaa00")
                style.configure("Red.Horizontal.TProgressbar", background="#ff4444")
                self._progress_styles_configured = True
            
            self.completion_progress.configure(style=style_name)
            
        except Exception as e:
            self.quick_stats_label.config(text=f"❌ Error: {str(e)[:30]}...")
            self.completion_progress['value'] = 0
            self.completion_label.config(text="0%")
    
    def auto_refresh_stats(self):
        """Auto-actualiza las estadísticas cada 30 segundos."""
        self.load_quick_stats()
        self.after(30000, self.auto_refresh_stats)  # Programar siguiente actualización
    
    def quick_enrichment(self):
        """Inicia un enriquecimiento rápido con configuración predeterminada."""
        try:
            # Verificar que hay pistas para procesar
            tracks_missing = self.enricher.get_tracks_with_missing_metadata()
            
            if not tracks_missing:
                messagebox.showinfo(
                    "Sin pistas para procesar",
                    "¡Excelente! No hay pistas con metadatos faltantes."
                )
                return
            
            # Confirmar acción
            result = messagebox.askyesno(
                "Análisis Rápido",
                f"Se procesarán {len(tracks_missing)} pistas con metadatos faltantes.\n\n"
                "Configuración:\n"
                "• Solo pistas incompletas\n"
                "• Guardar en base de datos\n"
                "• No modificar archivos\n\n"
                "¿Continuar?",
                icon="question"
            )
            
            if result:
                # Abrir diálogo con configuración predeterminada
                dialog = MetadataEnrichmentDialog(self.winfo_toplevel())
                dialog.transient(self.winfo_toplevel())
                
                # Configurar opciones predeterminadas
                dialog.enrich_all_var.set(False)  # Solo faltantes
                dialog.write_to_file_var.set(False)  # No escribir archivos
                
                # Iniciar automáticamente
                dialog.after(100, dialog.start_enrichment)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error en análisis rápido: {e}")
    
    def show_preview_from_panel(self):
        """Muestra vista previa desde el panel lateral."""
        try:
            tracks_missing = self.enricher.get_tracks_with_missing_metadata()
            
            if not tracks_missing:
                messagebox.showinfo(
                    "Sin pistas para procesar",
                    "No hay pistas con metadatos faltantes en este momento."
                )
                return
            
            # Mostrar información detallada
            preview_msg = f"📊 Análisis de tu biblioteca:\n\n"
            preview_msg += f"🔍 Pistas a procesar: {len(tracks_missing)}\n"
            
            # Analizar tipos de campos faltantes
            missing_genres = sum(1 for t in tracks_missing if not t.genre)
            missing_bpm = sum(1 for t in tracks_missing if not t.bpm)
            missing_keys = sum(1 for t in tracks_missing if not t.key)
            
            preview_msg += f"🎭 Sin género: {missing_genres}\n"
            preview_msg += f"🎵 Sin BPM: {missing_bpm}\n"
            preview_msg += f"🎹 Sin key: {missing_keys}\n\n"
            
            # Estimación de tiempo
            estimated_minutes = len(tracks_missing) * 0.5
            time_str = f"{estimated_minutes:.0f} minutos" if estimated_minutes >= 1 else "menos de 1 minuto"
            preview_msg += f"⏱️ Tiempo estimado: {time_str}\n\n"
            
            preview_msg += "¿Abrir el panel completo de enriquecimiento?"
            
            result = messagebox.askyesno(
                "Vista Previa de Metadatos",
                preview_msg,
                icon="question"
            )
            
            if result:
                self.open_enrichment_dialog()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error en vista previa: {e}")
    
    def validate_metadata(self):
        """Valida la integridad de los metadatos."""
        try:
            stats = self.enricher.get_enrichment_statistics()
            
            # Crear reporte de validación
            report = f"📋 Reporte de Validación de Metadatos\n\n"
            report += f"📊 Estadísticas Generales:\n"
            report += f"• Total de pistas: {stats['total_tracks']}\n"
            report += f"• Pistas completas: {stats['complete_tracks']}\n"
            report += f"• Pistas incompletas: {stats['incomplete_tracks']}\n"
            report += f"• Porcentaje de completitud: {stats['completion_percentage']:.1f}%\n\n"
            
            report += f"🔍 Campos Faltantes:\n"
            report += f"• Sin género: {stats['missing_genre']}\n"
            report += f"• Sin BPM: {stats['missing_bpm']}\n"
            report += f"• Sin key: {stats['missing_key']}\n\n"
            
            # Evaluación de calidad
            if stats['completion_percentage'] >= 90:
                quality = "🟢 Excelente"
            elif stats['completion_percentage'] >= 70:
                quality = "🟡 Buena"
            elif stats['completion_percentage'] >= 50:
                quality = "🟠 Regular"
            else:
                quality = "🔴 Necesita mejoras"
            
            report += f"📈 Calidad de metadatos: {quality}"
            
            messagebox.showinfo("Validación de Metadatos", report)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en validación: {e}")
    
    def export_metadata_report(self):
        """Exporta un reporte detallado de metadatos."""
        try:
            from tkinter import filedialog
            import json
            from datetime import datetime
            
            # Obtener estadísticas
            stats = self.enricher.get_enrichment_statistics()
            tracks_missing = self.enricher.get_tracks_with_missing_metadata()
            
            # Crear reporte completo
            report = {
                "timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "missing_tracks_count": len(tracks_missing),
                "missing_tracks": [
                    {
                        "file_path": track.file_path,
                        "title": track.title,
                        "artist": track.artist,
                        "missing_fields": track.missing_fields()
                    }
                    for track in tracks_missing[:100]  # Limitar a 100 para no hacer el archivo muy grande
                ]
            }
            
            # Pedir ubicación de guardado
            file_path = filedialog.asksaveasfilename(
                title="Guardar Reporte de Metadatos",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo(
                    "Reporte Exportado",
                    f"Reporte guardado exitosamente en:\n{file_path}"
                )
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar reporte: {e}")
    
    def open_enrichment_dialog(self):
        """Abre el diálogo de enriquecimiento."""
        try:
            dialog = MetadataEnrichmentDialog(self.winfo_toplevel())
            dialog.transient(self.winfo_toplevel())
            dialog.grab_set()
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir diálogo: {e}")