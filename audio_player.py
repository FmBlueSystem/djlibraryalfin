#!/usr/bin/env python3
"""
🎵 DjAlfin - Audio Player
Reproductor de audio real para la aplicación
"""

import os
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

class AudioPlayer(QObject):
    """Reproductor de audio profesional."""
    
    # Señales
    position_changed = pyqtSignal(float)  # Posición en segundos
    duration_changed = pyqtSignal(float)  # Duración total
    state_changed = pyqtSignal(str)  # "playing", "paused", "stopped"
    
    def __init__(self):
        super().__init__()
        
        # Intentar usar QMediaPlayer primero
        try:
            self.player = QMediaPlayer()
            self.player.positionChanged.connect(self._on_position_changed)
            self.player.durationChanged.connect(self._on_duration_changed)
            self.player.stateChanged.connect(self._on_state_changed)
            self.use_qt_player = True
            print("🎵 Using Qt Media Player")
        except Exception as e:
            print(f"⚠️ Qt Media Player not available: {e}")
            self.use_qt_player = False
            self._setup_fallback_player()
        
        self.current_file = None
        self.is_playing = False
        self.current_position = 0.0
        self.duration = 0.0
        
    def _setup_fallback_player(self):
        """Setup reproductor alternativo."""
        print("🎵 Setting up fallback audio player")
        
        # Timer para simular reproducción
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_position)
        self.timer.setInterval(50)  # 20 FPS
        
        # Variables para simulación
        self.start_time = 0
        self.pause_position = 0
        
    def load_file(self, file_path):
        """Cargar archivo de audio."""
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        self.current_file = file_path
        print(f"🎵 Loading: {os.path.basename(file_path)}")
        
        if self.use_qt_player:
            return self._load_with_qt_player(file_path)
        else:
            return self._load_with_fallback(file_path)
    
    def _load_with_qt_player(self, file_path):
        """Cargar con QMediaPlayer."""
        try:
            url = QUrl.fromLocalFile(file_path)
            content = QMediaContent(url)
            self.player.setMedia(content)
            return True
        except Exception as e:
            print(f"❌ Error loading with Qt Player: {e}")
            return False
    
    def _load_with_fallback(self, file_path):
        """Cargar con reproductor alternativo."""
        try:
            # Simular duración basada en tamaño de archivo
            file_size = os.path.getsize(file_path)
            # Aproximación: 1MB ≈ 1 minuto de audio MP3
            estimated_duration = (file_size / (1024 * 1024)) * 60
            self.duration = min(estimated_duration, 600)  # Máximo 10 minutos
            
            self.duration_changed.emit(self.duration)
            print(f"📊 Estimated duration: {self.duration:.1f}s")
            return True
            
        except Exception as e:
            print(f"❌ Error in fallback loader: {e}")
            return False
    
    def play(self):
        """Iniciar reproducción."""
        
        if not self.current_file:
            print("❌ No file loaded")
            return
        
        if self.use_qt_player:
            self.player.play()
        else:
            self._play_with_fallback()
        
        self.is_playing = True
        self.state_changed.emit("playing")
        print("▶️ Playing")
    
    def pause(self):
        """Pausar reproducción."""
        
        if self.use_qt_player:
            self.player.pause()
        else:
            self._pause_with_fallback()
        
        self.is_playing = False
        self.state_changed.emit("paused")
        print("⏸️ Paused")
    
    def stop(self):
        """Detener reproducción."""
        
        if self.use_qt_player:
            self.player.stop()
        else:
            self._stop_with_fallback()
        
        self.is_playing = False
        self.current_position = 0.0
        self.state_changed.emit("stopped")
        self.position_changed.emit(0.0)
        print("⏹️ Stopped")
    
    def seek(self, position):
        """Saltar a posición específica (en segundos)."""
        
        if not self.current_file:
            return
        
        position = max(0.0, min(self.duration, position))
        
        if self.use_qt_player:
            self.player.setPosition(int(position * 1000))  # QMediaPlayer usa milisegundos
        else:
            self._seek_with_fallback(position)
        
        self.current_position = position
        self.position_changed.emit(position)
        print(f"⏭️ Seeking to {position:.1f}s")
    
    def set_volume(self, volume):
        """Establecer volumen (0-100)."""
        
        if self.use_qt_player:
            self.player.setVolume(int(volume))
        
        print(f"🔊 Volume: {volume}%")
    
    def get_position(self):
        """Obtener posición actual."""
        return self.current_position
    
    def get_duration(self):
        """Obtener duración total."""
        return self.duration
    
    def is_playing_now(self):
        """Verificar si está reproduciendo."""
        return self.is_playing
    
    # Métodos para QMediaPlayer
    def _on_position_changed(self, position):
        """Callback de cambio de posición (QMediaPlayer)."""
        self.current_position = position / 1000.0  # Convertir de ms a segundos
        self.position_changed.emit(self.current_position)
    
    def _on_duration_changed(self, duration):
        """Callback de cambio de duración (QMediaPlayer)."""
        self.duration = duration / 1000.0  # Convertir de ms a segundos
        self.duration_changed.emit(self.duration)
    
    def _on_state_changed(self, state):
        """Callback de cambio de estado (QMediaPlayer)."""
        if state == QMediaPlayer.PlayingState:
            self.is_playing = True
            self.state_changed.emit("playing")
        elif state == QMediaPlayer.PausedState:
            self.is_playing = False
            self.state_changed.emit("paused")
        elif state == QMediaPlayer.StoppedState:
            self.is_playing = False
            self.state_changed.emit("stopped")
    
    # Métodos para reproductor alternativo
    def _play_with_fallback(self):
        """Reproducir con sistema alternativo."""
        if self.current_position > 0:
            # Reanudar desde pausa
            self.start_time = time.time() - self.current_position
        else:
            # Iniciar desde el principio
            self.start_time = time.time()
        
        self.timer.start()
    
    def _pause_with_fallback(self):
        """Pausar con sistema alternativo."""
        self.timer.stop()
        self.pause_position = self.current_position
    
    def _stop_with_fallback(self):
        """Detener con sistema alternativo."""
        self.timer.stop()
        self.current_position = 0.0
        self.pause_position = 0.0
    
    def _seek_with_fallback(self, position):
        """Saltar con sistema alternativo."""
        self.current_position = position
        if self.is_playing:
            self.start_time = time.time() - position
    
    def _update_position(self):
        """Actualizar posición (sistema alternativo)."""
        if self.is_playing and hasattr(self, 'start_time'):
            elapsed = time.time() - self.start_time
            self.current_position = elapsed
            
            if self.current_position >= self.duration:
                # Fin de la canción
                self.stop()
            else:
                self.position_changed.emit(self.current_position)

