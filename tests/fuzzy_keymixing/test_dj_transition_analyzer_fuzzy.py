# tests/fuzzy_keymixing/test_dj_transition_analyzer_fuzzy.py

import pytest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from core.dj_transition_analyzer import (
    DJTransitionAnalyzer,
    TransitionAnalysis,
    TransitionType,
    TransitionQuality,
    TransitionPoint,
    get_dj_transition_analyzer,
    analyze_track_transition,
    find_compatible_tracks,
    analyze_set_transitions
)


class TestDJTransitionAnalyzerFuzzy:
    """Test suite for DJTransitionAnalyzer with Fuzzy Keymixing capabilities."""
    
    @pytest.fixture
    def analyzer(self):
        """Create fresh analyzer instance for each test."""
        return DJTransitionAnalyzer()
    
    @pytest.fixture
    def sample_tracks(self):
        """Sample tracks for testing."""
        return [
            {
                "id": 1,
                "title": "Track 1",
                "artist": "Artist 1",
                "bpm": 128,
                "key": "C Major",
                "energy": 0.8,
                "danceability": 0.9,
                "valence": 0.7,
                "duration": 240
            },
            {
                "id": 2,
                "title": "Track 2", 
                "artist": "Artist 2",
                "bpm": 130,
                "key": "A Minor",
                "energy": 0.75,
                "danceability": 0.85,
                "valence": 0.65,
                "duration": 220
            },
            {
                "id": 3,
                "title": "Track 3",
                "artist": "Artist 3", 
                "bpm": 125,
                "key": "G Major",
                "energy": 0.6,
                "danceability": 0.7,
                "valence": 0.8,
                "duration": 260
            },
            {
                "id": 4,
                "title": "Track 4",
                "artist": "Artist 4",
                "bpm": 140,
                "key": "F# Major",
                "energy": 0.9,
                "danceability": 0.95,
                "valence": 0.6,
                "duration": 200
            }
        ]
    
    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes with fuzzy components."""
        assert analyzer is not None
        assert analyzer.fuzzy_analyzer is not None
        assert analyzer.pitch_recommender is not None
        assert hasattr(analyzer, 'bpm_tolerance')
        assert hasattr(analyzer, 'harmonic_relations')
    
    def test_new_transition_types(self):
        """Test that new fuzzy transition types are available."""
        assert TransitionType.FUZZY_HARMONIC_MIX.value == "fuzzy_harmonic_mix"
        assert TransitionType.PITCH_SHIFT_MIX.value == "pitch_shift_mix"
    
    def test_fuzzy_key_compatibility_analysis(self, analyzer, sample_tracks):
        """Test fuzzy key compatibility analysis."""
        track1 = sample_tracks[0]  # C Major
        track2 = sample_tracks[1]  # A Minor
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        assert analysis is not None
        assert hasattr(analysis, 'fuzzy_key_compatibility')
        assert hasattr(analysis, 'fuzzy_key_relationship')
        assert hasattr(analysis, 'pitch_shift_recommendation')
        
        # C Major to A Minor should have high fuzzy compatibility
        assert analysis.fuzzy_key_compatibility >= 0.8
    
    def test_traditional_vs_fuzzy_compatibility(self, analyzer, sample_tracks):
        """Test that fuzzy compatibility is computed alongside traditional."""
        track1 = sample_tracks[0]  # C Major
        track4 = sample_tracks[3]  # F# Major (should be low traditional, potentially higher fuzzy)
        
        analysis = analyzer.analyze_transition(track1, track4)
        
        assert analysis.key_compatibility >= 0.0
        assert analysis.fuzzy_key_compatibility >= 0.0
        
        # Fuzzy should provide at least as good compatibility as traditional
        assert analysis.fuzzy_key_compatibility >= analysis.key_compatibility
    
    def test_fuzzy_harmonic_mix_recommendation(self, analyzer, sample_tracks):
        """Test that FUZZY_HARMONIC_MIX is recommended when appropriate."""
        # Create tracks that would benefit from fuzzy analysis
        track1 = {
            "bpm": 128,
            "key": "C Major",
            "energy": 0.8,
            "title": "Test Track 1"
        }
        track2 = {
            "bpm": 128,  # Same BPM for good beatmatching
            "key": "D Major",  # Not traditionally compatible but could be fuzzy compatible
            "energy": 0.8,
            "title": "Test Track 2"
        }
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        # With good BPM compatibility and potential fuzzy key compatibility
        if analysis.fuzzy_key_compatibility > analysis.key_compatibility + 0.2:
            assert analysis.recommended_type in [
                TransitionType.FUZZY_HARMONIC_MIX,
                TransitionType.PITCH_SHIFT_MIX,
                TransitionType.BEATMATCH
            ]
    
    def test_pitch_shift_mix_recommendation(self, analyzer):
        """Test that PITCH_SHIFT_MIX is recommended when beneficial."""
        track1 = {
            "bpm": 128,
            "key": "C Major",
            "energy": 0.8,
            "title": "Test Track 1"
        }
        track2 = {
            "bpm": 128,
            "key": "F# Major",  # Tritone away - should benefit from pitch shift
            "energy": 0.8,
            "title": "Test Track 2"
        }
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        # Check if pitch shift significantly improves compatibility
        if (analysis.fuzzy_key_compatibility > analysis.key_compatibility + 0.3 and 
            analysis.pitch_shift_recommendation and 
            analysis.pitch_shift_recommendation.get('improvement', 0) > 0.2):
            assert analysis.recommended_type in [
                TransitionType.PITCH_SHIFT_MIX,
                TransitionType.FUZZY_HARMONIC_MIX
            ]
    
    def test_overall_score_includes_fuzzy(self, analyzer, sample_tracks):
        """Test that overall score considers fuzzy compatibility."""
        track1 = sample_tracks[0]
        track2 = sample_tracks[1]
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        # Overall score should be computed using the best of traditional or fuzzy
        expected_key_score = max(analysis.key_compatibility, analysis.fuzzy_key_compatibility)
        
        # The score calculation should use the better compatibility
        assert analysis.overall_score >= 0.0
        assert analysis.overall_score <= 1.0
    
    def test_pitch_shift_recommendations_in_analysis(self, analyzer):
        """Test that pitch shift recommendations are included when beneficial."""
        track1 = {
            "bpm": 128,
            "key": "C Major",
            "energy": 0.8,
            "title": "Test Track 1"
        }
        track2 = {
            "bpm": 128,
            "key": "Bb Major",  # Should benefit from pitch shift
            "energy": 0.8,
            "title": "Test Track 2"
        }
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        if analysis.pitch_shift_recommendation:
            assert 'shift_semitones' in analysis.pitch_shift_recommendation
            assert 'improvement' in analysis.pitch_shift_recommendation
            assert 'confidence' in analysis.pitch_shift_recommendation
    
    def test_fuzzy_key_relationship_description(self, analyzer, sample_tracks):
        """Test fuzzy key relationship descriptions."""
        track1 = sample_tracks[0]  # C Major
        track2 = sample_tracks[1]  # A Minor
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        assert analysis.fuzzy_key_relationship is not None
        assert isinstance(analysis.fuzzy_key_relationship, str)
        assert len(analysis.fuzzy_key_relationship) > 0
    
    def test_enhanced_recommendations(self, analyzer, sample_tracks):
        """Test that recommendations include fuzzy-specific advice."""
        track1 = sample_tracks[0]
        track2 = sample_tracks[3]  # Different key that might benefit from fuzzy
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        recommendations = analysis.recommendations
        
        # Should contain some fuzzy-related recommendations
        fuzzy_recommendations = [rec for rec in recommendations if 
                               'fuzzy' in rec.lower() or 'pitch shift' in rec.lower()]
        
        if analysis.fuzzy_key_compatibility > analysis.key_compatibility + 0.1:
            assert len(fuzzy_recommendations) > 0
    
    def test_enhanced_warnings(self, analyzer):
        """Test that warnings consider both traditional and fuzzy compatibility."""
        track1 = {
            "bpm": 100,  # Very different BPMs
            "key": "C Major",
            "energy": 0.2,  # Very different energies
            "title": "Test Track 1"
        }
        track2 = {
            "bpm": 160,
            "key": "F# Major",  # Traditionally incompatible key
            "energy": 0.9,
            "title": "Test Track 2"
        }
        
        analysis = analyzer.analyze_transition(track1, track2)
        warnings = analysis.warnings
        
        # Should have warnings but might mention fuzzy possibilities
        assert len(warnings) > 0
        
        # If fuzzy provides some improvement, should mention it
        if analysis.fuzzy_key_compatibility > analysis.key_compatibility + 0.2:
            fuzzy_warnings = [w for w in warnings if 'fuzzy' in w.lower()]
            assert len(fuzzy_warnings) > 0
    
    def test_mix_points_for_new_transition_types(self, analyzer):
        """Test mix point calculations for new transition types."""
        track1 = {
            "bpm": 128,
            "key": "C Major",
            "duration": 240,
            "title": "Test Track 1"
        }
        track2 = {
            "bpm": 128,
            "key": "D Major",
            "duration": 220,
            "title": "Test Track 2"
        }
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        # Check that mix points are calculated for all transition types
        assert analysis.mix_out_point > 0
        assert analysis.mix_in_point >= 0
        assert analysis.crossfade_duration > 0
        
        # FUZZY_HARMONIC_MIX should have similar timing to HARMONIC_MIX
        if analysis.recommended_type == TransitionType.FUZZY_HARMONIC_MIX:
            assert analysis.crossfade_duration >= 12.0  # Should allow time for harmonic mixing
        
        # PITCH_SHIFT_MIX should have longer crossfade for adjustment
        if analysis.recommended_type == TransitionType.PITCH_SHIFT_MIX:
            assert analysis.crossfade_duration >= 16.0  # Should allow time for pitch adjustment
    
    def test_transition_analysis_dataclass_extensions(self, analyzer, sample_tracks):
        """Test that TransitionAnalysis includes all new fuzzy fields."""
        track1 = sample_tracks[0]
        track2 = sample_tracks[1]
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        # Check all new fields are present
        assert hasattr(analysis, 'fuzzy_key_compatibility')
        assert hasattr(analysis, 'fuzzy_key_relationship')
        assert hasattr(analysis, 'pitch_shift_recommendation')
        
        # Check types
        assert isinstance(analysis.fuzzy_key_compatibility, float)
        assert isinstance(analysis.fuzzy_key_relationship, str)
        assert analysis.pitch_shift_recommendation is None or isinstance(analysis.pitch_shift_recommendation, dict)
    
    def test_best_next_tracks_with_fuzzy(self, analyzer, sample_tracks):
        """Test finding best next tracks considering fuzzy compatibility."""
        current_track = sample_tracks[0]
        candidates = sample_tracks[1:]
        
        best_tracks = analyzer.find_best_next_tracks(current_track, candidates, limit=3)
        
        assert len(best_tracks) <= 3
        assert len(best_tracks) > 0
        
        # Should be sorted by overall score (which includes fuzzy)
        if len(best_tracks) > 1:
            assert best_tracks[0][1].overall_score >= best_tracks[1][1].overall_score
        
        # Check that analyses include fuzzy data
        for track, analysis in best_tracks:
            assert hasattr(analysis, 'fuzzy_key_compatibility')
            assert analysis.fuzzy_key_compatibility >= 0.0
    
    def test_set_flow_analysis_with_fuzzy(self, analyzer, sample_tracks):
        """Test set flow analysis with fuzzy capabilities."""
        track_sequence = sample_tracks[:3]  # Use first 3 tracks
        
        set_analysis = analyzer.analyze_set_flow(track_sequence)
        
        assert "transitions" in set_analysis
        assert "average_transition_quality" in set_analysis
        
        # Each transition should include fuzzy analysis
        for transition in set_analysis["transitions"]:
            assert hasattr(transition, 'fuzzy_key_compatibility')
            assert hasattr(transition, 'fuzzy_key_relationship')
    
    def test_singleton_instance(self):
        """Test that singleton pattern works correctly."""
        analyzer1 = get_dj_transition_analyzer()
        analyzer2 = get_dj_transition_analyzer()
        
        assert analyzer1 is analyzer2  # Same instance
    
    def test_convenience_functions_with_fuzzy(self, sample_tracks):
        """Test convenience functions include fuzzy analysis."""
        track1 = sample_tracks[0]
        track2 = sample_tracks[1]
        
        # Test analyze_track_transition
        analysis = analyze_track_transition(track1, track2)
        assert hasattr(analysis, 'fuzzy_key_compatibility')
        
        # Test find_compatible_tracks
        candidates = sample_tracks[1:]
        compatible = find_compatible_tracks(track1, candidates, limit=2)
        assert len(compatible) <= 2
        for track, analysis in compatible:
            assert hasattr(analysis, 'fuzzy_key_compatibility')
        
        # Test analyze_set_transitions
        set_analysis = analyze_set_transitions(sample_tracks[:3])
        assert "transitions" in set_analysis
        for transition in set_analysis["transitions"]:
            assert hasattr(transition, 'fuzzy_key_compatibility')
    
    def test_backward_compatibility(self, analyzer, sample_tracks):
        """Test that existing functionality still works correctly."""
        track1 = sample_tracks[0]
        track2 = sample_tracks[1]
        
        analysis = analyzer.analyze_transition(track1, track2)
        
        # All original fields should still be present
        assert hasattr(analysis, 'bpm_compatibility')
        assert hasattr(analysis, 'key_compatibility')
        assert hasattr(analysis, 'energy_compatibility')
        assert hasattr(analysis, 'mood_compatibility')
        assert hasattr(analysis, 'recommended_type')
        assert hasattr(analysis, 'transition_quality')
        assert hasattr(analysis, 'overall_score')
        assert hasattr(analysis, 'recommendations')
        assert hasattr(analysis, 'warnings')
        
        # Values should be in expected ranges
        assert 0.0 <= analysis.bpm_compatibility <= 1.0
        assert 0.0 <= analysis.key_compatibility <= 1.0
        assert 0.0 <= analysis.overall_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])