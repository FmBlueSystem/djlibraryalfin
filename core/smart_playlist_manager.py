"""
Smart Playlist Manager for DjAlfin
Handles intelligent playlist generation based on various criteria.
Enhanced version with advanced features and better query handling.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta


class PlaylistCriteria(Enum):
    """Criteria types for smart playlists."""
    GENRE = "genre"
    ARTIST = "artist"
    ALBUM = "album"
    TITLE = "title"
    YEAR = "year"
    BPM = "bpm"
    DURATION = "duration"
    BITRATE = "bitrate"
    SAMPLE_RATE = "sample_rate"
    RECENTLY_PLAYED = "recently_played"
    MOST_PLAYED = "most_played"
    NEVER_PLAYED = "never_played"
    PLAY_COUNT = "play_count"
    LAST_PLAYED = "last_played"
    DATE_ADDED = "date_added"
    FILE_SIZE = "file_size"
    RATING = "rating"
    KEY = "key"  # Musical key
    ENERGY = "energy"  # Energy level (if available)


class ComparisonOperator(Enum):
    """Comparison operators for playlist criteria."""
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    NOT_EQUALS = "not_equals"
    NOT_CONTAINS = "not_contains"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IN_LAST_DAYS = "in_last_days"
    NOT_IN_LAST_DAYS = "not_in_last_days"


class LogicalOperator(Enum):
    """Logical operators for combining rules."""
    AND = "and"
    OR = "or"


@dataclass
class PlaylistRule:
    """Represents a single rule for a smart playlist."""
    criteria: PlaylistCriteria
    operator: ComparisonOperator
    value: Any
    value2: Optional[Any] = None  # For BETWEEN operator
    logical_operator: LogicalOperator = LogicalOperator.AND


@dataclass
class SmartPlaylist:
    """Represents a smart playlist with its rules."""
    name: str
    rules: List[PlaylistRule]
    limit: Optional[int] = None
    order_by: Optional[str] = None
    order_desc: bool = False
    match_all: bool = True  # True for AND logic, False for OR logic
    auto_update: bool = True
    description: Optional[str] = None


class SmartPlaylistManager:
    """Enhanced smart playlist manager with advanced features."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_smart_playlist_tables()
        self._create_playback_history_table()
    
    def _create_smart_playlist_tables(self) -> None:
        """Create tables for storing smart playlists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS smart_playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    limit_count INTEGER,
                    order_by TEXT,
                    order_desc BOOLEAN DEFAULT FALSE,
                    match_all BOOLEAN DEFAULT TRUE,
                    auto_update BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS smart_playlist_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER,
                    criteria TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    value TEXT NOT NULL,
                    value2 TEXT,
                    logical_operator TEXT DEFAULT 'and',
                    rule_order INTEGER DEFAULT 0,
                    FOREIGN KEY (playlist_id) REFERENCES smart_playlists (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
    
    def _create_playback_history_table(self) -> None:
        """Create table for tracking playback history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS playback_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_played INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (file_path) REFERENCES tracks (file_path) ON DELETE CASCADE
                )
            """)
            
            # Create index for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_playback_history_file_path 
                ON playback_history (file_path)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_playback_history_played_at 
                ON playback_history (played_at)
            """)
            
            conn.commit()
    
    def record_playback(self, file_path: str, duration_played: int = 0, completed: bool = False) -> None:
        """Record a track playback in the history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO playback_history (file_path, duration_played, completed)
                VALUES (?, ?, ?)
            """, (file_path, duration_played, completed))
            conn.commit()
    
    def get_play_count(self, file_path: str) -> int:
        """Get the play count for a specific track."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM playback_history 
                WHERE file_path = ? AND completed = TRUE
            """, (file_path,))
            return cursor.fetchone()[0]
    
    def get_last_played(self, file_path: str) -> Optional[datetime]:
        """Get the last played timestamp for a specific track."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(played_at) FROM playback_history 
                WHERE file_path = ?
            """, (file_path,))
            result = cursor.fetchone()[0]
            return datetime.fromisoformat(result) if result else None

    def create_smart_playlist(self, playlist: SmartPlaylist) -> int:
        """Create a new smart playlist and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert playlist
            cursor.execute("""
                INSERT INTO smart_playlists 
                (name, description, limit_count, order_by, order_desc, match_all, auto_update)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (playlist.name, playlist.description, playlist.limit, 
                  playlist.order_by, playlist.order_desc, playlist.match_all, playlist.auto_update))
            
            playlist_id = cursor.lastrowid
            
            # Insert rules
            for i, rule in enumerate(playlist.rules):
                cursor.execute("""
                    INSERT INTO smart_playlist_rules 
                    (playlist_id, criteria, operator, value, value2, logical_operator, rule_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (playlist_id, rule.criteria.value, rule.operator.value, 
                      str(rule.value), str(rule.value2) if rule.value2 else None,
                      rule.logical_operator.value, i))
            
            conn.commit()
            return playlist_id

    def _build_criteria_query(self, rule: Dict[str, Any]) -> tuple[str, List[Any]]:
        """Build SQL query fragment for a single criteria rule."""
        criteria = rule['criteria']
        operator = rule['operator']
        value = rule['value']
        value2 = rule['value2']
        
        query_parts = []
        params = []
        
        # Handle different criteria types
        if criteria in [PlaylistCriteria.GENRE.value, PlaylistCriteria.ARTIST.value, 
                       PlaylistCriteria.ALBUM.value, PlaylistCriteria.TITLE.value]:
            column = criteria
            if operator == ComparisonOperator.EQUALS.value:
                query_parts.append(f"{column} = ?")
                params.append(value)
            elif operator == ComparisonOperator.CONTAINS.value:
                query_parts.append(f"{column} LIKE ?")
                params.append(f"%{value}%")
            elif operator == ComparisonOperator.STARTS_WITH.value:
                query_parts.append(f"{column} LIKE ?")
                params.append(f"{value}%")
            elif operator == ComparisonOperator.ENDS_WITH.value:
                query_parts.append(f"{column} LIKE ?")
                params.append(f"%{value}")
            elif operator == ComparisonOperator.NOT_EQUALS.value:
                query_parts.append(f"{column} != ?")
                params.append(value)
            elif operator == ComparisonOperator.NOT_CONTAINS.value:
                query_parts.append(f"{column} NOT LIKE ?")
                params.append(f"%{value}%")
            elif operator == ComparisonOperator.IS_EMPTY.value:
                query_parts.append(f"({column} IS NULL OR {column} = '')")
            elif operator == ComparisonOperator.IS_NOT_EMPTY.value:
                query_parts.append(f"({column} IS NOT NULL AND {column} != '')")
        
        elif criteria in [PlaylistCriteria.YEAR.value, PlaylistCriteria.BPM.value, 
                         PlaylistCriteria.DURATION.value, PlaylistCriteria.BITRATE.value,
                         PlaylistCriteria.SAMPLE_RATE.value, PlaylistCriteria.FILE_SIZE.value]:
            column = criteria
            if operator == ComparisonOperator.EQUALS.value:
                query_parts.append(f"{column} = ?")
                params.append(self._convert_numeric_value(value, criteria))
            elif operator == ComparisonOperator.GREATER_THAN.value:
                query_parts.append(f"{column} > ?")
                params.append(self._convert_numeric_value(value, criteria))
            elif operator == ComparisonOperator.LESS_THAN.value:
                query_parts.append(f"{column} < ?")
                params.append(self._convert_numeric_value(value, criteria))
            elif operator == ComparisonOperator.BETWEEN.value and value2:
                query_parts.append(f"{column} BETWEEN ? AND ?")
                params.extend([
                    self._convert_numeric_value(value, criteria),
                    self._convert_numeric_value(value2, criteria)
                ])
        
        elif criteria == PlaylistCriteria.RECENTLY_PLAYED.value:
            days = int(value) if value else 7
            query_parts.append("""
                file_path IN (
                    SELECT DISTINCT file_path FROM playback_history 
                    WHERE played_at >= datetime('now', '-{} days')
                )
            """.format(days))
        
        elif criteria == PlaylistCriteria.MOST_PLAYED.value:
            limit = int(value) if value else 50
            query_parts.append("""
                file_path IN (
                    SELECT file_path FROM playback_history 
                    WHERE completed = TRUE
                    GROUP BY file_path 
                    ORDER BY COUNT(*) DESC 
                    LIMIT {}
                )
            """.format(limit))
        
        elif criteria == PlaylistCriteria.NEVER_PLAYED.value:
            query_parts.append("""
                file_path NOT IN (
                    SELECT DISTINCT file_path FROM playback_history
                )
            """)
        
        elif criteria == PlaylistCriteria.PLAY_COUNT.value:
            if operator == ComparisonOperator.GREATER_THAN.value:
                query_parts.append("""
                    (SELECT COUNT(*) FROM playback_history ph 
                     WHERE ph.file_path = tracks.file_path AND ph.completed = TRUE) > ?
                """)
                params.append(int(value))
            elif operator == ComparisonOperator.LESS_THAN.value:
                query_parts.append("""
                    (SELECT COUNT(*) FROM playback_history ph 
                     WHERE ph.file_path = tracks.file_path AND ph.completed = TRUE) < ?
                """)
                params.append(int(value))
            elif operator == ComparisonOperator.EQUALS.value:
                query_parts.append("""
                    (SELECT COUNT(*) FROM playback_history ph 
                     WHERE ph.file_path = tracks.file_path AND ph.completed = TRUE) = ?
                """)
                params.append(int(value))
        
        elif criteria == PlaylistCriteria.LAST_PLAYED.value:
            if operator == ComparisonOperator.IN_LAST_DAYS.value:
                days = int(value)
                query_parts.append("""
                    file_path IN (
                        SELECT file_path FROM playback_history 
                        WHERE played_at >= datetime('now', '-{} days')
                    )
                """.format(days))
            elif operator == ComparisonOperator.NOT_IN_LAST_DAYS.value:
                days = int(value)
                query_parts.append("""
                    file_path NOT IN (
                        SELECT file_path FROM playback_history 
                        WHERE played_at >= datetime('now', '-{} days')
                    )
                """.format(days))
        
        return " AND ".join(query_parts) if query_parts else "1=1", params
    
    def _convert_numeric_value(self, value: str, criteria: str) -> Union[int, float]:
        """Convert string value to appropriate numeric type."""
        if criteria in [PlaylistCriteria.YEAR.value, PlaylistCriteria.BITRATE.value, 
                       PlaylistCriteria.SAMPLE_RATE.value, PlaylistCriteria.FILE_SIZE.value]:
            return int(value)
        else:  # BPM, DURATION
            return float(value)

    def generate_playlist_tracks(self, playlist_id: int) -> List[Dict[str, Any]]:
        """Generate tracks for a smart playlist based on its rules with enhanced logic."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get playlist info
            cursor.execute("SELECT * FROM smart_playlists WHERE id = ?", (playlist_id,))
            playlist_info = cursor.fetchone()
            if not playlist_info:
                return []
            
            # Get rules ordered by rule_order
            cursor.execute("""
                SELECT * FROM smart_playlist_rules 
                WHERE playlist_id = ? 
                ORDER BY rule_order
            """, (playlist_id,))
            rules = cursor.fetchall()
            
            if not rules:
                return []
            
            # Build query with proper logical operators
            base_query = "SELECT * FROM tracks WHERE "
            all_conditions = []
            all_params = []
            
            for i, rule in enumerate(rules):
                condition, params = self._build_criteria_query(dict(rule))
                if condition and condition != "1=1":
                    if i == 0:
                        all_conditions.append(f"({condition})")
                    else:
                        logical_op = rule['logical_operator'].upper()
                        all_conditions.append(f" {logical_op} ({condition})")
                    all_params.extend(params)
            
            if not all_conditions:
                return []
            
            query = base_query + "".join(all_conditions)
            
            # Add ordering
            if playlist_info['order_by']:
                order_direction = "DESC" if playlist_info['order_desc'] else "ASC"
                # Validate order_by column to prevent SQL injection
                valid_columns = ['title', 'artist', 'album', 'genre', 'year', 'bpm', 'duration', 'bitrate']
                if playlist_info['order_by'] in valid_columns:
                    query += f" ORDER BY {playlist_info['order_by']} {order_direction}"
            
            # Add limit
            if playlist_info['limit_count']:
                query += " LIMIT ?"
                all_params.append(playlist_info['limit_count'])
            
            try:
                cursor.execute(query, all_params)
                tracks = [dict(row) for row in cursor.fetchall()]
                
                # Enhance tracks with play statistics
                for track in tracks:
                    track['play_count'] = self.get_play_count(track['file_path'])
                    track['last_played'] = self.get_last_played(track['file_path'])
                
                return tracks
            except sqlite3.Error as e:
                print(f"Error executing playlist query: {e}")
                print(f"Query: {query}")
                print(f"Params: {all_params}")
                return []
    
    def get_playlist_rules(self, playlist_id: int) -> List[Dict[str, Any]]:
        """Get all rules for a specific playlist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM smart_playlist_rules 
                WHERE playlist_id = ? 
                ORDER BY rule_order
            """, (playlist_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_smart_playlist(self, playlist_id: int, playlist: SmartPlaylist) -> bool:
        """Update an existing smart playlist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update playlist info
            cursor.execute("""
                UPDATE smart_playlists 
                SET name = ?, description = ?, limit_count = ?, order_by = ?, 
                    order_desc = ?, match_all = ?, auto_update = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (playlist.name, playlist.description, playlist.limit, 
                  playlist.order_by, playlist.order_desc, playlist.match_all, 
                  playlist.auto_update, playlist_id))
            
            # Delete existing rules
            cursor.execute("DELETE FROM smart_playlist_rules WHERE playlist_id = ?", (playlist_id,))
            
            # Insert new rules
            for i, rule in enumerate(playlist.rules):
                cursor.execute("""
                    INSERT INTO smart_playlist_rules 
                    (playlist_id, criteria, operator, value, value2, logical_operator, rule_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (playlist_id, rule.criteria.value, rule.operator.value, 
                      str(rule.value), str(rule.value2) if rule.value2 else None,
                      rule.logical_operator.value, i))
            
            conn.commit()
            return cursor.rowcount > 0

    def get_all_smart_playlists(self) -> List[Dict[str, Any]]:
        """Get all smart playlists with enhanced information."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sp.*, 
                       COUNT(spr.id) as rule_count,
                       (SELECT COUNT(*) FROM tracks WHERE file_path IN (
                           SELECT DISTINCT file_path FROM playback_history
                       )) as total_played_tracks
                FROM smart_playlists sp
                LEFT JOIN smart_playlist_rules spr ON sp.id = spr.playlist_id
                GROUP BY sp.id
                ORDER BY sp.name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_smart_playlist(self, playlist_id: int) -> bool:
        """Delete a smart playlist and its rules."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM smart_playlists WHERE id = ?", (playlist_id,))
            return cursor.rowcount > 0
    
    def get_playlist_preview(self, rules: List[PlaylistRule], limit: int = 10) -> List[Dict[str, Any]]:
        """Get a preview of tracks that would match the given rules."""
        # Create a temporary playlist for preview
        temp_playlist = SmartPlaylist(
            name="__preview__",
            rules=rules,
            limit=limit
        )
        
        # Use a temporary ID that won't conflict
        temp_id = -1
        
        # Temporarily store the playlist (we'll clean it up)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert temporary playlist
            cursor.execute("""
                INSERT INTO smart_playlists 
                (id, name, limit_count, order_by, order_desc, match_all)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (temp_id, temp_playlist.name, temp_playlist.limit, 
                  temp_playlist.order_by, temp_playlist.order_desc, temp_playlist.match_all))
            
            # Insert temporary rules
            for i, rule in enumerate(temp_playlist.rules):
                cursor.execute("""
                    INSERT INTO smart_playlist_rules 
                    (playlist_id, criteria, operator, value, value2, logical_operator, rule_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (temp_id, rule.criteria.value, rule.operator.value, 
                      str(rule.value), str(rule.value2) if rule.value2 else None,
                      rule.logical_operator.value, i))
            
            conn.commit()
        
        # Generate preview
        try:
            preview_tracks = self.generate_playlist_tracks(temp_id)
        except:
            preview_tracks = []
        
        # Clean up temporary playlist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM smart_playlists WHERE id = ?", (temp_id,))
            conn.commit()
        
        return preview_tracks


# Enhanced predefined smart playlists
PREDEFINED_PLAYLISTS = [
    SmartPlaylist(
        name="🔥 High Energy (>120 BPM)",
        description="High-energy tracks perfect for peak time",
        rules=[
            PlaylistRule(PlaylistCriteria.BPM, ComparisonOperator.GREATER_THAN, 120)
        ],
        order_by="bpm",
        order_desc=True,
        limit=100
    ),
    SmartPlaylist(
        name="🆕 Recent Hits (2020+)",
        description="Latest tracks from 2020 onwards",
        rules=[
            PlaylistRule(PlaylistCriteria.YEAR, ComparisonOperator.GREATER_THAN, 2020)
        ],
        order_by="year",
        order_desc=True,
        limit=50
    ),
    SmartPlaylist(
        name="🕺 Dance Mix (House/Electronic)",
        description="Perfect dance floor fillers",
        rules=[
            PlaylistRule(PlaylistCriteria.GENRE, ComparisonOperator.CONTAINS, "House"),
            PlaylistRule(PlaylistCriteria.BPM, ComparisonOperator.BETWEEN, 120, 140)
        ],
        order_by="bpm",
        limit=75
    ),
    SmartPlaylist(
        name="⚡ Short Tracks (<3 min)",
        description="Quick tracks for transitions",
        rules=[
            PlaylistRule(PlaylistCriteria.DURATION, ComparisonOperator.LESS_THAN, 180)
        ],
        order_by="duration",
        limit=30
    ),
    SmartPlaylist(
        name="🎵 Never Played",
        description="Discover new tracks in your library",
        rules=[
            PlaylistRule(PlaylistCriteria.NEVER_PLAYED, ComparisonOperator.EQUALS, "true")
        ],
        order_by="date_added",
        order_desc=True,
        limit=50
    ),
    SmartPlaylist(
        name="🔄 Recently Played (7 days)",
        description="Tracks played in the last week",
        rules=[
            PlaylistRule(PlaylistCriteria.RECENTLY_PLAYED, ComparisonOperator.IN_LAST_DAYS, 7)
        ],
        order_by="last_played",
        order_desc=True,
        limit=40
    ),
    SmartPlaylist(
        name="⭐ Most Played Favorites",
        description="Your most played tracks",
        rules=[
            PlaylistRule(PlaylistCriteria.PLAY_COUNT, ComparisonOperator.GREATER_THAN, 5)
        ],
        order_by="play_count",
        order_desc=True,
        limit=25
    ),
    SmartPlaylist(
        name="🎼 Classic Hits (80s-90s)",
        description="Timeless classics from the golden decades",
        rules=[
            PlaylistRule(PlaylistCriteria.YEAR, ComparisonOperator.BETWEEN, 1980, 1999)
        ],
        order_by="year",
        limit=60
    )
]