import sys
from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, Signal
from PySide6.QtWidgets import (QWidget, QTableView, QApplication, QHeaderView, 
                               QAbstractItemView, QLineEdit, QVBoxLayout)
import sqlite3


class TrackListModel(QAbstractTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self._headers = ["Title", "Artist", "Album", "Genre", "BPM", "Key", "Comment"]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            row = self._data[index.row()]
            col_name = self._headers[index.column()].lower()
            return row.get(col_name, "")
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None

    def get_track_at(self, index):
        """Devuelve el diccionario de datos para una fila específica."""
        if 0 <= index < len(self._data):
            return self._data[index]
        return None
    
    def update_track_data(self, row: int, data: dict):
        """Actualiza los datos de una fila y notifica a la vista."""
        if 0 <= row < len(self._data):
            self._data[row] = data
            # Creamos los índices para la fila que ha cambiado
            start_index = self.index(row, 0)
            end_index = self.index(row, self.columnCount() - 1)
            # Emitimos la señal para que la vista se actualice
            self.dataChanged.emit(start_index, end_index)
            return True
        return False

    def load_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

class TrackListView(QWidget):
    """
    Un widget compuesto que contiene una barra de búsqueda y una vista de tabla para las pistas.
    """
    # Señal emitida cuando el usuario selecciona una pista en la tabla.
    # Emite un diccionario con la información completa de la pista.
    track_selected = Signal(dict)

    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        
        self.model = TrackModel(db_connection, parent=self)
        
        # Proxy model para filtrado y ordenación
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # Buscar en todas las columnas

        # Crear los widgets de la UI
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search Library...")
        self.table_view = QTableView(self)
        self.table_view.setModel(self.proxy_model)
        
        # Configurar la tabla
        self.setup_table_view()

        # Conectar señales
        self.search_input.textChanged.connect(self.proxy_model.setFilterFixedString)
        self.table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Configurar el layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.search_input)
        layout.addWidget(self.table_view)

        # Carga inicial
        self.load_all_tracks()

    def setup_table_view(self):
        """Configura la apariencia y comportamiento de la tabla."""
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.hideColumn(0)  # Ocultar la columna de ID
        self.table_view.hideColumn(7) # Ocultar la columna de File Path

        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(False)
        
        # Configurar anchos específicos para cada columna
        header.setSectionResizeMode(1, QHeaderView.Stretch)      # Title - se estira
        header.setSectionResizeMode(2, QHeaderView.Stretch)      # Artist - se estira
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Album
        header.setSectionResizeMode(4, QHeaderView.Fixed)        # BPM - ancho fijo
        header.setSectionResizeMode(5, QHeaderView.Fixed)        # Key - ancho fijo
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Genre
        header.setSectionResizeMode(7, QHeaderView.Fixed)        # Duration - ancho fijo
        
        # Establecer anchos fijos para columnas específicas
        self.table_view.setColumnWidth(4, 60)   # BPM
        self.table_view.setColumnWidth(5, 50)   # Key
        self.table_view.setColumnWidth(7, 70)   # Duration

    def _on_selection_changed(self, selected, deselected):
        """Slot para manejar el cambio de selección en la tabla."""
        if not selected.indexes():
            return

        track_info = self.get_selected_track_info()
        if track_info:
            self.track_selected.emit(track_info)

    def refresh_current_row(self):
        """
        Refresca los datos de la vista de la tabla.
        Solución simple: recargar todo.
        TODO: Implementar una actualización de una sola fila para mejor rendimiento.
        """
        self.load_all_tracks()

    def get_selected_track_info(self):
        """Devuelve los datos de la pista seleccionada actualmente."""
        selected_proxy_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_proxy_indexes:
            return None
        
        source_index = self.proxy_model.mapToSource(selected_proxy_indexes[0])
        return self.model.get_track_at(source_index.row())

    def load_all_tracks(self):
        """Recarga el modelo con todas las pistas de la base de datos."""
        self.model.load_tracks()

    def load_tracks_by_ids(self, track_ids):
        """Carga en el modelo solo las pistas que coinciden con los IDs proporcionados."""
        self.model.load_tracks(track_ids=track_ids)

class TrackModel(QAbstractTableModel):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_conn = db_connection
        self._headers = ["ID", "Title", "Artist", "Album", "BPM", "Key", "Genre", "Duration", "File Path"]
        self._data = []

    def load_tracks(self, track_ids=None):
        self.beginResetModel()
        try:
            cursor = self.db_conn.cursor()
            query = "SELECT id, title, artist, album, bpm, key, genre, duration, file_path FROM tracks"
            params = []

            if track_ids is not None:
                if not track_ids:
                    self._data = []
                    self.endResetModel()
                    return
                
                placeholders = ','.join('?' for _ in track_ids)
                query += f" WHERE id IN ({placeholders})"
                params = list(track_ids)
            
            cursor.execute(query, params)
            
            # TODO: La forma ideal de hacer esto es configurar `db_conn.row_factory = sqlite3.Row`
            # en el punto de creación de la conexión (main.py).
            # Como parche, construimos los diccionarios manualmente.
            columns = [desc[0] for desc in cursor.description]
            self._data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            print(f"✅ Modelo de pistas cargado con {len(self._data)} canciones.")
        except sqlite3.Error as e:
            print(f"❌ Error al cargar pistas en el modelo: {e}")
            self._data = []
        finally:
            self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row_data = self._data[index.row()]
        col_name = self._headers[index.column()].lower().replace(" ", "_")

        if role == Qt.DisplayRole:
            value = row_data.get(col_name)
            
            # Formatear duración de segundos a MM:SS
            if col_name == "duration" and value:
                try:
                    total_seconds = float(value)
                    minutes = int(total_seconds // 60)
                    seconds = int(total_seconds % 60)
                    return f"{minutes:02d}:{seconds:02d}"
                except (ValueError, TypeError):
                    return str(value) if value else ""
            
            # Formatear BPM
            elif col_name == "bpm" and value:
                try:
                    bpm_val = float(value)
                    return f"{bpm_val:.1f}" if bpm_val > 0 else ""
                except (ValueError, TypeError):
                    return str(value) if value else ""
            
            return str(value) if value else ""

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None

    def get_track_at(self, row):
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

if __name__ == '__main__':
    # Esto permite probar el widget de forma aislada
    app = QApplication(sys.argv)
    
    # Datos de prueba
    sample_data = [
        {'title': 'A Sky Full Of Stars', 'artist': 'Coldplay', 'album': 'Ghost Stories', 'genre': 'Pop', 'bpm': '125', 'key': 'F#m', 'comment': 'Good vibes'},
        {'title': 'Strobe', 'artist': 'Deadmau5', 'album': 'For Lack of a Better Name', 'genre': 'Progressive House', 'bpm': '128', 'key': 'Gm', 'comment': ''},
        {'title': 'Something Just Like This', 'artist': 'The Chainsmokers & Coldplay', 'album': 'Memories...Do Not Open', 'genre': 'EDM', 'bpm': '103', 'key': 'B', 'comment': 'Festival track'},
    ]
    
    view = TrackListView()
    model = TrackListModel(sample_data)
    view.setModel(model)
    
    view.resize(800, 300)
    view.show()
    
    sys.exit(app.exec()) 