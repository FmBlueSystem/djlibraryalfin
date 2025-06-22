"""Service layer for smart playlist operations."""

from core.smart_playlist_engine import SmartPlaylistEngine
from core.database import get_db_path
import sqlite3
import json
from typing import List, Optional, Dict, Any


class PlaylistService:
    """Simplified high level interface for managing playlists."""

    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        self.engine = SmartPlaylistEngine(self.db_path)

    def list_playlists(self):
        """Return a list of (id, name) tuples for all playlists."""
        return self.engine.get_playlists()

    def get_playlist_details(self, playlist_id):
        """Return rules and match_all flag for a given playlist."""
        return self.engine.get_playlist_details(playlist_id)

    def save_playlist(self, name, rules, match_all):
        """Create or update a smart playlist."""
        return self.engine.save_playlist(name, rules, match_all)

    def get_tracks(self, rules, match_all=True):
        """Return track IDs matching the given rules."""
        return self.engine.get_tracks_for_rules(rules, match_all)

    def fetch_track_info(self, track_ids):
        """Return basic info for provided track IDs."""
        if not track_ids:
            return []
        import sqlite3
        from core.database import create_connection

        conn = create_connection()
        if not conn:
            return []
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        placeholders = ','.join('?' for _ in track_ids)
        query = f"SELECT id, title, artist, bpm, key, genre FROM tracks WHERE id IN ({placeholders})"
        cursor.execute(query, list(track_ids))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_all_playlists(self):
        """Return all regular playlists (not smart playlists)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.created_date, p.modified_date,
                       p.track_count, p.duration, p.is_favorite, p.color
                FROM playlists p
                ORDER BY p.name
            """)
            
            playlists = []
            for row in cursor.fetchall():
                playlist = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'created_date': row[3],
                    'modified_date': row[4],
                    'track_count': row[5],
                    'duration': row[6],
                    'is_favorite': bool(row[7]),
                    'color': row[8],
                    'type': 'regular'
                }
                playlists.append(playlist)
            
            conn.close()
            return playlists
            
        except sqlite3.Error as e:
            print(f"❌ Error cargando playlists regulares: {e}")
            return []
    
    def get_smart_playlists(self):
        """Return all smart playlists with basic info."""
        try:
            playlists = self.list_playlists()  # Retorna (id, name) tuples
            smart_playlists = []
            
            for playlist_id, name in playlists:
                playlist_info = self.get_playlist_info(playlist_id)
                if playlist_info:
                    # Obtener cantidad de tracks que coinciden
                    try:
                        track_ids = self.get_tracks(playlist_info['rules'], playlist_info['match_all'])
                        track_count = len(track_ids) if track_ids else 0
                    except:
                        track_count = 0
                    
                    smart_playlists.append({
                        'id': playlist_id,
                        'name': name,
                        'track_count': track_count,
                        'criteria': f"{len(playlist_info['rules'])} reglas"
                    })
            
            return smart_playlists
        except Exception as e:
            print(f"Error al obtener smart playlists: {e}")
            return []
    
    # === REGULAR PLAYLISTS CRUD OPERATIONS ===
    
    def create_playlist(self, name, description="", color="#2196F3"):
        """Create a new regular playlist."""
        try:
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO playlists (name, description, created_date, modified_date, color)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, current_time, current_time, color))
            
            playlist_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✅ Playlist '{name}' creada con ID: {playlist_id}")
            return playlist_id
            
        except sqlite3.IntegrityError:
            print(f"❌ Error: Ya existe una playlist con el nombre '{name}'")
            return None
        except sqlite3.Error as e:
            print(f"❌ Error creando playlist: {e}")
            return None
    
    def delete_playlist(self, playlist_id):
        """Delete a regular playlist and all its tracks."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener nombre para logging
            cursor.execute("SELECT name FROM playlists WHERE id = ?", (playlist_id,))
            result = cursor.fetchone()
            if not result:
                print(f"❌ Playlist con ID {playlist_id} no encontrada")
                conn.close()
                return False
            
            playlist_name = result[0]
            
            # Eliminar playlist (CASCADE eliminará automáticamente los tracks)
            cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                print(f"✅ Playlist '{playlist_name}' eliminada correctamente")
                return True
            else:
                conn.close()
                print(f"❌ No se pudo eliminar la playlist")
                return False
                
        except sqlite3.Error as e:
            print(f"❌ Error eliminando playlist: {e}")
            return False
    
    def rename_playlist(self, playlist_id, new_name):
        """Rename a regular playlist."""
        try:
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                UPDATE playlists 
                SET name = ?, modified_date = ?
                WHERE id = ?
            """, (new_name, current_time, playlist_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                print(f"✅ Playlist renombrada a '{new_name}'")
                return True
            else:
                conn.close()
                print(f"❌ Playlist con ID {playlist_id} no encontrada")
                return False
                
        except sqlite3.IntegrityError:
            print(f"❌ Error: Ya existe una playlist con el nombre '{new_name}'")
            return False
        except sqlite3.Error as e:
            print(f"❌ Error renombrando playlist: {e}")
            return False
    
    def add_tracks_to_playlist(self, playlist_id, track_ids):
        """Add tracks to a regular playlist."""
        if not track_ids:
            return True
            
        try:
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            # Obtener la última posición en la playlist
            cursor.execute("""
                SELECT COALESCE(MAX(position), 0) FROM playlist_tracks 
                WHERE playlist_id = ?
            """, (playlist_id,))
            last_position = cursor.fetchone()[0]
            
            # Agregar tracks evitando duplicados
            added_count = 0
            for i, track_id in enumerate(track_ids):
                try:
                    position = last_position + i + 1
                    cursor.execute("""
                        INSERT INTO playlist_tracks (playlist_id, track_id, position, added_date)
                        VALUES (?, ?, ?, ?)
                    """, (playlist_id, track_id, position, current_time))
                    added_count += 1
                except sqlite3.IntegrityError:
                    # Track ya está en la playlist, ignorar
                    continue
            
            # Actualizar estadísticas de la playlist
            self._update_playlist_stats(cursor, playlist_id)
            
            conn.commit()
            conn.close()
            
            print(f"✅ {added_count} tracks agregados a la playlist")
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Error agregando tracks a playlist: {e}")
            return False
    
    def remove_tracks_from_playlist(self, playlist_id, track_ids):
        """Remove tracks from a regular playlist."""
        if not track_ids:
            return True
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Eliminar tracks
            placeholders = ','.join('?' * len(track_ids))
            cursor.execute(f"""
                DELETE FROM playlist_tracks 
                WHERE playlist_id = ? AND track_id IN ({placeholders})
            """, [playlist_id] + track_ids)
            
            removed_count = cursor.rowcount
            
            # Reordenar posiciones
            cursor.execute("""
                SELECT id FROM playlist_tracks 
                WHERE playlist_id = ? 
                ORDER BY position
            """, (playlist_id,))
            
            for i, (pt_id,) in enumerate(cursor.fetchall(), 1):
                cursor.execute("""
                    UPDATE playlist_tracks SET position = ? WHERE id = ?
                """, (i, pt_id))
            
            # Actualizar estadísticas
            self._update_playlist_stats(cursor, playlist_id)
            
            conn.commit()
            conn.close()
            
            print(f"✅ {removed_count} tracks eliminados de la playlist")
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Error eliminando tracks de playlist: {e}")
            return False
    
    def get_playlist_tracks(self, playlist_id):
        """Get all tracks in a regular playlist in order."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT t.id, t.title, t.artist, t.album, t.genre, t.duration, 
                       t.bpm, t.key, t.file_path, pt.position, pt.added_date
                FROM playlist_tracks pt
                JOIN tracks t ON pt.track_id = t.id
                WHERE pt.playlist_id = ?
                ORDER BY pt.position
            """, (playlist_id,))
            
            tracks = []
            for row in cursor.fetchall():
                track = {
                    'id': row[0], 'title': row[1], 'artist': row[2], 'album': row[3],
                    'genre': row[4], 'duration': row[5], 'bpm': row[6], 'key': row[7],
                    'file_path': row[8], 'position': row[9], 'added_date': row[10]
                }
                tracks.append(track)
            
            conn.close()
            return tracks
            
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo tracks de playlist: {e}")
            return []
    
    def reorder_playlist_tracks(self, playlist_id, old_position, new_position):
        """Reorder tracks within a playlist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener el track a mover
            cursor.execute("""
                SELECT id FROM playlist_tracks 
                WHERE playlist_id = ? AND position = ?
            """, (playlist_id, old_position))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            track_to_move_id = result[0]
            
            # Actualizar posiciones
            if old_position < new_position:
                # Mover hacia abajo: decrementar posiciones intermedias
                cursor.execute("""
                    UPDATE playlist_tracks 
                    SET position = position - 1 
                    WHERE playlist_id = ? AND position > ? AND position <= ?
                """, (playlist_id, old_position, new_position))
            else:
                # Mover hacia arriba: incrementar posiciones intermedias
                cursor.execute("""
                    UPDATE playlist_tracks 
                    SET position = position + 1 
                    WHERE playlist_id = ? AND position >= ? AND position < ?
                """, (playlist_id, new_position, old_position))
            
            # Establecer nueva posición para el track movido
            cursor.execute("""
                UPDATE playlist_tracks 
                SET position = ? 
                WHERE id = ?
            """, (new_position, track_to_move_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Track reordenado de posición {old_position} a {new_position}")
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Error reordenando tracks: {e}")
            return False
    
    def _update_playlist_stats(self, cursor, playlist_id):
        """Update playlist statistics (track count and total duration)."""
        from datetime import datetime
        
        # Calcular estadísticas
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(t.duration), 0)
            FROM playlist_tracks pt
            JOIN tracks t ON pt.track_id = t.id
            WHERE pt.playlist_id = ?
        """, (playlist_id,))
        
        track_count, total_duration = cursor.fetchone()
        current_time = datetime.now().isoformat()
        
        # Actualizar estadísticas
        cursor.execute("""
            UPDATE playlists 
            SET track_count = ?, duration = ?, modified_date = ?
            WHERE id = ?
        """, (track_count, total_duration, current_time, playlist_id))
    
    def get_playlist_info(self, playlist_id):
        """Get playlist info for both regular and smart playlists."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try regular playlist first
            cursor.execute("""
                SELECT name, description, track_count, duration, 'regular' as type
                FROM playlists WHERE id = ?
            """, (playlist_id,))
            
            result = cursor.fetchone()
            if result:
                conn.close()
                return {
                    'id': playlist_id, 'name': result[0], 'description': result[1],
                    'track_count': result[2], 'duration': result[3], 'type': result[4]
                }
            
            # Try smart playlist
            cursor.execute("""
                SELECT name, rules, match_all, 'smart' as type
                FROM smart_playlists WHERE id = ?
            """, (playlist_id,))
            
            result = cursor.fetchone()
            if result:
                conn.close()
                return {
                    'id': playlist_id, 'name': result[0], 'type': result[3],
                    'rules': json.loads(result[1]), 'match_all': bool(result[2])
                }
            
            conn.close()
            return None
            
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo info de playlist: {e}")
            return None
