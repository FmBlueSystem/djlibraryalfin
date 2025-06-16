# ui/playback_panel.py

import sys
import qtawesome as qta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QFrame, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon
from ui.theme import COLORS, FONTS, GRADIENTS

class PlaybackPanel(QWidget):
    """Panel moderno de reproducción con controles profesionales."""
    
    # Señales
    playRequested = Signal()
    pauseRequested = Signal()
    stopRequested = Signal()
    previousRequested = Signal()
    nextRequested = Signal()
    positionChanged = Signal(int)
    volumeChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = False
        self.current_position = 0
        self.total_duration = 0
        self.setup_ui()
        self.apply_styles()
        
        # Timer para actualizar la posición
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # Actualizar cada 100ms
    
    def setup_ui(self):
        """Configura la interfaz de usuario moderna y compacta."""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Título del panel y controles de reproducción en la misma fila
        top_layout = QHBoxLayout()
        title_label = QLabel("PLAYBACK")
        title_label.setProperty("class", "title")
        top_layout.addWidget(title_label, 1, Qt.AlignmentFlag.AlignLeft)
        
        self.playback_controls_layout = self.create_playback_controls()
        top_layout.addLayout(self.playback_controls_layout)
        layout.addLayout(top_layout)

        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Layout principal para información de pista y controles
        main_content_layout = QHBoxLayout()
        layout.addLayout(main_content_layout)

        # Columna Izquierda: Información de la pista
        self.track_info_layout = self.create_track_info_section()
        main_content_layout.addLayout(self.track_info_layout, 2) # Más espacio para texto

        # Columna Derecha: Controles de progreso y volumen
        right_controls_layout = QVBoxLayout()
        right_controls_layout.setSpacing(4)
        main_content_layout.addLayout(right_controls_layout, 3) # Más espacio para sliders

        # Barra de progreso
        self.progress_layout = self.create_progress_section()
        right_controls_layout.addLayout(self.progress_layout)
        
        # Control de volumen
        # self.volume_layout = self.create_volume_section()
        # right_controls_layout.addLayout(self.volume_layout)
        
        # Espaciador
        layout.addStretch(0)
    
    def create_track_info_section(self):
        """Crea la sección de información de la pista actual, sin título de sección."""
        layout = QVBoxLayout()
        layout.setSpacing(2)
        
        self.track_title = QLabel("No track selected")
        self.track_title.setProperty("class", "track_title")
        self.track_title.setWordWrap(True)
        layout.addWidget(self.track_title)
        
        self.track_artist = QLabel("Unknown Artist")
        self.track_artist.setProperty("class", "track_artist")
        layout.addWidget(self.track_artist)
        
        layout.addStretch()
        return layout
    
    def create_playback_controls(self):
        """Crea los controles principales de reproducción, más compactos."""
        layout = QHBoxLayout()
        layout.setSpacing(6)
        
        self.prev_button = QPushButton(qta.icon('fa5s.step-backward', color=COLORS['text_primary']), "")
        self.prev_button.setProperty("class", "control_button")
        self.prev_button.setToolTip("Previous Track")
        self.prev_button.clicked.connect(self.previousRequested.emit)
        
        self.play_pause_button = QPushButton(qta.icon('fa5s.play', color=COLORS['text_primary']), "")
        self.play_pause_button.setProperty("class", "play_button")
        self.play_pause_button.setToolTip("Play/Pause")
        self.play_pause_button.clicked.connect(self.play_pause_clicked)
        
        self.stop_button = QPushButton(qta.icon('fa5s.stop', color=COLORS['text_primary']), "")
        self.stop_button.setProperty("class", "control_button")
        self.stop_button.setToolTip("Stop playback")
        self.stop_button.clicked.connect(self.stop_clicked)

        self.next_button = QPushButton(qta.icon('fa5s.step-forward', color=COLORS['text_primary']), "")
        self.next_button.setProperty("class", "control_button")
        self.next_button.setToolTip("Next Track")
        self.next_button.clicked.connect(self.nextRequested.emit)
        
        layout.addWidget(self.prev_button)
        layout.addWidget(self.play_pause_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.next_button)
        
        return layout
    
    def create_progress_section(self):
        """Crea la sección de progreso de reproducción, más compacta y sin título."""
        layout = QHBoxLayout()
        layout.setSpacing(6)
        
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setProperty("class", "time_label")
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setProperty("class", "progress_slider")
        # Permitir que el slider se expanda verticalmente para usar el espacio disponible
        self.progress_slider.setSizePolicy(self.progress_slider.sizePolicy().horizontalPolicy(), QSizePolicy.Expanding)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        self.progress_slider.sliderPressed.connect(self.progress_pressed)
        self.progress_slider.sliderReleased.connect(self.progress_released)
        self.progress_slider.valueChanged.connect(self.progress_changed)

        self.total_time_label = QLabel("00:00")
        self.total_time_label.setProperty("class", "time_label")
        
        layout.addWidget(self.current_time_label)
        layout.addWidget(self.progress_slider, 1) # Slider ocupa el espacio extra
        layout.addWidget(self.total_time_label)
        
        return layout
    
    def create_volume_section(self):
        """Crea la sección de control de volumen, más compacta y sin título."""
        layout = QHBoxLayout()
        layout.setSpacing(6)
        
        volume_icon = QLabel("🔊")
        volume_icon.setProperty("class", "volume_icon")
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setProperty("class", "volume_slider")
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.volume_changed_slot)
        
        self.volume_label = QLabel("70%")
        self.volume_label.setProperty("class", "volume_value")
        
        layout.addWidget(volume_icon)
        layout.addWidget(self.volume_slider, 1) # Slider ocupa el espacio extra
        layout.addWidget(self.volume_label)
        
        return layout
    
    def apply_styles(self):
        """Aplica los estilos modernos al panel."""
        self.setProperty("class", "panel")
        
        # Estilo específico para este panel
        panel_style = f"""
        PlaybackPanel {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {COLORS['background_panel']}, 
                stop:1 {COLORS['background_secondary']});
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
        }}
        
        QLabel[class="title"] {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['title']};
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: none; /* Sin borde */
            margin-bottom: 0px;
        }}
        
        /* Se elimina QLabel[class="subtitle"] porque ya no se usan */
        
        QLabel[class="track_title"] {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['title']};
            font-size: 13px;
            font-weight: bold;
            margin-bottom: 0px;
        }}
        
        QLabel[class="track_artist"] {{
            color: {COLORS['text_secondary']};
            font-family: {FONTS['main']};
            font-size: 11px;
            margin-bottom: 0px;
        }}
        
        QLabel[class="time_label"] {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['mono']};
            font-size: 11px;
            font-weight: bold;
            background: transparent; /* Sin fondo */
            padding: 2px;
            border-radius: 0px;
            border: none;
        }}
        
        QLabel[class="volume_icon"] {{
            font-size: 14px;
        }}
        
        QLabel[class="volume_value"] {{
            font-family: {FONTS['mono']};
            font-size: 11px;
            min-width: 35px;
            text-align: right;
        }}
        
        QPushButton[class="control_button"], QPushButton[class="play_button"] {{
            font-size: 16px;
            min-width: 36px;
            max-width: 36px;
            min-height: 36px;
            max-height: 36px;
            padding: 0;
            margin: 0;
            border: 1px solid {COLORS['border']};
            background-color: {COLORS['background_secondary']};
        }}

        QPushButton[class="control_button"]:hover, QPushButton[class="play_button"]:hover {{
            background-color: {COLORS['button_secondary_hover']};
            border: 1px solid {COLORS['primary']};
        }}

        QPushButton[class="play_button"] {{
            font-size: 16px; /* Ajustado para consistencia */
            background-color: {COLORS['primary']};
            border: 1px solid {COLORS['primary_dark']};
        }}
        
        QPushButton[class="play_button"]:hover {{
            background-color: {COLORS['primary_light']};
        }}

        QFrame[frameShape="5"] {{ /* HLine */
            color: {COLORS['separator']};
            margin: 4px 0;
        }}

        QSlider::groove:horizontal {{
            height: 6px; 
            background: {COLORS['background_tertiary']};
            border-radius: 3px;
            border: 1px solid {COLORS['border']};
        }}

        QSlider::handle:horizontal {{
            background: {COLORS['primary']};
            border: 1px solid {COLORS['primary_dark']};
            width: 14px;
            height: 14px;
            border-radius: 7px;
            margin: -5px 0; /* Centrar handle */
        }}

        QSlider::add-page:horizontal {{
            background: {COLORS['slider_track']};
        }}

        QSlider::sub-page:horizontal {{
            background: {COLORS['slider_progress']};
        }}
        """
        
        self.setStyleSheet(panel_style)
    
    def play_pause_clicked(self):
        """Maneja el clic del botón play/pause, emitiendo la señal apropiada."""
        if self.is_playing:
            self.pauseRequested.emit()
        else:
            self.playRequested.emit()
    
    def stop_clicked(self):
        """Maneja el clic del botón stop."""
        self.stopRequested.emit()
    
    def progress_pressed(self):
        """Se llama cuando se presiona el slider de progreso."""
        self.update_timer.stop()
    
    def progress_released(self):
        """Se llama cuando se suelta el slider de progreso."""
        position = self.progress_slider.value()
        self.positionChanged.emit(position)
    
    def progress_changed(self, value):
        """Se llama cuando cambia el valor del slider de progreso."""
        if self.total_duration > 0:
            seconds = int((value / 100.0) * self.total_duration)
            self.current_time_label.setText(self.format_time(seconds))
    
    def volume_changed_slot(self, value):
        """Se llama cuando cambia el volumen."""
        self.volume_label.setText(f"{value}%")
        self.volumeChanged.emit(value)
    
    def set_playing_state(self, is_playing):
        """Actualiza el estado de reproducción y el icono del botón, SIN emitir señales."""
        self.is_playing = is_playing
        if self.is_playing:
            self.play_pause_button.setIcon(qta.icon('fa5s.pause', color=COLORS['text_primary']))
            if self.total_duration > 0:
                self.update_timer.start(100)
        else:
            self.play_pause_button.setIcon(qta.icon('fa5s.play', color=COLORS['text_primary']))
            self.update_timer.stop()
    
    def set_track_info(self, title, artist="Unknown Artist"):
        """Actualiza la información de la pista actual."""
        self.track_title.setText(title or "No track selected")
        self.track_artist.setText(artist or "Unknown Artist")
    
    def set_duration(self, duration_seconds):
        """Establece la duración total de la pista."""
        self.total_duration = duration_seconds
        self.total_time_label.setText(self.format_time(duration_seconds))
    
    def set_position(self, position_seconds):
        """Actualiza la posición actual de reproducción."""
        self.current_position = position_seconds
        self.current_time_label.setText(self.format_time(position_seconds))
        
        if self.total_duration > 0:
            progress = int((position_seconds / self.total_duration) * 100)
            self.progress_slider.setValue(progress)
    
    def update_display(self):
        """Actualiza la visualización periódicamente."""
        # Este método se puede usar para actualizaciones periódicas
        # si se necesita simular la reproducción sin el backend de audio.
        # Se deja vacío para que el control lo lleve el backend de audio real.
        pass
    
    def format_time(self, seconds):
        """Formatea el tiempo en formato MM:SS."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    panel = PlaybackPanel()
    panel.setEnabled(True) # Habilitar para la prueba
    panel.show()
    sys.exit(app.exec()) 