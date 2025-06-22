import sys
from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, Signal, QTimer
from PySide6.QtWidgets import (QWidget, QTableView, QApplication, QHeaderView, 
                               QAbstractItemView, QLineEdit, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QMenu, QMessageBox)
from PySide6.QtGui import QFont, QIcon, QAction
import sqlite3

# Importar los nuevos componentes
from ui.base.column_manager import ColumnManager
from ui.base.advanced_header_view import AdvancedHeaderView
from ui.base.enhanced_track_model import EnhancedTrackModel

# Importar componentes para playlists
from ui.components.playlist_dialog import PlaylistDialog
from services.playlist_service import PlaylistService


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
        
        # Manejo mejorado de valores nulos/vacíos
        left_empty = not left_data or str(left_data).strip() == ""
        right_empty = not right_data or str(right_data).strip() == ""
        
        if left_empty and right_empty:
            return False
        if left_empty:
            return True  # Vacíos van al final
        if right_empty:
            return False
        
        try:
            # Ordenamiento por tipo específico de datos
            if col_config.data_type == 'number':
                left_val = self._extract_number(left_data)
                right_val = self._extract_number(right_data)
                return left_val < right_val
            
            elif col_config.data_type == 'bpm':
                left_val = self._extract_bpm(left_data)
                right_val = self._extract_bpm(right_data)
                return left_val < right_val
            
            elif col_config.data_type == 'time':
                left_val = self._extract_duration(left_data)
                right_val = self._extract_duration(right_data)
                return left_val < right_val
                
            elif col_config.data_type == 'key':
                # Ordenamiento especial para claves musicales
                return self._compare_musical_keys(left_data, right_data)
                
            elif col_config.key == 'year':
                # Año como número
                left_val = self._extract_year(left_data)
                right_val = self._extract_year(right_data)
                return left_val < right_val
                
            else:
                # Ordenamiento de texto mejorado (case-insensitive, con números naturales)
                return self._natural_sort_compare(str(left_data), str(right_data))
                
        except (ValueError, TypeError):
            # Fallback a comparación de texto natural
            return self._natural_sort_compare(str(left_data), str(right_data))
    
    def _extract_number(self, data):
        """Extrae un número de los datos."""
        if not data:
            return 0.0
        try:
            # Remover caracteres no numéricos excepto punto y coma
            clean_str = str(data).replace(',', '.').strip()
            # Extraer primer número encontrado
            import re
            match = re.search(r'[-+]?\d*\.?\d+', clean_str)
            if match:
                return float(match.group())
            return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _extract_bpm(self, data):
        """Extrae BPM como número flotante."""
        if not data:
            return 0.0
        try:
            clean_str = str(data).replace(',', '.').strip()
            # Remover "BPM" si está presente
            clean_str = clean_str.replace('BPM', '').replace('bpm', '').strip()
            return float(clean_str) if clean_str else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _extract_duration(self, data):
        """Extrae duración en segundos."""
        if not data:
            return 0.0
        try:
            time_str = str(data).strip()
            if ':' in time_str:
                # Formato MM:SS o HH:MM:SS
                parts = time_str.split(':')
                if len(parts) == 2:  # MM:SS
                    minutes, seconds = map(int, parts)
                    return minutes * 60 + seconds
                elif len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = map(int, parts)
                    return hours * 3600 + minutes * 60 + seconds
            else:
                # Asumir que son segundos
                return float(time_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _extract_year(self, data):
        """Extrae año como número."""
        if not data:
            return 0
        try:
            year_str = str(data).strip()
            import re
            # Buscar un año de 4 dígitos
            match = re.search(r'\b(19|20)\d{2}\b', year_str)
            if match:
                return int(match.group())
            # Si no es formato de año, tratar como número
            return int(float(year_str))
        except (ValueError, TypeError):
            return 0
    
    def _compare_musical_keys(self, left, right):
        """Comparación especial para claves musicales usando notación Camelot."""
        # Orden Camelot: 1A, 1B, 2A, 2B, ..., 12A, 12B
        def parse_camelot_key(key_str):
            if not key_str:
                return (999, 'Z')  # Claves vacías van al final
            
            key_str = str(key_str).strip().upper()
            
            # Buscar patrón número + letra (ej: "8A", "12B")
            import re
            match = re.match(r'(\d+)([AB])', key_str)
            if match:
                number = int(match.group(1))
                letter = match.group(2)
                return (number, letter)
            
            # Si no es formato Camelot, usar comparación alfabética
            return (999, key_str)
        
        left_parsed = parse_camelot_key(left)
        right_parsed = parse_camelot_key(right)
        
        return left_parsed < right_parsed
    
    def _natural_sort_compare(self, left, right):
        """Comparación natural que maneja números dentro del texto."""
        try:
            import re
            
            def natural_key(text):
                # Convertir texto a lista de strings y números para comparación natural
                parts = re.split(r'(\d+)', str(text))
                result = []
                for part in parts:
                    if part.isdigit():
                        result.append(int(part))
                    else:
                        result.append(part.lower())
                return result
            
            left_clean = str(left).strip()
            right_clean = str(right).strip()
            
            left_key = natural_key(left_clean)
            right_key = natural_key(right_clean)
            
            return left_key < right_key
        except (RecursionError, ValueError, TypeError):
            # Fallback simple en caso de error
            return str(left).lower() < str(right).lower()


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
    playlist_created = Signal()  # Señal para refrescar el panel de playlists
    
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        
        # Inicializar servicios
        from core.database import get_db_path
        self.playlist_service = PlaylistService(get_db_path())
        
        # Contexto de navegación
        self.current_context = "library"  # "library" o "playlist"
        self.current_playlist_name = ""
        
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
        
        # Auto-distribuir columnas en la carga inicial
        self._auto_distribute_initial()
        
    def setup_ui(self):
        """Configura la interfaz de usuario mejorada."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # Barra de herramientas superior
        toolbar_layout = QHBoxLayout()
        
        # Indicador de contexto y navegación
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        # Botón "Biblioteca" 
        self.home_btn = QPushButton("🏠 Biblioteca")
        self.home_btn.setToolTip("Regresar a la biblioteca completa")
        self.home_btn.setProperty("class", "btn_minimal")
        self.home_btn.clicked.connect(self.go_to_library)
        
        # Indicador de ubicación actual
        self.context_label = QLabel("📚 Biblioteca")
        self.context_label.setProperty("class", "context_indicator")
        self.context_label.setToolTip("Ubicación actual")
        
        nav_layout.addWidget(self.home_btn)
        nav_layout.addWidget(QLabel("→"))  # Separador visual
        nav_layout.addWidget(self.context_label)
        
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
        
        toolbar_layout.addLayout(nav_layout)  # Navegación a la izquierda
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
        self.table_view.setSortingEnabled(True)
        
        # Configurar el proxy model para sorting mejorado
        self.table_view.setSortingEnabled(True)
        self.proxy_model.sort(0, Qt.SortOrder.AscendingOrder)  # Ordenar por título por defecto
        
        # Asegurar que los headers muestren indicadores de sorting
        self.header_view.setSortIndicatorShown(True)
        self.header_view.setSectionsClickable(True)
        
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
            selection-background-color: {Theme.PRIMARY_LIGHT};
            selection-color: #1a1a1a;
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
            background: {Theme.PRIMARY_LIGHT};
            color: #1a1a1a;
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
        
        /* Indicador de contexto */
        QLabel[class="context_indicator"] {{
            background: {Theme.BACKGROUND_TERTIARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: bold;
            color: {Theme.TEXT_SECONDARY};
        }}
        """)
    
    def connect_signals(self):
        """Conecta las señales de los widgets a sus manejadores."""
        # Búsqueda
        self.search_input.textChanged.connect(self.on_search_changed)
        
        # Botones
        self.advanced_search_btn.clicked.connect(self.show_advanced_search)
        self.config_columns_btn.clicked.connect(self.header_view.show_column_config)
        
        # Tabla y selección
        self.table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.table_view.doubleClicked.connect(self.play_selected_track)
        self.table_view.customContextMenuRequested.connect(self.show_table_context_menu)

        # Ordenamiento - conectar correctamente con proxy model
        self.header_view.sectionClicked.connect(self._handle_header_click)
        
        # Columnas (el modelo ya maneja sus propios cambios de columnas)
        self.header_view.sectionResized.connect(self.column_manager.set_column_width)
        
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
    
    def _handle_header_click(self, logical_index):
        """Maneja clicks en el header para sorting."""
        # Obtener el orden actual
        current_order = self.header_view.sortIndicatorOrder()
        
        # Alternar entre ascendente y descendente
        if self.header_view.sortIndicatorSection() == logical_index:
            new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            new_order = Qt.SortOrder.AscendingOrder
        
        # Aplicar el sorting
        self.proxy_model.sort(logical_index, new_order)
        
        # Actualizar indicador visual
        self.header_view.setSortIndicator(logical_index, new_order)
    
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
        add_to_playlist_action.triggered.connect(lambda: self.show_add_to_playlist_menu(selected_tracks))
        menu.addAction(add_to_playlist_action)
        
        # Acción de recomendaciones (solo para track único)
        if len(selected_tracks) == 1:
            recommend_action = QAction("🎯 Sugerir canciones compatibles", self)
            recommend_action.triggered.connect(lambda: self.show_track_recommendations(selected_tracks[0]))
            menu.addAction(recommend_action)
        
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
        print("🎵 TrackListView: play_selected_track() called")
        
        selected_tracks = self.get_selected_tracks()
        print(f"🎵 TrackListView: Found {len(selected_tracks)} selected tracks")
        
        if selected_tracks:
            track = selected_tracks[0]
            print(f"🎵 TrackListView: Track data keys: {list(track.keys())}")
            
            # Verificar que el archivo existe
            file_path = track.get('file_path')
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            
            print(f"🎵 TrackListView: Track info - Title: '{title}', Artist: '{artist}', Path: '{file_path}'")
            
            if file_path:
                import os
                if os.path.exists(file_path):
                    print(f"🎵 TrackListView: File exists, emitting track_selected signal")
                    print(f"🎵 Playing: {title} - {artist}")
                    self.track_selected.emit(track)
                    print(f"🎵 TrackListView: track_selected signal emitted successfully")
                else:
                    print(f"❌ TrackListView: File not found: {file_path}")
                    self.show_error_message("Archivo no encontrado", 
                                           f"No se pudo encontrar el archivo:\n{file_path}\n\nVerifica que el archivo no haya sido movido o eliminado.")
            else:
                print("❌ TrackListView: No file path in track data")
                self.show_error_message("Datos incompletos", 
                                       "El track seleccionado no tiene información de archivo válida.")
        else:
            print("❌ TrackListView: No track selected for playback")
            self.show_status_message("No hay ningún track seleccionado para reproducir")
    
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
    
    def get_current_track(self):
        """Obtiene el track actualmente seleccionado (el primero si hay múltiples)."""
        selected_tracks = self.get_selected_tracks()
        return selected_tracks[0] if selected_tracks else None
    
    def _auto_distribute_initial(self):
        """Auto-distribuye las columnas al cargar inicialmente."""
        # Usar QTimer para asegurar que el widget está completamente renderizado
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._perform_auto_distribution)
    
    def _perform_auto_distribution(self):
        """Realiza la auto-distribución de columnas."""
        if self.table_view and self.header_view:
            viewport_width = self.table_view.viewport().width()
            if viewport_width > 100:  # Solo si el viewport es válido
                self.column_manager.distribute_columns_to_width(viewport_width)
    
    def resizeEvent(self, event):
        """Maneja el redimensionamiento del widget."""
        super().resizeEvent(event)
        
        # Auto-redistribuir cuando cambia el tamaño significativamente
        if hasattr(self, 'table_view') and self.table_view:
            new_width = event.size().width()
            if hasattr(event, 'oldSize') and event.oldSize().isValid():
                old_width = event.oldSize().width()
                # Solo redistribuir si el cambio es significativo (>5%)
                if abs(new_width - old_width) > old_width * 0.05:
                    self._perform_auto_distribution()
    
    def fit_columns_to_viewport(self):
        """Método público para ajustar columnas al viewport."""
        if self.header_view:
            self.header_view.auto_fit_to_viewport()

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
        Versión mejorada con mejor sincronización de UI.
        """
        print("🔄 TrackListView: Iniciando refresh_current_row...")
        
        # Obtener la selección actual
        selected_proxy_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_proxy_indexes:
            print("⚠️ No hay selección, recargando todos los tracks")
            # Si no hay selección, recargar todo
            self.load_all_tracks()
            return
        
        # Obtener el índice de la fuente (modelo real)
        source_index = self.proxy_model.mapToSource(selected_proxy_indexes[0])
        selected_row = source_index.row()
        
        print(f"🎯 Refrescando fila {selected_row} del modelo fuente")
        
        # Obtener el ID de la pista seleccionada
        track = self.model.get_track_at(selected_row)
        if track and 'id' in track:
            track_id = track['id']
            print(f"🎵 Refrescando track ID: {track_id}")
            
            # Recargar solo los datos de esta pista desde la BD
            try:
                cursor = self.db_connection.cursor()
                
                # Query mejorado que incluye todas las columnas necesarias
                all_columns = self.column_manager.get_all_columns()
                columns_list = list(all_columns.keys())
                columns_str = ', '.join(columns_list)
                
                print(f"🔍 Ejecutando query para actualizar track ID {track_id}: SELECT {columns_str[:100]}...")
                cursor.execute(f"""
                    SELECT {columns_str}
                    FROM tracks WHERE id = ?
                """, [track_id])
                
                row_data = cursor.fetchone()
                if row_data:
                    # Actualizar los datos en el modelo
                    columns = [desc[0] for desc in cursor.description]
                    updated_track = dict(zip(columns, row_data))
                    
                    print(f"📊 Datos actualizados obtenidos para track: {updated_track.get('title', 'Unknown')}")
                    print(f"   Género actualizado: {updated_track.get('genre', 'N/A')}")
                    
                    # Usar el método del modelo mejorado si está disponible
                    if hasattr(self.model, 'update_track_data') and self.model.update_track_data(selected_row, updated_track):
                        print(f"✅ Fila {selected_row} actualizada en modelo usando update_track_data")
                    else:
                        # Fallback: forzar recarga completa del modelo
                        print("🔄 Fallback: Recargando modelo completo...")
                        self.model.load_tracks()
                        # Re-seleccionar el track después de la recarga
                        for row in range(self.proxy_model.rowCount()):
                            proxy_index = self.proxy_model.index(row, 0)
                            source_index = self.proxy_model.mapToSource(proxy_index)
                            track_data = self.model.get_track_at(source_index.row())
                            if track_data and track_data.get('id') == track_id:
                                self.table_view.selectRow(row)
                                print(f"✅ Track re-seleccionado en fila {row}")
                                break
                    
                    # Mantener/restaurar la selección original
                    original_proxy_row = selected_proxy_indexes[0].row()
                    self.table_view.selectRow(original_proxy_row)
                    
                    # Emitir señal con datos actualizados
                    self.track_selected.emit(updated_track)
                    print(f"📡 Señal track_selected emitida con datos actualizados")
                    
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
        
    def select_previous_track(self):
        """Selecciona y reproduce el track anterior en la lista."""
        current_selection = self.table_view.selectionModel().selectedRows()
        if not current_selection:
            # Si no hay selección, seleccionar el primer track
            if self.proxy_model.rowCount() > 0:
                self._select_track_at_row(0)
            return
            
        current_row = current_selection[0].row()
        previous_row = max(0, current_row - 1)
        
        if previous_row != current_row:  # Solo si hay un track anterior
            self._select_track_at_row(previous_row)
        else:
            print("⏮️ Ya estás en el primer track")
            
    def select_next_track(self):
        """Selecciona y reproduce el track siguiente en la lista."""
        current_selection = self.table_view.selectionModel().selectedRows()
        max_row = self.proxy_model.rowCount() - 1
        
        if not current_selection:
            # Si no hay selección, seleccionar el primer track
            if max_row >= 0:
                self._select_track_at_row(0)
            return
            
        current_row = current_selection[0].row()
        next_row = min(max_row, current_row + 1)
        
        if next_row != current_row:  # Solo si hay un track siguiente
            self._select_track_at_row(next_row)
        else:
            print("⏭️ Ya estás en el último track")
            
    def _select_track_at_row(self, row):
        """Selecciona un track en la fila especificada y emite la señal."""
        if 0 <= row < self.proxy_model.rowCount():
            # Seleccionar la fila
            proxy_index = self.proxy_model.index(row, 0)
            self.table_view.selectionModel().clearSelection()
            self.table_view.selectionModel().select(proxy_index, 
                self.table_view.selectionModel().SelectionFlag.SelectCurrent | 
                self.table_view.selectionModel().SelectionFlag.Rows)
            
            # Hacer scroll para asegurar que la fila esté visible
            self.table_view.scrollTo(proxy_index, QAbstractItemView.ScrollHint.EnsureVisible)
            
            # Obtener los datos del track y emitir la señal
            source_index = self.proxy_model.mapToSource(proxy_index)
            track_data = self.model.get_track_at(source_index.row())
            
            if track_data:
                print(f"🎵 TrackListView: Seleccionado '{track_data.get('title', 'Unknown')}' - '{track_data.get('artist', 'Unknown')}'")
                self.track_selected.emit(track_data)

    def load_all_tracks(self):
        """Recarga el modelo con todas las pistas de la base de datos."""
        self.model.load_tracks()
        
        # Habilitar sorting DESPUÉS de cargar los datos
        self.table_view.setSortingEnabled(True)
        
        # Configurar ordenamiento inicial por artista
        self.table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
        # Auto-ajustar columnas después de cargar datos
        self._auto_resize_columns()
        
        # Actualizar contexto de navegación
        self.set_context("library", "")

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
    
    def force_refresh(self):
        """Fuerza una actualización completa de la vista de tracks."""
        print("🔄 TrackListView: Iniciando force_refresh...")
        
        try:
            # Verificar conexión a la base de datos
            if not self.db_connection:
                print("❌ TrackListView: No hay conexión a la base de datos")
                return False
            
            # Deshabilitar sorting temporalmente para evitar problemas durante la carga
            self.table_view.setSortingEnabled(False)
            
            # Limpiar selección actual
            self.table_view.clearSelection()
            
            # Forzar recarga del modelo
            print("🔄 TrackListView: Recargando modelo de tracks...")
            self.model.load_tracks()
            
            # Verificar que se cargaron datos
            row_count = self.model.rowCount()
            print(f"📊 TrackListView: Modelo cargado con {row_count} filas")
            
            if row_count > 0:
                # Rehabilitar sorting
                self.table_view.setSortingEnabled(True)
                
                # Aplicar ordenamiento por defecto (artista)
                self.table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
                
                # Auto-ajustar columnas
                self._auto_resize_columns()
                
                # Actualizar contador
                self.update_results_count()
                
                print(f"✅ TrackListView: Force refresh completado exitosamente ({row_count} tracks)")
                return True
            else:
                print("⚠️ TrackListView: No se cargaron tracks en el modelo")
                self.update_results_count()
                return False
                
        except Exception as e:
            print(f"❌ TrackListView: Error en force_refresh: {e}")
            # Rehabilitar sorting en caso de error
            self.table_view.setSortingEnabled(True)
            return False
    
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
    
    def show_error_message(self, title, message):
        """Muestra un mensaje de error al usuario."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def show_status_message(self, message, duration=3000):
        """Muestra un mensaje de estado temporal."""
        # Actualizar el label de resultados temporalmente
        original_text = self.results_label.text()
        self.results_label.setText(f"⚠️ {message}")
        self.results_label.setProperty("class", "results_counter_warning")
        self.results_label.style().unpolish(self.results_label)
        self.results_label.style().polish(self.results_label)
        
        # Restaurar el texto original después del tiempo especificado
        QTimer.singleShot(duration, lambda: self._restore_results_label(original_text))
    
    def _restore_results_label(self, original_text):
        """Restaura el texto original del label de resultados."""
        self.results_label.setText(original_text)
        self.results_label.setProperty("class", "results_counter")
        self.results_label.style().unpolish(self.results_label)
        self.results_label.style().polish(self.results_label)
    
    def show_add_to_playlist_menu(self, selected_tracks):
        """Muestra menú para agregar tracks a playlists existentes o crear nueva."""
        if not selected_tracks:
            return
        
        menu = QMenu("Agregar a Playlist", self)
        
        # Obtener playlists existentes
        try:
            existing_playlists = self.playlist_service.get_all_playlists()
            
            # Agregar opción para crear nueva playlist
            create_new_action = QAction("➕ Nueva Playlist con estos tracks", self)
            create_new_action.triggered.connect(lambda: self.create_playlist_with_tracks(selected_tracks))
            menu.addAction(create_new_action)
            
            if existing_playlists:
                menu.addSeparator()
                menu.addSection("📂 Playlists Existentes")
                
                # Agregar cada playlist existente
                for playlist in existing_playlists:
                    playlist_name = playlist['name']
                    track_count = playlist.get('track_count', 0)
                    action_text = f"📝 {playlist_name} ({track_count} tracks)"
                    
                    action = QAction(action_text, self)
                    action.triggered.connect(lambda checked, pid=playlist['id'], name=playlist_name: 
                                           self.add_tracks_to_existing_playlist(selected_tracks, pid, name))
                    menu.addAction(action)
            else:
                menu.addSeparator()
                menu.addAction("(No hay playlists creadas)").setEnabled(False)
            
            # Mostrar menú
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            menu.exec(self.mapToGlobal(cursor_pos))
            
        except Exception as e:
            print(f"❌ Error mostrando menú de playlists: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo cargar las playlists:\n{e}")
    
    def create_playlist_with_tracks(self, selected_tracks):
        """Crea una nueva playlist con los tracks seleccionados."""
        dialog = PlaylistDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            playlist_data = dialog.get_playlist_data()
            
            # Crear la playlist
            playlist_id = self.playlist_service.create_playlist(
                playlist_data['name'],
                playlist_data['description'],
                playlist_data['color']
            )
            
            if playlist_id:
                # Obtener IDs de los tracks
                track_ids = [track['id'] for track in selected_tracks if 'id' in track]
                
                # Agregar tracks a la nueva playlist
                if track_ids:
                    success = self.playlist_service.add_tracks_to_playlist(playlist_id, track_ids)
                    
                    if success:
                        QMessageBox.information(
                            self, 
                            "Playlist Creada", 
                            f"Playlist '{playlist_data['name']}' creada exitosamente con {len(track_ids)} tracks."
                        )
                        # Emitir señal para refrescar el panel de playlists
                        self.playlist_created.emit()
                    else:
                        QMessageBox.warning(self, "Error", "No se pudieron agregar todos los tracks a la playlist.")
                else:
                    QMessageBox.warning(self, "Error", "No se encontraron tracks válidos para agregar.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo crear la playlist.")
    
    def add_tracks_to_existing_playlist(self, selected_tracks, playlist_id, playlist_name):
        """Agrega tracks a una playlist existente."""
        track_ids = [track['id'] for track in selected_tracks if 'id' in track]
        
        if track_ids:
            success = self.playlist_service.add_tracks_to_playlist(playlist_id, track_ids)
            
            if success:
                QMessageBox.information(
                    self, 
                    "Tracks Agregados", 
                    f"{len(track_ids)} tracks agregados a '{playlist_name}' exitosamente."
                )
                # Emitir señal para refrescar el panel de playlists
                self.playlist_created.emit()
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron agregar los tracks a '{playlist_name}'.")
        else:
            QMessageBox.warning(self, "Error", "No se encontraron tracks válidos para agregar.")
    
    def go_to_library(self):
        """Regresa a la vista de biblioteca completa."""
        self.load_all_tracks()
        self.set_context("library", "")
        self.show_status_message("Regresando a la biblioteca completa", 2000)
    
    def set_context(self, context_type, playlist_name=""):
        """Actualiza el contexto de navegación y la UI."""
        self.current_context = context_type
        self.current_playlist_name = playlist_name
        
        if context_type == "library":
            self.context_label.setText("📚 Biblioteca")
            self.home_btn.setVisible(False)  # Ocultar si ya estamos en biblioteca
        elif context_type == "playlist":
            self.context_label.setText(f"📋 {playlist_name}")
            self.home_btn.setVisible(True)   # Mostrar para poder regresar
    
    def load_playlist_tracks(self, track_ids, playlist_name):
        """Carga tracks de una playlist específica y actualiza contexto."""
        # Cargar tracks usando el método existente
        self.model.load_tracks(track_ids=track_ids)
        
        # Habilitar sorting después de cargar datos filtrados
        self.table_view.setSortingEnabled(True)
        
        # Auto-ajustar columnas
        self._auto_resize_columns()
        
        self.update_results_count()
        
        # Actualizar contexto de navegación
        self.set_context("playlist", playlist_name)
    
    def show_track_recommendations(self, track):
        """Muestra diálogo con recomendaciones de canciones compatibles."""
        try:
            print(f"🎯 Abriendo recomendaciones para: {track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')}")
            
            # Validar track antes de proceder
            if not track:
                QMessageBox.warning(self, "Error", "No se ha seleccionado ningún track.")
                return
            
            if not track.get('id'):
                QMessageBox.warning(self, "Error", "El track seleccionado no tiene un ID válido.")
                return
            
            # Verificar datos mínimos necesarios
            missing_data = []
            if not track.get('bpm') or track.get('bpm') <= 0:
                missing_data.append("BPM")
            if not track.get('key') or track.get('key') == 'Unknown':
                missing_data.append("Tonalidad")
            
            if missing_data:
                QMessageBox.information(
                    self, 
                    "Datos Incompletos", 
                    f"El track '{track.get('title', 'Unknown')}' no tiene datos completos para generar recomendaciones precisas.\n\n"
                    f"Faltan: {', '.join(missing_data)}\n\n"
                    f"Las recomendaciones se basarán en los datos disponibles."
                )
            
            from ui.components.recommendations_dialog import RecommendationsDialog
            
            dialog = RecommendationsDialog(track, self)
            dialog.track_selected.connect(self.track_selected.emit)  # Conectar señal para reproducir tracks recomendados
            dialog.show()
            
            print("✅ Diálogo de recomendaciones abierto")
            
        except ImportError as e:
            print(f"❌ Error importando RecommendationsDialog: {e}")
            QMessageBox.critical(self, "Error", "No se pudo cargar el módulo de recomendaciones.")
        except Exception as e:
            print(f"❌ Error mostrando recomendaciones: {e}")
            import traceback
            print(f"   Detalle: {traceback.format_exc()}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las recomendaciones:\n\n{str(e)}")

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