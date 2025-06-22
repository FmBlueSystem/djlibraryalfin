# ui/base/enhanced_track_model.py

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QFont, QBrush, QColor
import sqlite3
from typing import List, Dict, Optional


class EnhancedTrackModel(QAbstractTableModel):
    """Modelo mejorado para TrackList que trabaja con ColumnManager."""
    
    def __init__(self, db_connection, column_manager, parent=None):
        super().__init__(parent)
        self.db_conn = db_connection
        self.column_manager = column_manager
        self._data = []
        
        # Conectar a cambios de columnas
        self.column_manager.columnsChanged.connect(self._on_columns_changed)
    
    def _on_columns_changed(self):
        """Maneja cambios en la configuración de columnas."""
        # Notificar que la estructura de columnas cambió
        self.beginResetModel()
        self.endResetModel()
    
    def load_tracks(self, track_ids: Optional[List[int]] = None):
        """Carga tracks desde la base de datos."""
        print(f"🔄 EnhancedTrackModel: Iniciando carga de tracks (IDs: {track_ids})")
        self.beginResetModel()
        
        try:
            # Verificar conexión a la base de datos
            if not self.db_conn:
                print("❌ EnhancedTrackModel: No hay conexión a la base de datos")
                self._data = []
                self.endResetModel()
                return
            
            cursor = self.db_conn.cursor()
            
            # Obtener todas las columnas disponibles para optimizar la query
            all_columns = self.column_manager.get_all_columns()
            column_names = list(all_columns.keys())
            print(f"📊 EnhancedTrackModel: Cargando columnas: {column_names}")
            
            # Construir query con solo las columnas necesarias
            query = f"SELECT {', '.join(column_names)} FROM tracks"
            params = []

            if track_ids is not None:
                if not track_ids:
                    print("📭 EnhancedTrackModel: Lista de track_ids vacía, limpiando datos")
                    self._data = []
                    self.endResetModel()
                    return
                
                placeholders = ','.join('?' for _ in track_ids)
                query += f" WHERE id IN ({placeholders})"
                params = list(track_ids)
                print(f"🔍 EnhancedTrackModel: Query filtrada para {len(track_ids)} tracks específicos")
            else:
                print("🔍 EnhancedTrackModel: Query para todos los tracks")
            
            print(f"💾 EnhancedTrackModel: Ejecutando query: {query}")
            cursor.execute(query, params)
            
            # Convertir a diccionarios
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            self._data = [dict(zip(columns, row)) for row in rows]
            
            print(f"✅ EnhancedTrackModel: {len(self._data)} tracks cargados exitosamente")
            
        except sqlite3.Error as e:
            print(f"❌ EnhancedTrackModel: Error de SQLite al cargar tracks: {e}")
            self._data = []
        except Exception as e:
            print(f"❌ EnhancedTrackModel: Error general al cargar tracks: {e}")
            self._data = []
        finally:
            self.endResetModel()
            print(f"🔄 EnhancedTrackModel: Modelo reseteado, {len(self._data)} filas disponibles")
    
    def rowCount(self, parent=QModelIndex()):
        """Número de filas."""
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        """Número de columnas visibles."""
        return len(self.column_manager.get_visible_columns())
    
    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        """Datos para la vista."""
        if not index.isValid() or index.row() >= len(self._data):
            return None
        
        visible_columns = self.column_manager.get_visible_columns()
        if index.column() >= len(visible_columns):
            return None
        
        row_data = self._data[index.row()]
        column = visible_columns[index.column()]
        column_key = column.key
        
        if role == Qt.ItemDataRole.DisplayRole:
            value = row_data.get(column_key)
            return self.column_manager.format_cell_data(column_key, value)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Alineación basada en tipo de columna
            if column.alignment == 'center':
                return Qt.AlignmentFlag.AlignCenter
            elif column.alignment == 'right':
                return Qt.AlignmentFlag.AlignRight
            else:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        elif role == Qt.ItemDataRole.FontRole:
            # Fuente especial para ciertos tipos de datos
            if column.data_type in ['bpm', 'time', 'number']:
                font = QFont()
                font.setFamily("monospace")
                return font
        
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Colores de fondo especiales
            if column_key == 'key':
                # Color basado en la clave musical
                value = row_data.get(column_key, '')
                return self._get_key_color(value)
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Color de texto
            if column_key == 'bpm':
                value = row_data.get(column_key)
                return self._get_bpm_color(value)
        
        elif role == Qt.ItemDataRole.ToolTipRole:
            # Tooltip con información completa
            return self._get_tooltip(row_data, column_key)
        
        elif role == Qt.ItemDataRole.UserRole:
            # Datos completos del track para uso interno
            return row_data
        
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Datos del header."""
        if orientation != Qt.Orientation.Horizontal:
            return None
        
        visible_columns = self.column_manager.get_visible_columns()
        if section >= len(visible_columns):
            return None
        
        column = visible_columns[section]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return column.title
        
        elif role == Qt.ItemDataRole.ToolTipRole:
            return f"{column.title}\nTipo: {column.data_type}\nClick para ordenar"
        
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont()
            font.setBold(True)
            return font
        
        return None
    
    def sort(self, column, order):
        """
        NOTA: El sorting es manejado por QSortFilterProxyModel.
        Este método se mantiene por compatibilidad pero no hace nada.
        El proxy model maneja todo el ordenamiento automáticamente.
        """
        # No hacer nada - el QSortFilterProxyModel maneja el sorting
        pass
    
    def get_track_at(self, row: int) -> Optional[Dict]:
        """Obtiene los datos completos de un track por fila."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
    
    def update_track_data(self, row: int, data: Dict) -> bool:
        """Actualiza los datos de una fila específica."""
        if 0 <= row < len(self._data):
            self._data[row].update(data)
            # Notificar cambio en toda la fila
            start_index = self.index(row, 0)
            end_index = self.index(row, self.columnCount() - 1)
            self.dataChanged.emit(start_index, end_index)
            return True
        return False
    
    def _get_key_color(self, key_value: str) -> QBrush:
        """Obtiene color de fondo para claves musicales."""
        # Colores sutiles para diferentes familias de claves
        key_colors = {
            # Claves mayores - tonos cálidos
            'C': QColor(255, 245, 245),  # Rojo muy claro
            'D': QColor(255, 250, 240),  # Naranja muy claro
            'E': QColor(255, 255, 240),  # Amarillo muy claro
            'F': QColor(245, 255, 245),  # Verde muy claro
            'G': QColor(240, 250, 255),  # Azul muy claro
            'A': QColor(250, 240, 255),  # Violeta muy claro
            'B': QColor(255, 240, 250),  # Rosa muy claro
        }
        
        if key_value and len(key_value) > 0:
            main_key = key_value[0].upper()
            return QBrush(key_colors.get(main_key, QColor(250, 250, 250)))
        
        return QBrush(QColor(255, 255, 255))
    
    def _get_bpm_color(self, bpm_value) -> QBrush:
        """Obtiene color de texto para BPM basado en rango."""
        try:
            bpm = float(bpm_value or 0)
            if bpm == 0:
                return QBrush(QColor(150, 150, 150))  # Gris para sin BPM
            elif bpm < 100:
                return QBrush(QColor(100, 150, 200))  # Azul para BPM lento
            elif bpm < 130:
                return QBrush(QColor(50, 150, 50))    # Verde para BPM medio
            elif bpm < 160:
                return QBrush(QColor(200, 150, 50))   # Naranja para BPM alto
            else:
                return QBrush(QColor(200, 50, 50))    # Rojo para BPM muy alto
        except (ValueError, TypeError):
            return QBrush(QColor(150, 150, 150))
    
    def _get_tooltip(self, row_data: Dict, column_key: str) -> str:
        """Genera tooltip informativo para una celda."""
        base_info = f"Track: {row_data.get('title', 'N/A')}\n"
        base_info += f"Artista: {row_data.get('artist', 'N/A')}\n"
        
        if column_key == 'bpm':
            bpm = row_data.get('bpm')
            if bpm:
                base_info += f"BPM: {bpm}\n"
                try:
                    bpm_val = float(bpm)
                    if bpm_val < 100:
                        base_info += "Categoría: Lento"
                    elif bpm_val < 130:
                        base_info += "Categoría: Medio"
                    elif bpm_val < 160:
                        base_info += "Categoría: Rápido"
                    else:
                        base_info += "Categoría: Muy Rápido"
                except (ValueError, TypeError):
                    pass
        
        elif column_key == 'key':
            key = row_data.get('key')
            if key:
                base_info += f"Clave Musical: {key}\n"
                base_info += "Click para ver claves compatibles"
        
        elif column_key == 'duration':
            duration = row_data.get('duration')
            if duration:
                try:
                    seconds = float(duration)
                    minutes = int(seconds // 60)
                    secs = int(seconds % 60)
                    base_info += f"Duración: {minutes:02d}:{secs:02d} ({seconds:.1f}s)"
                except (ValueError, TypeError):
                    base_info += f"Duración: {duration}"
        
        return base_info.strip()
    
    # === DRAG & DROP SUPPORT ===
    
    def supportedDragActions(self):
        """Define las acciones de drag soportadas."""
        return Qt.DropAction.CopyAction
    
    def mimeTypes(self):
        """Define los tipos MIME soportados para drag & drop."""
        return ['application/x-djlibrarytrack-ids']
    
    def mimeData(self, indexes):
        """Genera datos MIME para drag & drop."""
        from PySide6.QtCore import QMimeData
        import json
        
        # Obtener filas únicas (evitar duplicados si múltiples columnas están seleccionadas)
        rows = list(set(index.row() for index in indexes if index.isValid()))
        
        # Obtener IDs de tracks
        track_ids = []
        track_info = []
        
        for row in rows:
            if 0 <= row < len(self._data):
                track = self._data[row]
                track_ids.append(track.get('id'))
                # Información básica para mostrar durante el drag
                track_info.append({
                    'id': track.get('id'),
                    'title': track.get('title', 'Unknown'),
                    'artist': track.get('artist', 'Unknown'),
                    'duration': track.get('duration', 0)
                })
        
        # Crear MIME data
        mime_data = QMimeData()
        
        # Datos principales (IDs para la base de datos)
        data = {
            'track_ids': track_ids,
            'track_info': track_info,
            'source': 'djlibrary'
        }
        
        mime_data.setData('application/x-djlibrarytrack-ids', json.dumps(data).encode('utf-8'))
        
        # Texto plano como fallback
        text_lines = []
        for info in track_info:
            text_lines.append(f"{info['artist']} - {info['title']}")
        
        mime_data.setText('\n'.join(text_lines))
        
        return mime_data