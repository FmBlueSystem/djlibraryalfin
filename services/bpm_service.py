"""Service layer for BPM analysis independent of any UI framework."""
from core.bpm_analyzer import analyze_track_bpm

class BPMService:
    """Wraps BPM analysis logic for easy consumption by higher layers."""

    def analyze(self, file_path: str):
        """Return BPM analysis result for the given audio file."""
        return analyze_track_bpm(file_path)