class AudioPlayerWidget(QObject):
    """Widget de control del reproductor."""
    
    def __init__(self, waveform_widget):
        super().__init__()
        self.waveform = waveform_widget
        self.player = AudioPlayer()
        
        # Conectar señales
        self.player.position_changed.connect(self._on_position_changed)
        self.player.duration_changed.connect(self._on_duration_changed)
        self.player.state_changed.connect(self._on_state_changed)
        
        self.current_file_path = None
    
    def load_track(self, file_path):
        """Cargar track para reproducción."""
        self.current_file_path = file_path
        success = self.player.load_file(file_path)
        
        if success:
            print(f"✅ Track loaded: {os.path.basename(file_path)}")
        else:
            print(f"❌ Failed to load: {os.path.basename(file_path)}")
        
        return success
    
    def play_pause(self):
        """Alternar reproducción/pausa."""
        if self.player.is_playing_now():
            self.player.pause()
        else:
            self.player.play()
    
    def stop(self):
        """Detener reproducción."""
        self.player.stop()
    
    def seek_to_cue(self, cue_position):
        """Saltar a un cue point."""
        self.player.seek(cue_position)
        print(f"🎯 Jumped to cue at {cue_position:.1f}s")
    
    def _on_position_changed(self, position):
        """Actualizar posición en waveform."""
        if self.waveform:
            self.waveform.current_position = position
            self.waveform.update()
    
    def _on_duration_changed(self, duration):
        """Actualizar duración."""
        print(f"📊 Duration: {duration:.1f}s")
    
    def _on_state_changed(self, state):
        """Manejar cambio de estado."""
        print(f"🎵 Player state: {state}")

def test_audio_player():
    """Test del reproductor de audio."""
    
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    player = AudioPlayer()
    
    # Buscar archivo de prueba
    audio_folder = "/Volumes/KINGSTON/Audio"
    if os.path.exists(audio_folder):
        mp3_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3') and not f.startswith('._')]
        
        if mp3_files:
            test_file = os.path.join(audio_folder, mp3_files[0])
            print(f"🧪 Testing with: {mp3_files[0]}")
            
            if player.load_file(test_file):
                print("✅ File loaded successfully")
                print("Commands: p=play, s=stop, q=quit")
                
                # Simular algunos comandos
                player.play()
                
                # Mantener la aplicación corriendo
                app.exec_()
            else:
                print("❌ Failed to load file")
        else:
            print("❌ No MP3 files found")
    else:
        print("❌ Audio folder not found")

if __name__ == "__main__":
    test_audio_player()
