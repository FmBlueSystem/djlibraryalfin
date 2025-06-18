# ui/metadata_panel.py

import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QApplication, QGroupBox, QHBoxLayout, QLabel, QTextEdit, QFrame, QGridLayout,
    QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QUrl, Slot # Añadido QUrl, Slot
from PySide6.QtGui import QPixmap # Añadido QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply # Añadido para imágenes

from ui.theme import COLORS, FONTS, GRADIENTS, get_complete_style
import qtawesome as qta

class MetadataPanel(QWidget):
    """Panel moderno para mostrar y editar metadatos de pistas."""
    
    # Señales
    metadataChanged = Signal(dict)
    enrichRequested = Signal()
    refreshRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_track = None
        self.setMinimumWidth(380) # Aumentar un poco el ancho mínimo
        self.network_manager = QNetworkAccessManager(self) # Para descargar imágenes
        self.network_manager.finished.connect(self.on_image_loaded)
        self.current_image_reply = None # Para manejar la respuesta de la imagen
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Configura la interfaz de usuario moderna."""
        
        # Widget principal que contendrá todo el contenido desplazable
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(15, 15, 15, 15)

        # Título del panel
        title_label = QLabel("TRACK METADATA")
        title_label.setProperty("class", "title")
        content_layout.addWidget(title_label)

        # --- Sección de Arte de Portada ---
        self.album_art_label = QLabel()
        self.album_art_label.setObjectName("albumArtLabel")
        self.album_art_label.setMinimumSize(150, 150) # Tamaño mínimo para el arte
        self.album_art_label.setMaximumSize(200, 200) # Tamaño máximo
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setFrameShape(QFrame.Shape.StyledPanel) # Para que se vea el borde
        self.album_art_label.setScaledContents(False) # No escalar, usar pixmap.scaled
        content_layout.addWidget(self.album_art_label, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addSpacing(10)

        # Información básica
        basic_info_layout = self.create_info_section("BASIC INFO")
        content_layout.addLayout(basic_info_layout)
        content_layout.addSpacing(15)

        # Información técnica
        technical_info_layout = self.create_technical_section("TECHNICAL")
        content_layout.addLayout(technical_info_layout)
        content_layout.addSpacing(15)

        # Información adicional
        additional_info_layout = self.create_additional_section_compact("ADDITIONAL")
        content_layout.addLayout(additional_info_layout)
        content_layout.addSpacing(15)

        # --- Nueva Sección de IDs Externos ---
        external_ids_layout = self.create_external_ids_section("EXTERNAL IDs")
        content_layout.addLayout(external_ids_layout)
        content_layout.addSpacing(15)

        # Botones de acción
        buttons_layout = self.create_buttons_section()
        content_layout.addLayout(buttons_layout)
        
        # Nuevos botones de enriquecimiento
        enrichment_layout = self.create_enrichment_section()
        content_layout.addLayout(enrichment_layout)

        # Espaciador
        content_layout.addStretch()

        # Configurar el QScrollArea
        scroll_area = QScrollArea() # No pasar 'self' aquí todavía
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # El layout principal del MetadataPanel (que es 'self') ahora solo contiene el QScrollArea
        main_panel_layout = QVBoxLayout(self) # 'self' es el MetadataPanel
        main_panel_layout.setContentsMargins(0,0,0,0)
        main_panel_layout.addWidget(scroll_area)
        # self.setLayout(main_panel_layout) # No es necesario si se pasa 'self' al QVBoxLayout

    def create_info_section(self, title):
        """Crea la sección de información básica."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)

        section_title = QLabel(title)
        section_title.setProperty("class", "subtitle")
        main_layout.addWidget(section_title)

        grid_widget = QWidget()
        grid_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred) 
        grid_widget.setMinimumWidth(330) 
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(8)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnMinimumWidth(0, 60) 

        title_label = QLabel("Title:")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Track title...")
        self.title_edit.setMinimumHeight(35)
        self.title_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.title_edit.setMinimumWidth(200) 
        
        artist_label = QLabel("Artist:")
        self.artist_edit = QLineEdit()
        self.artist_edit.setPlaceholderText("Artist name...")
        self.artist_edit.setMinimumHeight(35)
        self.artist_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.artist_edit.setMinimumWidth(200)
        
        album_label = QLabel("Album:")
        self.album_edit = QLineEdit()
        self.album_edit.setPlaceholderText("Album name...")
        self.album_edit.setMinimumHeight(35)
        self.album_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.album_edit.setMinimumWidth(200)

        grid_layout.addWidget(title_label, 0, 0)
        grid_layout.addWidget(self.title_edit, 0, 1)
        grid_layout.addWidget(artist_label, 1, 0)
        grid_layout.addWidget(self.artist_edit, 1, 1)
        grid_layout.addWidget(album_label, 2, 0)
        grid_layout.addWidget(self.album_edit, 2, 1)
        main_layout.addWidget(grid_widget)
        return main_layout
    
    def create_technical_section(self, title):
        """Crea la sección de información técnica con un diseño de 'badge'."""
        layout = QVBoxLayout()
        layout.setSpacing(8)

        section_title = QLabel(title)
        section_title.setProperty("class", "subtitle")
        layout.addWidget(section_title)

        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(12)

        bpm_label = QLabel("BPM:")
        self.bpm_value = QLabel("---")
        self.bpm_value.setProperty("class", "value_badge")
        self.bpm_value.setMinimumWidth(60)
        self.bpm_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(bpm_label, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(self.bpm_value, 0, 1, Qt.AlignmentFlag.AlignVCenter)

        key_label = QLabel("Key:")
        self.key_value = QLabel("---")
        self.key_value.setProperty("class", "value_badge")
        self.key_value.setMinimumWidth(60)
        self.key_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(key_label, 0, 2, Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(self.key_value, 0, 3, Qt.AlignmentFlag.AlignVCenter)

        genre_label = QLabel("Genre:")
        self.genre_edit = QTextEdit()
        self.genre_edit.setPlaceholderText("Music genre...")
        self.genre_edit.setFixedHeight(60) 
        grid_layout.addWidget(genre_label, 1, 0, Qt.AlignmentFlag.AlignTop)
        grid_layout.addWidget(self.genre_edit, 1, 1, 1, 3)

        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)
        layout.addLayout(grid_layout)
        return layout
    
    def create_additional_section_compact(self, title):
        """Crea la sección de información adicional usando QFormLayout."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)

        section_title = QLabel(title)
        section_title.setProperty("class", "subtitle")
        main_layout.addWidget(section_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.year_edit = QLineEdit()
        self.year_edit.setPlaceholderText("Year...")
        self.year_edit.setMaximumWidth(100)
        self.year_edit.setMinimumHeight(35)
        form_layout.addRow("Year:", self.year_edit)

        self.comments_edit = QTextEdit()
        self.comments_edit.setPlaceholderText("Additional notes...")
        self.comments_edit.setMinimumHeight(70) 
        form_layout.addRow("Comments:", self.comments_edit)
        main_layout.addLayout(form_layout)
        return main_layout

    def create_external_ids_section(self, title):
        """Crea la sección para mostrar IDs de servicios externos."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)

        section_title = QLabel(title)
        section_title.setProperty("class", "subtitle")
        main_layout.addWidget(section_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight) # Alinea las etiquetas a la derecha

        self.mb_recording_id_edit = QLineEdit()
        self.mb_recording_id_edit.setReadOnly(True)
        self.mb_recording_id_edit.setProperty("class", "id_field")
        form_layout.addRow("MB Recording:", self.mb_recording_id_edit)
        
        self.mb_artist_id_edit = QLineEdit()
        self.mb_artist_id_edit.setReadOnly(True)
        self.mb_artist_id_edit.setProperty("class", "id_field")
        form_layout.addRow("MB Artist:", self.mb_artist_id_edit)

        self.mb_release_id_edit = QLineEdit()
        self.mb_release_id_edit.setReadOnly(True)
        self.mb_release_id_edit.setProperty("class", "id_field")
        form_layout.addRow("MB Release:", self.mb_release_id_edit)

        self.spotify_track_id_edit = QLineEdit()
        self.spotify_track_id_edit.setReadOnly(True)
        self.spotify_track_id_edit.setProperty("class", "id_field")
        form_layout.addRow("Spotify Track:", self.spotify_track_id_edit)

        self.spotify_artist_id_edit = QLineEdit()
        self.spotify_artist_id_edit.setReadOnly(True)
        self.spotify_artist_id_edit.setProperty("class", "id_field")
        form_layout.addRow("Spotify Artist:", self.spotify_artist_id_edit)

        self.spotify_album_id_edit = QLineEdit()
        self.spotify_album_id_edit.setReadOnly(True)
        self.spotify_album_id_edit.setProperty("class", "id_field")
        form_layout.addRow("Spotify Album:", self.spotify_album_id_edit)

        self.discogs_release_id_edit = QLineEdit()
        self.discogs_release_id_edit.setReadOnly(True)
        self.discogs_release_id_edit.setProperty("class", "id_field")
        form_layout.addRow("Discogs Release:", self.discogs_release_id_edit)

        main_layout.addLayout(form_layout)
        return main_layout

    def create_buttons_section(self):
        """Crea la sección de botones de acción."""
        layout = QHBoxLayout()
        layout.setSpacing(8)
        
        self.enrich_button = QPushButton("ENRICH")
        self.enrich_button.setToolTip("Enrich metadata from online sources")
        self.enrich_button.setMinimumHeight(40)
        self.enrich_button.clicked.connect(self.enrichRequested.emit)

        self.refresh_button = QPushButton(qta.icon('fa5s.sync-alt', color=COLORS['text_primary']), " REFRESH")
        self.refresh_button.setToolTip("Reread tags from the audio file")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.refreshRequested.emit)
        
        layout.addWidget(self.enrich_button)
        layout.addWidget(self.refresh_button)
        layout.addStretch()
        
        self.save_button = QPushButton("SAVE")
        self.save_button.setProperty("class", "secondary")
        self.save_button.setToolTip("Save metadata changes")
        self.save_button.setMinimumHeight(40)
        self.save_button.setAutoDefault(False) # Evitar activación automática
        self.save_button.clicked.connect(self.save_metadata)
        
        self.cancel_button = QPushButton("CANCEL")
        self.cancel_button.setProperty("class", "secondary")
        self.cancel_button.setToolTip("Cancel changes")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self.cancel_changes)
        
        layout.addWidget(self.save_button)
        layout.addWidget(self.cancel_button)
        
        return layout
    
    def create_enrichment_section(self):
        """Crea la sección de enriquecimiento de metadatos."""
        layout = QVBoxLayout()
        layout.setSpacing(8)

        section_title = QLabel("🌐 ENRIQUECIMIENTO")
        section_title.setProperty("class", "subtitle")
        layout.addWidget(section_title)

        # Botones de enriquecimiento
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.enrich_spotify_button = QPushButton("🎵 Spotify")
        self.enrich_spotify_button.setProperty("class", "enrich_button")
        self.enrich_spotify_button.setToolTip("Enriquecer con datos de Spotify")
        self.enrich_spotify_button.clicked.connect(self._enrich_with_spotify)

        self.enrich_discogs_button = QPushButton("💿 Discogs") 
        self.enrich_discogs_button.setProperty("class", "enrich_button")
        self.enrich_discogs_button.setToolTip("Enriquecer con datos de Discogs")
        self.enrich_discogs_button.clicked.connect(self._enrich_with_discogs)

        self.enrich_auto_button = QPushButton("⚡ Auto")
        self.enrich_auto_button.setProperty("class", "enrich_button_primary")
        self.enrich_auto_button.setToolTip("Enriquecimiento automático con todas las fuentes")
        self.enrich_auto_button.clicked.connect(self._enrich_automatic)

        buttons_layout.addWidget(self.enrich_spotify_button)
        buttons_layout.addWidget(self.enrich_discogs_button)
        buttons_layout.addWidget(self.enrich_auto_button)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        # Status del enriquecimiento
        self.enrichment_status = QLabel("Listo para enriquecer metadatos")
        self.enrichment_status.setProperty("class", "status_label")
        layout.addWidget(self.enrichment_status)

        return layout
    
    def apply_styles(self):
        """Aplica los estilos modernos al panel."""
        self.setProperty("class", "panel")
        
        panel_style = f"""
        MetadataPanel {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {COLORS['background_panel']}, 
                stop:1 {COLORS['background_secondary']});
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
        }}
        QLabel#albumArtLabel {{
            border: 2px dashed {COLORS['border_light']};
            border-radius: 8px;
            background-color: {COLORS['background_input']}; /* Fondo mientras carga */
            color: {COLORS['text_placeholder']}; /* Texto si no hay imagen */
            font-size: 10px;
        }}
        QLabel {{
            color: {COLORS['text_secondary']};
            font-family: {FONTS['main']};
            font-size: 11px;
            font-weight: 500;
            margin-bottom: 3px;
        }}
        QLabel[class="title"] {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['title']};
            font-size: 16px;
            font-weight: bold;
            padding: 8px 0px;
            border-bottom: 3px solid {COLORS['primary']};
            margin-bottom: 12px;
            text-align: center;
        }}
        QLabel[class="subtitle"] {{
            color: {COLORS['primary_bright']};
            font-family: {FONTS['title']};
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 8px;
            margin-bottom: 6px;
            padding: 4px;
            background: rgba(255, 107, 53, 0.1);
            border-radius: 4px;
            border-left: 3px solid {COLORS['primary']};
        }}
        QLabel[class="value_badge"] {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['mono']};
            font-size: 13px;
            font-weight: bold;
            background-color: {COLORS['primary']};
            padding: 4px 10px;
            border-radius: 5px;
            text-align: center;
            min-height: 20px;
        }}
        QLineEdit {{
            background: {COLORS['background_input']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 8px;
            font-family: {FONTS['main']};
            font-size: 12px;
        }}
        QLineEdit[class="id_field"] {{ /* Estilo para campos de ID */
            background: {COLORS['background_tertiary']}; /* Ligeramente diferente para solo lectura */
            color: {COLORS['text_secondary']};
            font-size: 10px; /* Más pequeño */
            padding: 6px;
        }}
        QLineEdit::placeholder {{
            color: {COLORS['text_placeholder']};
            font-style: italic;
        }}
        QLineEdit:focus {{
            border: 1px solid {COLORS['border_focus']};
            background: {COLORS['background_secondary']};
        }}
        QLineEdit:hover {{
            border: 1px solid {COLORS['border_light']};
        }}
        QPushButton {{
            background: {GRADIENTS['primary']};
            color: {COLORS['text_primary']};
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            font-family: {FONTS['title']};
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 2px;
        }}
        QPushButton:hover {{
            background: {COLORS['primary_light']};
        }}
        QPushButton:pressed {{
            background: {COLORS['primary_dark']};
        }}
        QPushButton[class="secondary"] {{
            background: {COLORS['button_secondary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border_light']};
        }}
        QPushButton[class="secondary"]:hover {{
            background: {COLORS['button_secondary_hover']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['primary']};
        }}
        QPushButton[class="secondary"]:pressed {{
            background: {COLORS['background_tertiary']};
            border: 1px solid {COLORS['primary_dark']};
        }}
        QTextEdit:hover {{
            border: 1px solid {COLORS['border_light']};
        }}
        QTextEdit::placeholder {{
            color: {COLORS['text_placeholder']};
            font-style: italic;
        }}
        QLabel[class="volume_icon"] {{
            margin: 0px;
            padding: 0px;
        }}
        
        QPushButton[class="enrich_button"] {{
            background: {COLORS['button_secondary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-family: {FONTS['title']};
            font-size: 11px;
            font-weight: bold;
            min-width: 70px;
        }}

        QPushButton[class="enrich_button"]:hover {{
            background: {COLORS['button_secondary_hover']};
            border: 1px solid {COLORS['primary']};
        }}

        QPushButton[class="enrich_button_primary"] {{
            background: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-family: {FONTS['title']};
            font-size: 11px;
            font-weight: bold;
            min-width: 70px;
        }}

        QPushButton[class="enrich_button_primary"]:hover {{
            background: {COLORS['primary_bright']};
        }}

        QLabel[class="status_label"] {{
            color: {COLORS['text_muted']};
            font-family: {FONTS['main']};
            font-size: 10px;
            font-style: italic;
            margin: 5px 0;
        }}
        """
        self.setStyleSheet(panel_style)

    @Slot(QNetworkReply)
    def on_image_loaded(self, reply: QNetworkReply):
        if self.current_image_reply != reply: # Si es una respuesta antigua, ignorarla
            reply.deleteLater()
            return

        self.current_image_reply = None # Limpiar la referencia

        if reply.error() == QNetworkReply.NetworkError.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # Escalar la imagen manteniendo la relación de aspecto, para que quepa en el QLabel
                scaled_pixmap = pixmap.scaled(self.album_art_label.size(), 
                                              Qt.AspectRatioMode.KeepAspectRatio, 
                                              Qt.TransformationMode.SmoothTransformation)
                self.album_art_label.setPixmap(scaled_pixmap)
            else:
                self.album_art_label.setText("Error al cargar imagen")
                print(f"Error: No se pudo cargar QPixmap desde los datos descargados. URL: {reply.url().toString()}")
        else:
            self.album_art_label.setText("No disponible")
            print(f"Error al descargar imagen: {reply.errorString()} URL: {reply.url().toString()}")
        reply.deleteLater()

    def load_album_art(self, url_string: str):
        if self.current_image_reply: # Si hay una descarga en curso, cancelarla
            self.current_image_reply.abort()
            # self.current_image_reply.deleteLater() # No es necesario, finished se encarga
            self.current_image_reply = None

        if url_string:
            url = QUrl(url_string)
            if url.isValid():
                self.album_art_label.setText("Cargando arte...") # Placeholder
                request = QNetworkRequest(url)
                # Añadir un User-Agent puede ayudar con algunos servidores
                request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "DjAlfin/0.1 Image Downloader")
                self.current_image_reply = self.network_manager.get(request)
            else:
                self.album_art_label.setText("URL de arte inválida")
                self.album_art_label.setPixmap(QPixmap()) # Limpiar imagen anterior
        else:
            self.album_art_label.setText("Arte no especificado")
            self.album_art_label.setPixmap(QPixmap()) # Limpiar imagen anterior

    def update_track_info(self, track_data: dict):
        """Actualiza los campos del panel con la información de la pista."""
        if track_data:
            self.current_track = track_data
            self.title_edit.setText(track_data.get('title', ''))
            self.artist_edit.setText(track_data.get('artist', ''))
            self.album_edit.setText(track_data.get('album', ''))
            self.genre_edit.setText(track_data.get('genre', ''))
            self.year_edit.setText(str(track_data.get('year', '') if track_data.get('year') is not None else ''))
            
            self.comments_edit.setText(track_data.get('comment', ''))

            bpm_val = track_data.get('bpm')
            self.bpm_value.setText(str(bpm_val) if bpm_val is not None else "---")
            
            key_val = track_data.get('key')
            self.key_value.setText(str(key_val) if key_val is not None and str(key_val).strip() else "---")

            # Cargar arte de portada
            self.load_album_art(track_data.get('album_art_url'))

            # Actualizar campos de IDs externos
            self.mb_recording_id_edit.setText(track_data.get('musicbrainz_recording_id', ''))
            self.mb_artist_id_edit.setText(track_data.get('musicbrainz_artist_id', ''))
            self.mb_release_id_edit.setText(track_data.get('musicbrainz_release_id', ''))
            self.spotify_track_id_edit.setText(track_data.get('spotify_track_id', ''))
            self.spotify_artist_id_edit.setText(track_data.get('spotify_artist_id', ''))
            self.spotify_album_id_edit.setText(track_data.get('spotify_album_id', ''))
            self.discogs_release_id_edit.setText(track_data.get('discogs_release_id', ''))

            can_enrich = bool(track_data.get('artist') and track_data.get('title'))
            self.enrich_button.setEnabled(can_enrich)
            self.refresh_button.setEnabled(True)
            self.save_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
        else:
            self.clear_fields()

    def clear_fields(self):
        """Limpia todos los campos del panel de metadatos."""
        self.current_track = None
        
        self.title_edit.clear()
        self.artist_edit.clear()
        self.album_edit.clear()
        self.genre_edit.clear()
        self.year_edit.clear()
        self.comments_edit.clear()
        
        self.bpm_value.setText("---")
        self.key_value.setText("---")
        
        self.album_art_label.setText("Seleccione una pista") # Mensaje por defecto
        self.album_art_label.setPixmap(QPixmap()) # Limpiar imagen

        # Limpiar campos de IDs externos
        self.mb_recording_id_edit.clear()
        self.mb_artist_id_edit.clear()
        self.mb_release_id_edit.clear()
        self.spotify_track_id_edit.clear()
        self.spotify_artist_id_edit.clear()
        self.spotify_album_id_edit.clear()
        self.discogs_release_id_edit.clear()
        
        self.enrich_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
    
    def get_metadata(self):
        """Recupera los metadatos actuales de los campos de la UI."""
        # No incluimos los IDs aquí ya que no son editables por el usuario directamente
        # y se obtienen del enriquecimiento.
        return {
            "title": self.title_edit.text(),
            "artist": self.artist_edit.text(),
            "album": self.album_edit.text(),
            "genre": self.genre_edit.toPlainText(),
            "year": self.year_edit.text(),
            "comments": self.comments_edit.toPlainText(),
            # BPM y Key no son editables directamente en este panel, se leen de los badges
            # Si se quisiera hacerlos editables, se necesitarían QLineEdit para ellos.
            # Por ahora, los tomamos de los labels, asumiendo que se actualizan por otras vías.
            "key": self.key_value.text() if self.key_value.text() != "---" else "",
            "bpm": self.bpm_value.text() if self.bpm_value.text() != "---" else ""
        }
    
    def save_metadata(self):
        """Emite la señal para guardar los metadatos."""
        if not self.current_track:
            print("No hay pista seleccionada para guardar.")
            return
            
        metadata = self.get_metadata()
        
        # Mantener el file_path original
        metadata['file_path'] = self.current_track['file_path']
        # Los IDs y album_art_url no se envían desde aquí, ya que se gestionan
        # a través del proceso de enriquecimiento y se guardan en la DB.
        # Esta función es para guardar los cambios manuales del usuario.
        self.metadataChanged.emit(metadata)
        print(f"✔️ Metadatos guardados para: {self.current_track.get('title')}")

    def cancel_changes(self):
        """Cancela los cambios y recarga los datos originales."""
        if self.current_track:
            self.update_track_info(self.current_track)
        print("Cambios cancelados en el panel de metadatos.")

    def _enrich_with_spotify(self):
        """Enriquece metadatos usando solo Spotify."""
        if not self.current_track:
            self.enrichment_status.setText("⚠️ No hay pista seleccionada")
            return
            
        self.enrichment_status.setText("🔄 Enriqueciendo con Spotify...")
        self.enrich_spotify_button.setEnabled(False)
        
        try:
            from core import spotify_client
            
            artist = self.current_track.get('artist', '')
            title = self.current_track.get('title', '')
            
            if not artist or not title:
                self.enrichment_status.setText("❌ Faltan datos básicos (artista/título)")
                return
            
            spotify_data = spotify_client.search_track(artist, title)
            if spotify_data:
                self._apply_enriched_data(spotify_data, "Spotify")
                self.enrichment_status.setText("✅ Enriquecido con Spotify")
            else:
                self.enrichment_status.setText("⚠️ No encontrado en Spotify")
                
        except Exception as e:
            self.enrichment_status.setText(f"❌ Error Spotify: {str(e)[:30]}...")
            print(f"Error en enriquecimiento Spotify: {e}")
        finally:
            self.enrich_spotify_button.setEnabled(True)

    def _enrich_with_discogs(self):
        """Enriquece metadatos usando solo Discogs."""
        if not self.current_track:
            self.enrichment_status.setText("⚠️ No hay pista seleccionada")
            return
            
        self.enrichment_status.setText("🔄 Enriqueciendo con Discogs...")
        self.enrich_discogs_button.setEnabled(False)
        
        try:
            from core import discogs_client
            
            artist = self.current_track.get('artist', '')
            title = self.current_track.get('title', '')
            
            if not artist or not title:
                self.enrichment_status.setText("❌ Faltan datos básicos (artista/título)")
                return
            
            discogs_data = discogs_client.search_release(artist, title)
            if discogs_data:
                self._apply_enriched_data(discogs_data, "Discogs")
                self.enrichment_status.setText("✅ Enriquecido con Discogs")
            else:
                self.enrichment_status.setText("⚠️ No encontrado en Discogs")
                
        except Exception as e:
            self.enrichment_status.setText(f"❌ Error Discogs: {str(e)[:30]}...")
            print(f"Error en enriquecimiento Discogs: {e}")
        finally:
            self.enrich_discogs_button.setEnabled(True)

    def _enrich_automatic(self):
        """Enriquecimiento automático usando todas las fuentes disponibles."""
        if not self.current_track:
            self.enrichment_status.setText("⚠️ No hay pista seleccionada")
            return
            
        self.enrichment_status.setText("🔄 Enriquecimiento automático...")
        self.enrich_auto_button.setEnabled(False)
        
        try:
            from core.metadata_enricher import enrich_metadata
            
            enriched_data = enrich_metadata(self.current_track)
            if enriched_data:
                self._apply_enriched_data(enriched_data, "Multi-fuente")
                self.enrichment_status.setText("✅ Enriquecimiento automático completado")
            else:
                self.enrichment_status.setText("⚠️ No se encontraron datos adicionales")
                
        except Exception as e:
            self.enrichment_status.setText(f"❌ Error auto: {str(e)[:30]}...")
            print(f"Error en enriquecimiento automático: {e}")
        finally:
            self.enrich_auto_button.setEnabled(True)

    def _apply_enriched_data(self, enriched_data: dict, source: str):
        """Aplica datos enriquecidos a los campos del panel."""
        print(f"Aplicando datos de {source}: {enriched_data}")
        
        # Mapear campos de diferentes fuentes
        field_mapping = {
            # Spotify
            'name': 'title',
            'artists': 'artist',
            'album': 'album',
            'release_date': 'year',
            
            # Discogs
            'title': 'title',
            'year': 'year',
            'genre': 'genre',
            'style': 'genre',
            
            # Campos directos
            'artist': 'artist',
            'bpm': 'bpm',
            'key': 'key'
        }
        
        # Aplicar datos a los campos
        for source_field, target_field in field_mapping.items():
            if source_field in enriched_data:
                value = enriched_data[source_field]
                
                # Procesamiento especial por tipo de campo
                if target_field == 'artist' and isinstance(value, list):
                    value = ', '.join([a.get('name', str(a)) for a in value])
                elif target_field == 'year' and isinstance(value, str):
                    value = value.split('-')[0]  # Extraer solo el año
                elif target_field == 'genre' and isinstance(value, list):
                    value = ', '.join(value)
                
                # Actualizar campo correspondiente
                if target_field == 'title':
                    self.title_edit.setText(str(value))
                elif target_field == 'artist':
                    self.artist_edit.setText(str(value))
                elif target_field == 'album':
                    self.album_edit.setText(str(value))
                elif target_field == 'genre':
                    self.genre_edit.setPlainText(str(value))
                elif target_field == 'year':
                    self.year_edit.setText(str(value))
        
        # Cargar artwork si está disponible
        if 'album_art_url' in enriched_data or 'cover_image' in enriched_data:
            art_url = enriched_data.get('album_art_url') or enriched_data.get('cover_image')
            if art_url:
                self.load_album_art(art_url)

