# ui/base/column_manager.py

from PySide6.QtCore import QObject, Signal, QSettings
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ColumnConfig:
    """Configuración de una columna individual."""
    key: str                # Clave única de la columna (ej: 'title', 'artist')
    title: str              # Título mostrado en el header
    visible: bool = True    # Si la columna está visible
    width: int = 100        # Ancho en píxeles
    min_width: int = 50     # Ancho mínimo
    max_width: int = 500    # Ancho máximo
    resizable: bool = True  # Si se puede redimensionar
    sortable: bool = True   # Si se puede ordenar
    data_type: str = 'text' # Tipo de datos: 'text', 'number', 'time', 'bpm', 'key'
    alignment: str = 'left' # Alineación: 'left', 'center', 'right'
    format_func: Optional[callable] = None  # Función para formatear datos


class ColumnManager(QObject):
    """Gestor de configuración de columnas para TrackListView."""
    
    # Señales para notificar cambios
    columnsChanged = Signal()
    columnVisibilityChanged = Signal(str, bool)  # key, visible
    columnWidthChanged = Signal(str, int)        # key, width
    columnOrderChanged = Signal(list)            # new order list
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("DjAlfin", "TrackList")
        self._columns = {}
        self._column_order = []
        self._setup_default_columns()
        self._load_settings()
    
    def _setup_default_columns(self):
        """Define las columnas por defecto del TrackList optimizadas para DJ workflow."""
        default_columns = [
            # Orden optimizado para DJs: información esencial primero
            ColumnConfig('title', 'Título', visible=True, width=200, min_width=120, max_width=400),
            ColumnConfig('artist', 'Artista', visible=True, width=160, min_width=100, max_width=300),
            ColumnConfig('bpm', 'BPM', visible=True, width=70, min_width=50, max_width=100, 
                        data_type='bpm', alignment='center', format_func=self._format_bpm),
            ColumnConfig('key', 'Key', visible=True, width=50, min_width=40, max_width=80,
                        data_type='key', alignment='center'),
            ColumnConfig('genre', 'Género', visible=True, width=120, min_width=80, max_width=180),
            ColumnConfig('album', 'Álbum', visible=True, width=150, min_width=100, max_width=300),
            ColumnConfig('duration', 'Duración', visible=True, width=80, min_width=60, max_width=120,
                        data_type='time', alignment='center', format_func=self._format_duration),
            
            # Columnas adicionales (ocultas por defecto)
            ColumnConfig('id', 'ID', visible=False, width=50, sortable=True, data_type='number'),
            ColumnConfig('year', 'Año', visible=False, width=60, min_width=50, max_width=80,
                        data_type='number', alignment='center'),
            ColumnConfig('play_count', 'Reproducciones', visible=False, width=100, min_width=60, max_width=150,
                        data_type='number', alignment='center'),
            ColumnConfig('comment', 'Comentario', visible=False, width=200, min_width=100, max_width=300),
            ColumnConfig('file_path', 'Archivo', visible=False, width=300, min_width=200, max_width=600),
        ]
        
        for col in default_columns:
            self._columns[col.key] = col
            
        self._column_order = [col.key for col in default_columns]
    
    def _format_bpm(self, value):
        """Formatea valores de BPM."""
        if not value:
            return ""
        try:
            bpm_val = float(value)
            return f"{bpm_val:.1f}" if bpm_val > 0 else ""
        except (ValueError, TypeError):
            return str(value) if value else ""
    
    def _format_duration(self, value):
        """Formatea duración de segundos a MM:SS."""
        if not value:
            return ""
        try:
            total_seconds = float(value)
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            return f"{minutes:02d}:{seconds:02d}"
        except (ValueError, TypeError):
            return str(value) if value else ""
    
    def get_column(self, key: str) -> Optional[ColumnConfig]:
        """Obtiene configuración de una columna por su clave."""
        return self._columns.get(key)
    
    def get_all_columns(self) -> Dict[str, ColumnConfig]:
        """Obtiene todas las columnas disponibles."""
        return self._columns.copy()
    
    def get_visible_columns(self) -> List[ColumnConfig]:
        """Obtiene solo las columnas visibles en orden."""
        return [self._columns[key] for key in self._column_order 
                if key in self._columns and self._columns[key].visible]
    
    def get_column_order(self) -> List[str]:
        """Obtiene el orden actual de las columnas."""
        return self._column_order.copy()
    
    def set_column_visible(self, key: str, visible: bool):
        """Establece la visibilidad de una columna."""
        if key in self._columns:
            self._columns[key].visible = visible
            self.columnVisibilityChanged.emit(key, visible)
            self.columnsChanged.emit()
            self._save_settings()
    
    def set_column_width(self, key: str, width: int):
        """Establece el ancho de una columna."""
        if key in self._columns:
            col = self._columns[key]
            width = max(col.min_width, min(width, col.max_width))
            col.width = width
            self.columnWidthChanged.emit(key, width)
            self._save_settings()
    
    def set_column_order(self, new_order: List[str]):
        """Establece un nuevo orden para las columnas."""
        # Validar que todas las claves existan
        valid_keys = [key for key in new_order if key in self._columns]
        if len(valid_keys) == len(self._columns):
            self._column_order = valid_keys
            self.columnOrderChanged.emit(valid_keys)
            self.columnsChanged.emit()
            self._save_settings()
    
    def move_column(self, from_index: int, to_index: int):
        """Mueve una columna de una posición a otra."""
        if 0 <= from_index < len(self._column_order) and 0 <= to_index < len(self._column_order):
            key = self._column_order.pop(from_index)
            self._column_order.insert(to_index, key)
            self.columnOrderChanged.emit(self._column_order)
            self.columnsChanged.emit()
            self._save_settings()
    
    def reset_to_defaults(self):
        """Restaura la configuración por defecto."""
        self._setup_default_columns()
        self.columnsChanged.emit()
        self._save_settings()
    
    def auto_size_column(self, key: str, content_width: int):
        """Auto-ajusta el ancho de una columna basado en contenido."""
        if key in self._columns:
            col = self._columns[key]
            # Agregar padding al contenido
            adjusted_width = content_width + 20
            width = max(col.min_width, min(adjusted_width, col.max_width))
            self.set_column_width(key, width)
    
    def _save_settings(self):
        """Guarda la configuración actual en QSettings."""
        self.settings.beginGroup("Columns")
        
        # Guardar orden de columnas
        self.settings.setValue("order", self._column_order)
        
        # Guardar configuración de cada columna
        for key, col in self._columns.items():
            self.settings.beginGroup(key)
            self.settings.setValue("visible", col.visible)
            self.settings.setValue("width", col.width)
            self.settings.endGroup()
        
        self.settings.endGroup()
    
    def _load_settings(self):
        """Carga la configuración guardada desde QSettings."""
        self.settings.beginGroup("Columns")
        
        # Cargar orden de columnas
        saved_order = self.settings.value("order", self._column_order)
        if saved_order and isinstance(saved_order, list):
            # Validar que todas las claves existan
            valid_order = [key for key in saved_order if key in self._columns]
            if len(valid_order) == len(self._columns):
                self._column_order = valid_order
        
        # Cargar configuración de cada columna
        for key in self._columns:
            if self.settings.childGroups():
                self.settings.beginGroup(key)
                
                # Cargar visibilidad
                visible = self.settings.value("visible", self._columns[key].visible)
                if isinstance(visible, str):
                    visible = visible.lower() == 'true'
                self._columns[key].visible = bool(visible)
                
                # Cargar ancho
                width = self.settings.value("width", self._columns[key].width)
                try:
                    width = int(width)
                    col = self._columns[key]
                    width = max(col.min_width, min(width, col.max_width))
                    self._columns[key].width = width
                except (ValueError, TypeError):
                    pass
                
                self.settings.endGroup()
        
        self.settings.endGroup()
    
    def get_column_headers(self) -> List[str]:
        """Obtiene los títulos de las columnas visibles en orden."""
        return [self._columns[key].title for key in self._column_order 
                if key in self._columns and self._columns[key].visible]
    
    def get_column_keys(self) -> List[str]:
        """Obtiene las claves de las columnas visibles en orden."""
        return [key for key in self._column_order 
                if key in self._columns and self._columns[key].visible]
    
    def format_cell_data(self, key: str, value) -> str:
        """Formatea el contenido de una celda según su tipo de columna."""
        if key not in self._columns:
            return str(value) if value else ""
        
        col = self._columns[key]
        if col.format_func:
            return col.format_func(value)
        
        return str(value) if value else ""