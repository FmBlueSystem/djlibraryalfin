# ui/playback_panel.py

import qtawesome as qta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtMultimedia import QMediaPlayer

from ui.theme import COLORS, FONTS
from ui.widgets import CustomSlider, TimeLabel
from core.audio_service import AudioService


class PlaybackPanel(QWidget):
    """
    Panel con controles de reproducción, visualización de tiempo y BPM.
    Este widget es ahora un cliente del AudioService, que contiene toda la lógica.
    """
    
    # Señal emitida para notificar al exterior (ej. MainWindow) que un análisis
    # de BPM ha finalizado y sus resultados deben ser guardados.
    bpmAnalyzed = Signal(dict)

    def __init__(self, audio_service: AudioService, parent=None):
        super().__init__(parent)
        
        if not isinstance(audio_service, AudioService):
            raise TypeError("PlaybackPanel debe recibir una instancia de AudioService.")
            
        self.audio_service = audio_service
        self.is_slider_pressed = False # Flag para evitar que la UI actualice el slider mientras el usuario lo arrastra

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Construye la interfaz de usuario del panel."""
        self.setProperty("class", "PlaybackPanel")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(8)

        # --- Fila de Progreso ---
        progress_layout = QHBoxLayout()
        self.current_time_label = TimeLabel("00:00")
        self.progress_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.total_time_label = TimeLabel("00:00")
        
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)

        # --- Fila de Controles ---
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.play_pause_button = QPushButton()
        self.play_pause_button.setProperty("class", "play_button")
        self.play_pause_button.setIcon(qta.icon("fa5s.play-circle", color=COLORS['text_primary']))
        self.play_pause_button.setFixedSize(40, 40)

        self.stop_button = QPushButton(icon=qta.icon("fa5s.stop-circle", color=COLORS['text_primary']))
        self.stop_button.setFixedSize(40, 40)

        self.bpm_value = QLabel("--- BPM")
        self.bpm_value.setFont(FONTS["Medium"])
        self.bpm_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.analyze_bpm_button = QPushButton("Analizar")
        self.analyze_bpm_button.setProperty("class", "bpm_button")
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.bpm_value)
        controls_layout.addWidget(self.analyze_bpm_button)
        controls_layout.addStretch()

        main_layout.addLayout(progress_layout)
        main_layout.addLayout(controls_layout)

    def connect_signals(self):
        """Conecta los widgets de la UI al AudioService y viceversa."""
        
        # 1. Conectar acciones del usuario (botones, sliders) a los métodos del servicio
        self.play_pause_button.clicked.connect(self.audio_service.play_pause)
        self.stop_button.clicked.connect(self.audio_service.stop)
        self.analyze_bpm_button.clicked.connect(self.audio_service.analyze_bpm)
        
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

    # --- Slots que responden a las señales del AudioService ---

    def update_play_pause_button(self, state: QMediaPlayer.PlaybackState):
        """Actualiza el ícono del botón Play/Pause según el estado del reproductor."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setIcon(qta.icon("fa5s.pause-circle", color=COLORS['text_primary']))
        else:
            self.play_pause_button.setIcon(qta.icon("fa5s.play-circle", color=COLORS['text_primary']))

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
        self.bpm_value.setText(f"{result.get('bpm', 0):.1f} BPM")
        self.analyze_bpm_button.setText("Analizar")
        self.analyze_bpm_button.setEnabled(True)
        # Propagar la señal hacia el exterior (a MainWindow)
        self.bpmAnalyzed.emit(result)

    def reset_for_new_track(self, track_info: dict):
        """Reinicia los widgets del panel cuando se carga una nueva pista."""
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")
        self.progress_slider.setValue(0)
        # Asumimos que la info de la pista puede venir de la DB
        bpm = track_info.get('bpm', '---')
        self.bpm_value.setText(f"{bpm} BPM")
        self.update_play_pause_button(QMediaPlayer.PlaybackState.StoppedState)

    def on_service_error(self, error_message: str):
        """Muestra un error proveniente del servicio."""
        print(f"ERROR en AudioService: {error_message}")
        # Aquí se podría mostrar un tooltip o una notificación en la status bar.
        # Por ahora, restauramos el botón de análisis si estaba activo.
        if "BPM" in error_message:
            self.analyze_bpm_button.setText("Analizar")
            self.analyze_bpm_button.setEnabled(True)

    # --- Manejadores de eventos de la UI ---

    def on_slider_value_changed(self, value: int):
        """Si el usuario está moviendo el slider, actualiza la posición del reproductor."""
        if self.is_slider_pressed:
            self.audio_service.set_position(value)
    
    def _format_time(self, ms: int) -> str:
        """Formatea milisegundos a un string MM:SS."""
        if ms < 0: ms = 0
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes:02d}:{seconds:02d}"

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
                 self.bpm_value.setText(f"{float(bpm):.1f} BPM")
            else:
                 self.bpm_value.setText("--- BPM")
        else:
            # Si no hay ruta, limpiar el panel
            self.reset_for_new_track({}) 