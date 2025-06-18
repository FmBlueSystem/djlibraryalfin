from PySide6.QtWidgets import QTreeView, QVBoxLayout, QWidget
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Signal

class PlaylistPanel(QWidget):
    """
    Un panel para mostrar la biblioteca y las listas de reproducción.
    Emite una señal cuando se selecciona un elemento.
    
    Señales:
        selection_changed(str, object): Se emite cuando la selección cambia.
            - str: El tipo de selección ('library', 'smart_playlist').
            - object: El ID del elemento seleccionado (el ID de la playlist o None para la biblioteca).
    """
    selection_changed = Signal(str, object)

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Playlists'])

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tree_view)

        self.populate_playlists()

        self.tree_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self, selected, deselected):
        """Manejador para cuando la selección en el árbol cambia."""
        if not selected.indexes():
            return
        
        index = selected.indexes()[0]
        item = self.model.itemFromIndex(index)
        
        item_id = item.data(Qt.UserRole)
        item_text = item.text()

        # Determinar el tipo de selección basado en el padre o texto del item
        parent = item.parent()
        if parent and parent.text() == "Smart Playlists":
            self.selection_changed.emit('smart_playlist', item_id)
        elif item_text == "Library":
            self.selection_changed.emit('library', None)

    def populate_playlists(self):
        """Carga y muestra las playlists desde la base de datos."""
        # Limpiar el modelo actual, pero manteniendo las conexiones de señales
        self.model.clear()
        
        # Item principal de la Biblioteca
        library_item = QStandardItem("Library")
        library_item.setData("library", Qt.UserRole)
        self.model.appendRow(library_item)

        # Sección de Smart Playlists
        smart_playlists_root = QStandardItem("Smart Playlists")
        self.model.appendRow(smart_playlists_root)

        playlists = self.engine.get_playlists()  # Esto devuelve [(id, name), ...]
        if playlists:
            for playlist_id, playlist_name in playlists:
                playlist_item = QStandardItem(playlist_name)
                playlist_item.setData(playlist_id, Qt.UserRole)
                smart_playlists_root.appendRow(playlist_item)
        
        # Expandir la sección de playlists por defecto
        self.tree_view.expand(smart_playlists_root.index())

    def refresh_playlists(self):
        """Vuelve a cargar las playlists y refresca la vista."""
        print("Refrescando la lista de playlists...")
        self.populate_playlists() 