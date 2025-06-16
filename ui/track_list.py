import sys
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtWidgets import QTableView, QApplication, QHeaderView, QAbstractItemView


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

class TrackListView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        
        # Configurar el header horizontal para mejor distribución de columnas
        header = self.horizontalHeader()
        header.setStretchLastSection(False)  # No estirar solo la última columna
        
        # Configurar anchos de columnas después de que se establezca el modelo
        self.model_set = False
    
    def setModel(self, model):
        super().setModel(model)
        if not self.model_set:
            self._configure_column_widths()
            self.model_set = True
    
    def _configure_column_widths(self):
        """Configura los anchos de las columnas para mejor visualización."""
        header = self.horizontalHeader()
        
        # Nuevas proporciones para dar más espacio a Title, Artist y Album
        total_width = self.width() if self.width() > 0 else 1000  # Usar un ancho por defecto más realista
        
        # Asignar anchos iniciales optimizados
        header.resizeSection(0, int(total_width * 0.30))  # Title
        header.resizeSection(1, int(total_width * 0.20))  # Artist  
        header.resizeSection(2, int(total_width * 0.20))  # Album
        header.resizeSection(3, int(total_width * 0.15))  # Genre
        header.resizeSection(4, 60)   # BPM - ancho fijo
        header.resizeSection(5, 60)   # Key - ancho fijo
        header.resizeSection(6, int(total_width * 0.15)) # Comment
        
        # Permitir que las columnas principales se estiren y redimensionen
        header.setSectionResizeMode(0, QHeaderView.Stretch)      # Title se estira para llenar el espacio
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Artist redimensionable por el usuario
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # Album redimensionable por el usuario
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # Genre redimensionable por el usuario
        header.setSectionResizeMode(4, QHeaderView.Fixed)        # BPM fijo
        header.setSectionResizeMode(5, QHeaderView.Fixed)        # Key fijo
        header.setSectionResizeMode(6, QHeaderView.Interactive)  # Comment redimensionable

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