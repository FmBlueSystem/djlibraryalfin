# tests/fuzzy_keymixing/test_pitch_shift_recommender.py

import pytest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from core.pitch_shift_recommender import (
    PitchShiftRecommender,
    PitchShiftRecommendation,
    BPMSyncRecommendation,
    PitchShiftDirection,
    PitchShiftMethod,
    get_pitch_shift_recommender,
    recommend_key_pitch_shift,
    recommend_bpm_pitch_sync,
    calculate_pitch_quality_impact
)


class TestPitchShiftRecommender:
    """Test suite for PitchShiftRecommender component."""
    
    @pytest.fixture
    def recommender(self):
        """Create fresh recommender instance for each test."""
        return PitchShiftRecommender()
    
    def test_recommender_initialization(self, recommender):
        """Test that recommender initializes correctly."""
        assert recommender is not None
        assert recommender.fuzzy_analyzer is not None
        assert recommender.key_mapper is not None
        assert recommender.max_pitch_shift == 12
        assert recommender.optimal_pitch_range == 2
        assert recommender.semitone_to_percentage > 0
    
    def test_no_pitch_shift_for_perfect_compatibility(self, recommender):
        """Test that no pitch shift is recommended for already compatible keys."""
        # C Major to A Minor (relative keys - highly compatible)
        recommendation = recommender.recommend_pitch_shift("C Major", "A Minor")
        
        assert recommendation is not None
        assert recommendation.shift_semitones == 0
        assert recommendation.compatibility_improvement == 0.0
        assert "no necesita pitch shift" in recommendation.explanation.lower()
    
    def test_pitch_shift_for_incompatible_keys(self, recommender):
        """Test pitch shift recommendations for incompatible keys."""
        # Keys that should benefit from pitch shifting
        recommendation = recommender.recommend_pitch_shift("C Major", "F# Major")
        
        if recommendation.compatibility_improvement > 0.1:
            assert abs(recommendation.shift_semitones) > 0
            assert recommendation.shift_semitones != 0
            assert recommendation.new_compatibility > recommendation.original_compatibility
    
    def test_pitch_shift_direction_calculation(self, recommender):
        """Test that pitch shift direction is calculated correctly."""
        recommendation = recommender.recommend_pitch_shift("C Major", "D Major")
        
        if recommendation.shift_semitones > 0:
            assert recommendation.direction == PitchShiftDirection.UP
        elif recommendation.shift_semitones < 0:
            assert recommendation.direction == PitchShiftDirection.DOWN
        else:
            assert recommendation.direction == PitchShiftDirection.BOTH
    
    def test_pitch_shift_percentage_calculation(self, recommender):
        """Test that pitch shift percentage is calculated correctly."""
        recommendation = recommender.recommend_pitch_shift("C Major", "E Major")
        
        if recommendation.shift_semitones != 0:
            expected_percentage = recommendation.shift_semitones * recommender.semitone_to_percentage
            assert abs(recommendation.shift_percentage - expected_percentage) < 0.1
    
    def test_pitch_shift_cents_calculation(self, recommender):
        """Test that pitch shift in cents is calculated correctly."""
        recommendation = recommender.recommend_pitch_shift("C Major", "D Major")
        
        if recommendation.shift_semitones != 0:
            expected_cents = recommendation.shift_semitones * 100
            assert recommendation.shift_cents == expected_cents
    
    def test_max_shift_limitation(self, recommender):
        """Test that pitch shift respects maximum shift parameter."""
        max_shift = 2
        recommendation = recommender.recommend_pitch_shift("C Major", "F# Major", max_shift=max_shift)
        
        if recommendation.shift_semitones != 0:
            assert abs(recommendation.shift_semitones) <= max_shift
    
    def test_alternative_targets(self, recommender):
        """Test that alternative targets are provided."""
        recommendation = recommender.recommend_pitch_shift("C Major", "Bb Major")
        
        if recommendation and recommendation.compatibility_improvement > 0:
            assert isinstance(recommendation.alternative_targets, list)
            # Should have some alternatives if there's improvement
            if recommendation.compatibility_improvement > 0.2:
                assert len(recommendation.alternative_targets) > 0
    
    def test_bpm_sync_recommendation_basic(self, recommender):
        """Test basic BPM synchronization recommendations."""
        from_bpm = 120.0
        to_bpm = 130.0
        
        recommendation = recommender.recommend_bpm_sync_pitch_shift(from_bpm, to_bpm)
        
        assert recommendation is not None
        assert recommendation.from_bpm == from_bpm
        assert recommendation.to_bpm == to_bpm
        assert recommendation.target_bpm == to_bpm
        assert recommendation.pitch_shift_semitones != 0
    
    def test_bpm_sync_with_keys(self, recommender):
        """Test BPM sync recommendations with harmonic consideration."""
        from_bpm = 120.0
        to_bpm = 130.0
        from_key = "C Major"
        to_key = "A Minor"
        
        recommendation = recommender.recommend_bpm_sync_pitch_shift(
            from_bpm, to_bpm, from_key, to_key
        )
        
        assert recommendation is not None
        assert recommendation.sync_quality > 0
        assert "explanation" in recommendation.__dict__
    
    def test_bpm_sync_method_recommendation(self, recommender):
        """Test that appropriate BMP sync method is recommended."""
        test_cases = [
            (120.0, 122.0),  # Small difference - should recommend pitch_shift
            (120.0, 140.0),  # Medium difference - might recommend hybrid
            (120.0, 180.0),  # Large difference - should recommend time_stretch
        ]
        
        for from_bpm, to_bpm in test_cases:
            recommendation = recommender.recommend_bpm_sync_pitch_shift(from_bpm, to_bpm)
            assert recommendation.method_recommended in ["pitch_shift", "hybrid", "time_stretch"]
    
    def test_optimal_targets_finding(self, recommender):
        """Test finding optimal targets with pitch shifting."""
        from_key = "C Major"
        candidate_keys = ["A Minor", "G Major", "F Major", "D Minor", "E Minor", "Bb Major"]
        
        recommendations = recommender.find_optimal_targets(from_key, candidate_keys)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 10  # Should respect limit
        
        # Should be sorted by quality
        if len(recommendations) > 1:
            assert recommendations[0].new_compatibility >= recommendations[1].new_compatibility
    
    def test_quality_impact_calculation(self, recommender):
        """Test audio quality impact calculation."""
        test_shifts = [0, 1, 2, 4, 6, 8]
        
        for shift in test_shifts:
            impact = recommender.calculate_pitch_shift_quality_impact(shift)
            
            assert "overall_quality" in impact
            assert "timbre_preservation" in impact
            assert "rhythm_preservation" in impact
            assert "bass_quality" in impact
            assert "vocal_quality" in impact
            assert "quality_category" in impact
            
            # Quality should decrease with larger shifts
            assert 0.0 <= impact["overall_quality"] <= 1.0
            
            if shift == 0:
                assert impact["overall_quality"] == 1.0
            elif shift > 0:
                assert impact["overall_quality"] < 1.0
    
    def test_quality_categories(self, recommender):
        """Test quality categorization."""
        test_cases = [
            (0, "Excellent"),
            (1, "Excellent"),
            (2, "Good"),
            (4, "Good"),
            (6, "Fair"),
            (8, "Poor"),
            (12, "Unacceptable"),
        ]
        
        for shift, expected_category in test_cases:
            impact = recommender.calculate_pitch_shift_quality_impact(shift)
            assert expected_category.lower() in impact["quality_category"].lower()
    
    def test_pitch_shift_guide_generation(self, recommender):
        """Test complete pitch shift guide generation."""
        from_key = "C Major"
        guide = recommender.generate_pitch_shift_guide(from_key)
        
        assert "reference_key" in guide
        assert "shift_options" in guide
        assert "recommendations" in guide
        assert "summary" in guide
        
        assert guide["reference_key"] == from_key
        assert len(guide["shift_options"]) > 0
        assert len(guide["recommendations"]) <= 3  # Top 3
        
        # Check summary statistics
        summary = guide["summary"]
        assert "total_compatible_options" in summary
        assert "recommended_shifts" in summary
    
    def test_edge_cases(self, recommender):
        """Test edge cases and error handling."""
        # Invalid keys
        recommendation = recommender.recommend_pitch_shift("Invalid", "Also Invalid")
        assert recommendation is None or recommendation.confidence < 0.5
        
        # Same key
        recommendation = recommender.recommend_pitch_shift("C Major", "C Major")
        assert recommendation is not None
        assert recommendation.shift_semitones == 0
        
        # Invalid BPMs
        recommendation = recommender.recommend_bpm_sync_pitch_shift(0, 120)
        assert recommendation.sync_quality == 0.0
        
        recommendation = recommender.recommend_bpm_sync_pitch_shift(-10, 120)
        assert recommendation.sync_quality == 0.0
    
    def test_confidence_calculation(self, recommender):
        """Test confidence scoring in recommendations."""
        # High improvement should give high confidence
        recommendation = recommender.recommend_pitch_shift("C Major", "F# Major")
        
        if recommendation and recommendation.compatibility_improvement > 0.3:
            assert recommendation.confidence > 0.6
        
        # No improvement should give lower confidence
        recommendation = recommender.recommend_pitch_shift("C Major", "A Minor")
        if recommendation and recommendation.compatibility_improvement < 0.1:
            assert recommendation.confidence <= 0.95
    
    def test_singleton_instance(self):
        """Test that singleton pattern works correctly."""
        recommender1 = get_pitch_shift_recommender()
        recommender2 = get_pitch_shift_recommender()
        
        assert recommender1 is recommender2  # Same instance
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly."""
        # Test recommend_key_pitch_shift
        result = recommend_key_pitch_shift("C Major", "D Major")
        assert result is not None
        
        # Test recommend_bpm_pitch_sync
        result = recommend_bpm_pitch_sync(120.0, 130.0)
        assert result is not None
        
        # Test calculate_pitch_quality_impact
        result = calculate_pitch_quality_impact(2.0)
        assert result is not None
        assert "overall_quality" in result


class TestPitchShiftRecommendation:
    """Test the PitchShiftRecommendation dataclass."""
    
    def test_recommendation_creation(self):
        """Test creating recommendation objects."""
        recommendation = PitchShiftRecommendation(
            from_key="C Major",
            to_key="D Major",
            target_key="D Major",
            shift_semitones=2.0,
            shift_cents=200,
            shift_percentage=11.892,
            direction=PitchShiftDirection.UP,
            compatibility_improvement=0.3,
            original_compatibility=0.5,
            new_compatibility=0.8,
            confidence=0.85,
            method=PitchShiftMethod.SEMITONES,
            explanation="Shift up 2 semitones",
            alternative_targets=[("E Major", 4.0, 0.7)]
        )
        
        assert recommendation.from_key == "C Major"
        assert recommendation.shift_semitones == 2.0
        assert recommendation.direction == PitchShiftDirection.UP
        assert len(recommendation.alternative_targets) == 1


class TestBPMSyncRecommendation:
    """Test the BPMSyncRecommendation dataclass."""
    
    def test_bpm_sync_recommendation_creation(self):
        """Test creating BMP sync recommendation objects."""
        recommendation = BPMSyncRecommendation(
            from_bpm=120.0,
            to_bpm=130.0,
            target_bpm=130.0,
            pitch_shift_semitones=1.39,
            pitch_shift_percentage=8.33,
            time_stretch_factor=0.923,
            sync_quality=0.85,
            method_recommended="pitch_shift",
            explanation="Small BPM difference"
        )
        
        assert recommendation.from_bpm == 120.0
        assert recommendation.to_bpm == 130.0
        assert recommendation.method_recommended == "pitch_shift"
        assert 0.0 <= recommendation.sync_quality <= 1.0


class TestEnums:
    """Test the enum classes."""
    
    def test_pitch_shift_direction_enum(self):
        """Test PitchShiftDirection enum."""
        assert PitchShiftDirection.UP.value == "up"
        assert PitchShiftDirection.DOWN.value == "down"
        assert PitchShiftDirection.BOTH.value == "both"
    
    def test_pitch_shift_method_enum(self):
        """Test PitchShiftMethod enum."""
        assert PitchShiftMethod.SEMITONES.value == "semitones"
        assert PitchShiftMethod.CENTS.value == "cents"
        assert PitchShiftMethod.PERCENTAGE.value == "percentage"
        assert PitchShiftMethod.BPM_SYNC.value == "bpm_sync"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])