# ui/metadata_panel.py

import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from ui.theme import COLORS, FONTS, get_complete_style
from ui.base import BasePanel, FormSection, ActionBar

try:
    import os
    os.environ['QT_API'] = 'pyside6'
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False


class MetadataPanel(BasePanel):
    """Panel minimalista para mostrar y editar metadatos de pistas."""
    
    metadataChanged = Signal(dict)
    enrichRequested = Signal()
    refreshRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(title="METADATOS", parent=parent)
        self.current_track = None
        self.setMinimumWidth(320)
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.on_image_loaded)
        self.current_image_reply = None
        self.setup_content()
        
    def setup_content(self):
        """Configura el contenido del panel."""
        # Scroll area para contenido
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)
        scroll_area.setProperty("class", "metadata_scroll")
        
        # Widget de contenido
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(4, 4, 4, 4)
        
        # Album Art (minimalista)
        self.album_art_label = QLabel()
        self.album_art_label.setProperty("class", "album_art_mini")
        self.album_art_label.setFixedSize(100, 100)
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setText("Sin portada")
        self.album_art_label.setStyleSheet(f"""
        QLabel[class="album_art_mini"] {{
            background: {COLORS['background_secondary']};
            border: 1px dashed {COLORS['border_light']};
            border-radius: 4px;
            color: {COLORS['text_muted']};
            font-size: 9px;
        }}
        """)
        
        content_layout.addWidget(self.album_art_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Información básica
        self.basic_section = FormSection("INFORMACIÓN BÁSICA", compact=True)
        self.basic_section.add_field("Título", "title", placeholder="Título del track...")
        self.basic_section.add_field("Artista", "artist", placeholder="Nombre del artista...")
        self.basic_section.add_field("Álbum", "album", placeholder="Nombre del álbum...")
        self.basic_section.add_field("Año", "year", field_type="number", placeholder="2024", width=60)
        self.basic_section.add_field("Género", "genre", placeholder="Electronic, Dance...")
        
        content_layout.addWidget(self.basic_section)
        
        # Información técnica
        self.technical_section = self.create_technical_section()
        content_layout.addWidget(self.technical_section)
        
        # Información adicional
        self.additional_section = FormSection("INFORMACIÓN ADICIONAL", compact=True)
        self.additional_section.add_field("BPM", "bpm", field_type="readonly")
        self.additional_section.add_field("Key", "initialkey", field_type="readonly", width=50)
        self.additional_section.add_field("Duración", "duration", field_type="readonly", width=80)
        self.additional_section.add_field("Archivo", "file_path", field_type="readonly")
        
        content_layout.addWidget(self.additional_section)
        
        # Stretch
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        self.add_content(scroll_area)
        
        # Action bar
        self.action_bar = ActionBar(compact=True)
        self.action_bar.add_button("refresh", "🔄", tooltip="Refrescar")
        self.action_bar.add_button("enrich", "🌐", tooltip="Enriquecer")
        self.action_bar.add_button("save", "Guardar", "fa5s.save", "primary", enabled=False)
        
        # Conectar señales
        self.action_bar.get_button("refresh").clicked.connect(self.refreshRequested.emit)
        self.action_bar.get_button("enrich").clicked.connect(self.enrichRequested.emit)
        self.action_bar.get_button("save").clicked.connect(self.save_metadata)
        
        self.add_content(self.action_bar)
        
        # Conectar cambios de datos
        self.basic_section.dataChanged.connect(self._on_data_changed)
        
    def create_technical_section(self):
        """Crea la sección técnica con valores de solo lectura."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Título
        title = QLabel("DATOS TÉCNICOS")
        title.setProperty("class", "section_title")
        layout.addWidget(title)
        
        # Grid compacto para valores técnicos
        values_layout = QHBoxLayout()
        
        # BPM
        bpm_label = QLabel("BPM:")
        bpm_label.setProperty("class", "field_label")
        self.bpm_display = QLabel("---")
        self.bpm_display.setProperty("class", "value_badge_minimal")
        self.bpm_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bpm_display.setFixedWidth(50)
        
        # Key
        key_label = QLabel("Key:")
        key_label.setProperty("class", "field_label")
        self.key_display = QLabel("---")
        self.key_display.setProperty("class", "value_badge_minimal")
        self.key_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_display.setFixedWidth(40)
        
        # Duration
        duration_label = QLabel("Tiempo:")
        duration_label.setProperty("class", "field_label")
        self.duration_display = QLabel("---")
        self.duration_display.setProperty("class", "value_badge_minimal")
        self.duration_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        values_layout.addWidget(bpm_label)
        values_layout.addWidget(self.bpm_display)
        values_layout.addSpacing(8)
        values_layout.addWidget(key_label)
        values_layout.addWidget(self.key_display)
        values_layout.addSpacing(8)
        values_layout.addWidget(duration_label)
        values_layout.addWidget(self.duration_display)
        values_layout.addStretch()
        
        layout.addLayout(values_layout)
        
        return section
        
    def update_track_info(self, track_data: dict):
        """Actualiza el panel con información del track."""
        if not track_data:
            self.clear_fields()
            return
            
        self.current_track = track_data
        
        # Actualizar información básica
        basic_data = {
            'title': track_data.get('title', ''),
            'artist': track_data.get('artist', ''),
            'album': track_data.get('album', ''),
            'year': str(track_data.get('year', '') if track_data.get('year') else ''),
            'genre': track_data.get('genre', '')
        }
        
        for field_name, value in basic_data.items():
            self.basic_section.set_field_value(field_name, value)
            
        # Actualizar información técnica
        bpm = track_data.get('bpm', '---')
        self.bpm_display.setText(f"{float(bpm):.0f}" if bpm and str(bpm).replace('.', '').isdigit() else "---")
        
        key = track_data.get('initialkey', '---')
        self.key_display.setText(str(key) if key and str(key).strip() else "---")
        
        duration = track_data.get('duration', 0)
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            self.duration_display.setText(f"{minutes}:{seconds:02d}")
        else:
            self.duration_display.setText("---")
            
        # Actualizar información adicional
        additional_data = {
            'bpm': str(bpm) if bpm else '',
            'initialkey': str(key) if key else '',
            'duration': f"{minutes}:{seconds:02d}" if duration else '',
            'file_path': track_data.get('file_path', '')
        }
        
        for field_name, value in additional_data.items():
            self.additional_section.set_field_value(field_name, value)
        
        # Cargar artwork
        art_url = track_data.get('album_art_url')
        if art_url:
            self.load_album_art(art_url)
        else:
            self.album_art_label.setText("Sin portada")
            self.album_art_label.setPixmap(QPixmap())
            
        # Habilitar botón guardar
        self.action_bar.set_button_enabled("save", True)
        
    def clear_fields(self):
        """Limpia todos los campos."""
        self.current_track = None
        self.basic_section.clear_all()
        self.additional_section.clear_all()
        
        # Limpiar displays técnicos
        self.bpm_display.setText("---")
        self.key_display.setText("---")
        self.duration_display.setText("---")
        
        # Limpiar artwork
        self.album_art_label.setText("Sin selección")
        self.album_art_label.setPixmap(QPixmap())
        
        # Deshabilitar botón guardar
        self.action_bar.set_button_enabled("save", False)
        
    def save_metadata(self):
        """Guarda los metadatos editados."""
        if not self.current_track:
            return
            
        metadata = self.basic_section.get_all_values()
        metadata['id'] = self.current_track.get('id')
        metadata['file_path'] = self.current_track.get('file_path')
        
        self.metadataChanged.emit(metadata)
        
    def load_album_art(self, url_string: str):
        """Carga artwork desde URL."""
        if self.current_image_reply:
            self.current_image_reply.abort()
            
        if url_string:
            from PySide6.QtCore import QUrl
            url = QUrl(url_string)
            if url.isValid():
                self.album_art_label.setText("Cargando...")
                request = QNetworkRequest(url)
                request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "DjAlfin/1.0")
                self.current_image_reply = self.network_manager.get(request)
        else:
            self.album_art_label.setText("Sin portada")
            self.album_art_label.setPixmap(QPixmap())
            
    def on_image_loaded(self, reply):
        """Maneja la descarga de imagen."""
        if reply != self.current_image_reply:
            reply.deleteLater()
            return
            
        self.current_image_reply = None
        
        if reply.error() == QNetworkReply.NetworkError.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                scaled_pixmap = pixmap.scaled(
                    self.album_art_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.album_art_label.setPixmap(scaled_pixmap)
            else:
                self.album_art_label.setText("Error al cargar")
        else:
            self.album_art_label.setText("No disponible")
            
        reply.deleteLater()
        
    def _on_data_changed(self, data):
        """Maneja cambios en los datos del formulario."""
        # Habilitar botón de guardar cuando hay cambios
        self.action_bar.set_button_enabled("save", bool(data and any(data.values())))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(get_complete_style())
    
    panel = MetadataPanel()
    
    # Datos de prueba
    sample_track = {
        'id': 1,
        'title': 'A Sky Full Of Stars',
        'artist': 'Coldplay',
        'album': 'Ghost Stories',
        'genre': 'Alternative Rock',
        'year': 2014,
        'bpm': 125.0,
        'initialkey': '6B',
        'duration': 268,
        'file_path': '/path/to/track.mp3',
        'album_art_url': 'https://upload.wikimedia.org/wikipedia/en/8/8d/Coldplay_-_Ghost_Stories.png'
    }
    
    panel.update_track_info(sample_track)
    panel.show()
    
    sys.exit(app.exec())