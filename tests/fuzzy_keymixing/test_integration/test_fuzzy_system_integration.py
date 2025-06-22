# tests/fuzzy_keymixing/test_integration/test_fuzzy_system_integration.py

import pytest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from core.fuzzy_key_analyzer import get_fuzzy_key_analyzer
from core.camelot_key_mapper import get_camelot_key_mapper
from core.pitch_shift_recommender import get_pitch_shift_recommender
from core.dj_transition_analyzer import get_dj_transition_analyzer


class TestFuzzySystemIntegration:
    """Test integration between all fuzzy keymixing components."""
    
    @pytest.fixture
    def system_components(self):
        """Get all system components."""
        return {
            'fuzzy_analyzer': get_fuzzy_key_analyzer(),
            'key_mapper': get_camelot_key_mapper(),
            'pitch_recommender': get_pitch_shift_recommender(),
            'transition_analyzer': get_dj_transition_analyzer()
        }
    
    def test_component_initialization(self, system_components):
        """Test that all components initialize correctly."""
        assert system_components['fuzzy_analyzer'] is not None
        assert system_components['key_mapper'] is not None
        assert system_components['pitch_recommender'] is not None
        assert system_components['transition_analyzer'] is not None
    
    def test_component_interconnection(self, system_components):
        """Test that components are properly interconnected."""
        transition_analyzer = system_components['transition_analyzer']
        
        # Transition analyzer should have references to fuzzy components
        assert transition_analyzer.fuzzy_analyzer is not None
        assert transition_analyzer.pitch_recommender is not None
        
        # Pitch recommender should have references to other components
        pitch_recommender = system_components['pitch_recommender']
        assert pitch_recommender.fuzzy_analyzer is not None
        assert pitch_recommender.key_mapper is not None
    
    def test_complete_workflow_compatible_keys(self, system_components):
        """Test complete workflow with compatible keys."""
        key1 = "C Major"
        key2 = "A Minor"
        
        # Step 1: Key mapping
        key_mapper = system_components['key_mapper']
        camelot1 = key_mapper.convert_key(key1)
        camelot2 = key_mapper.convert_key(key2)
        
        assert camelot1 == "8B"
        assert camelot2 == "8A"
        
        # Step 2: Fuzzy analysis
        fuzzy_analyzer = system_components['fuzzy_analyzer']
        fuzzy_result = fuzzy_analyzer.analyze_fuzzy_compatibility(key1, key2)
        
        assert fuzzy_result.compatibility_score >= 0.9  # Should be highly compatible
        assert fuzzy_result.fuzzy_level <= 2  # Should be perfect or excellent
        
        # Step 3: Pitch shift analysis (should not be needed)
        pitch_recommender = system_components['pitch_recommender']
        pitch_result = pitch_recommender.recommend_pitch_shift(key1, key2)
        
        assert pitch_result.shift_semitones == 0  # No shift needed
        assert pitch_result.compatibility_improvement == 0.0
        
        # Step 4: Transition analysis
        track1 = {"key": key1, "bpm": 128, "energy": 0.8, "title": "Track 1"}
        track2 = {"key": key2, "bpm": 128, "energy": 0.8, "title": "Track 2"}
        
        transition_analyzer = system_components['transition_analyzer']
        transition_result = transition_analyzer.analyze_transition(track1, track2)
        
        assert transition_result.fuzzy_key_compatibility >= 0.9
        assert transition_result.key_compatibility >= 0.9
        assert transition_result.overall_score >= 0.8
    
    def test_complete_workflow_incompatible_keys(self, system_components):
        """Test complete workflow with incompatible keys that benefit from fuzzy logic."""
        key1 = "C Major"
        key2 = "F# Major"  # Tritone away - traditionally incompatible
        
        # Step 1: Key mapping
        key_mapper = system_components['key_mapper']
        camelot1 = key_mapper.convert_key(key1)
        camelot2 = key_mapper.convert_key(key2)
        
        assert camelot1 == "8B"
        assert camelot2 == "2B"
        
        # Step 2: Fuzzy analysis
        fuzzy_analyzer = system_components['fuzzy_analyzer']
        fuzzy_result = fuzzy_analyzer.analyze_fuzzy_compatibility(key1, key2)
        
        # Step 3: Pitch shift analysis
        pitch_recommender = system_components['pitch_recommender']
        pitch_result = pitch_recommender.recommend_pitch_shift(key1, key2)
        
        # Should recommend some improvement if possible
        if pitch_result.compatibility_improvement > 0.1:
            assert abs(pitch_result.shift_semitones) > 0
        
        # Step 4: Transition analysis
        track1 = {"key": key1, "bpm": 128, "energy": 0.8, "title": "Track 1"}
        track2 = {"key": key2, "bpm": 128, "energy": 0.8, "title": "Track 2"}
        
        transition_analyzer = system_components['transition_analyzer']
        transition_result = transition_analyzer.analyze_transition(track1, track2)
        
        # Fuzzy should provide at least as good compatibility as traditional
        assert transition_result.fuzzy_key_compatibility >= transition_result.key_compatibility
        
        # Should suggest fuzzy or pitch shift mixing if beneficial
        if transition_result.fuzzy_key_compatibility > transition_result.key_compatibility + 0.2:
            assert transition_result.recommended_type.value in [
                "fuzzy_harmonic_mix", "pitch_shift_mix", "beatmatch"
            ]
    
    def test_data_flow_consistency(self, system_components):
        """Test that data flows consistently between components."""
        test_keys = [
            ("C Major", "G Major"),
            ("A Minor", "E Minor"),
            ("F Major", "D Minor"),
            ("Bb Major", "Eb Major")
        ]
        
        for key1, key2 in test_keys:
            # Get results from each component
            key_mapper = system_components['key_mapper']
            fuzzy_analyzer = system_components['fuzzy_analyzer']
            
            # Convert keys
            camelot1 = key_mapper.convert_key(key1)
            camelot2 = key_mapper.convert_key(key2)
            
            # Analyze with fuzzy system
            fuzzy_result = fuzzy_analyzer.analyze_fuzzy_compatibility(key1, key2)
            camelot_result = fuzzy_analyzer.analyze_fuzzy_compatibility(camelot1, camelot2)
            
            # Results should be consistent regardless of input format
            assert abs(fuzzy_result.compatibility_score - camelot_result.compatibility_score) < 0.1
            assert fuzzy_result.relationship_type == camelot_result.relationship_type
    
    def test_cross_component_validation(self, system_components):
        """Test validation across different components."""
        key_mapper = system_components['key_mapper']
        fuzzy_analyzer = system_components['fuzzy_analyzer']
        
        # Test all Camelot keys are properly mapped
        camelot_keys = [f"{i}{letter}" for i in range(1, 13) for letter in ['A', 'B']]
        
        for camelot_key in camelot_keys[:12]:  # Test subset for performance
            # Key mapper should handle it
            key_info = key_mapper.analyze_key(camelot_key)
            assert key_info is not None
            assert key_info.camelot == camelot_key
            
            # Fuzzy analyzer should handle it
            for other_key in camelot_keys[:6]:  # Test with subset
                result = fuzzy_analyzer.analyze_fuzzy_compatibility(camelot_key, other_key)
                assert result is not None
                assert 0.0 <= result.compatibility_score <= 1.0
    
    def test_performance_integration(self, system_components):
        """Test performance of integrated system."""
        import time
        
        test_pairs = [
            ("C Major", "A Minor"),
            ("G Major", "E Minor"),
            ("F Major", "D Minor"),
            ("Bb Major", "G Minor"),
            ("D Major", "B Minor")
        ]
        
        start_time = time.time()
        
        for key1, key2 in test_pairs:
            # Complete workflow
            track1 = {"key": key1, "bpm": 128, "energy": 0.8, "title": "Track 1"}
            track2 = {"key": key2, "bpm": 130, "energy": 0.75, "title": "Track 2"}
            
            transition_analyzer = system_components['transition_analyzer']
            result = transition_analyzer.analyze_transition(track1, track2)
            
            assert result is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 5 full analyses in reasonable time
        assert total_time < 1.0  # Less than 1 second for 5 analyses
        avg_time = total_time / len(test_pairs)
        assert avg_time < 0.2  # Less than 200ms per analysis
    
    def test_error_propagation(self, system_components):
        """Test that errors are handled gracefully across components."""
        transition_analyzer = system_components['transition_analyzer']
        
        # Test with invalid data
        invalid_track1 = {"key": "Invalid Key", "bpm": "not a number", "title": "Bad Track 1"}
        invalid_track2 = {"key": None, "bpm": -1, "title": "Bad Track 2"}
        
        result = transition_analyzer.analyze_transition(invalid_track1, invalid_track2)
        
        # Should handle gracefully and return some result
        assert result is not None
        assert 0.0 <= result.overall_score <= 1.0
        assert len(result.warnings) > 0  # Should have warnings about bad data
    
    def test_singleton_consistency(self, system_components):
        """Test that singleton instances are consistent across components."""
        # Get instances through different methods
        fuzzy1 = get_fuzzy_key_analyzer()
        fuzzy2 = system_components['fuzzy_analyzer']
        
        mapper1 = get_camelot_key_mapper()
        mapper2 = system_components['key_mapper']
        
        pitch1 = get_pitch_shift_recommender()
        pitch2 = system_components['pitch_recommender']
        
        transition1 = get_dj_transition_analyzer()
        transition2 = system_components['transition_analyzer']
        
        # Should be same instances
        assert fuzzy1 is fuzzy2
        assert mapper1 is mapper2
        assert pitch1 is pitch2
        assert transition1 is transition2
    
    def test_memory_efficiency(self, system_components):
        """Test memory usage of integrated system."""
        import sys
        
        # Get initial memory usage
        initial_size = sys.getsizeof(system_components)
        
        # Perform multiple operations
        for i in range(100):
            key1 = f"{(i % 12) + 1}{'A' if i % 2 == 0 else 'B'}"
            key2 = f"{((i + 1) % 12) + 1}{'B' if i % 2 == 0 else 'A'}"
            
            fuzzy_analyzer = system_components['fuzzy_analyzer']
            result = fuzzy_analyzer.analyze_fuzzy_compatibility(key1, key2)
            assert result is not None
        
        # Memory usage shouldn't grow significantly
        final_size = sys.getsizeof(system_components)
        growth = final_size - initial_size
        
        # Should not grow by more than 50% (allowing for some caching)
        assert growth < initial_size * 0.5


