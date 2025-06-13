"""
Smart Playlist Manager for DjAlfin
Handles intelligent playlist generation based on various criteria.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PlaylistCriteria(Enum):
    """Criteria types for smart playlists."""
    GENRE = "genre"
    ARTIST = "artist"
    YEAR = "year"
    BPM = "bpm"
    DURATION = "duration"
    RECENTLY_PLAYED = "recently_played"
    MOST_PLAYED = "most_played"
    NEVER_PLAYED = "never_played"


class ComparisonOperator(Enum):
    """Comparison operators for playlist criteria."""
    EQUALS = "equals"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    NOT_EQUALS = "not_equals"


@dataclass
class PlaylistRule:
    """Represents a single rule for a smart playlist."""
    criteria: PlaylistCriteria
    operator: ComparisonOperator
    value: Any
    value2: Optional[Any] = None  # For BETWEEN operator


@dataclass
class SmartPlaylist:
    """Represents a smart playlist with its rules."""
    name: str
    rules: List[PlaylistRule]
    limit: Optional[int] = None
    order_by: Optional[str] = None
    order_desc: bool = False


class SmartPlaylistManager:
    """Manages smart playlists and their generation."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_smart_playlist_tables()
    
    def _create_smart_playlist_tables(self) -> None:
        """Create tables for storing smart playlists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS smart_playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    limit_count INTEGER,
                    order_by TEXT,
                    order_desc BOOLEAN DEFAULT FALSE,
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
                    FOREIGN KEY (playlist_id) REFERENCES smart_playlists (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
    
    def create_smart_playlist(self, playlist: SmartPlaylist) -> int:
        """Create a new smart playlist and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert playlist
            cursor.execute("""
                INSERT INTO smart_playlists (name, limit_count, order_by, order_desc)
                VALUES (?, ?, ?, ?)
            """, (playlist.name, playlist.limit, playlist.order_by, playlist.order_desc))
            
            playlist_id = cursor.lastrowid
            
            # Insert rules
            for rule in playlist.rules:
                cursor.execute("""
                    INSERT INTO smart_playlist_rules (playlist_id, criteria, operator, value, value2)
                    VALUES (?, ?, ?, ?, ?)
                """, (playlist_id, rule.criteria.value, rule.operator.value, 
                     str(rule.value), str(rule.value2) if rule.value2 else None))
            
            conn.commit()
            return playlist_id
    
    def generate_playlist_tracks(self, playlist_id: int) -> List[Dict[str, Any]]:
        """Generate tracks for a smart playlist based on its rules."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get playlist info
            cursor.execute("SELECT * FROM smart_playlists WHERE id = ?", (playlist_id,))
            playlist_info = cursor.fetchone()
            if not playlist_info:
                return []
            
            # Get rules
            cursor.execute("SELECT * FROM smart_playlist_rules WHERE playlist_id = ?", (playlist_id,))
            rules = cursor.fetchall()
            
            # Build query
            query = "SELECT * FROM tracks WHERE 1=1"
            params = []
            
            for rule in rules:
                criteria = rule['criteria']
                operator = rule['operator']
                value = rule['value']
                value2 = rule['value2']
                
                if criteria == PlaylistCriteria.GENRE.value:
                    if operator == ComparisonOperator.EQUALS.value:
                        query += " AND genre = ?"
                        params.append(value)
                    elif operator == ComparisonOperator.CONTAINS.value:
                        query += " AND genre LIKE ?"
                        params.append(f"%{value}%")
                
                elif criteria == PlaylistCriteria.ARTIST.value:
                    if operator == ComparisonOperator.EQUALS.value:
                        query += " AND artist = ?"
                        params.append(value)
                    elif operator == ComparisonOperator.CONTAINS.value:
                        query += " AND artist LIKE ?"
                        params.append(f"%{value}%")
                
                elif criteria == PlaylistCriteria.YEAR.value:
                    if operator == ComparisonOperator.EQUALS.value:
                        query += " AND year = ?"
                        params.append(int(value))
                    elif operator == ComparisonOperator.GREATER_THAN.value:
                        query += " AND year > ?"
                        params.append(int(value))
                    elif operator == ComparisonOperator.LESS_THAN.value:
                        query += " AND year < ?"
                        params.append(int(value))
                    elif operator == ComparisonOperator.BETWEEN.value and value2:
                        query += " AND year BETWEEN ? AND ?"
                        params.extend([int(value), int(value2)])
                
                elif criteria == PlaylistCriteria.BPM.value:
                    if operator == ComparisonOperator.GREATER_THAN.value:
                        query += " AND bpm > ?"
                        params.append(float(value))
                    elif operator == ComparisonOperator.LESS_THAN.value:
                        query += " AND bpm < ?"
                        params.append(float(value))
                    elif operator == ComparisonOperator.BETWEEN.value and value2:
                        query += " AND bpm BETWEEN ? AND ?"
                        params.extend([float(value), float(value2)])
                
                elif criteria == PlaylistCriteria.DURATION.value:
                    if operator == ComparisonOperator.GREATER_THAN.value:
                        query += " AND duration > ?"
                        params.append(float(value))
                    elif operator == ComparisonOperator.LESS_THAN.value:
                        query += " AND duration < ?"
                        params.append(float(value))
                    elif operator == ComparisonOperator.BETWEEN.value and value2:
                        query += " AND duration BETWEEN ? AND ?"
                        params.extend([float(value), float(value2)])
            
            # Add ordering
            if playlist_info['order_by']:
                order_direction = "DESC" if playlist_info['order_desc'] else "ASC"
                query += f" ORDER BY {playlist_info['order_by']} {order_direction}"
            
            # Add limit
            if playlist_info['limit_count']:
                query += " LIMIT ?"
                params.append(playlist_info['limit_count'])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_smart_playlists(self) -> List[Dict[str, Any]]:
        """Get all smart playlists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM smart_playlists ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_smart_playlist(self, playlist_id: int) -> bool:
        """Delete a smart playlist and its rules."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM smart_playlists WHERE id = ?", (playlist_id,))
            return cursor.rowcount > 0


# Predefined smart playlists
PREDEFINED_PLAYLISTS = [
    SmartPlaylist(
        name="High Energy (>120 BPM)",
        rules=[
            PlaylistRule(PlaylistCriteria.BPM, ComparisonOperator.GREATER_THAN, 120)
        ],
        order_by="bpm",
        order_desc=True
    ),
    SmartPlaylist(
        name="Recent Hits (2020+)",
        rules=[
            PlaylistRule(PlaylistCriteria.YEAR, ComparisonOperator.GREATER_THAN, 2020)
        ],
        order_by="year",
        order_desc=True
    ),
    SmartPlaylist(
        name="Dance Mix (House/Electronic)",
        rules=[
            PlaylistRule(PlaylistCriteria.GENRE, ComparisonOperator.CONTAINS, "House"),
            PlaylistRule(PlaylistCriteria.BPM, ComparisonOperator.BETWEEN, 120, 140)
        ],
        order_by="bpm"
    ),
    SmartPlaylist(
        name="Short Tracks (<3 min)",
        rules=[
            PlaylistRule(PlaylistCriteria.DURATION, ComparisonOperator.LESS_THAN, 180)
        ],
        order_by="duration"
    )
]