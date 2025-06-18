import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QLabel, QPushButton, QFrame, QRadioButton, QGroupBox,
    QComboBox, QTableWidget, QHeaderView, QTableWidgetItem, QMessageBox,
    QDialog
)
from PySide6.QtCore import Qt

# Navegar a la raíz del proyecto para asegurar que los imports funcionen
# Asume que este script está en DjAlfin/ui/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from services import PlaylistService
from core.database import get_db_path

class SmartPlaylistEditor(QDialog):
    """
    Editor de Listas de Reproducción Inteligentes.

    Permite a los usuarios crear y editar listas de reproducción basadas en reglas
    que se aplican a los metadatos de las pistas.
    """
    def __init__(self, service: PlaylistService, parent=None, playlist_id=None, seed_track_data=None):
        """
        Inicializa el editor de listas de reproducción inteligentes.

        Args:
            service (PlaylistService): Capa de servicio para manejar playlists.
            parent (QWidget, optional): El widget padre. Defaults to None.
            playlist_id (int, optional): El ID de la lista a editar. Defaults to None.
            seed_track_data (dict, optional): Datos de una pista para precargar reglas.
        """
        super().__init__(parent)
        self.setWindowTitle("Smart Playlist Editor")
        self.setGeometry(100, 100, 700, 600)

        # Service layer to interact with playlists
        self.service = service

        self.playlist_id = playlist_id
        
        self._init_ui()
        self._connect_signals()
        
        if self.playlist_id:
            self._load_playlist_data()
        elif seed_track_data:
            self._seed_from_track(seed_track_data)

    def _init_ui(self):
        """Inicializa la interfaz de usuario y todos sus componentes."""
        main_layout = QVBoxLayout(self)

        # --- Nombre de la Playlist ---
        name_layout = QHBoxLayout()
        name_label = QLabel("Playlist Name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)

        # --- Contenedor de Condiciones ---
        conditions_group = QGroupBox("Conditions")
        conditions_layout = QVBoxLayout()
        
        self.rules_grid_layout = QGridLayout()
        self.rules_grid_layout.setColumnStretch(0, 1) # Field
        self.rules_grid_layout.setColumnStretch(1, 1) # Operator
        self.rules_grid_layout.setColumnStretch(2, 2) # Value
        self.rules_grid_layout.setColumnStretch(3, 2) # Value 2 (for between)
        
        # Cabeceras del grid
        self.rules_grid_layout.addWidget(QLabel("<b>Field</b>"), 0, 0)
        self.rules_grid_layout.addWidget(QLabel("<b>Operator</b>"), 0, 1)
        self.rules_grid_layout.addWidget(QLabel("<b>Value</b>"), 0, 2, 1, 2) # Span 2 columns
        
        # Añadir una fila de regla de ejemplo (se gestionará dinámicamente)
        self._add_rule_row()

        conditions_layout.addLayout(self.rules_grid_layout)
        
        # Botón para añadir más condiciones
        self.add_condition_btn = QPushButton("  [+] Add Condition")
        self.add_condition_btn.setFlat(True)
        add_btn_layout = QHBoxLayout()
        add_btn_layout.addWidget(self.add_condition_btn)
        add_btn_layout.addStretch()
        conditions_layout.addLayout(add_btn_layout)

        conditions_group.setLayout(conditions_layout)
        main_layout.addWidget(conditions_group)
        
        # --- Lógica de Coincidencia (Match ALL / ANY) ---
        match_group = QGroupBox("Match Logic")
        match_layout = QHBoxLayout()
        self.match_all_radio = QRadioButton("Match ALL rules")
        self.match_any_radio = QRadioButton("Match ANY rule")
        self.match_all_radio.setChecked(True)
        match_layout.addWidget(self.match_all_radio)
        match_layout.addWidget(self.match_any_radio)
        match_group.setLayout(match_layout)
        main_layout.addWidget(match_group)
        
        # --- Vista Previa (Preview) ---
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.update_preview_btn = QPushButton("Update Preview")
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(["Track Name", "Artist", "BPM", "Key", "Genre"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        preview_layout.addWidget(self.update_preview_btn)
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # --- Botones de Acción ---
        action_layout = QHBoxLayout()
        self.create_from_track_btn = QPushButton("Create from Current Track")
        self.freeze_btn = QPushButton("❄️ Freeze")
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        
        action_layout.addWidget(self.create_from_track_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.freeze_btn)
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(action_layout)
        
        # Deshabilitar 'Freeze' si es una nueva playlist sin guardar
        self.freeze_btn.setEnabled(self.playlist_id is not None)

    def _connect_signals(self):
        """Conecta los señales de los botones y widgets."""
        self.add_condition_btn.clicked.connect(self._add_rule_row)
        self.update_preview_btn.clicked.connect(self._update_preview)
        self.save_btn.clicked.connect(self._save_playlist)
        self.cancel_btn.clicked.connect(self.close)
        self.create_from_track_btn.clicked.connect(self._request_seed_data)
        self.freeze_btn.clicked.connect(self._freeze_playlist)

    def _get_rules_from_ui(self) -> list:
        """Recopila todas las reglas definidas en la interfaz de usuario."""
        rules = []
        for row in range(1, self.rules_grid_layout.rowCount()): # Empezar en 1 para saltar la cabecera
            field_combo = self.rules_grid_layout.itemAtPosition(row, 0).widget()
            operator_combo = self.rules_grid_layout.itemAtPosition(row, 1).widget()
            value1_input = self.rules_grid_layout.itemAtPosition(row, 2).widget()
            value2_input = self.rules_grid_layout.itemAtPosition(row, 3).widget()

            field_text = field_combo.currentText().lower().replace(" ", "_")
            operator_text = operator_combo.currentText().lower().replace(" ", "_")
            
            value = value1_input.text()
            if operator_text == "between":
                value = [value, value2_input.text()]
            
            # Simple validación para no incluir reglas vacías
            if value and value[0] and (operator_text != "between" or value[1]):
                 rules.append({
                    "field": field_text,
                    "operator": operator_text,
                    "value": value
                })
        return rules

    def _update_preview(self):
        """Obtiene las reglas, consulta el motor y actualiza la tabla de vista previa."""
        rules = self._get_rules_from_ui()
        match_all = self.match_all_radio.isChecked()
        
        # Obtener IDs de pistas usando el servicio
        track_ids = self.service.get_tracks(rules, match_all)
        matching_tracks = self.service.fetch_track_info(track_ids)
        
        self.preview_table.setRowCount(0) # Limpiar tabla
        
        if not matching_tracks:
            return

        # 2. Poblar la tabla directamente con los resultados (sin hacer otra consulta DB).
        self.preview_table.setRowCount(len(matching_tracks))
        for row_idx, track_data in enumerate(matching_tracks):
            self.preview_table.setItem(row_idx, 0, QTableWidgetItem(track_data.get('title', '')))
            self.preview_table.setItem(row_idx, 1, QTableWidgetItem(track_data.get('artist', '')))
            self.preview_table.setItem(row_idx, 2, QTableWidgetItem(str(track_data.get('bpm', ''))))
            self.preview_table.setItem(row_idx, 3, QTableWidgetItem(track_data.get('key', '')))
            self.preview_table.setItem(row_idx, 4, QTableWidgetItem(track_data.get('genre', '')))

    def _add_rule_row(self, rule_data=None):
        """Añade una nueva fila de widgets para definir una regla."""
        row = self.rules_grid_layout.rowCount()
        
        # ComboBox para el campo (BPM, Genre, etc.)
        field_combo = QComboBox()
        field_combo.addItems(["BPM", "Genre", "Key", "Date Added", "Play Count", "Artist", "Title"])
        
        # ComboBox para el operador (Is, Between, etc.)
        operator_combo = QComboBox()
        operator_combo.addItems(["Is", "Is Not", "Contains", "Does Not Contain", "Greater Than", "Less Than", "Between", "Is In Range"])

        # Widgets para el valor
        value1_input = QLineEdit()
        value2_input = QLineEdit()
        value2_input.setVisible(False) # Oculto por defecto, solo para "Between"

        self.rules_grid_layout.addWidget(field_combo, row, 0)
        self.rules_grid_layout.addWidget(operator_combo, row, 1)
        self.rules_grid_layout.addWidget(value1_input, row, 2)
        self.rules_grid_layout.addWidget(value2_input, row, 3)

        # Lógica para mostrar el segundo campo de valor
        operator_combo.currentTextChanged.connect(
            lambda text, v2=value2_input: v2.setVisible(text in ["Between", "Is In Range"])
        )

        if rule_data:
            field_text = rule_data['field'].replace('_', ' ').title()
            operator_text = rule_data['operator'].replace('_', ' ').title()
            value = json.loads(rule_data['value'])

            field_combo.setCurrentText(field_text)
            operator_combo.setCurrentText(operator_text)
            
            if isinstance(value, list):
                value1_input.setText(str(value[0]))
                value2_input.setText(str(value[1]))
            else:
                value1_input.setText(str(value))

    def _save_playlist(self):
        """Recolecta los datos de la UI y los guarda en la BD."""
        playlist_name = self.name_input.text().strip()
        if not playlist_name:
            QMessageBox.warning(self, "Validation Error", "Playlist name cannot be empty.")
            return

        rules = self._get_rules_from_ui()
        if not rules:
            QMessageBox.warning(self, "Validation Error", "At least one condition is required.")
            return

        match_all = self.match_all_radio.isChecked()

        try:
            self.service.save_playlist(playlist_name, rules, match_all)
            QMessageBox.information(self, "Success", f"Playlist '{playlist_name}' saved successfully.")
            self.accept()  # Cierra el diálogo
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save the playlist: {e}")

    def _load_playlist_data(self):
        """Carga los datos de una playlist existente a través del servicio."""
        if not self.playlist_id:
            return

        playlist = self.service.get_playlist_info(self.playlist_id)
        if not playlist:
            QMessageBox.warning(self, "Error", "Playlist not found.")
            self.close()
            return

        self.name_input.setText(playlist["name"])
        if playlist["match_all"]:
            self.match_all_radio.setChecked(True)
        else:
            self.match_any_radio.setChecked(True)

        # Limpiar filas de reglas existentes (excepto la cabecera)
        while self.rules_grid_layout.rowCount() > 1:
            self._remove_last_rule_row()

        rules = playlist.get("rules", [])
        if not rules:
            self._add_rule_row()
        else:
            for rule in rules:
                self._add_rule_row(rule_data=rule)

    def _remove_last_rule_row(self):
        """Elimina la última fila de widgets de regla."""
        if self.rules_grid_layout.rowCount() <= 1: # No eliminar la cabecera
            return
        
        row_to_remove = self.rules_grid_layout.rowCount() - 1
        for col in range(self.rules_grid_layout.columnCount()):
            item = self.rules_grid_layout.itemAtPosition(row_to_remove, col)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                self.rules_grid_layout.removeItem(item)

    def _request_seed_data(self):
        """
        Simula la obtención de datos de la pista actual y precarga el editor.
        En la integración real, esto emitiría una señal al `main_window`.
        """
        # --- DATOS DE EJEMPLO ---
        # En la app real, obtendrías esto de la pista seleccionada en la tracklist principal.
        sample_track = {
            'bpm': 124.0,
            'key': '6A',
            'genre': 'Techno'
        }
        # -------------------------
        
        QMessageBox.information(self, "Seeding Rules", 
                                f"Creating rules based on a sample track:\n"
                                f"BPM: {sample_track['bpm']}, Key: {sample_track['key']}, Genre: {sample_track['genre']}")
        
        self._seed_from_track(sample_track)

    def _seed_from_track(self, track_data: dict):
        """Precarga las reglas en la UI basadas en los metadatos de una pista."""
        # Limpiar reglas existentes
        while self.rules_grid_layout.rowCount() > 1:
            self._remove_last_rule_row()
            
        # Crear reglas basadas en los datos de la pista
        rules_to_seed = []
        if track_data.get('bpm'):
            bpm = float(track_data['bpm'])
            rules_to_seed.append({'field': 'BPM', 'operator': 'Between', 'value': [bpm - 2.5, bpm + 2.5]})
        if track_data.get('key'):
            rules_to_seed.append({'field': 'Key', 'operator': 'Is', 'value': track_data['key']})
        if track_data.get('genre'):
            rules_to_seed.append({'field': 'Genre', 'operator': 'Is', 'value': track_data['genre']})
        
        # Poblar la UI con las nuevas reglas
        for i, rule in enumerate(rules_to_seed):
            if i > 0:
                self._add_rule_row()
            
            # Obtener widgets de la fila actual
            field_combo = self.rules_grid_layout.itemAtPosition(i + 1, 0).widget()
            operator_combo = self.rules_grid_layout.itemAtPosition(i + 1, 1).widget()
            value1_input = self.rules_grid_layout.itemAtPosition(i + 1, 2).widget()
            value2_input = self.rules_grid_layout.itemAtPosition(i + 1, 3).widget()

            # Establecer valores
            field_combo.setCurrentText(rule['field'])
            operator_combo.setCurrentText(rule['operator'])
            
            if rule['operator'] == 'Between':
                value1_input.setText(str(rule['value'][0]))
                value2_input.setText(str(rule['value'][1]))
            else:
                value1_input.setText(str(rule['value']))
        
        # Sugerir un nombre para la playlist
        self.name_input.setText(f"Mix for {track_data.get('genre', 'track')}")

    def _freeze_playlist(self):
        """Convierte una lista de reproducción inteligente en una lista estática."""
        if not self.playlist_id:
            QMessageBox.warning(self, "Cannot Freeze", "Please save the playlist before freezing it.")
            return

        reply = QMessageBox.question(self, "Freeze Playlist",
                                     "Are you sure you want to freeze this playlist?\n"
                                     "It will no longer update automatically.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("UPDATE smart_playlists SET is_static = 1, updated_at = datetime('now') WHERE id = ?", 
                               (self.playlist_id,))
                self.db_conn.commit()
                
                # Deshabilitar controles para reflejar el estado congelado
                self._disable_editing()
                QMessageBox.information(self, "Success", "Playlist has been frozen.")
                self.freeze_btn.setEnabled(False)

            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Could not freeze the playlist: {e}")

    def _disable_editing(self):
        """Deshabilita todos los controles de edición si la lista está congelada."""
        self.name_input.setReadOnly(True)
        self.add_condition_btn.setEnabled(False)
        self.match_all_radio.setEnabled(False)
        self.match_any_radio.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.create_from_track_btn.setEnabled(False)
        self.freeze_btn.setEnabled(False)
        
        # Deshabilitar todos los widgets en el grid de reglas
        for row in range(1, self.rules_grid_layout.rowCount()):
            for col in range(self.rules_grid_layout.columnCount()):
                item = self.rules_grid_layout.itemAtPosition(row, col)
                if item and item.widget():
                    item.widget().setEnabled(False)
        
        self.setWindowTitle(f"Smart Playlist Editor (Frozen) - {self.name_input.text()}")

# Para probar el widget de forma independiente
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Para probar la creación:
    editor = SmartPlaylistEditor()
    # Para probar la edición (asume que existe una playlist con ID=1):
    # editor = SmartPlaylistEditor(playlist_id=1) 
    # Para probar el "seeding" desde una pista:
    # seed_data = {'bpm': 128.0, 'key': '8A', 'genre': 'House'}
    # editor = SmartPlaylistEditor(seed_track_data=seed_data)
    editor.show()
    sys.exit(app.exec()) 