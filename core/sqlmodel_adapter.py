"""
SQLModel adapter for DjAlfin - bridges old SQLite code with new SQLModel.
Provides backward compatibility while migrating to SQLModel gradually.
"""

from typing import Dict, List, Optional, Any, Union
from sqlmodel import Session, select, and_, or_
from sqlalchemy import func, text

from .sqlmodel_database import (
    Track, Artist, Album, Playlist, PlaylistTrack, 
    get_session, db_config
)
from . import database as old_db


class SQLModelAdapter:
    """Adapter that provides the same interface as old database.py but uses SQLModel."""
    
    def __init__(self):
        self.session_factory = get_session
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.session_factory()
    
    # ===== TRACK OPERATIONS =====
    
    def add_track(self, track_data: Dict[str, Any]) -> bool:
        """Add or update a track with SQLModel validation."""
        try:
            with self.get_session() as session:
                # Check if track exists by file_path
                existing_track = session.exec(
                    select(Track).where(Track.file_path == track_data["file_path"])
                ).first()
                
                if existing_track:
                    # Update existing track
                    self._update_track_from_dict(existing_track, track_data)
                    session.add(existing_track)
                else:
                    # Create new track
                    track = self._create_track_from_dict(track_data)
                    session.add(track)
                
                session.commit()
                return True
                
        except Exception as e:
            print(f"❌ SQLModel add_track error: {e}")
            return False
    
    def get_all_tracks(self) -> List[Dict[str, Any]]:
        """Get all tracks as dictionaries (backward compatibility)."""
        try:
            with self.get_session() as session:
                tracks = session.exec(select(Track)).all()
                return [self._track_to_dict(track) for track in tracks]
        except Exception as e:
            print(f"❌ SQLModel get_all_tracks error: {e}")
            return []
    
    def get_track_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get track by file path."""
        try:
            with self.get_session() as session:
                track = session.exec(
                    select(Track).where(Track.file_path == file_path)
                ).first()
                
                return self._track_to_dict(track) if track else None
        except Exception as e:
            print(f"❌ SQLModel get_track_by_path error: {e}")
            return None
    
    def update_track_field(self, track_id: int, field: str, value: Any) -> bool:
        """Update a specific field of a track."""
        try:
            with self.get_session() as session:
                track = session.get(Track, track_id)
                if track:
                    setattr(track, field, value)
                    session.add(track)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"❌ SQLModel update_track_field error: {e}")
            return False
    
    def search_tracks(self, query: str, field: str = None) -> List[Dict[str, Any]]:
        """Search tracks with improved SQLModel querying."""
        try:
            with self.get_session() as session:
                if field:
                    # Search specific field
                    if field == "title":
                        tracks = session.exec(
                            select(Track).where(Track.title.contains(query))
                        ).all()
                    elif field == "artist":
                        tracks = session.exec(
                            select(Track).where(Track.artist.has(Artist.name.contains(query)))
                        ).all()
                    elif field == "genre":
                        tracks = session.exec(
                            select(Track).where(Track.genre.contains(query))
                        ).all()
                    else:
                        # Fallback to generic search
                        tracks = self._generic_search(session, query)
                else:
                    # Search all fields
                    tracks = self._generic_search(session, query)
                
                return [self._track_to_dict(track) for track in tracks]
        except Exception as e:
            print(f"❌ SQLModel search_tracks error: {e}")
            return []
    
    def _generic_search(self, session: Session, query: str) -> List[Track]:
        """Generic search across multiple fields."""
        # Join with Artist to search artist names too
        from sqlalchemy.orm import selectinload
        return session.exec(
            select(Track)
            .options(selectinload(Track.artist))
            .join(Artist, Track.artist_id == Artist.id, isouter=True)
            .where(
                or_(
                    Track.title.contains(query),
                    Track.genre.contains(query), 
                    Track.comments.contains(query),
                    Artist.name.contains(query)
                )
            )
        ).all()
    
    # ===== PLAYLIST OPERATIONS =====
    
    def create_playlist(self, name: str, description: str = None) -> int:
        """Create a new playlist."""
        try:
            with self.get_session() as session:
                playlist = Playlist(name=name, description=description)
                session.add(playlist)
                session.commit()
                session.refresh(playlist)
                return playlist.id
        except Exception as e:
            print(f"❌ SQLModel create_playlist error: {e}")
            return -1
    
    def get_all_playlists(self) -> List[Dict[str, Any]]:
        """Get all playlists."""
        try:
            with self.get_session() as session:
                playlists = session.exec(select(Playlist)).all()
                return [self._playlist_to_dict(playlist) for playlist in playlists]
        except Exception as e:
            print(f"❌ SQLModel get_all_playlists error: {e}")
            return []
    
    def add_track_to_playlist(self, playlist_id: int, track_id: int) -> bool:
        """Add track to playlist."""
        try:
            with self.get_session() as session:
                # Get current max position
                max_pos = session.exec(
                    select(func.max(PlaylistTrack.position))
                    .where(PlaylistTrack.playlist_id == playlist_id)
                ).first() or 0
                
                playlist_track = PlaylistTrack(
                    playlist_id=playlist_id,
                    track_id=track_id,
                    position=max_pos + 1
                )
                session.add(playlist_track)
                session.commit()
                return True
        except Exception as e:
            print(f"❌ SQLModel add_track_to_playlist error: {e}")
            return False
    
    def get_playlist_tracks(self, playlist_id: int) -> List[Dict[str, Any]]:
        """Get tracks in a playlist with position ordering."""
        try:
            with self.get_session() as session:
                playlist_tracks = session.exec(
                    select(PlaylistTrack, Track)
                    .join(Track)
                    .where(PlaylistTrack.playlist_id == playlist_id)
                    .order_by(PlaylistTrack.position)
                ).all()
                
                return [self._track_to_dict(track) for _, track in playlist_tracks]
        except Exception as e:
            print(f"❌ SQLModel get_playlist_tracks error: {e}")
            return []
    
    # ===== ARTIST OPERATIONS =====
    
    def get_or_create_artist(self, name: str) -> int:
        """Get existing artist or create new one."""
        try:
            with self.get_session() as session:
                artist = session.exec(
                    select(Artist).where(Artist.name == name)
                ).first()
                
                if not artist:
                    artist = Artist(name=name)
                    session.add(artist)
                    session.commit()
                    session.refresh(artist)
                
                return artist.id
        except Exception as e:
            print(f"❌ SQLModel get_or_create_artist error: {e}")
            return -1
    
    # ===== MIGRATION HELPERS =====
    
    def migrate_from_old_db(self, old_db_path: str = "djlib.db") -> bool:
        """Migrate data from old SQLite database to SQLModel."""
        try:
            import sqlite3
            
            print(f"🔄 Starting migration from {old_db_path}...")
            
            # Connect to old database
            old_conn = sqlite3.connect(old_db_path)
            old_conn.row_factory = sqlite3.Row
            
            with self.get_session() as session:
                # Migrate tracks
                old_tracks = old_conn.execute("SELECT * FROM tracks").fetchall()
                print(f"📊 Migrating {len(old_tracks)} tracks...")
                
                for old_track in old_tracks:
                    # Handle artist
                    artist_name = old_track.get("artist", "Unknown")
                    if artist_name and artist_name != "Unknown":
                        artist = session.exec(
                            select(Artist).where(Artist.name == artist_name)
                        ).first()
                        if not artist:
                            artist = Artist(name=artist_name)
                            session.add(artist)
                            session.flush()  # Get ID without committing
                        artist_id = artist.id
                    else:
                        artist_id = None
                    
                    # Handle album
                    album_name = old_track.get("album", "Unknown")
                    album_id = None
                    if album_name and album_name != "Unknown" and artist_id:
                        album = session.exec(
                            select(Album).where(
                                and_(Album.title == album_name, Album.artist_id == artist_id)
                            )
                        ).first()
                        if not album:
                            album = Album(
                                title=album_name,
                                artist_id=artist_id,
                                year=old_track.get("year") if old_track.get("year") != "Unknown" else None
                            )
                            session.add(album)
                            session.flush()
                        album_id = album.id
                    
                    # Create track
                    track_data = {
                        "title": old_track.get("title", "Unknown"),
                        "artist_id": artist_id,
                        "album_id": album_id,
                        "file_path": old_track["file_path"],
                        "file_type": old_track.get("file_type", "mp3"),
                        "duration": old_track.get("duration"),
                        "bitrate": old_track.get("bitrate"),
                        "bpm": self._safe_float(old_track.get("bmp")),  # Note: old typo 'bmp'
                        "key": old_track.get("key") if old_track.get("key") != "Unknown" else None,
                        "year": self._safe_int(old_track.get("year")),
                        "genre": old_track.get("genre") if old_track.get("genre") != "Unknown" else None,
                        "comments": old_track.get("comment"),
                        "last_modified_date": old_track.get("last_modified_date"),
                        "sync_status": "migrated"
                    }
                    
                    track = Track(**{k: v for k, v in track_data.items() if v is not None})
                    session.add(track)
                
                session.commit()
                print("✅ Migration completed successfully")
                return True
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
        finally:
            if 'old_conn' in locals():
                old_conn.close()
    
    # ===== UTILITY METHODS =====
    
    def _create_track_from_dict(self, data: Dict[str, Any]) -> Track:
        """Create Track object from dictionary."""
        # Handle artist
        artist_id = None
        if data.get("artist"):
            artist_id = self.get_or_create_artist(data["artist"])
        
        # Filter out None values and unknown placeholders
        clean_data = {}
        for key, value in data.items():
            if key == "artist":
                clean_data["artist_id"] = artist_id
            elif value is not None and str(value).strip() not in ["N/A", "Unknown", ""]:
                clean_data[key] = value
        
        return Track(**clean_data)
    
    def _update_track_from_dict(self, track: Track, data: Dict[str, Any]):
        """Update Track object from dictionary."""
        for key, value in data.items():
            if key == "artist" and value:
                track.artist_id = self.get_or_create_artist(value)
            elif hasattr(track, key) and value is not None:
                setattr(track, key, value)
    
    def _track_to_dict(self, track: Track) -> Dict[str, Any]:
        """Convert Track object to dictionary for backward compatibility."""
        if not track:
            return {}
        
        return {
            "id": track.id,
            "title": track.title or "Unknown",
            "artist": track.artist.name if track.artist else "Unknown",
            "album": track.album.title if track.album else "Unknown",
            "file_path": track.file_path,
            "file_type": track.file_type,
            "duration": track.duration,
            "bitrate": track.bitrate,
            "bpm": track.bpm or "N/A",
            "key": track.key or "Unknown",
            "year": track.year or "Unknown",
            "genre": track.genre or "Unknown",
            "comment": track.comments or "",
            "last_modified_date": track.last_modified_date,
            "rating": track.rating,
            "energy": track.energy,
            "play_count": track.play_count,
            "created_at": track.created_at,
            "updated_at": track.updated_at
        }
    
    def _playlist_to_dict(self, playlist: Playlist) -> Dict[str, Any]:
        """Convert Playlist object to dictionary."""
        return {
            "id": playlist.id,
            "name": playlist.name,
            "description": playlist.description or "",
            "is_smart": playlist.is_smart,
            "track_count": playlist.track_count,
            "created_at": playlist.created_at,
            "updated_at": playlist.updated_at
        }
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int."""
        if value is None or str(value).strip() in ["", "N/A", "Unknown"]:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None or str(value).strip() in ["", "N/A", "Unknown"]:
            return None
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return None
    
    # ===== STATISTICS AND ANALYTICS =====
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Get comprehensive library statistics."""
        try:
            with self.get_session() as session:
                stats = {}
                
                # Basic counts
                stats["total_tracks"] = session.exec(select(func.count(Track.id))).first()
                stats["total_artists"] = session.exec(select(func.count(Artist.id))).first()
                stats["total_albums"] = session.exec(select(func.count(Album.id))).first()
                stats["total_playlists"] = session.exec(select(func.count(Playlist.id))).first()
                
                # Duration statistics
                total_duration = session.exec(select(func.sum(Track.duration))).first() or 0
                stats["total_duration_hours"] = total_duration / 3600
                
                # Genre distribution
                genre_counts = session.exec(
                    select(Track.genre, func.count(Track.id))
                    .where(Track.genre.isnot(None))
                    .group_by(Track.genre)
                    .order_by(func.count(Track.id).desc())
                    .limit(10)
                ).all()
                stats["top_genres"] = dict(genre_counts)
                
                # Year distribution
                year_counts = session.exec(
                    select(Track.year, func.count(Track.id))
                    .where(Track.year.isnot(None))
                    .group_by(Track.year)
                    .order_by(Track.year.desc())
                    .limit(10)
                ).all()
                stats["tracks_by_year"] = dict(year_counts)
                
                # BPM statistics
                bpm_stats = session.exec(
                    select(
                        func.min(Track.bpm),
                        func.max(Track.bpm),
                        func.avg(Track.bpm)
                    ).where(Track.bpm.isnot(None))
                ).first()
                if bpm_stats and bpm_stats[0]:
                    stats["bpm_range"] = {
                        "min": float(bpm_stats[0]),
                        "max": float(bpm_stats[1]),
                        "average": float(bpm_stats[2])
                    }
                
                return stats
                
        except Exception as e:
            print(f"❌ SQLModel get_library_stats error: {e}")
            return {}


# Global adapter instance
sqlmodel_adapter = SQLModelAdapter()


# ===== BACKWARD COMPATIBILITY FUNCTIONS =====
# These provide the same interface as the old database.py

def add_track(track_data: Dict[str, Any]) -> bool:
    """Backward compatibility: add track using SQLModel."""
    return sqlmodel_adapter.add_track(track_data)

def get_all_tracks() -> List[Dict[str, Any]]:
    """Backward compatibility: get all tracks."""
    return sqlmodel_adapter.get_all_tracks()

def get_track_by_path(file_path: str) -> Optional[Dict[str, Any]]:
    """Backward compatibility: get track by path."""
    return sqlmodel_adapter.get_track_by_path(file_path)

def update_track_field(track_id: int, field: str, value: Any) -> bool:
    """Backward compatibility: update track field."""
    return sqlmodel_adapter.update_track_field(track_id, field, value)

def search_tracks(query: str, field: str = None) -> List[Dict[str, Any]]:
    """Backward compatibility: search tracks."""
    return sqlmodel_adapter.search_tracks(query, field)

def create_playlist(name: str, description: str = None) -> int:
    """Backward compatibility: create playlist."""
    return sqlmodel_adapter.create_playlist(name, description)

def get_all_playlists() -> List[Dict[str, Any]]:
    """Backward compatibility: get all playlists."""
    return sqlmodel_adapter.get_all_playlists()


if __name__ == "__main__":
    # Test the adapter
    adapter = SQLModelAdapter()
    
    # Test adding a track
    test_track = {
        "title": "SQLModel Test Track",
        "artist": "Test Artist",
        "file_path": "/test/sqlmodel_test.mp3",
        "file_type": "mp3",
        "bpm": 128.5,
        "key": "4A",
        "genre": "Electronic"
    }
    
    print("🧪 Testing SQLModel adapter...")
    success = adapter.add_track(test_track)
    print(f"Add track: {'✅' if success else '❌'}")
    
    # Test retrieving tracks
    tracks = adapter.get_all_tracks()
    print(f"Retrieved {len(tracks)} tracks")
    
    # Test statistics
    stats = adapter.get_library_stats()
    print(f"Library stats: {stats}")
    
    print("✅ SQLModel adapter test completed")