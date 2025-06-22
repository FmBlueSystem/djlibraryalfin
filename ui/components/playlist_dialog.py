#!/usr/bin/env python3
"""
Playlist Dialog - DjAlfin
Diálogo para crear y editar playlists regulares.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor

class PlaylistDialog(QDialog):
    """Diálogo para crear/editar playlists regulares."""
    
    def __init__(self, parent=None, playlist_data=None):
        super().__init__(parent)
        self.playlist_data = playlist_data
        self.selected_color = "#2196F3"  # Color por defecto
        
        self.setup_ui()
        
        # Si es edición, llenar datos
        if playlist_data:
            self.setWindowTitle("Editar Playlist")
            self.name_edit.setText(playlist_data.get('name', ''))
            self.description_edit.setPlainText(playlist_data.get('description', ''))
            self.selected_color = playlist_data.get('color', '#2196F3')
            self.update_color_button()
        else:
            self.setWindowTitle("Nueva Playlist")
    
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("Nueva Playlist" if not self.playlist_data else "Editar Playlist")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Formulario
        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        
        # Nombre
        name_label = QLabel("Nombre:")
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre de la playlist...")
        self.name_edit.setMaxLength(100)
        
        form_layout.addWidget(name_label, 0, 0)
        form_layout.addWidget(self.name_edit, 0, 1)
        
        # Descripción
        desc_label = QLabel("Descripción:")
        desc_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descripción opcional...")
        self.description_edit.setMaximumHeight(80)
        
        form_layout.addWidget(desc_label, 1, 0, Qt.AlignmentFlag.AlignTop)
        form_layout.addWidget(self.description_edit, 1, 1)
        
        # Color
        color_label = QLabel("Color:")
        color_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        color_layout = QHBoxLayout()
        self.color_button = QPushButton("Seleccionar Color")
        self.color_button.setFixedHeight(30)
        self.color_button.clicked.connect(self.select_color)
        self.update_color_button()
        
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        
        form_layout.addWidget(color_label, 2, 0)
        form_layout.addLayout(color_layout, 2, 1)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Crear" if not self.playlist_data else "Guardar")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.accept)
        
        # Estilo para botones
        button_style = """
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
        """
        
        cancel_style = button_style + """
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """
        
        save_style = button_style + """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        
        self.cancel_btn.setStyleSheet(cancel_style)
        self.save_btn.setStyleSheet(save_style)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Enfocar campo de nombre
        self.name_edit.setFocus()
        
        # Validación en tiempo real
        self.name_edit.textChanged.connect(self.validate_form)
        self.validate_form()
    
    def select_color(self):
        """Abre el diálogo de selección de color."""
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Seleccionar Color de Playlist")
        
        if color.isValid():
            self.selected_color = color.name()
            self.update_color_button()
    
    def update_color_button(self):
        """Actualiza el botón de color con el color seleccionado."""
        style = f"""
            QPushButton {{
                background-color: {self.selected_color};
                color: white;
                border: 2px solid #333;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid #555;
            }}
        """
        self.color_button.setStyleSheet(style)
        self.color_button.setText(f"Color: {self.selected_color}")
    
    def validate_form(self):
        """Valida el formulario y habilita/deshabilita el botón de guardar."""
        name = self.name_edit.text().strip()
        is_valid = len(name) >= 1
        
        self.save_btn.setEnabled(is_valid)
        
        if not is_valid and name:
            self.name_edit.setStyleSheet("QLineEdit { border: 2px solid #F44336; }")
        else:
            self.name_edit.setStyleSheet("")
    
    def get_playlist_data(self):
        """Retorna los datos de la playlist del formulario."""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'color': self.selected_color
        }
    
    def accept(self):
        """Valida y acepta el diálogo."""
        data = self.get_playlist_data()
        
        if not data['name']:
            self.name_edit.setFocus()
            return
        
        super().accept()


class ConfirmDeleteDialog(QDialog):
    """Diálogo de confirmación para eliminar playlists."""
    
    def __init__(self, playlist_name, track_count=0, parent=None):
        super().__init__(parent)
        self.playlist_name = playlist_name
        self.track_count = track_count
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del diálogo de confirmación."""
        self.setWindowTitle("Confirmar Eliminación")
        self.setFixedSize(350, 150)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Icono y mensaje
        message_layout = QHBoxLayout()
        
        icon_label = QLabel("⚠️")
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        message_text = f"¿Está seguro de eliminar la playlist\n'{self.playlist_name}'?"
        if self.track_count > 0:
            message_text += f"\n\nContiene {self.track_count} tracks."
        message_text += "\n\nEsta acción no se puede deshacer."
        
        message_label = QLabel(message_text)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        message_layout.addWidget(icon_label)
        message_layout.addWidget(message_label)
        
        layout.addLayout(message_layout)
        layout.addStretch()
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.clicked.connect(self.accept)
        self.delete_btn.setDefault(True)
        
        # Estilo para botones
        cancel_style = """
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """
        
        delete_style = """
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """
        
        self.cancel_btn.setStyleSheet(cancel_style)
        self.delete_btn.setStyleSheet(delete_style)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)