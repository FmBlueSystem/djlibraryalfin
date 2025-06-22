#!/usr/bin/env python3
"""
Playlist Importer/Exporter - DjAlfin
Sistema para importar y exportar playlists en formatos M3U, PLS y JSON.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PySide6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from services.playlist_service import PlaylistService


class PlaylistExportWorker(QThread):
    """Worker thread para exportar playlists sin bloquear la UI."""
    
    progressUpdated = Signal(int, str)  # current, message
    finished = Signal(bool, str)  # success, result_path_or_error
    
    def __init__(self, playlist_service, playlist_id, file_path, format_type):
        super().__init__()
        self.playlist_service = playlist_service
        self.playlist_id = playlist_id
        self.file_path = file_path
        self.format_type = format_type.lower()
    
    def run(self):
        """Ejecuta la exportación en segundo plano."""
        try:
            # Obtener información de la playlist
            self.progressUpdated.emit(10, "Obteniendo información de playlist...")
            playlist_info = self.playlist_service.get_playlist_info(self.playlist_id)
            
            if not playlist_info:
                self.finished.emit(False, "Playlist no encontrada")
                return
            
            # Obtener tracks
            self.progressUpdated.emit(30, "Obteniendo tracks...")
            tracks = self.playlist_service.get_playlist_tracks(self.playlist_id)
            
            if not tracks:
                self.finished.emit(False, "La playlist está vacía")
                return
            
            # Exportar según formato
            self.progressUpdated.emit(50, f"Exportando en formato {self.format_type.upper()}...")
            
            if self.format_type == 'm3u':
                success = self._export_m3u(playlist_info, tracks)
            elif self.format_type == 'pls':
                success = self._export_pls(playlist_info, tracks)
            elif self.format_type == 'json':
                success = self._export_json(playlist_info, tracks)
            else:
                self.finished.emit(False, f"Formato {self.format_type} no soportado")
                return
            
            self.progressUpdated.emit(100, "Exportación completada")
            
            if success:
                self.finished.emit(True, self.file_path)
            else:
                self.finished.emit(False, "Error escribiendo archivo")
                
        except Exception as e:
            self.finished.emit(False, f"Error durante exportación: {str(e)}")
    
    def _export_m3u(self, playlist_info, tracks):
        """Exporta en formato M3U."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write(f"#PLAYLIST:{playlist_info['name']}\n")
                
                for track in tracks:
                    # Línea de información extendida
                    duration = int(float(track.get('duration', 0)))
                    artist = track.get('artist', 'Unknown Artist')
                    title = track.get('title', 'Unknown Title')
                    f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                    
                    # Ruta del archivo
                    file_path = track.get('file_path', '')
                    if file_path and os.path.exists(file_path):
                        f.write(f"{file_path}\n")
                    else:
                        f.write(f"# MISSING: {file_path}\n")
            
            return True
        except Exception as e:
            print(f"Error exportando M3U: {e}")
            return False
    
    def _export_pls(self, playlist_info, tracks):
        """Exporta en formato PLS."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write("[playlist]\n")
                f.write(f"NumberOfEntries={len(tracks)}\n")
                
                for i, track in enumerate(tracks, 1):
                    file_path = track.get('file_path', '')
                    title = f"{track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}"
                    duration = int(float(track.get('duration', 0)))
                    
                    f.write(f"File{i}={file_path}\n")
                    f.write(f"Title{i}={title}\n")
                    f.write(f"Length{i}={duration}\n")
                
                f.write("Version=2\n")
            
            return True
        except Exception as e:
            print(f"Error exportando PLS: {e}")
            return False
    
    def _export_json(self, playlist_info, tracks):
        """Exporta en formato JSON (DjAlfin nativo)."""
        try:
            export_data = {
                'playlist_info': playlist_info,
                'tracks': tracks,
                'export_timestamp': QTimer().singleShot.__class__.__name__,  # Simple timestamp
                'format_version': '1.0',
                'exported_by': 'DjAlfin'
            }
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exportando JSON: {e}")
            return False


class PlaylistImporter(QObject):
    """Clase para importar playlists desde archivos externos."""
    
    importProgress = Signal(int, str)  # progress, message
    importFinished = Signal(bool, str, int)  # success, message, playlist_id
    
    def __init__(self, playlist_service: PlaylistService):
        super().__init__()
        self.playlist_service = playlist_service
    
    def import_playlist_file(self, file_path: str, playlist_name: str = None) -> Tuple[bool, str, Optional[int]]:
        """Importa una playlist desde archivo."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, "Archivo no encontrado", None
        
        # Determinar formato por extensión
        format_type = file_path.suffix.lower()
        
        try:
            if format_type == '.m3u':
                return self._import_m3u(file_path, playlist_name)
            elif format_type == '.pls':
                return self._import_pls(file_path, playlist_name)
            elif format_type == '.json':
                return self._import_json(file_path, playlist_name)
            else:
                return False, f"Formato {format_type} no soportado", None
                
        except Exception as e:
            return False, f"Error importando: {str(e)}", None
    
    def _import_m3u(self, file_path: Path, playlist_name: str = None) -> Tuple[bool, str, Optional[int]]:
        """Importa playlist M3U."""
        if not playlist_name:
            playlist_name = file_path.stem
        
        tracks_to_import = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]
            
            current_track_info = {}
            
            for line in lines:
                if line.startswith('#EXTM3U'):
                    continue
                elif line.startswith('#PLAYLIST:'):
                    if not playlist_name:
                        playlist_name = line.split(':', 1)[1].strip()
                elif line.startswith('#EXTINF:'):
                    # Parsear información del track
                    parts = line.split(':', 1)[1].split(',', 1)
                    if len(parts) == 2:
                        duration = parts[0].strip()
                        title_part = parts[1].strip()
                        
                        # Intentar separar artista y título
                        if ' - ' in title_part:
                            artist, title = title_part.split(' - ', 1)
                            current_track_info = {
                                'duration': duration,
                                'artist': artist.strip(),
                                'title': title.strip()
                            }
                        else:
                            current_track_info = {
                                'duration': duration,
                                'title': title_part
                            }
                elif line and not line.startswith('#'):
                    # Ruta del archivo
                    if os.path.exists(line):
                        # Buscar el track en la base de datos por file_path
                        track_id = self._find_track_by_path(line)
                        if track_id:
                            tracks_to_import.append(track_id)
                    
                    current_track_info = {}
            
            # Crear playlist e importar tracks
            playlist_id = self.playlist_service.create_playlist(
                name=playlist_name,
                description=f"Importada desde {file_path.name}"
            )
            
            if playlist_id and tracks_to_import:
                success = self.playlist_service.add_tracks_to_playlist(playlist_id, tracks_to_import)
                if success:
                    return True, f"Importados {len(tracks_to_import)} tracks", playlist_id
                else:
                    return False, "Error agregando tracks a playlist", playlist_id
            elif playlist_id:
                return True, "Playlist creada pero sin tracks válidos encontrados", playlist_id
            else:
                return False, "Error creando playlist", None
                
        except Exception as e:
            return False, f"Error leyendo archivo M3U: {str(e)}", None
    
    def _import_pls(self, file_path: Path, playlist_name: str = None) -> Tuple[bool, str, Optional[int]]:
        """Importa playlist PLS."""
        if not playlist_name:
            playlist_name = file_path.stem
        
        tracks_to_import = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]
            
            file_paths = {}
            
            for line in lines:
                if line.startswith('File'):
                    # File1=/path/to/file
                    num = line.split('=')[0][4:]  # Obtener número
                    path = line.split('=', 1)[1]
                    file_paths[num] = path
            
            # Buscar tracks en la base de datos
            for file_path in file_paths.values():
                if os.path.exists(file_path):
                    track_id = self._find_track_by_path(file_path)
                    if track_id:
                        tracks_to_import.append(track_id)
            
            # Crear playlist e importar tracks
            playlist_id = self.playlist_service.create_playlist(
                name=playlist_name,
                description=f"Importada desde {file_path.name}"
            )
            
            if playlist_id and tracks_to_import:
                success = self.playlist_service.add_tracks_to_playlist(playlist_id, tracks_to_import)
                if success:
                    return True, f"Importados {len(tracks_to_import)} tracks", playlist_id
                else:
                    return False, "Error agregando tracks a playlist", playlist_id
            elif playlist_id:
                return True, "Playlist creada pero sin tracks válidos encontrados", playlist_id
            else:
                return False, "Error creando playlist", None
                
        except Exception as e:
            return False, f"Error leyendo archivo PLS: {str(e)}", None
    
    def _import_json(self, file_path: Path, playlist_name: str = None) -> Tuple[bool, str, Optional[int]]:
        """Importa playlist JSON (formato DjAlfin)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            playlist_info = data.get('playlist_info', {})
            tracks = data.get('tracks', [])
            
            if not playlist_name:
                playlist_name = playlist_info.get('name', file_path.stem)
            
            # Buscar tracks en la base de datos
            track_ids = []
            for track in tracks:
                file_path_track = track.get('file_path')
                if file_path_track and os.path.exists(file_path_track):
                    track_id = self._find_track_by_path(file_path_track)
                    if track_id:
                        track_ids.append(track_id)
            
            # Crear playlist
            playlist_id = self.playlist_service.create_playlist(
                name=playlist_name,
                description=playlist_info.get('description', f"Importada desde {file_path.name}"),
                color=playlist_info.get('color', '#2196F3')
            )
            
            if playlist_id and track_ids:
                success = self.playlist_service.add_tracks_to_playlist(playlist_id, track_ids)
                if success:
                    return True, f"Importados {len(track_ids)} tracks", playlist_id
                else:
                    return False, "Error agregando tracks a playlist", playlist_id
            elif playlist_id:
                return True, "Playlist creada pero sin tracks válidos encontrados", playlist_id
            else:
                return False, "Error creando playlist", None
                
        except Exception as e:
            return False, f"Error leyendo archivo JSON: {str(e)}", None
    
    def _find_track_by_path(self, file_path: str) -> Optional[int]:
        """Busca un track en la base de datos por su file_path."""
        try:
            # Usar el servicio de playlist para acceder a la base de datos
            # Esto requeriría agregar un método al PlaylistService
            # Por ahora, simulamos la búsqueda
            import sqlite3
            from core.database import get_db_path
            
            with sqlite3.connect(get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM tracks WHERE file_path = ?", (file_path,))
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            print(f"Error buscando track por path: {e}")
            return None


class PlaylistExporter(QObject):
    """Clase para exportar playlists a archivos externos."""
    
    exportProgress = Signal(int, str)  # progress, message
    exportFinished = Signal(bool, str)  # success, result_path_or_error
    
    def __init__(self, playlist_service: PlaylistService):
        super().__init__()
        self.playlist_service = playlist_service
        self.export_worker = None
    
    def export_playlist(self, playlist_id: int, parent_widget=None) -> bool:
        """Inicia el proceso de exportación de playlist."""
        try:
            # Obtener información de la playlist
            playlist_info = self.playlist_service.get_playlist_info(playlist_id)
            if not playlist_info:
                QMessageBox.warning(parent_widget, "Error", "Playlist no encontrada")
                return False
            
            playlist_name = playlist_info['name']
            
            # Diálogo para seleccionar archivo y formato
            file_path, selected_filter = QFileDialog.getSaveFileName(
                parent_widget,
                f"Exportar Playlist '{playlist_name}'",
                f"{playlist_name}.m3u",
                "M3U Playlist (*.m3u);;PLS Playlist (*.pls);;JSON DjAlfin (*.json)"
            )
            
            if not file_path:
                return False
            
            # Determinar formato por filtro seleccionado
            if 'M3U' in selected_filter:
                format_type = 'm3u'
            elif 'PLS' in selected_filter:
                format_type = 'pls'
            elif 'JSON' in selected_filter:
                format_type = 'json'
            else:
                # Determinar por extensión
                ext = Path(file_path).suffix.lower()
                format_type = ext[1:] if ext else 'm3u'
            
            # Crear y configurar worker thread
            self.export_worker = PlaylistExportWorker(
                self.playlist_service, playlist_id, file_path, format_type
            )
            
            # Crear diálogo de progreso
            progress_dialog = QProgressDialog(
                f"Exportando playlist '{playlist_name}'...",
                "Cancelar", 0, 100, parent_widget
            )
            progress_dialog.setWindowTitle("Exportando Playlist")
            progress_dialog.setModal(True)
            
            # Conectar señales
            self.export_worker.progressUpdated.connect(
                lambda value, message: (
                    progress_dialog.setValue(value),
                    progress_dialog.setLabelText(message)
                )
            )
            
            self.export_worker.finished.connect(
                lambda success, result: self._export_finished(
                    success, result, progress_dialog, parent_widget
                )
            )
            
            progress_dialog.canceled.connect(self.export_worker.terminate)
            
            # Iniciar exportación
            self.export_worker.start()
            progress_dialog.show()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", f"Error iniciando exportación: {str(e)}")
            return False
    
    def _export_finished(self, success: bool, result: str, progress_dialog, parent_widget):
        """Maneja el final de la exportación."""
        progress_dialog.close()
        
        if success:
            QMessageBox.information(
                parent_widget, 
                "Exportación Exitosa", 
                f"Playlist exportada correctamente a:\n{result}"
            )
            self.exportFinished.emit(True, result)
        else:
            QMessageBox.critical(
                parent_widget, 
                "Error de Exportación", 
                f"Error exportando playlist:\n{result}"
            )
            self.exportFinished.emit(False, result)
        
        # Limpiar worker
        if self.export_worker:
            self.export_worker.deleteLater()
            self.export_worker = None