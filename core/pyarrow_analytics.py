"""
PyArrow Analytics Engine for DjAlfin.
Ultra-fast columnar analytics for DJ library management with 10-100x performance improvements.
"""

import pyarrow as pa
import pyarrow.compute as pc
import polars as pl
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
import json
import time
from pathlib import Path

from .sqlmodel_adapter import sqlmodel_adapter
from .sqlmodel_database import get_session, Track, Artist, Album
from sqlmodel import select


@dataclass
class AnalyticsResult:
    """Result container for analytics operations."""
    data: Any
    execution_time: float
    rows_processed: int
    operation: str


class PyArrowAnalyticsEngine:
    """
    High-performance analytics engine using PyArrow columnar processing.
    
    Benefits:
    - 10-100x faster than pandas for large datasets
    - Zero-copy operations for memory efficiency
    - Lazy evaluation for complex pipelines
    - Native multi-threading
    - Arrow interchange format compatibility
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_refresh = 0
        
    def _get_tracks_arrow_table(self, force_refresh: bool = False) -> pa.Table:
        """Get tracks data as PyArrow table with caching."""
        now = time.time()
        
        if not force_refresh and self.last_refresh + self.cache_ttl > now and 'tracks_table' in self.cache:
            return self.cache['tracks_table']
        
        print("🔄 Loading tracks data into PyArrow table...")
        start_time = time.time()
        
        # Get data from SQLModel
        tracks_data = sqlmodel_adapter.get_all_tracks()
        
        if not tracks_data:
            # Return empty table with schema
            schema = self._get_tracks_schema()
            empty_table = pa.table([], schema=schema)
            self.cache['tracks_table'] = empty_table
            return empty_table
        
        # Convert to Arrow table
        arrow_data = self._tracks_to_arrow_dict(tracks_data)
        table = pa.table(arrow_data)
        
        load_time = time.time() - start_time
        print(f"✅ Loaded {len(tracks_data)} tracks to Arrow in {load_time:.3f}s")
        
        self.cache['tracks_table'] = table
        self.last_refresh = now
        
        return table
    
    def _get_tracks_schema(self) -> pa.Schema:
        """Define Arrow schema for tracks data."""
        return pa.schema([
            ('id', pa.int64()),
            ('title', pa.string()),
            ('artist', pa.string()),
            ('album', pa.string()),
            ('genre', pa.string()),
            ('year', pa.int32()),
            ('bpm', pa.float64()),
            ('key', pa.string()),
            ('energy', pa.int32()),
            ('rating', pa.int32()),
            ('duration', pa.float64()),
            ('bitrate', pa.int32()),
            ('play_count', pa.int32()),
            ('file_type', pa.string()),
            ('danceability', pa.float64()),
            ('valence', pa.float64()),
            ('acousticness', pa.float64()),
            ('instrumentalness', pa.float64()),
            ('liveness', pa.float64()),
            ('speechiness', pa.float64()),
            ('loudness', pa.float64())
        ])
    
    def _tracks_to_arrow_dict(self, tracks_data: List[Dict]) -> Dict[str, List]:
        """Convert tracks data to Arrow-compatible dictionary."""
        arrow_dict = {
            'id': [],
            'title': [],
            'artist': [],
            'album': [],
            'genre': [],
            'year': [],
            'bpm': [],
            'key': [],
            'energy': [],
            'rating': [],
            'duration': [],
            'bitrate': [],
            'play_count': [],
            'file_type': [],
            'danceability': [],
            'valence': [],
            'acousticness': [],
            'instrumentalness': [],
            'liveness': [],
            'speechiness': [],
            'loudness': []
        }
        
        for track in tracks_data:
            arrow_dict['id'].append(track.get('id', 0))
            arrow_dict['title'].append(track.get('title', 'Unknown'))
            arrow_dict['artist'].append(track.get('artist', 'Unknown'))
            arrow_dict['album'].append(track.get('album', 'Unknown'))
            arrow_dict['genre'].append(track.get('genre', 'Unknown'))
            
            # Handle numeric fields safely
            arrow_dict['year'].append(self._safe_int(track.get('year')))
            arrow_dict['bpm'].append(self._safe_float(track.get('bpm')))
            arrow_dict['energy'].append(self._safe_int(track.get('energy')))
            arrow_dict['rating'].append(self._safe_int(track.get('rating')))
            arrow_dict['duration'].append(self._safe_float(track.get('duration')))
            arrow_dict['bitrate'].append(self._safe_int(track.get('bitrate')))
            arrow_dict['play_count'].append(self._safe_int(track.get('play_count', 0)))
            
            arrow_dict['key'].append(track.get('key', 'Unknown'))
            arrow_dict['file_type'].append(track.get('file_type', 'mp3'))
            
            # Audio analysis features (if available)
            arrow_dict['danceability'].append(self._safe_float(track.get('danceability')))
            arrow_dict['valence'].append(self._safe_float(track.get('valence')))
            arrow_dict['acousticness'].append(self._safe_float(track.get('acousticness')))
            arrow_dict['instrumentalness'].append(self._safe_float(track.get('instrumentalness')))
            arrow_dict['liveness'].append(self._safe_float(track.get('liveness')))
            arrow_dict['speechiness'].append(self._safe_float(track.get('speechiness')))
            arrow_dict['loudness'].append(self._safe_float(track.get('loudness')))
        
        return arrow_dict
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to int."""
        if value is None or str(value).strip() in ['', 'N/A', 'Unknown']:
            return default
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        if value is None or str(value).strip() in ['', 'N/A', 'Unknown']:
            return default
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return default
    
    # ===== BASIC ANALYTICS =====
    
    def get_library_overview(self) -> AnalyticsResult:
        """Get comprehensive library overview with PyArrow speed."""
        start_time = time.time()
        table = self._get_tracks_arrow_table()
        
        if table.num_rows == 0:
            return AnalyticsResult(
                data={},
                execution_time=time.time() - start_time,
                rows_processed=0,
                operation="library_overview"
            )
        
        # Compute statistics using Arrow
        overview = {
            'total_tracks': table.num_rows,
            'total_duration_hours': pc.sum(table['duration']).as_py() / 3600,
            'avg_bpm': pc.mean(table['bpm']).as_py(),
            'bpm_std': pc.stddev(table['bpm']).as_py(),
            'avg_energy': pc.mean(table['energy']).as_py(),
            'total_artists': pc.count_distinct(table['artist']).as_py(),
            'total_albums': pc.count_distinct(table['album']).as_py(),
            'file_formats': self._value_counts(table, 'file_type')
        }
        
        execution_time = time.time() - start_time
        
        return AnalyticsResult(
            data=overview,
            execution_time=execution_time,
            rows_processed=table.num_rows,
            operation="library_overview"
        )
    
    def analyze_bpm_distribution(self) -> AnalyticsResult:
        """Analyze BPM patterns with Arrow compute."""
        start_time = time.time()
        table = self._get_tracks_arrow_table()
        
        if table.num_rows == 0:
            return AnalyticsResult(data={}, execution_time=0, rows_processed=0, operation="bpm_analysis")
        
        # Filter out invalid BPM values
        valid_bpm = pc.filter(table, pc.and_(
            pc.greater(table['bpm'], 50),
            pc.less(table['bpm'], 300)
        ))
        
        # Use Polars for statistical operations (handles scalars better)
        df = pl.from_arrow(valid_bpm)
        
        bpm_analysis = {
            'min_bpm': df['bpm'].min(),
            'max_bpm': df['bpm'].max(),
            'avg_bpm': df['bpm'].mean(),
            'median_bpm': df['bpm'].median(),
            'std_bpm': df['bpm'].std(),
            'bpm_ranges': self._bpm_range_analysis(valid_bpm),
            'genre_bpm_avg': self._genre_bpm_analysis(valid_bpm)
        }
        
        execution_time = time.time() - start_time
        
        return AnalyticsResult(
            data=bpm_analysis,
            execution_time=execution_time,
            rows_processed=valid_bpm.num_rows,
            operation="bpm_analysis"
        )
    
    def _bpm_range_analysis(self, table: pa.Table) -> Dict[str, int]:
        """Analyze BPM range distribution."""
        ranges = {
            'Very Slow (50-90)': 0,
            'Slow (90-120)': 0,
            'Medium (120-140)': 0,
            'Fast (140-180)': 0,
            'Very Fast (180+)': 0
        }
        
        bpm_col = table['bpm']
        
        ranges['Very Slow (50-90)'] = pc.sum(pc.and_(
            pc.greater_equal(bpm_col, 50),
            pc.less(bpm_col, 90)
        )).as_py()
        
        ranges['Slow (90-120)'] = pc.sum(pc.and_(
            pc.greater_equal(bpm_col, 90),
            pc.less(bpm_col, 120)
        )).as_py()
        
        ranges['Medium (120-140)'] = pc.sum(pc.and_(
            pc.greater_equal(bpm_col, 120),
            pc.less(bpm_col, 140)
        )).as_py()
        
        ranges['Fast (140-180)'] = pc.sum(pc.and_(
            pc.greater_equal(bpm_col, 140),
            pc.less(bpm_col, 180)
        )).as_py()
        
        ranges['Very Fast (180+)'] = pc.sum(
            pc.greater_equal(bpm_col, 180)
        ).as_py()
        
        return ranges
    
    def _genre_bpm_analysis(self, table: pa.Table) -> Dict[str, float]:
        """Analyze average BPM by genre."""
        # Use Polars for complex group operations (faster than pure Arrow for this)
        df = pl.from_arrow(table)
        
        genre_bpm = (
            df.group_by("genre")
            .agg(pl.col("bpm").mean().alias("avg_bpm"))
            .sort("avg_bpm", descending=True)
            .limit(10)
        )
        
        return dict(zip(genre_bpm["genre"].to_list(), genre_bpm["avg_bpm"].to_list()))
    
    def analyze_genre_distribution(self) -> AnalyticsResult:
        """Analyze genre patterns."""
        start_time = time.time()
        table = self._get_tracks_arrow_table()
        
        if table.num_rows == 0:
            return AnalyticsResult(data={}, execution_time=0, rows_processed=0, operation="genre_analysis")
        
        genre_stats = {
            'total_genres': pc.count_distinct(table['genre']).as_py(),
            'top_genres': self._value_counts(table, 'genre', limit=10),
            'genre_diversity': self._calculate_diversity(table, 'genre'),
            'tracks_per_genre': {}
        }
        
        # Use Polars for complex aggregations
        df = pl.from_arrow(table)
        genre_agg = (
            df.group_by("genre")
            .agg([
                pl.count().alias("track_count"),
                pl.col("duration").sum().alias("total_duration"),
                pl.col("energy").mean().alias("avg_energy"),
                pl.col("bpm").mean().alias("avg_bpm")
            ])
            .sort("track_count", descending=True)
        )
        
        genre_stats['detailed_stats'] = genre_agg.to_dicts()
        
        execution_time = time.time() - start_time
        
        return AnalyticsResult(
            data=genre_stats,
            execution_time=execution_time,
            rows_processed=table.num_rows,
            operation="genre_analysis"
        )
    
    def _value_counts(self, table: pa.Table, column: str, limit: int = None) -> Dict[str, int]:
        """Get value counts for a column."""
        # Use Polars for value_counts (more efficient)
        df = pl.from_arrow(table.select([column]))
        counts = df.get_column(column).value_counts().sort("count", descending=True)
        
        if limit:
            counts = counts.limit(limit)
        
        return dict(zip(counts.get_column(column).to_list(), counts.get_column("count").to_list()))
    
    def _calculate_diversity(self, table: pa.Table, column: str) -> float:
        """Calculate Shannon diversity index."""
        counts = self._value_counts(table, column)
        total = sum(counts.values())
        
        if total == 0:
            return 0.0
        
        diversity = 0.0
        for count in counts.values():
            if count > 0:
                p = count / total
                diversity -= p * np.log2(p)
        
        return diversity
    
    # ===== ADVANCED ANALYTICS =====
    
    def find_similar_tracks(self, track_id: int, limit: int = 10) -> AnalyticsResult:
        """Find similar tracks using Arrow compute for speed."""
        start_time = time.time()
        table = self._get_tracks_arrow_table()
        
        if table.num_rows == 0:
            return AnalyticsResult(data=[], execution_time=0, rows_processed=0, operation="similarity")
        
        # Find target track
        target_track = pc.filter(table, pc.equal(table['id'], track_id))
        
        if target_track.num_rows == 0:
            return AnalyticsResult(data=[], execution_time=0, rows_processed=0, operation="similarity")
        
        target_bpm = target_track['bpm'][0].as_py()
        target_energy = target_track['energy'][0].as_py()
        target_genre = target_track['genre'][0].as_py()
        
        # Calculate similarity scores using Arrow compute
        df = pl.from_arrow(table)
        
        similar_tracks = (
            df.with_columns([
                # BPM similarity (closer = higher score)
                (1.0 / (1.0 + pl.col("bpm").sub(target_bpm).abs())).alias("bpm_similarity"),
                # Energy similarity
                (1.0 / (1.0 + pl.col("energy").sub(target_energy).abs() / 10.0)).alias("energy_similarity"),
                # Genre match (1.0 if same, 0.5 if different)
                pl.when(pl.col("genre") == target_genre).then(1.0).otherwise(0.5).alias("genre_similarity")
            ])
            .with_columns([
                # Combined similarity score
                (pl.col("bpm_similarity") * 0.4 + 
                 pl.col("energy_similarity") * 0.3 + 
                 pl.col("genre_similarity") * 0.3).alias("similarity_score")
            ])
            .filter(pl.col("id") != track_id)  # Exclude the track itself
            .sort("similarity_score", descending=True)
            .limit(limit)
            .select(["id", "title", "artist", "bpm", "energy", "genre", "similarity_score"])
        )
        
        execution_time = time.time() - start_time
        
        return AnalyticsResult(
            data=similar_tracks.to_dicts(),
            execution_time=execution_time,
            rows_processed=table.num_rows,
            operation="similarity"
        )
    
    def generate_smart_playlist(self, criteria: Dict[str, Any], limit: int = 50) -> AnalyticsResult:
        """Generate smart playlist using Arrow filtering."""
        start_time = time.time()
        table = self._get_tracks_arrow_table()
        
        if table.num_rows == 0:
            return AnalyticsResult(data=[], execution_time=0, rows_processed=0, operation="smart_playlist")
        
        df = pl.from_arrow(table)
        
        # Apply filters based on criteria
        filtered_df = df
        
        if 'bpm_min' in criteria:
            filtered_df = filtered_df.filter(pl.col("bpm") >= criteria['bpm_min'])
        
        if 'bpm_max' in criteria:
            filtered_df = filtered_df.filter(pl.col("bpm") <= criteria['bpm_max'])
        
        if 'genres' in criteria:
            filtered_df = filtered_df.filter(pl.col("genre").is_in(criteria['genres']))
        
        if 'energy_min' in criteria:
            filtered_df = filtered_df.filter(pl.col("energy") >= criteria['energy_min'])
        
        if 'energy_max' in criteria:
            filtered_df = filtered_df.filter(pl.col("energy") <= criteria['energy_max'])
        
        if 'year_min' in criteria:
            filtered_df = filtered_df.filter(pl.col("year") >= criteria['year_min'])
        
        if 'year_max' in criteria:
            filtered_df = filtered_df.filter(pl.col("year") <= criteria['year_max'])
        
        # Sort by criteria
        sort_by = criteria.get('sort_by', 'random')
        if sort_by == 'bpm':
            filtered_df = filtered_df.sort("bpm")
        elif sort_by == 'energy':
            filtered_df = filtered_df.sort("energy", descending=True)
        elif sort_by == 'rating':
            filtered_df = filtered_df.sort("rating", descending=True)
        elif sort_by == 'random':
            filtered_df = filtered_df.sample(min(limit, filtered_df.height))
        
        result_tracks = filtered_df.limit(limit).select([
            "id", "title", "artist", "album", "bpm", "energy", "genre", "year"
        ])
        
        execution_time = time.time() - start_time
        
        return AnalyticsResult(
            data=result_tracks.to_dicts(),
            execution_time=execution_time,
            rows_processed=table.num_rows,
            operation="smart_playlist"
        )
    
    def real_time_filter(self, filters: Dict[str, Any]) -> AnalyticsResult:
        """Real-time filtering with Arrow compute for instant results."""
        start_time = time.time()
        table = self._get_tracks_arrow_table()
        
        if table.num_rows == 0:
            return AnalyticsResult(data=[], execution_time=0, rows_processed=0, operation="filter")
        
        df = pl.from_arrow(table)
        
        # Build filter expression
        filter_expr = True
        
        if 'search_text' in filters and filters['search_text']:
            search_text = filters['search_text'].lower()
            filter_expr = (
                pl.col("title").str.to_lowercase().str.contains(search_text) |
                pl.col("artist").str.to_lowercase().str.contains(search_text) |
                pl.col("album").str.to_lowercase().str.contains(search_text) |
                pl.col("genre").str.to_lowercase().str.contains(search_text)
            )
        
        if 'bpm_range' in filters:
            bpm_min, bpm_max = filters['bpm_range']
            filter_expr = filter_expr & (pl.col("bpm") >= bpm_min) & (pl.col("bpm") <= bpm_max)
        
        if 'genres' in filters:
            filter_expr = filter_expr & pl.col("genre").is_in(filters['genres'])
        
        if 'years' in filters:
            filter_expr = filter_expr & pl.col("year").is_in(filters['years'])
        
        if 'energy_range' in filters:
            energy_min, energy_max = filters['energy_range']
            filter_expr = filter_expr & (pl.col("energy") >= energy_min) & (pl.col("energy") <= energy_max)
        
        # Apply filter
        filtered_df = df.filter(filter_expr) if filter_expr is not True else df
        
        # Sort results
        sort_by = filters.get('sort_by', 'title')
        ascending = filters.get('ascending', True)
        
        if sort_by in filtered_df.columns:
            filtered_df = filtered_df.sort(sort_by, descending=not ascending)
        
        execution_time = time.time() - start_time
        
        return AnalyticsResult(
            data=filtered_df.to_dicts(),
            execution_time=execution_time,
            rows_processed=table.num_rows,
            operation="filter"
        )
    
    # ===== UTILITY METHODS =====
    
    def refresh_cache(self):
        """Force refresh of cached data."""
        self.cache.clear()
        self.last_refresh = 0
        print("🔄 PyArrow analytics cache refreshed")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics of the analytics engine."""
        table = self._get_tracks_arrow_table()
        
        return {
            'rows_cached': table.num_rows if 'tracks_table' in self.cache else 0,
            'memory_usage_mb': table.nbytes / (1024 * 1024) if 'tracks_table' in self.cache else 0,
            'last_refresh': self.last_refresh,
            'cache_entries': len(self.cache),
            'arrow_version': pa.__version__,
            'polars_version': pl.__version__
        }


# Global analytics engine instance
analytics_engine = PyArrowAnalyticsEngine()


# Convenience functions for easy use
def get_library_overview() -> Dict[str, Any]:
    """Get library overview using PyArrow analytics."""
    result = analytics_engine.get_library_overview()
    print(f"📊 Library overview computed in {result.execution_time:.3f}s ({result.rows_processed} tracks)")
    return result.data


def analyze_bpm_patterns() -> Dict[str, Any]:
    """Analyze BPM patterns across the library."""
    result = analytics_engine.analyze_bpm_distribution()
    print(f"🎵 BPM analysis completed in {result.execution_time:.3f}s ({result.rows_processed} tracks)")
    return result.data


def find_similar_tracks(track_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Find tracks similar to the given track ID."""
    result = analytics_engine.find_similar_tracks(track_id, limit)
    print(f"🔍 Found {len(result.data)} similar tracks in {result.execution_time:.3f}s")
    return result.data


def generate_smart_playlist(criteria: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
    """Generate smart playlist based on criteria."""
    result = analytics_engine.generate_smart_playlist(criteria, limit)
    print(f"🎵 Generated playlist with {len(result.data)} tracks in {result.execution_time:.3f}s")
    return result.data


def real_time_search(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Perform real-time search with instant results."""
    result = analytics_engine.real_time_filter(filters)
    print(f"⚡ Real-time search: {len(result.data)} results in {result.execution_time:.3f}s")
    return result.data


if __name__ == "__main__":
    # Test the analytics engine
    print("🚀 Testing PyArrow Analytics Engine...")
    
    # Test library overview
    overview = get_library_overview()
    print(f"📊 Library Overview: {overview}")
    
    # Test BPM analysis
    bpm_analysis = analyze_bpm_patterns()
    print(f"🎵 BPM Analysis: {bpm_analysis}")
    
    # Test performance stats
    stats = analytics_engine.get_performance_stats()
    print(f"⚡ Performance Stats: {stats}")
    
    print("✅ PyArrow Analytics Engine test completed")