"""
SQLModel-based database models for DjAlfin.
High-performance, type-safe replacement for direct SQLite operations.
"""

from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship
from sqlalchemy import String, Text, Float, Integer, DateTime, Boolean


class Artist(SQLModel, table=True):
    """Artist model with enhanced metadata and relationships."""
    
    __tablename__ = "artists"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=255)
    sort_name: Optional[str] = Field(default=None, max_length=255)
    
    # External IDs for enrichment
    musicbrainz_artist_id: Optional[str] = Field(default=None, max_length=36)
    spotify_artist_id: Optional[str] = Field(default=None, max_length=50)
    discogs_artist_id: Optional[str] = Field(default=None, max_length=50)
    
    # Metadata
    genre: Optional[str] = Field(default=None, max_length=255)
    country: Optional[str] = Field(default=None, max_length=100)
    formed_year: Optional[int] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tracks: List["Track"] = Relationship(back_populates="artist")
    albums: List["Album"] = Relationship(back_populates="artist")


class Album(SQLModel, table=True):
    """Album model with comprehensive metadata."""
    
    __tablename__ = "albums"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=255)
    artist_id: Optional[int] = Field(default=None, foreign_key="artists.id")
    
    # External IDs
    musicbrainz_release_id: Optional[str] = Field(default=None, max_length=36)
    spotify_album_id: Optional[str] = Field(default=None, max_length=50)
    discogs_release_id: Optional[str] = Field(default=None, max_length=50)
    
    # Metadata
    year: Optional[int] = Field(default=None, index=True)
    genre: Optional[str] = Field(default=None, max_length=255)
    label: Optional[str] = Field(default=None, max_length=255)
    catalog_number: Optional[str] = Field(default=None, max_length=100)
    
    # Album art
    album_art_url: Optional[str] = Field(default=None, max_length=500)
    album_art_local_path: Optional[str] = Field(default=None, max_length=500)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    artist: Optional[Artist] = Relationship(back_populates="albums")
    tracks: List["Track"] = Relationship(back_populates="album")


class Track(SQLModel, table=True):
    """
    Enhanced Track model with comprehensive DJ metadata and relationships.
    Replaces direct SQLite track table with type safety and validation.
    """
    
    __tablename__ = "tracks"
    
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Basic metadata
    title: str = Field(index=True, max_length=255)
    artist_id: Optional[int] = Field(default=None, foreign_key="artists.id")
    album_id: Optional[int] = Field(default=None, foreign_key="albums.id")
    
    # File information
    file_path: str = Field(unique=True, max_length=1000)
    file_type: str = Field(max_length=10)
    file_size: Optional[int] = Field(default=None)
    last_modified_date: Optional[float] = Field(default=None)
    
    # Audio properties
    duration: Optional[float] = Field(default=None, ge=0)  # seconds
    bitrate: Optional[int] = Field(default=None, ge=0)     # kbps
    sample_rate: Optional[int] = Field(default=None, ge=0) # Hz
    channels: Optional[int] = Field(default=None, ge=1, le=8)
    
    # DJ-specific metadata with validation
    bpm: Optional[float] = Field(default=None, ge=50, le=300)  # Realistic BPM range
    key: Optional[str] = Field(default=None, max_length=10)    # Musical key (C, Am, 4A, etc.)
    energy: Optional[int] = Field(default=None, ge=1, le=10)   # Energy level 1-10
    mood: Optional[str] = Field(default=None, max_length=100)
    rating: Optional[int] = Field(default=None, ge=1, le=5)    # Star rating
    
    # Track metadata
    track_number: Optional[int] = Field(default=None, ge=1)
    disc_number: Optional[int] = Field(default=1, ge=1)
    year: Optional[int] = Field(default=None, ge=1900, le=2100, index=True)
    genre: Optional[str] = Field(default=None, max_length=255, index=True)
    comments: Optional[str] = Field(default=None, sa_type=Text)
    
    # External service IDs for enrichment
    musicbrainz_recording_id: Optional[str] = Field(default=None, max_length=36)
    spotify_track_id: Optional[str] = Field(default=None, max_length=50)
    discogs_track_id: Optional[str] = Field(default=None, max_length=50)
    
    # Audio analysis (from librosa/DJ software)
    tempo_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    key_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    danceability: Optional[float] = Field(default=None, ge=0, le=1)
    valence: Optional[float] = Field(default=None, ge=0, le=1)  # Musical positivity
    acousticness: Optional[float] = Field(default=None, ge=0, le=1)
    instrumentalness: Optional[float] = Field(default=None, ge=0, le=1)
    liveness: Optional[float] = Field(default=None, ge=0, le=1)
    speechiness: Optional[float] = Field(default=None, ge=0, le=1)
    loudness: Optional[float] = Field(default=None)  # dB
    
    # DJ usage statistics
    play_count: int = Field(default=0, ge=0)
    last_played: Optional[datetime] = Field(default=None)
    times_loaded: int = Field(default=0, ge=0)  # Loaded into deck
    
    # Cue points and loop data (JSON storage)
    cue_points: Optional[str] = Field(default=None, sa_type=Text)  # JSON string
    loops: Optional[str] = Field(default=None, sa_type=Text)       # JSON string
    
    # Import/sync metadata
    import_source: Optional[str] = Field(default=None, max_length=100)  # e.g., "library_scan"
    sync_status: str = Field(default="pending", max_length=20)  # pending, synced, error
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    artist: Optional[Artist] = Relationship(back_populates="tracks")
    album: Optional[Album] = Relationship(back_populates="tracks")
    playlist_tracks: List["PlaylistTrack"] = Relationship(back_populates="track")


