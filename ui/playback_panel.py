# ui/playback_panel.py

try:
    import os
    os.environ['QT_API'] = 'pyside6'
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtMultimedia import QMediaPlayer

from ui.theme import COLORS
from ui.widgets import CustomSlider, TimeLabel
from ui.base import BasePanel
from core.audio_service import AudioService


class PlaybackPanel(QWidget):
    """
    Panel minimalista con controles básicos de reproducción.
    """
    
    bpmAnalyzed = Signal(dict)

    def __init__(self, audio_service: AudioService, parent=None):
        super().__init__(parent)
        
        if not isinstance(audio_service, AudioService):
            raise TypeError("PlaybackPanel debe recibir una instancia de AudioService.")
            
        self.audio_service = audio_service
        self.is_slider_pressed = False

        self.setup_ui()
        self.connect_signals()
        self.initialize_volume()

    def setup_ui(self):
        """Construye la interfaz minimalista del panel."""
        self.setProperty("class", "panel_minimal")
        self.setFixedHeight(46)  # Panel minimalista
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(12)

        # --- Información del Track (ultracompacta) ---
        self.track_title = QLabel("Sin selección")
        self.track_title.setProperty("class", "playback_title")
        self.track_title.setFixedWidth(180)
        
        # --- Controles Centrales ---
        self.play_pause_button = QPushButton()
        self.play_pause_button.setProperty("class", "btn_minimal_primary")
        if HAS_QTAWESOME:
            self.play_pause_button.setIcon(qta.icon("fa5s.play", color="white"))
        else:
            self.play_pause_button.setText("▶")
        self.play_pause_button.setFixedSize(30, 30)

        self.stop_button = QPushButton()
        self.stop_button.setProperty("class", "btn_minimal")
        if HAS_QTAWESOME:
            self.stop_button.setIcon(qta.icon("fa5s.stop", color=COLORS['text_primary']))
        else:
            self.stop_button.setText("⏹")
        self.stop_button.setFixedSize(26, 26)
        
        # Progreso ultracompacto
        self.current_time_label = TimeLabel("0:00")
        self.current_time_label.setProperty("class", "time_mini")
        
        self.progress_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setFixedHeight(12)
        self.progress_slider.setProperty("class", "progress_minimal")
        
        self.total_time_label = TimeLabel("0:00")
        self.total_time_label.setProperty("class", "time_mini")
        
        # --- Información BPM ---
        bpm_label = QLabel("BPM")
        bpm_label.setProperty("class", "field_label")
        bpm_label.setFixedWidth(24)
        
        self.bpm_value = QLabel("--")
        self.bpm_value.setProperty("class", "value_badge_minimal")
        self.bpm_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bpm_value.setFixedWidth(40)
        
        # Control de volumen ultraminimal
        volume_icon = QLabel("🔊")
        volume_icon.setFixedWidth(16)
        
        self.volume_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setProperty("class", "volume_minimal")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(50)
        self.volume_slider.setFixedHeight(12)
        self.volume_slider.setTickPosition(self.volume_slider.TickPosition.NoTicks)
        self.volume_slider.setSingleStep(5)  # Pasos de 5%
        self.volume_slider.setPageStep(10)   # Pasos grandes de 10%
        
        # Ensamblar layout con separadores visuales
        main_layout.addWidget(self.track_title)
        main_layout.addWidget(self._create_separator())
        main_layout.addWidget(self.play_pause_button)
        main_layout.addWidget(self.stop_button)
        main_layout.addWidget(self.current_time_label)
        main_layout.addWidget(self.progress_slider, 1)  # Se expande
        main_layout.addWidget(self.total_time_label)
        main_layout.addWidget(self._create_separator())
        main_layout.addWidget(bpm_label)
        main_layout.addWidget(self.bpm_value)
        main_layout.addWidget(self._create_separator())
        main_layout.addWidget(volume_icon)
        main_layout.addWidget(self.volume_slider)
        
    def _create_separator(self):
        """Crea un separador visual minimalista."""
        separator = QLabel("|")
        separator.setProperty("class", "playback_separator")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator.setFixedWidth(8)
        return separator
        
    def connect_signals(self):
        """Conecta los widgets de la UI al AudioService y viceversa."""
        
        # 1. Conectar acciones del usuario (botones, sliders) a los métodos del servicio
        self.play_pause_button.clicked.connect(self.audio_service.play_pause)
        self.stop_button.clicked.connect(self.audio_service.stop)
        
        # Conectar control de volumen
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        
        self.progress_slider.sliderPressed.connect(lambda: setattr(self, 'is_slider_pressed', True))
        self.progress_slider.sliderReleased.connect(lambda: setattr(self, 'is_slider_pressed', False))
        self.progress_slider.valueChanged.connect(self.on_slider_value_changed)
        
        # 2. Conectar señales del servicio a los métodos de esta clase para actualizar la UI
        self.audio_service.playbackStateChanged.connect(self.update_play_pause_button)
        self.audio_service.durationChanged.connect(self.update_duration)
        self.audio_service.positionChanged.connect(self.update_position)
        self.audio_service.bpmAnalyzed.connect(self.on_bpm_analyzed_from_service)
        self.audio_service.trackLoaded.connect(self.reset_for_new_track)
        self.audio_service.errorOccurred.connect(self.on_service_error)
    
    def initialize_volume(self):
        """Inicializa el volumen del AudioService al valor del slider."""
        initial_volume = self.volume_slider.value()  # 70% por defecto
        self.audio_service.set_volume(initial_volume)
        self.volume_slider.setToolTip(f"Volumen: {initial_volume}%")
        print(f"🔊 PlaybackPanel: Volumen inicial establecido a {initial_volume}%")

    # --- Slots que responden a las señales del AudioService ---

    def update_play_pause_button(self, state: QMediaPlayer.PlaybackState):
        """Actualiza el ícono del botón Play/Pause según el estado del reproductor."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            if HAS_QTAWESOME:
                self.play_pause_button.setIcon(qta.icon("fa5s.pause", color=COLORS['text_primary']))
            else:
                self.play_pause_button.setText("⏸")
        else:
            if HAS_QTAWESOME:
                self.play_pause_button.setIcon(qta.icon("fa5s.play", color=COLORS['text_primary']))
            else:
                self.play_pause_button.setText("▶")

    def update_duration(self, duration_ms: int):
        """Actualiza el rango del slider y la etiqueta de tiempo total."""
        self.progress_slider.setMaximum(duration_ms)
        self.total_time_label.setText(self._format_time(duration_ms))

    def update_position(self, position_ms: int):
        """Actualiza la posición del slider y la etiqueta de tiempo actual."""
        if not self.is_slider_pressed:
            self.progress_slider.setValue(position_ms)
        self.current_time_label.setText(self._format_time(position_ms))
    
    def on_bpm_analyzed_from_service(self, result: dict):
        """Actualiza la UI cuando el servicio termina de analizar el BPM."""
        self.bpm_value.setText(f"{result.get('bpm', 0):.0f}")
        # Propagar la señal hacia el exterior (a MainWindow)
        self.bpmAnalyzed.emit(result)

    def reset_for_new_track(self, track_info: dict):
        """Reinicia los widgets del panel cuando se carga una nueva pista."""
        self.current_time_label.setText("0:00")
        self.total_time_label.setText("0:00")
        self.progress_slider.setValue(0)
        
        # Actualizar información del track
        title = track_info.get('title', 'Sin título')
        artist = track_info.get('artist', 'Artista desconocido')
        # Combinar título y artista en un solo label
        display_text = f"{title} - {artist}" if artist != 'Artista desconocido' else title
        self.track_title.setText(display_text)
        
        # Actualizar BPM
        bpm = track_info.get('bpm', '--')
        if bpm and str(bpm).replace('.', '').isdigit():
            self.bpm_value.setText(f"{float(bpm):.0f}")
        else:
            self.bpm_value.setText("--")
        
        self.update_play_pause_button(QMediaPlayer.PlaybackState.StoppedState)

    def on_service_error(self, error_message: str):
        """Muestra un error proveniente del servicio."""
        print(f"ERROR en AudioService: {error_message}")

    # --- Manejadores de eventos de la UI ---

    def on_slider_value_changed(self, value: int):
        """Si el usuario está moviendo el slider, actualiza la posición del reproductor."""
        if self.is_slider_pressed:
            self.audio_service.set_position(value)
    
    def _format_time(self, ms: int) -> str:
        """Formatea milisegundos a un string M:SS."""
        if ms < 0: ms = 0
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"

    def on_volume_changed(self, value: int):
        """Actualiza el volumen del audio."""
        print(f"🔊 PlaybackPanel: Volume changed to {value}%")
        
        # Actualizar el volumen en el AudioService
        self.audio_service.set_volume(value)
        
        # Actualizar tooltip del slider para mostrar el valor actual
        self.volume_slider.setToolTip(f"Volumen: {value}%")

    # --- Método público para ser llamado desde el exterior ---

    def load_track(self, track_info: dict):
        """
        Método de conveniencia llamado por MainWindow para iniciar la carga
        de una nueva pista en el servicio.
        """
        file_path = track_info.get('file_path')
        if file_path:
            self.audio_service.load_track(file_path)
            # La UI se actualizará a través de la señal trackLoaded.
            bpm = track_info.get('bpm')
            if bpm:
                 self.bpm_value.setText(f"{float(bpm):.0f}")
            else:
                 self.bpm_value.setText("--")
        else:
            # Si no hay ruta, limpiar el panel
            self.track_title.setText("Sin selección")
            self.bpm_value.setText("--")
            self.reset_for_new_track({})