# ui/components/metadata_sliding_panel.py

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QProgressBar, QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap

from .sliding_panel import SlidingPanel

try:
    import os
    os.environ['QT_API'] = 'pyside6'
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False

class MetadataSlidingPanel(SlidingPanel):
    """
    Panel deslizante para enriquecimiento de metadatos que se muestra desde el borde derecho.
    """
    
    # Señales específicas del panel de metadatos
    enrichmentRequested = Signal(str)  # source (individual)
    multiSourceEnrichmentRequested = Signal(dict)  # track_info (multi-fuente)
    metadataUpdated = Signal(dict)  # track_data
    saveRequested = Signal(dict)  # metadata
    bpmAnalysisRequested = Signal(str)  # file_path
    
    def __init__(self, parent=None):
        # Inicializar panel base (lado derecho, 350px de ancho, sin auto-hide)
        super().__init__(parent=parent, side='right', width=350, auto_hide_delay=0)
        
        self.current_track = None
        self.enrichment_sources = ['discogs', 'musicbrainz', 'lastfm', 'spotify']
        self.enrichment_status = {}
        
        self.setup_ui()
        
        # Forzar aplicación de estilos CSS
        self.setProperty("class", "sliding_panel")
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Aplicar estilos inline como fallback
        self.apply_field_styles()
        
    def setup_ui(self):
        """Configura la interfaz del panel de metadatos."""
        # Scroll area para manejar contenido largo
        scroll_area = QScrollArea(self)
        scroll_widget = QWidget()
        main_layout = QVBoxLayout(scroll_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # --- Header del Panel ---
        header_layout = QHBoxLayout()
        
        # Título
        title_label = QLabel("🎛️ METADATA")
        title_label.setProperty("class", "sliding_panel_title")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        
        # Botón de guardar
        self.save_btn = QPushButton()
        if HAS_QTAWESOME:
            self.save_btn.setIcon(qta.icon("fa5s.save", color="white"))
        else:
            self.save_btn.setText("💾")
        self.save_btn.setProperty("class", "sliding_panel_button")
        self.save_btn.setFixedSize(30, 30)
        self.save_btn.setToolTip("Guardar Cambios")
        self.save_btn.clicked.connect(self.save_metadata)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.save_btn)
        
        # --- Ensamblar Layout ---
        main_layout.addLayout(header_layout)
        
        # --- Información Básica ---
        main_layout.addWidget(self._create_separator())
        basic_info_label = QLabel("📝 INFORMACIÓN BÁSICA")
        basic_info_label.setProperty("class", "sliding_panel_section")
        main_layout.addWidget(basic_info_label)
        self.setup_basic_info_section(main_layout)
        
        # --- Información Técnica ---
        main_layout.addWidget(self._create_separator())
        tech_info_label = QLabel("⚙️ INFORMACIÓN TÉCNICA")
        tech_info_label.setProperty("class", "sliding_panel_section")
        main_layout.addWidget(tech_info_label)
        self.setup_technical_section(main_layout)
        
        # --- Enriquecimiento ---
        main_layout.addWidget(self._create_separator())
        enrichment_label = QLabel("🌐 ENRIQUECIMIENTO")
        enrichment_label.setProperty("class", "sliding_panel_section")
        main_layout.addWidget(enrichment_label)
        self.setup_enrichment_section(main_layout)
        
        main_layout.addStretch()
        
        # Configurar scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setProperty("class", "sliding_panel_scroll")
        
        # Layout principal del panel
        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(scroll_area)
        
    def setup_basic_info_section(self, main_layout):
        """Configura la sección de información básica."""
        # Grid para los campos básicos
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        
        # Título
        title_label = QLabel("Título:")
        title_label.setProperty("class", "sliding_panel_field_label")
        self.title_edit = QLineEdit()
        self.title_edit.setProperty("class", "sliding_panel_field")
        self.title_edit.setPlaceholderText("Nombre del track...")
        
        # Artista
        artist_label = QLabel("Artista:")
        artist_label.setProperty("class", "sliding_panel_field_label")
        self.artist_edit = QLineEdit()
        self.artist_edit.setProperty("class", "sliding_panel_field")
        self.artist_edit.setPlaceholderText("Nombre del artista...")
        
        # Álbum
        album_label = QLabel("Álbum:")
        album_label.setProperty("class", "sliding_panel_field_label")
        self.album_edit = QLineEdit()
        self.album_edit.setProperty("class", "sliding_panel_field")
        self.album_edit.setPlaceholderText("Nombre del álbum...")
        
        # Año
        year_label = QLabel("Año:")
        year_label.setProperty("class", "sliding_panel_field_label")
        self.year_edit = QLineEdit()
        self.year_edit.setProperty("class", "sliding_panel_field")
        self.year_edit.setPlaceholderText("2024")
        self.year_edit.setMaxLength(4)
        
        # Género
        genre_label = QLabel("Género:")
        genre_label.setProperty("class", "sliding_panel_field_label")
        self.genre_edit = QLineEdit()
        self.genre_edit.setProperty("class", "sliding_panel_field")
        self.genre_edit.setPlaceholderText("Art Pop; Electronic...")
        self.genre_edit.setToolTip("Géneros musicales principales (máximo 4). Los más descriptivos aparecen primero.")
        
        # Comentarios
        comment_label = QLabel("Comentarios:")
        comment_label.setProperty("class", "sliding_panel_field_label")
        self.comment_edit = QTextEdit()
        self.comment_edit.setProperty("class", "sliding_panel_field")
        self.comment_edit.setMaximumHeight(60)
        self.comment_edit.setPlaceholderText("Notas sobre el track...")
        
        # Agregar al grid
        grid_layout.addWidget(title_label, 0, 0)
        grid_layout.addWidget(self.title_edit, 0, 1)
        grid_layout.addWidget(artist_label, 1, 0)
        grid_layout.addWidget(self.artist_edit, 1, 1)
        grid_layout.addWidget(album_label, 2, 0)
        grid_layout.addWidget(self.album_edit, 2, 1)
        grid_layout.addWidget(year_label, 3, 0)
        grid_layout.addWidget(self.year_edit, 3, 1)
        grid_layout.addWidget(genre_label, 4, 0)
        grid_layout.addWidget(self.genre_edit, 4, 1)
        grid_layout.addWidget(comment_label, 5, 0, 1, 2)
        grid_layout.addWidget(self.comment_edit, 6, 0, 1, 2)
        
        main_layout.addLayout(grid_layout)
        
    def setup_technical_section(self, main_layout):
        """Configura la sección de información técnica."""
        # Grid para info técnica
        tech_grid = QGridLayout()
        tech_grid.setSpacing(8)
        
        # BPM
        bpm_label = QLabel("BPM:")
        bpm_label.setProperty("class", "sliding_panel_field_label")
        self.bpm_edit = QLineEdit()
        self.bpm_edit.setProperty("class", "sliding_panel_field")
        self.bpm_edit.setPlaceholderText("128")
        self.bpm_edit.setMaxLength(6)
        
        # Key
        key_label = QLabel("Key:")
        key_label.setProperty("class", "sliding_panel_field_label")
        self.key_edit = QLineEdit()
        self.key_edit.setProperty("class", "sliding_panel_field")
        self.key_edit.setPlaceholderText("8A")
        self.key_edit.setMaxLength(3)
        
        # Energy
        energy_label = QLabel("Energy:")
        energy_label.setProperty("class", "sliding_panel_field_label")
        self.energy_edit = QLineEdit()
        self.energy_edit.setProperty("class", "sliding_panel_field")
        self.energy_edit.setPlaceholderText("7")
        self.energy_edit.setMaxLength(2)
        
        # Botón de análisis BPM
        self.analyze_btn = QPushButton("Analizar BPM")
        self.analyze_btn.setProperty("class", "sliding_panel_list_item")
        self.analyze_btn.clicked.connect(self.analyze_bpm)
        
        tech_grid.addWidget(bpm_label, 0, 0)
        tech_grid.addWidget(self.bpm_edit, 0, 1)
        tech_grid.addWidget(key_label, 1, 0)
        tech_grid.addWidget(self.key_edit, 1, 1)
        tech_grid.addWidget(energy_label, 2, 0)
        tech_grid.addWidget(self.energy_edit, 2, 1)
        tech_grid.addWidget(self.analyze_btn, 3, 0, 1, 2)
        
        main_layout.addLayout(tech_grid)
        
    def setup_enrichment_section(self, main_layout):
        """Configura la sección de enriquecimiento con sistema multi-fuente."""
        enrichment_layout = QVBoxLayout()
        enrichment_layout.setSpacing(12)
        
        # Descripción
        desc_label = QLabel("🤖 Enriquecimiento Inteligente de Metadatos")
        desc_label.setProperty("class", "sliding_panel_description")
        desc_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        desc_label.setFont(font)
        enrichment_layout.addWidget(desc_label)
        
        # Botón principal de enriquecimiento inteligente
        self.smart_enrichment_btn = QPushButton("🧠 Auto-Enriquecimiento Multi-Fuente")
        self.smart_enrichment_btn.setProperty("class", "sliding_panel_button")
        self.smart_enrichment_btn.setMinimumHeight(40)
        self.smart_enrichment_btn.clicked.connect(self.request_smart_enrichment)
        self.smart_enrichment_btn.setToolTip(
            "Usa IA para combinar datos de múltiples fuentes con scoring de confianza"
        )
        enrichment_layout.addWidget(self.smart_enrichment_btn)
        
        # Progress bar para enriquecimiento inteligente
        self.smart_progress = QProgressBar()
        self.smart_progress.setProperty("class", "sliding_panel_progress")
        self.smart_progress.setVisible(False)
        self.smart_progress.setMaximumHeight(25)
        enrichment_layout.addWidget(self.smart_progress)
        
        # Información de resultado
        self.enrichment_info_label = QLabel("")
        self.enrichment_info_label.setProperty("class", "sliding_panel_description")
        self.enrichment_info_label.setWordWrap(True)
        self.enrichment_info_label.setVisible(False)
        enrichment_layout.addWidget(self.enrichment_info_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        enrichment_layout.addWidget(separator)
        
        # Sección de opciones avanzadas (colapsable)
        self.advanced_section = QFrame()
        self.advanced_section.setVisible(False)
        self.setup_advanced_enrichment_section()
        enrichment_layout.addWidget(self.advanced_section)
        
        # Botón para mostrar/ocultar opciones avanzadas
        self.toggle_advanced_btn = QPushButton("⚙️ Opciones Avanzadas")
        self.toggle_advanced_btn.setProperty("class", "sliding_panel_list_item")
        self.toggle_advanced_btn.clicked.connect(self.toggle_advanced_options)
        enrichment_layout.addWidget(self.toggle_advanced_btn)
        
        # Estado del enriquecimiento
        self.enrichment_status_label = QLabel("🎯 Sistema Inteligente Listo")
        self.enrichment_status_label.setProperty("class", "sliding_panel_description")
        self.enrichment_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enrichment_layout.addWidget(self.enrichment_status_label)
        
        main_layout.addLayout(enrichment_layout)
        
    def setup_advanced_enrichment_section(self):
        """Configura la sección avanzada con botones individuales."""
        advanced_layout = QVBoxLayout(self.advanced_section)
        advanced_layout.setSpacing(6)
        
        # Título de sección avanzada
        advanced_title = QLabel("🔧 Fuentes Individuales")
        advanced_title.setProperty("class", "sliding_panel_description")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        advanced_title.setFont(font)
        advanced_layout.addWidget(advanced_title)
        
        # Botones de fuentes individuales
        self.enrichment_buttons = {}
        self.enrichment_progress = {}
        
        for source in self.enrichment_sources:
            # Container para cada fuente
            source_layout = QHBoxLayout()
            
            # Botón de la fuente
            btn = QPushButton(source.title())
            btn.setProperty("class", "sliding_panel_list_item")
            btn.clicked.connect(lambda checked, s=source: self.request_enrichment(s))
            self.enrichment_buttons[source] = btn
            
            # Progress bar
            progress = QProgressBar()
            progress.setProperty("class", "sliding_panel_progress")
            progress.setVisible(False)
            progress.setMaximumHeight(18)
            self.enrichment_progress[source] = progress
            
            source_layout.addWidget(btn, 1)
            source_layout.addWidget(progress, 1)
            
            advanced_layout.addLayout(source_layout)
        
    def apply_field_styles(self):
        """Aplica estilos inline a los campos como fallback."""
        field_style = """
            QLineEdit, QTextEdit {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #FF6B35;
                background-color: #353535;
                color: #FFFFFF;
            }
        """
        
        # Aplicar a todos los campos de entrada
        fields = [
            self.title_edit, self.artist_edit, self.album_edit,
            self.year_edit, self.genre_edit, self.comment_edit,
            self.bpm_edit, self.key_edit, self.energy_edit
        ]
        
        for field in fields:
            field.setStyleSheet(field_style)
            
        # Aplicar estilos a labels también
        label_style = """
            QLabel {
                color: #BDBDBD;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 0px;
            }
        """
        
        # Encontrar y aplicar a labels
        for widget in self.findChildren(self.__class__.mro()[0]):
            if hasattr(widget, 'setStyleSheet') and 'label' in widget.objectName().lower():
                widget.setStyleSheet(label_style)
        
    def _create_separator(self):
        """Crea un separador visual."""
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setProperty("class", "sliding_panel_separator")
        return separator
        
    # --- Métodos de funcionalidad ---
    
    def update_track_info(self, track_data):
        """Actualiza la información del track mostrado."""
        self.current_track = track_data
        
        if not track_data:
            self.clear_fields()
            return
            
        # Llenar campos básicos
        self.title_edit.setText(track_data.get('title', ''))
        self.artist_edit.setText(track_data.get('artist', ''))
        self.album_edit.setText(track_data.get('album', ''))
        self.year_edit.setText(str(track_data.get('year', '')))
        
        # Manejo especial del género con información de fuente
        genre_text = track_data.get('genre', '')
        self.genre_edit.setText(genre_text)
        
        # Crear tooltip informativo para el género
        if genre_text:
            # Determinar posibles fuentes basadas en metadatos disponibles
            sources = []
            if track_data.get('spotify_track_id'):
                sources.append('Spotify')
            if track_data.get('musicbrainz_recording_id'):
                sources.append('MusicBrainz')
            if track_data.get('discogs_release_id'):
                sources.append('Discogs')
            
            if sources:
                source_info = f"Fuentes: {', '.join(sources)}"
            else:
                source_info = "Fuente: Tags locales"
            
            tooltip = f"Géneros normalizados\n{source_info}\nMáximo 4 géneros, priorizando los más descriptivos"
            self.genre_edit.setToolTip(tooltip)
        
        self.comment_edit.setPlainText(track_data.get('comment', ''))
        
        # Llenar campos técnicos
        self.bpm_edit.setText(str(track_data.get('bpm', '')))
        self.key_edit.setText(track_data.get('key', ''))
        self.energy_edit.setText(str(track_data.get('energy', '')))
        
        # Forzar actualización visual
        self.update()
        self.repaint()
        
        # Resetear estado de enriquecimiento
        self.reset_enrichment_status()
        
    def on_panel_shown(self):
        """Se ejecuta cuando el panel se muestra. Obtiene el track actualmente seleccionado."""
        # Buscar el main_window en la jerarquía de padres
        parent = self.parent()
        
        while parent:
            if hasattr(parent, 'track_list_view'):
                current_track = parent.track_list_view.get_current_track()
                if current_track:
                    self.update_track_info(current_track)
                break
            parent = parent.parent()
        
    def clear_fields(self):
        """Limpia todos los campos."""
        self.title_edit.clear()
        self.artist_edit.clear()
        self.album_edit.clear()
        self.year_edit.clear()
        self.genre_edit.clear()
        self.comment_edit.clear()
        self.bpm_edit.clear()
        self.key_edit.clear()
        self.energy_edit.clear()
        
    def get_metadata(self):
        """Retorna los metadatos actuales del formulario."""
        return {
            'title': self.title_edit.text().strip(),
            'artist': self.artist_edit.text().strip(),
            'album': self.album_edit.text().strip(),
            'year': self.year_edit.text().strip(),
            'genre': self.genre_edit.text().strip(),
            'comment': self.comment_edit.toPlainText().strip(),
            'bpm': self.bpm_edit.text().strip(),
            'key': self.key_edit.text().strip(),
            'energy': self.energy_edit.text().strip()
        }
        
    def save_metadata(self):
        """Guarda los metadatos."""
        if not self.current_track:
            return
            
        metadata = self.get_metadata()
        metadata['id'] = self.current_track.get('id')
        metadata['file_path'] = self.current_track.get('file_path')
        
        print(f"💾 Guardando metadatos para: {metadata.get('title', 'Unknown')}")
        self.saveRequested.emit(metadata)
        
    def request_smart_enrichment(self):
        """Solicita enriquecimiento inteligente multi-fuente."""
        if not self.current_track:
            return
            
        print(f"🤖 Iniciando enriquecimiento inteligente para: {self.current_track.get('title', 'Unknown')}")
        
        # Preparar información del track
        track_info = {
            'title': self.current_track.get('title', ''),
            'artist': self.current_track.get('artist', ''),
            'album': self.current_track.get('album', ''),
            'year': self.current_track.get('year', ''),
            'file_path': self.current_track.get('file_path', '')
        }
        
        # Actualizar UI para mostrar progreso
        self.smart_enrichment_btn.setEnabled(False)
        self.smart_enrichment_btn.setText("🔄 Procesando Multi-Fuente...")
        self.smart_progress.setVisible(True)
        self.smart_progress.setRange(0, 0)  # Progreso indeterminado
        self.enrichment_status_label.setText("🧠 Analizando múltiples fuentes...")
        
        # Emitir señal para enriquecimiento multi-fuente
        self.multiSourceEnrichmentRequested.emit(track_info)
        
    def on_smart_enrichment_completed(self, result):
        """Maneja la finalización del enriquecimiento inteligente."""
        try:
            # Restaurar botón
            self.smart_enrichment_btn.setEnabled(True)
            self.smart_enrichment_btn.setText("🧠 Auto-Enriquecimiento Multi-Fuente")
            self.smart_progress.setVisible(False)
            
            if result and result.get('success'):
                # Obtener información del resultado
                final_genres = result.get('final_genres', [])
                confidence_score = result.get('confidence_score', 0.0)
                sources_used = result.get('sources_used', [])
                processing_time = result.get('processing_time', 0.0)
                
                # Actualizar campos si se obtuvieron datos
                if result.get('enriched_data'):
                    enriched_data = result['enriched_data']
                    
                    # Actualizar géneros
                    if final_genres:
                        self.genre_edit.setText('; '.join(final_genres))
                        
                    # Actualizar otros campos si están disponibles
                    for field in ['title', 'artist', 'album', 'year']:
                        if enriched_data.get(field):
                            field_widget = getattr(self, f'{field}_edit', None)
                            if field_widget:
                                field_widget.setText(str(enriched_data[field]))
                
                # Mostrar información de resultado
                info_text = f"✅ Enriquecimiento completado\n"
                info_text += f"📊 Confianza: {confidence_score:.1%}\n"
                info_text += f"🔗 Fuentes: {', '.join(sources_used)}\n"
                info_text += f"⏱️ Tiempo: {processing_time:.2f}s"
                
                if final_genres:
                    info_text += f"\n🎵 Géneros: {'; '.join(final_genres)}"
                
                self.enrichment_info_label.setText(info_text)
                self.enrichment_info_label.setVisible(True)
                self.enrichment_status_label.setText("✅ Enriquecimiento Inteligente Completado")
                
                # Ocultar info después de 10 segundos
                QTimer.singleShot(10000, lambda: self.enrichment_info_label.setVisible(False))
                
                print(f"✅ Enriquecimiento inteligente completado - Confianza: {confidence_score:.1%}")
                
            else:
                error_msg = result.get('error', 'Error desconocido') if result else 'Sin resultado'
                print(f"❌ Error en enriquecimiento inteligente: {error_msg}")
                
                self.enrichment_info_label.setText(f"❌ Error: {error_msg}")
                self.enrichment_info_label.setVisible(True)
                self.enrichment_status_label.setText("❌ Error en Enriquecimiento")
                
                # Ocultar error después de 8 segundos
                QTimer.singleShot(8000, lambda: self.enrichment_info_label.setVisible(False))
                
        except Exception as e:
            print(f"❌ Error procesando resultado de enriquecimiento inteligente: {e}")
            self.smart_enrichment_btn.setEnabled(True)
            self.smart_enrichment_btn.setText("🧠 Auto-Enriquecimiento Multi-Fuente")
            self.smart_progress.setVisible(False)
            self.enrichment_status_label.setText("❌ Error Procesando Resultado")
            
        # Restaurar estado después de 5 segundos
        QTimer.singleShot(5000, lambda: self.enrichment_status_label.setText("🎯 Sistema Inteligente Listo"))
        
    def toggle_advanced_options(self):
        """Muestra/oculta las opciones avanzadas."""
        is_visible = self.advanced_section.isVisible()
        self.advanced_section.setVisible(not is_visible)
        
        if is_visible:
            self.toggle_advanced_btn.setText("⚙️ Opciones Avanzadas")
        else:
            self.toggle_advanced_btn.setText("🔼 Ocultar Opciones Avanzadas")
        
    def request_enrichment(self, source):
        """Solicita enriquecimiento desde una fuente específica."""
        if not self.current_track:
            return
            
        print(f"🌐 Solicitando enriquecimiento desde {source}")
        
        # Mostrar progreso
        self.enrichment_buttons[source].setEnabled(False)
        self.enrichment_progress[source].setVisible(True)
        self.enrichment_progress[source].setRange(0, 0)  # Progreso indeterminado
        
        self.enrichment_status_label.setText(f"Enriqueciendo desde {source.title()}...")
        
        # Emitir señal
        self.enrichmentRequested.emit(source)
        
        # Simular finalización después de 3 segundos (en implementación real sería asíncrono)
        QTimer.singleShot(3000, lambda: self.enrichment_completed(source, True, "Completado"))
        
    def enrichment_completed(self, source, success, message):
        """Maneja la finalización del enriquecimiento."""
        # Restaurar UI
        self.enrichment_buttons[source].setEnabled(True)
        self.enrichment_progress[source].setVisible(False)
        
        if success:
            self.enrichment_status_label.setText(f"✅ {source.title()}: {message}")
        else:
            self.enrichment_status_label.setText(f"❌ {source.title()}: {message}")
            
        # Limpiar mensaje después de 5 segundos
        QTimer.singleShot(5000, lambda: self.enrichment_status_label.setText("Listo para enriquecer"))
        
    def reset_enrichment_status(self):
        """Resetea el estado de enriquecimiento."""
        for source in self.enrichment_sources:
            self.enrichment_buttons[source].setEnabled(True)
            self.enrichment_progress[source].setVisible(False)
            
        self.enrichment_status_label.setText("Listo para enriquecer")
        
    def analyze_bpm(self):
        """Inicia análisis de BPM real usando el AudioService."""
        if not self.current_track:
            return
        
        file_path = self.current_track.get('file_path')
        if not file_path:
            print("❌ No hay ruta de archivo para análisis de BPM")
            return
            
        print(f"🎵 Iniciando análisis real de BPM para: {self.current_track.get('title', 'Unknown')}")
        
        # Actualizar UI para mostrar progreso
        self.analyze_btn.setText("Analizando...")
        self.analyze_btn.setEnabled(False)
        
        # Emitir señal para solicitar análisis real
        self.bpmAnalysisRequested.emit(file_path)
        
    def on_bpm_analysis_completed(self, result):
        """Maneja el resultado del análisis real de BPM."""
        try:
            # Restaurar botón
            self.analyze_btn.setText("Analizar BPM")
            self.analyze_btn.setEnabled(True)
            
            if result and result.get('bpm'):
                bpm = result.get('bpm')
                confidence = result.get('confidence', 0.0)
                
                # Actualizar campo BPM
                self.bpm_edit.setText(f"{bpm:.1f}")
                
                # Mostrar información de confianza
                confidence_percent = confidence * 100
                print(f"✅ BPM detectado: {bpm:.1f} (Confianza: {confidence_percent:.0f}%)")
                
                # Opcional: mostrar confianza en tooltip
                if hasattr(self, 'bpm_edit'):
                    self.bpm_edit.setToolTip(f"BPM: {bpm:.1f}\nConfianza: {confidence_percent:.0f}%")
                
            else:
                error_msg = result.get('error', 'Error desconocido') if result else 'Sin resultado'
                print(f"❌ Error en análisis BPM: {error_msg}")
                
                # Mostrar mensaje de error al usuario
                if hasattr(self, 'bpm_edit'):
                    self.bpm_edit.setToolTip(f"Error: {error_msg}")
                    
        except Exception as e:
            print(f"❌ Error procesando resultado BPM: {e}")
            self.analyze_btn.setText("Analizar BPM")
            self.analyze_btn.setEnabled(True)
        
    # --- Métodos públicos ---
    
    def has_changes(self):
        """Verifica si hay cambios sin guardar."""
        if not self.current_track:
            return False
            
        current_metadata = self.get_metadata()
        
        # Comparar con datos originales
        for key, value in current_metadata.items():
            if str(self.current_track.get(key, '')) != str(value):
                return True
                
        return False