class Playlist(SQLModel, table=True):
    """Enhanced Playlist model with metadata and relationships."""
    
    __tablename__ = "playlists"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None, sa_type=Text)
    
    # Playlist metadata
    is_smart: bool = Field(default=False)  # Smart vs manual playlist
    rules: Optional[str] = Field(default=None, sa_type=Text)  # JSON rules for smart playlists
    color: Optional[str] = Field(default=None, max_length=7)  # Hex color
    
    # Statistics
    track_count: int = Field(default=0, ge=0)
    total_duration: Optional[float] = Field(default=None, ge=0)  # seconds
    
    # Export settings
    export_format: Optional[str] = Field(default="m3u", max_length=10)
    auto_export: bool = Field(default=False)
    export_path: Optional[str] = Field(default=None, max_length=500)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_played: Optional[datetime] = Field(default=None)
    
    # Relationships
    playlist_tracks: List["PlaylistTrack"] = Relationship(back_populates="playlist")


class PlaylistTrack(SQLModel, table=True):
    """Association table for playlist-track many-to-many relationship."""
    
    __tablename__ = "playlist_tracks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlists.id", index=True)
    track_id: int = Field(foreign_key="tracks.id", index=True)
    
    # Position and metadata
    position: int = Field(default=0, ge=0, index=True)  # Order in playlist
    added_at: datetime = Field(default_factory=datetime.utcnow)
    
    # DJ-specific metadata for this playlist entry
    fade_in_duration: Optional[float] = Field(default=None, ge=0)  # seconds
    fade_out_duration: Optional[float] = Field(default=None, ge=0) # seconds
    crossfade_point: Optional[float] = Field(default=None, ge=0)   # seconds from start
    
    # Relationships
    playlist: Playlist = Relationship(back_populates="playlist_tracks")
    track: Track = Relationship(back_populates="playlist_tracks")


