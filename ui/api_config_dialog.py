"""
Dialog para configurar las API keys de Discogs y Spotify.
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QLabel, QGroupBox, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.theme import COLORS, FONTS

class APIConfigDialog(QDialog):
    """Dialog moderno para configurar API keys de servicios externos."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de APIs Externas")
        self.setFixedSize(600, 500)
        self.setup_ui()
        self.apply_styles()
        self.load_current_config()
    
    def setup_ui(self):
        """Configura la interfaz del dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Título
        title_label = QLabel("🌐 CONFIGURACIÓN DE APIs EXTERNAS")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Descripción
        desc_label = QLabel(
            "Configure sus API keys para enriquecimiento automático de metadatos.\n"
            "Estas claves se guardan localmente en el archivo .env"
        )
        desc_label.setProperty("class", "description")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Spotify Configuration
        spotify_group = self.create_spotify_section()
        layout.addWidget(spotify_group)
        
        # Discogs Configuration
        discogs_group = self.create_discogs_section()
        layout.addWidget(discogs_group)
        
        # Botones
        buttons_layout = self.create_buttons_section()
        layout.addLayout(buttons_layout)
    
    def create_spotify_section(self):
        """Crea la sección de configuración de Spotify."""
        group = QGroupBox("🎵 Spotify API")
        group.setProperty("class", "api_group")
        
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Info
        info_label = QLabel(
            "Para obtener características de audio, popularidad y artwork.\n"
            "Crear app en: https://developer.spotify.com/dashboard"
        )
        info_label.setProperty("class", "info_label")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.spotify_client_id = QLineEdit()
        self.spotify_client_id.setPlaceholderText("Client ID de Spotify...")
        self.spotify_client_id.setProperty("class", "api_input")
        
        self.spotify_client_secret = QLineEdit()
        self.spotify_client_secret.setPlaceholderText("Client Secret de Spotify...")
        self.spotify_client_secret.setProperty("class", "api_input")
        self.spotify_client_secret.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Client ID:", self.spotify_client_id)
        form_layout.addRow("Client Secret:", self.spotify_client_secret)
        
        layout.addLayout(form_layout)
        return group
    
    def create_discogs_section(self):
        """Crea la sección de configuración de Discogs."""
        group = QGroupBox("💿 Discogs API")
        group.setProperty("class", "api_group")
        
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Info
        info_label = QLabel(
            "Para obtener información detallada de releases, precios y artwork.\n"
            "Crear token en: https://discogs.com/settings/developers"
        )
        info_label.setProperty("class", "info_label")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.discogs_token = QLineEdit()
        self.discogs_token.setPlaceholderText("Personal Access Token de Discogs...")
        self.discogs_token.setProperty("class", "api_input")
        self.discogs_token.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Token:", self.discogs_token)
        
        layout.addLayout(form_layout)
        return group
    
    def create_buttons_section(self):
        """Crea la sección de botones."""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        self.test_button = QPushButton("🧪 Probar Conexiones")
        self.test_button.setProperty("class", "secondary_button")
        self.test_button.clicked.connect(self.test_connections)
        
        layout.addWidget(self.test_button)
        layout.addStretch()
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setProperty("class", "secondary_button")
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("💾 Guardar Configuración")
        self.save_button.setProperty("class", "primary_button")
        self.save_button.clicked.connect(self.save_config)
        
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.save_button)
        
        return layout
    
    def apply_styles(self):
        """Aplica estilos al dialog."""
        self.setStyleSheet(f"""
        APIConfigDialog {{
            background: {COLORS['background_dark']};
            color: {COLORS['text_primary']};
        }}
        
        QLabel[class="title"] {{
            color: {COLORS['primary']};
            font-family: {FONTS['title']};
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        QLabel[class="description"] {{
            color: {COLORS['text_secondary']};
            font-family: {FONTS['main']};
            font-size: 12px;
            margin: 10px 0;
        }}
        
        QGroupBox[class="api_group"] {{
            font-family: {FONTS['title']};
            font-size: 14px;
            font-weight: bold;
            color: {COLORS['primary']};
            border: 2px solid {COLORS['border']};
            border-radius: 8px;
            margin: 10px 0;
            padding-top: 15px;
        }}
        
        QLabel[class="info_label"] {{
            color: {COLORS['text_muted']};
            font-family: {FONTS['main']};
            font-size: 11px;
            font-style: italic;
        }}
        
        QLineEdit[class="api_input"] {{
            background: {COLORS['background_input']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 10px;
            font-family: {FONTS['mono']};
            font-size: 11px;
            color: {COLORS['text_primary']};
            min-height: 20px;
        }}
        
        QLineEdit[class="api_input"]:focus {{
            border: 2px solid {COLORS['primary']};
        }}
        
        QPushButton[class="primary_button"] {{
            background: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px 20px;
            font-family: {FONTS['title']};
            font-size: 12px;
            font-weight: bold;
            min-width: 120px;
        }}
        
        QPushButton[class="primary_button"]:hover {{
            background: {COLORS['primary_bright']};
        }}
        
        QPushButton[class="secondary_button"] {{
            background: {COLORS['button_secondary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 12px 20px;
            font-family: {FONTS['title']};
            font-size: 12px;
            font-weight: bold;
        }}
        
        QPushButton[class="secondary_button"]:hover {{
            background: {COLORS['button_secondary_hover']};
            border: 1px solid {COLORS['primary']};
        }}
        """)
    
    def load_current_config(self):
        """Carga la configuración actual desde variables de entorno."""
        # Cargar desde .env si existe
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
                
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    if key == "SPOTIPY_CLIENT_ID" and value != "TU_CLIENT_ID_DE_SPOTIFY_AQUI":
                        self.spotify_client_id.setText(value)
                    elif key == "SPOTIPY_CLIENT_SECRET" and value != "TU_CLIENT_SECRET_DE_SPOTIFY_AQUI":
                        self.spotify_client_secret.setText(value)
                    elif key == "DISCOGS_USER_TOKEN" and value != "TU_DISCOGS_USER_TOKEN_AQUI":
                        self.discogs_token.setText(value)
    
    def save_config(self):
        """Guarda la configuración en el archivo .env."""
        env_content = []
        
        # Spotify
        client_id = self.spotify_client_id.text().strip()
        client_secret = self.spotify_client_secret.text().strip()
        
        if client_id:
            env_content.append(f'SPOTIPY_CLIENT_ID="{client_id}"')
        if client_secret:
            env_content.append(f'SPOTIPY_CLIENT_SECRET="{client_secret}"')
        
        # Discogs
        discogs_token = self.discogs_token.text().strip()
        if discogs_token:
            env_content.append(f'DISCOGS_USER_TOKEN="{discogs_token}"')
        
        try:
            with open('.env', 'w') as f:
                f.write('\n'.join(env_content) + '\n')
            
            QMessageBox.information(
                self, 
                "✅ Configuración Guardada", 
                "Las API keys se han guardado correctamente.\n\n"
                "Reinicie la aplicación para que los cambios surtan efecto."
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "❌ Error al Guardar", 
                f"Error al guardar la configuración:\n{str(e)}"
            )
    
    def test_connections(self):
        """Prueba las conexiones con las APIs configuradas."""
        results = []
        
        # Test Spotify
        client_id = self.spotify_client_id.text().strip()
        client_secret = self.spotify_client_secret.text().strip()
        
        if client_id and client_secret:
            try:
                import spotipy
                from spotipy.oauth2 import SpotifyClientCredentials
                
                auth_manager = SpotifyClientCredentials(
                    client_id=client_id, 
                    client_secret=client_secret
                )
                sp = spotipy.Spotify(auth_manager=auth_manager)
                sp.search(q='test', type='track', limit=1)
                results.append("✅ Spotify: Conexión exitosa")
            except Exception as e:
                results.append(f"❌ Spotify: {str(e)}")
        else:
            results.append("⚠️ Spotify: Faltan credenciales")
        
        # Test Discogs
        discogs_token = self.discogs_token.text().strip()
        if discogs_token:
            try:
                import requests
                headers = {
                    "User-Agent": "DjAlfin/0.1",
                    "Authorization": f"Discogs token={discogs_token}"
                }
                response = requests.get(
                    "https://api.discogs.com/database/search?q=test&type=release&per_page=1",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                results.append("✅ Discogs: Conexión exitosa")
            except Exception as e:
                results.append(f"❌ Discogs: {str(e)}")
        else:
            results.append("⚠️ Discogs: Falta token")
        
        # Mostrar resultados
        QMessageBox.information(
            self,
            "🧪 Resultados de Prueba",
            "\n".join(results)
        ) 