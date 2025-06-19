import sys
from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, Signal
from PySide6.QtWidgets import (QWidget, QTableView, QApplication, QHeaderView, 
                               QAbstractItemView, QLineEdit, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QMenu)
from PySide6.QtGui import QFont, QIcon, QAction
import sqlite3

# Importar los nuevos componentes
from ui.base.column_manager import ColumnManager
from ui.base.advanced_header_view import AdvancedHeaderView
from ui.base.enhanced_track_model import EnhancedTrackModel


class CustomSortFilterProxyModel(QSortFilterProxyModel):
    """Proxy model personalizado con sorting inteligente por tipo de columna."""
    
    def __init__(self, column_manager, parent=None):
        super().__init__(parent)
        self.column_manager = column_manager
    
    def lessThan(self, left, right):
        """Comparación personalizada basada en el tipo de datos de la columna."""
        if not self.column_manager:
            return super().lessThan(left, right)
        
        visible_columns = self.column_manager.get_visible_columns()
        column = left.column()
        
        if column >= len(visible_columns):
            return super().lessThan(left, right)
        
        col_config = visible_columns[column]
        left_data = self.sourceModel().data(left, Qt.ItemDataRole.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.ItemDataRole.DisplayRole)
        
        # Manejo de valores nulos/vacíos
        if not left_data and not right_data:
            return False
        if not left_data:
            return True
        if not right_data:
            return False
        
        try:
            # Ordenamiento por tipo de datos
            if col_config.data_type in ['number', 'time']:
                left_val = float(left_data) if left_data else 0.0
                right_val = float(right_data) if right_data else 0.0
                return left_val < right_val
            
            elif col_config.data_type == 'bpm':
                # BPM puede tener formato "120.5" 
                left_val = float(str(left_data).replace(',', '.')) if left_data else 0.0
                right_val = float(str(right_data).replace(',', '.')) if right_data else 0.0
                return left_val < right_val
            
            else:
                # Ordenamiento de texto (case-insensitive)
                left_str = str(left_data).lower()
                right_str = str(right_data).lower()
                return left_str < right_str
                
        except (ValueError, TypeError):
            # Fallback a comparación de texto
            left_str = str(left_data).lower()
            right_str = str(right_data).lower()
            return left_str < right_str


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
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
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
    Widget robusto de lista de tracks con funcionalidades avanzadas:
    - Ordenamiento avanzado con indicadores visuales
    - Reordenamiento de columnas con drag & drop
    - Auto-tamaño inteligente de columnas
    - Búsqueda y filtrado mejorado
    - Menús contextuales
    - Configuración persistente de columnas
    """
    
    # Señales
    track_selected = Signal(dict)
    
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        
        # Inicializar componentes base
        self.column_manager = ColumnManager(self)
        self.model = EnhancedTrackModel(db_connection, self.column_manager, self)
        
        # Proxy model personalizado para filtrado y ordenación inteligente
        self.proxy_model = CustomSortFilterProxyModel(self.column_manager, self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # Buscar en todas las columnas
        self.proxy_model.setDynamicSortFilter(True)
        
        # Configurar ordenamiento personalizado para mejores resultados
        self.proxy_model.setSortRole(Qt.ItemDataRole.DisplayRole)
        
        # Configurar interfaz
        self.setup_ui()
        self.setup_table_view()
        self.connect_signals()
        
        # Carga inicial
        self.load_all_tracks()
        
    def setup_ui(self):
        """Configura la interfaz de usuario mejorada."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # Barra de herramientas superior
        toolbar_layout = QHBoxLayout()
        
        # Búsqueda mejorada
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar en biblioteca... (título, artista, álbum, etc.)")
        self.search_input.setProperty("class", "search_enhanced")
        
        # Botón de búsqueda avanzada
        self.advanced_search_btn = QPushButton("Filtros")
        self.advanced_search_btn.setToolTip("Búsqueda y filtros avanzados")
        self.advanced_search_btn.setProperty("class", "btn_minimal")
        
        # Botón de configuración de columnas
        self.config_columns_btn = QPushButton("Columnas")
        self.config_columns_btn.setToolTip("Configurar columnas visibles")
        self.config_columns_btn.setProperty("class", "btn_minimal")
        
        # Contador de resultados
        self.results_label = QLabel("0 tracks")
        self.results_label.setProperty("class", "results_counter")
        
        toolbar_layout.addWidget(self.search_input, 1)  # Se expande
        toolbar_layout.addWidget(self.advanced_search_btn)
        toolbar_layout.addWidget(self.config_columns_btn)
        toolbar_layout.addWidget(self.results_label)
        
        layout.addLayout(toolbar_layout)
        
        # Vista de tabla mejorada
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        
        # Header personalizado
        self.header_view = AdvancedHeaderView(Qt.Orientation.Horizontal)
        self.header_view.set_column_manager(self.column_manager)
        self.table_view.setHorizontalHeader(self.header_view)
        
        layout.addWidget(self.table_view)

    def setup_table_view(self):
        """Configura la apariencia y comportamiento de la tabla mejorada."""
        # Configuración básica
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Multi-selección
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)
        
        # IMPORTANTE: Habilitar sorting DESPUÉS de establecer el modelo
        # El sorting será habilitado en load_all_tracks()
        
        # Configuración avanzada
        self.table_view.setShowGrid(False)
        self.table_view.setWordWrap(False)
        self.table_view.setCornerButtonEnabled(False)
        
        # Configurar scroll suave
        self.table_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        # Configurar drag & drop
        self.table_view.setDragEnabled(True)
        self.table_view.setDropIndicatorShown(True)
        self.table_view.setDragDropMode(QAbstractItemView.DragOnly)
        
        # Configurar menú contextual
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Aplicar estilos personalizados
        self.apply_table_styles()
    
    def apply_table_styles(self):
        """Aplica estilos personalizados a la tabla."""
        from config.design_system import Theme
        
        self.setStyleSheet(f"""
        /* Búsqueda mejorada */
        QLineEdit[class="search_enhanced"] {{
            background: {Theme.BACKGROUND_INPUT};
            border: 2px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
            color: {Theme.TEXT_PRIMARY};
        }}
        
        QLineEdit[class="search_enhanced"]:focus {{
            border-color: {Theme.PRIMARY};
            background: {Theme.BACKGROUND};
        }}
        
        /* Contador de resultados */
        QLabel[class="results_counter"] {{
            color: {Theme.TEXT_SECONDARY};
            font-size: 10px;
            font-weight: bold;
            padding: 4px 8px;
            background: {Theme.BACKGROUND_SECONDARY};
            border-radius: 4px;
            min-width: 60px;
        }}
        
        /* Tabla mejorada */
        QTableView {{
            background: {Theme.BACKGROUND};
            alternate-background-color: {Theme.BACKGROUND_SECONDARY};
            selection-background-color: {Theme.PRIMARY};
            selection-color: white;
            gridline-color: transparent;
            border: 1px solid {Theme.BORDER};
            border-radius: 6px;
            font-size: 11px;
        }}
        
        QTableView::item {{
            padding: 6px 8px;
            border-bottom: 1px solid {Theme.BORDER_LIGHT};
        }}
        
        QTableView::item:selected {{
            background: {Theme.PRIMARY};
            color: white;
            font-weight: bold;
        }}
        
        QTableView::item:hover {{
            background: {Theme.BACKGROUND_TERTIARY};
        }}
        
        /* Botones minimalistas */
        QPushButton[class="btn_minimal"] {{
            background: {Theme.BACKGROUND_SECONDARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 11px;
            color: {Theme.TEXT_PRIMARY};
        }}
        
        QPushButton[class="btn_minimal"]:hover {{
            background: {Theme.PRIMARY};
            color: white;
        }}
        """)
    
    def connect_signals(self):
        """Conecta todas las señales necesarias."""
        # Búsqueda
        self.search_input.textChanged.connect(self.on_search_changed)
        
        # Selección de tracks
        self.table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        
        # Menú contextual de tabla
        self.table_view.customContextMenuRequested.connect(self.show_table_context_menu)
        
        # Auto-tamaño de columnas
        self.header_view.columnAutoSizeRequested.connect(self.auto_size_column)
        
        # Botones de toolbar
        self.config_columns_btn.clicked.connect(self.header_view.show_column_config)
        self.advanced_search_btn.clicked.connect(self.show_advanced_search)
        
        # Cambios de modelo
        self.proxy_model.rowsInserted.connect(self.update_results_count)
        self.proxy_model.rowsRemoved.connect(self.update_results_count)
        self.proxy_model.modelReset.connect(self.update_results_count)
    
    def on_search_changed(self, text):
        """Maneja cambios en el texto de búsqueda."""
        self.proxy_model.setFilterFixedString(text)
        self.update_results_count()
    
    def update_results_count(self):
        """Actualiza el contador de resultados."""
        count = self.proxy_model.rowCount()
        total = self.model.rowCount()
        
        if count == total:
            self.results_label.setText(f"{count} tracks")
        else:
            self.results_label.setText(f"{count} de {total} tracks")
    
    def auto_size_column(self, logical_index):
        """Auto-ajusta el ancho de una columna específica."""
        if logical_index < 0:
            return
        
        # Calcular ancho basado en contenido
        self.table_view.resizeColumnToContents(logical_index)
        
        # Obtener el ancho calculado y aplicar límites
        new_width = self.table_view.columnWidth(logical_index)
        visible_columns = self.column_manager.get_visible_columns()
        
        if logical_index < len(visible_columns):
            col = visible_columns[logical_index]
            # Aplicar límites min/max
            adjusted_width = max(col.min_width, min(new_width + 20, col.max_width))
            self.column_manager.set_column_width(col.key, adjusted_width)
    
    def show_advanced_search(self):
        """Muestra el diálogo de búsqueda avanzada."""
        # TODO: Implementar diálogo de búsqueda avanzada
        print("🔍 Búsqueda avanzada - Por implementar")
    
    def show_table_context_menu(self, position):
        """Muestra el menú contextual para tracks."""
        if not self.table_view.indexAt(position).isValid():
            return
        
        menu = QMenu(self)
        
        # Información del track seleccionado
        selected_tracks = self.get_selected_tracks()
        if len(selected_tracks) == 1:
            track = selected_tracks[0]
            menu.addSection(f"♪ {track.get('title', 'Track desconocido')}")
        elif len(selected_tracks) > 1:
            menu.addSection(f"♪ {len(selected_tracks)} tracks seleccionados")
        
        # Acciones de reproducción
        play_action = QAction("▶️ Reproducir", self)
        play_action.triggered.connect(lambda: self.play_selected_track())
        menu.addAction(play_action)
        
        add_to_queue_action = QAction("➕ Agregar a Cola", self)
        menu.addAction(add_to_queue_action)
        
        menu.addSeparator()
        
        # Acciones de playlist
        add_to_playlist_action = QAction("📝 Agregar a Playlist...", self)
        menu.addAction(add_to_playlist_action)
        
        menu.addSeparator()
        
        # Acciones de metadatos
        edit_metadata_action = QAction("✏️ Editar Metadatos", self)
        menu.addAction(edit_metadata_action)
        
        analyze_audio_action = QAction("🔍 Analizar Audio", self)
        menu.addAction(analyze_audio_action)
        
        menu.addSeparator()
        
        # Información del archivo
        show_info_action = QAction("ℹ️ Mostrar Información", self)
        menu.addAction(show_info_action)
        
        if len(selected_tracks) == 1:
            show_in_finder_action = QAction("📁 Mostrar en Finder", self)
            menu.addAction(show_in_finder_action)
        
        # Mostrar menú
        menu.exec(self.table_view.mapToGlobal(position))
    
    def play_selected_track(self):
        """Reproduce el track seleccionado."""
        selected_tracks = self.get_selected_tracks()
        if selected_tracks:
            track = selected_tracks[0]
            self.track_selected.emit(track)
    
    def get_selected_tracks(self):
        """Obtiene los tracks seleccionados actualmente."""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        tracks = []
        
        for proxy_index in selected_indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            track = self.model.get_track_at(source_index.row())
            if track:
                tracks.append(track)
        
        return tracks

    def _on_selection_changed(self, selected, deselected):
        """Slot para manejar el cambio de selección en la tabla."""
        if not selected.indexes():
            return

        track_info = self.get_selected_track_info()
        if track_info:
            self.track_selected.emit(track_info)

    def refresh_current_row(self):
        """
        Refresca los datos de la fila actual manteniendo la selección.
        """
        # Obtener la selección actual
        selected_proxy_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_proxy_indexes:
            # Si no hay selección, recargar todo
            self.load_all_tracks()
            return
        
        # Obtener el índice de la fuente (modelo real)
        source_index = self.proxy_model.mapToSource(selected_proxy_indexes[0])
        selected_row = source_index.row()
        
        # Obtener el ID de la pista seleccionada
        track = self.model.get_track_at(selected_row)
        if track and 'id' in track:
            track_id = track['id']
            # Recargar solo los datos de esta pista desde la BD
            try:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    SELECT id, title, artist, album, bpm, key, genre, duration, file_path 
                    FROM tracks WHERE id = ?
                """, [track_id])
                
                row_data = cursor.fetchone()
                if row_data:
                    # Actualizar los datos en el modelo
                    columns = [desc[0] for desc in cursor.description]
                    updated_track = dict(zip(columns, row_data))
                    
                    # Usar el método del modelo mejorado
                    if self.model.update_track_data(selected_row, updated_track):
                        print(f"✅ Fila {selected_row} actualizada correctamente")
                        
                        # Mantener la selección
                        self.table_view.selectRow(selected_proxy_indexes[0].row())
                        
                        # Emitir señal con datos actualizados
                        self.track_selected.emit(updated_track)
                    else:
                        print(f"⚠️ Error al actualizar datos del modelo")
                else:
                    print(f"⚠️ No se encontró la pista con ID {track_id} en la BD")
                    
            except sqlite3.Error as e:
                print(f"❌ Error al actualizar fila: {e}")
                # En caso de error, recargar todo
                self.load_all_tracks()
        else:
            print("⚠️ No se pudo obtener el ID de la pista seleccionada")
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
        
        # Habilitar sorting DESPUÉS de cargar los datos
        self.table_view.setSortingEnabled(True)
        
        # Configurar ordenamiento inicial por artista
        self.table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
        # Auto-ajustar columnas después de cargar datos
        self._auto_resize_columns()

    def load_tracks_by_ids(self, track_ids):
        """Carga en el modelo solo las pistas que coinciden con los IDs proporcionados."""
        self.model.load_tracks(track_ids=track_ids)
        
        # Habilitar sorting después de cargar datos filtrados
        self.table_view.setSortingEnabled(True)
        
        # Auto-ajustar columnas
        self._auto_resize_columns()
        
        self.update_results_count()
    
    def clear_tracks(self):
        """Limpia la lista de tracks."""
        self.model.load_tracks(track_ids=[])
        self.update_results_count()
    
    def _auto_resize_columns(self):
        """Auto-ajusta las columnas de manera inteligente."""
        if not self.column_manager:
            return
        
        visible_columns = self.column_manager.get_visible_columns()
        if not visible_columns:
            return
        
        # Obtener ancho total disponible
        total_width = self.table_view.viewport().width()
        
        # Anchos fijos para columnas específicas
        fixed_widths = {
            'bpm': 70,
            'key': 50, 
            'duration': 80,
            'year': 60
        }
        
        # Calcular ancho usado por columnas fijas
        fixed_width_used = 0
        flexible_columns = []
        
        for i, col in enumerate(visible_columns):
            if col.key in fixed_widths:
                width = fixed_widths[col.key]
                self.table_view.setColumnWidth(i, width)
                fixed_width_used += width
            else:
                flexible_columns.append((i, col))
        
        # Distribuir ancho restante entre columnas flexibles
        remaining_width = total_width - fixed_width_used - 50  # 50px de margen
        if remaining_width > 0 and flexible_columns:
            # Pesos para distribución proporcional
            weights = {
                'title': 3,
                'artist': 2, 
                'album': 2,
                'genre': 1.5,
                'comment': 2
            }
            
            total_weight = sum(weights.get(col.key, 1) for _, col in flexible_columns)
            
            for i, col in flexible_columns:
                weight = weights.get(col.key, 1)
                width = int((remaining_width * weight) / total_weight)
                width = max(col.min_width, min(width, col.max_width))
                self.table_view.setColumnWidth(i, width)

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
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
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