class SmartPlaylistRule(SQLModel, table=True):
    """Smart playlist rules for advanced filtering."""
    
    __tablename__ = "smart_playlist_rules"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlists.id", index=True)
    
    # Rule definition
    field: str = Field(max_length=100)  # bpm, genre, artist, etc.
    operator: str = Field(max_length=20)  # equals, contains, greater_than, etc.
    value: str = Field(max_length=255)  # The comparison value
    
    # Rule metadata
    rule_type: str = Field(default="include", max_length=10)  # include, exclude
    weight: int = Field(default=1, ge=1, le=10)  # Rule importance
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AudioAnalysis(SQLModel, table=True):
    """Detailed audio analysis results for tracks."""
    
    __tablename__ = "audio_analysis"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key="tracks.id", unique=True)
    
    # BPM analysis
    detected_bpm: Optional[float] = Field(default=None, ge=50, le=300)
    bpm_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    tempo_stability: Optional[float] = Field(default=None, ge=0, le=1)
    
    # Key analysis
    detected_key: Optional[str] = Field(default=None, max_length=10)
    key_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    camelot_key: Optional[str] = Field(default=None, max_length=3)  # e.g., "4A"
    
    # Audio features
    spectral_centroid: Optional[float] = Field(default=None)
    spectral_rolloff: Optional[float] = Field(default=None)
    zero_crossing_rate: Optional[float] = Field(default=None)
    mfcc_features: Optional[str] = Field(default=None, sa_type=Text)  # JSON array
    
    # Segment analysis
    verse_positions: Optional[str] = Field(default=None, sa_type=Text)  # JSON array
    chorus_positions: Optional[str] = Field(default=None, sa_type=Text)  # JSON array
    bridge_positions: Optional[str] = Field(default=None, sa_type=Text)  # JSON array
    
    # Analysis metadata
    analysis_version: str = Field(default="1.0", max_length=20)
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    analysis_duration: Optional[float] = Field(default=None)  # seconds to analyze


# Database configuration
class DatabaseConfig:
    """Database configuration and connection management."""
    
    def __init__(self, database_url: str = "sqlite:///djlib.db"):
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
    
    def create_tables(self):
        """Create all tables in the database."""
        SQLModel.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return Session(self.engine)
    
    def drop_tables(self):
        """Drop all tables (for testing/reset)."""
        SQLModel.metadata.drop_all(self.engine)


# Global database instance
db_config = DatabaseConfig()


def get_session() -> Session:
    """Get a database session - use this in application code."""
    return db_config.get_session()


def init_sqlmodel_db():
    """Initialize SQLModel database and create tables."""
    db_config.create_tables()
    print("✅ SQLModel database initialized successfully")


# Migration utilities
def migrate_from_sqlite(old_db_path: str = "djlib.db"):
    """
    Migrate existing SQLite database to SQLModel schema.
    This will be used in the migration phase.
    """
    import sqlite3
    
    print(f"🔄 Starting migration from {old_db_path}...")
    
    # Connect to old database
    old_conn = sqlite3.connect(old_db_path)
    old_conn.row_factory = sqlite3.Row
    
    # Get new session
    with get_session() as session:
        try:
            # Migrate tracks
            old_tracks = old_conn.execute("SELECT * FROM tracks").fetchall()
            print(f"📊 Migrating {len(old_tracks)} tracks...")
            
            for old_track in old_tracks:
                new_track = Track(
                    title=old_track.get("title", "Unknown"),
                    file_path=old_track["file_path"],
                    file_type=old_track.get("file_type", "mp3"),
                    duration=old_track.get("duration"),
                    bitrate=old_track.get("bitrate"),
                    bpm=old_track.get("bpm") if old_track.get("bpm") != "N/A" else None,
                    key=old_track.get("key") if old_track.get("key") != "Unknown" else None,
                    year=old_track.get("year") if old_track.get("year") != "Unknown" else None,
                    genre=old_track.get("genre") if old_track.get("genre") != "Unknown" else None,
                    comments=old_track.get("comment"),
                    last_modified_date=old_track.get("last_modified_date"),
                    sync_status="migrated"
                )
                session.add(new_track)
            
            session.commit()
            print("✅ Migration completed successfully")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            old_conn.close()


if __name__ == "__main__":
    # Test the models
    init_sqlmodel_db()
    
    with get_session() as session:
        # Create test artist
        artist = Artist(name="Test Artist", genre="Electronic")
        session.add(artist)
        session.commit()
        session.refresh(artist)
        
        # Create test track
        track = Track(
            title="Test Track",
            artist_id=artist.id,
            file_path="/test/path.mp3",
            file_type="mp3",
            bpm=128.0,
            key="4A",
            energy=7
        )
        session.add(track)
        session.commit()
        
        print(f"✅ Created test track: {track.title} by {artist.name}")