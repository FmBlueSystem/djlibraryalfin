"""Service layer for smart playlist operations."""

from core.smart_playlist_engine import SmartPlaylistEngine
from core.database import get_db_path


class PlaylistService:
    """Provide a high level interface for managing smart playlists."""

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
    def get_playlist_info(self, playlist_id):
        """Return playlist name, rules list and match_all flag."""
        import sqlite3
        from core.database import create_connection

        conn = create_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, rules, match_all FROM smart_playlists WHERE id = ?",
            (playlist_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            name, rules_json, match_all = row
            import json
            return {
                "id": playlist_id,
                "name": name,
                "rules": json.loads(rules_json),
                "match_all": bool(match_all),
            }
        return None