if __name__ == '__main__':
    # Bloque para probar el panel de forma aislada
    app = QApplication(sys.argv)
    
    # Aplicar el tema globalmente para una prueba consistente
    app.setStyleSheet(get_complete_style())
    
    panel = MetadataPanel()
    
    # Simular la carga de datos
    sample_track = {
        'file_path': '/path/to/dummy.mp3',
        'title': 'A Sky Full Of Stars', 
        'artist': 'Coldplay', 
        'album': 'Ghost Stories',
        'genre': 'Alternative Rock; Pop Rock', 
        'bpm': 125.0, 
        'key': '6B',
        'year': 2014,
        'comment': 'Great track! From their sixth studio album.',
        'album_art_url': 'https://upload.wikimedia.org/wikipedia/en/8/8d/Coldplay_-_Ghost_Stories.png', # URL de ejemplo
        'musicbrainz_recording_id': 'mbrec-xxxx-yyyy-zzzz',
        'musicbrainz_artist_id': 'mbart-aaaa-bbbb-cccc',
        'musicbrainz_release_id': 'mbrel-dddd-eeee-ffff',
        'spotify_track_id': 'spotify-track-12345',
        'spotify_artist_id': 'spotify-artist-67890',
        'spotify_album_id': 'spotify-album-abcde',
        'discogs_release_id': 'discogs-release-vwxyz'
    }
    panel.update_track_info(sample_track)
    
    panel.show()
    sys.exit(app.exec())
