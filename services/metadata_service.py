"""Service layer for metadata enrichment independent of the GUI."""
from core.metadata_enricher import enrich_metadata

class MetadataService:
    """Expose metadata enrichment without tying to a UI framework."""

    def enrich(self, track_info: dict):
        """Return enriched metadata for the given track info."""
        return enrich_metadata(track_info)