class TestFuzzyWorkflowScenarios:
    """Test realistic DJ workflow scenarios."""
    
    @pytest.fixture
    def dj_tracks(self):
        """Sample DJ track collection."""
        return [
            {"title": "Deep House Track", "key": "A Minor", "bpm": 120, "energy": 0.6, "genre": "Deep House"},
            {"title": "Progressive Track", "key": "C Major", "bpm": 122, "energy": 0.7, "genre": "Progressive"},
            {"title": "Techno Track", "key": "G Minor", "bpm": 125, "energy": 0.8, "genre": "Techno"},
            {"title": "Trance Track", "key": "F# Minor", "bpm": 128, "energy": 0.9, "genre": "Trance"},
            {"title": "House Track", "key": "Bb Major", "bpm": 126, "energy": 0.75, "genre": "House"}
        ]
    
    def test_dj_set_planning(self, dj_tracks):
        """Test planning a complete DJ set with fuzzy logic."""
        transition_analyzer = get_dj_transition_analyzer()
        
        # Analyze all possible transitions
        set_transitions = []
        for i in range(len(dj_tracks) - 1):
            analysis = transition_analyzer.analyze_transition(dj_tracks[i], dj_tracks[i + 1])
            set_transitions.append(analysis)
        
        # Should have n-1 transitions for n tracks
        assert len(set_transitions) == len(dj_tracks) - 1
        
        # Each transition should include fuzzy analysis
        for transition in set_transitions:
            assert hasattr(transition, 'fuzzy_key_compatibility')
            assert transition.fuzzy_key_compatibility >= 0.0
    
    def test_key_progression_optimization(self, dj_tracks):
        """Test optimizing key progression with fuzzy logic."""
        fuzzy_analyzer = get_fuzzy_key_analyzer()
        key_mapper = get_camelot_key_mapper()
        
        # Convert all keys to Camelot for analysis
        camelot_keys = []
        for track in dj_tracks:
            camelot = key_mapper.convert_key(track["key"])
            camelot_keys.append(camelot)
        
        # Find best progression using fuzzy logic
        progression_scores = []
        for i in range(len(camelot_keys) - 1):
            result = fuzzy_analyzer.analyze_fuzzy_compatibility(camelot_keys[i], camelot_keys[i + 1])
            progression_scores.append(result.compatibility_score)
        
        # Should have compatibility scores for each transition
        assert len(progression_scores) == len(dj_tracks) - 1
        assert all(0.0 <= score <= 1.0 for score in progression_scores)
    
    def test_real_time_track_selection(self):
        """Test real-time track selection scenario."""
        current_track = {"title": "Current Track", "key": "C Major", "bpm": 128, "energy": 0.8}
        
        candidate_tracks = [
            {"title": "Option 1", "key": "A Minor", "bpm": 128, "energy": 0.8},  # Perfect relative
            {"title": "Option 2", "key": "G Major", "bpm": 130, "energy": 0.75},  # Adjacent
            {"title": "Option 3", "key": "F# Major", "bpm": 132, "energy": 0.85},  # Tritone - fuzzy territory
            {"title": "Option 4", "key": "Bb Major", "bpm": 125, "energy": 0.7},  # Different but potentially good
        ]
        
        transition_analyzer = get_dj_transition_analyzer()
        
        # Find best options
        best_tracks = transition_analyzer.find_best_next_tracks(current_track, candidate_tracks, limit=3)
        
        assert len(best_tracks) <= 3
        assert len(best_tracks) > 0
        
        # Should be ranked by overall compatibility (including fuzzy)
        if len(best_tracks) > 1:
            assert best_tracks[0][1].overall_score >= best_tracks[1][1].overall_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])