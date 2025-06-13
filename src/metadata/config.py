"""
Configuration module for metadata improvement pipeline.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MetadataConfig:
    """Configuration for metadata improvement pipeline."""
    
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    anomaly_model_path: Optional[str] = None
    quality_threshold: float = 0.7
    max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    
    @classmethod
    def from_env(cls) -> 'MetadataConfig':
        """Create configuration from environment variables."""
        return cls(
            spotify_client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            spotify_client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            anomaly_model_path=os.getenv('ANOMALY_MODEL_PATH', 'models/anomaly_detector.pkl'),
            quality_threshold=float(os.getenv('QUALITY_THRESHOLD', '0.7')),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            cache_enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            cache_ttl_hours=int(os.getenv('CACHE_TTL_HOURS', '24'))
        )
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.spotify_client_id or not self.spotify_client_secret:
            return False
        return True