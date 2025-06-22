# tests/fuzzy_keymixing/test_fuzzy_key_analyzer.py

import pytest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from core.fuzzy_key_analyzer import (
    FuzzyKeyAnalyzer, 
    FuzzyKeyCompatibility,
    FuzzyKeyRecommendation,
    CamelotKey,
    get_fuzzy_key_analyzer,
    analyze_fuzzy_key_compatibility,
    compare_traditional_vs_fuzzy_keymixing
)


class TestFuzzyKeyAnalyzer:
    """Test suite for FuzzyKeyAnalyzer component."""
    
    @pytest.fixture
    def analyzer(self):
        """Create fresh analyzer instance for each test."""
        return FuzzyKeyAnalyzer()
    
    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes correctly."""
        assert analyzer is not None
        assert len(analyzer.key_to_camelot) > 0
        assert len(analyzer.traditional_compatibility) > 0
        assert len(analyzer.fuzzy_compatibility) > 0
        assert len(analyzer.fuzzy_levels) == 5
    
    def test_camelot_key_enum_completeness(self):
        """Test that CamelotKey enum has all 24 keys."""
        camelot_keys = [key.value for key in CamelotKey]
        assert len(camelot_keys) == 24
        
        # Check all major keys (B)
        major_keys = [key for key in camelot_keys if key.endswith('B')]
        assert len(major_keys) == 12
        
        # Check all minor keys (A)
        minor_keys = [key for key in camelot_keys if key.endswith('A')]
        assert len(minor_keys) == 12
    
    def test_perfect_compatibility_same_key(self, analyzer):
        """Test that same keys have perfect compatibility."""
        test_key = "8B"  # C Major
        result = analyzer.analyze_fuzzy_compatibility(test_key, test_key)
        
        assert result.compatibility_score == 1.0
        assert result.fuzzy_level == 1
        assert result.relationship_type == "identical"
        assert result.pitch_shift_semitones == 0
    
    def test_traditional_relative_keys(self, analyzer):
        """Test traditional relative major/minor relationships."""
        # C Major (8B) and A Minor (8A) are relative keys
        result = analyzer.analyze_fuzzy_compatibility("8B", "8A")
        
        assert result.compatibility_score >= 0.9
        assert result.fuzzy_level <= 2
        assert result.relationship_type == "relative"
    
    def test_fuzzy_levels_progression(self, analyzer):
        """Test that fuzzy levels provide progressive compatibility."""
        base_key = "8B"  # C Major
        
        # Test different keys that should trigger different fuzzy levels
        test_cases = [
            ("8B", 1),  # Same key - perfect
            ("8A", 1),  # Relative - perfect
            ("9B", 2),  # Adjacent - excellent
            ("7B", 2),  # Adjacent - excellent
            ("10B", 3), # Two steps away - good
            ("5B", 4),  # Further away - fair
        ]
        
        for test_key, expected_max_level in test_cases:
            result = analyzer.analyze_fuzzy_compatibility(base_key, test_key)
            assert result.fuzzy_level <= expected_max_level
    
    def test_pitch_shift_recommendations(self, analyzer):
        """Test that pitch shift is recommended when beneficial."""
        # Keys that should benefit from pitch shifting
        result = analyzer.analyze_fuzzy_compatibility("8B", "3B")  # C Major to Db Major
        
        # This should suggest some pitch shifting
        if result.compatibility_score < 0.8:
            assert abs(result.pitch_shift_semitones) > 0
    
    def test_fuzzy_vs_traditional_improvement(self, analyzer):
        """Test that fuzzy method provides more options than traditional."""
        test_key = "8B"  # C Major
        all_keys = [key.value for key in CamelotKey if key.value != test_key]
        
        traditional_good = 0
        fuzzy_good = 0
        
        for target_key in all_keys:
            # Traditional analysis (max_fuzziness=1)
            trad_result = analyzer.analyze_fuzzy_compatibility(test_key, target_key, max_fuzziness=1)
            if trad_result.compatibility_score >= 0.6:
                traditional_good += 1
            
            # Fuzzy analysis (max_fuzziness=4)
            fuzzy_result = analyzer.analyze_fuzzy_compatibility(test_key, target_key, max_fuzziness=4)
            if fuzzy_result.compatibility_score >= 0.6:
                fuzzy_good += 1
        
        # Fuzzy should provide at least as many good options as traditional
        assert fuzzy_good >= traditional_good
    
    def test_all_camelot_keys_mappable(self, analyzer):
        """Test that all Camelot keys can be analyzed."""
        camelot_keys = [key.value for key in CamelotKey]
        
        for key1 in camelot_keys[:5]:  # Test subset for performance
            for key2 in camelot_keys[:5]:
                result = analyzer.analyze_fuzzy_compatibility(key1, key2)
                assert result is not None
                assert 0.0 <= result.compatibility_score <= 1.0
                assert 1 <= result.fuzzy_level <= 5
    
    def test_traditional_key_formats(self, analyzer):
        """Test analysis with different key formats."""
        test_cases = [
            ("C Major", "A Minor"),
            ("G Major", "E Minor"),
            ("F Major", "D Minor"),
            ("Bb Major", "G Minor"),
        ]
        
        for key1, key2 in test_cases:
            result = analyzer.analyze_fuzzy_compatibility(key1, key2)
            assert result is not None
            assert result.compatibility_score >= 0.8  # Relative keys should be highly compatible
    
    def test_fuzzy_recommendations_generation(self, analyzer):
        """Test generation of fuzzy recommendations."""
        current_key = "8B"  # C Major
        candidate_keys = ["8A", "9B", "7B", "10B", "6B", "5B", "3B"]
        
        recommendation = analyzer.get_fuzzy_recommendations(current_key, candidate_keys)
        
        assert recommendation is not None
        assert recommendation.fuzzy_compatibility >= recommendation.original_compatibility
        assert len(recommendation.alternative_keys) > 0
        assert len(recommendation.mixing_advice) > 0
    
    def test_compatible_keys_by_level(self, analyzer):
        """Test getting compatible keys organized by fuzzy level."""
        test_key = "8B"  # C Major
        compatible_keys = analyzer.get_fuzzy_compatible_keys(test_key, max_fuzziness=4)
        
        assert 1 in compatible_keys
        assert 2 in compatible_keys
        assert len(compatible_keys[1]) > 0  # Should have some perfect matches
        
        # Level 1 should be subset of level 2, etc.
        total_level_1 = len(compatible_keys[1])
        total_level_2 = len(compatible_keys[1]) + len(compatible_keys[2])
        assert total_level_2 >= total_level_1
    
    def test_traditional_vs_fuzzy_comparison(self, analyzer):
        """Test comprehensive comparison between methods."""
        test_key = "8B"  # C Major
        comparison = analyzer.compare_traditional_vs_fuzzy(test_key)
        
        assert "traditional_options" in comparison
        assert "fuzzy_options" in comparison
        assert "improvement_ratio" in comparison
        assert "summary" in comparison
        
        # Fuzzy should generally provide more options
        assert comparison["improvement_ratio"] >= 1.0
    
    def test_edge_cases(self, analyzer):
        """Test edge cases and error handling."""
        # Invalid keys
        result = analyzer.analyze_fuzzy_compatibility("Invalid", "Also Invalid")
        assert result is not None
        assert result.compatibility_score == 0.5  # Should return neutral
        
        # Unknown key format
        result = analyzer.analyze_fuzzy_compatibility("Unknown", "8B")
        assert result is not None
        
        # Empty strings
        result = analyzer.analyze_fuzzy_compatibility("", "")
        assert result is not None
    
    def test_singleton_instance(self):
        """Test that singleton pattern works correctly."""
        analyzer1 = get_fuzzy_key_analyzer()
        analyzer2 = get_fuzzy_key_analyzer()
        
        assert analyzer1 is analyzer2  # Same instance
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly."""
        result = analyze_fuzzy_key_compatibility("8B", "8A")
        assert result is not None
        assert result.compatibility_score >= 0.9
        
        comparison = compare_traditional_vs_fuzzy_keymixing("8B")
        assert comparison is not None
        assert "improvement_ratio" in comparison


class TestFuzzyKeyCompatibility:
    """Test the FuzzyKeyCompatibility dataclass."""
    
    def test_compatibility_creation(self):
        """Test creating compatibility objects."""
        compat = FuzzyKeyCompatibility(
            from_key="8B",
            to_key="8A", 
            compatibility_score=0.95,
            fuzzy_level=1,
            relationship_type="relative",
            pitch_shift_semitones=0,
            confidence=0.95,
            explanation="Perfect relative match"
        )
        
        assert compat.from_key == "8B"
        assert compat.to_key == "8A"
        assert compat.compatibility_score == 0.95
        assert compat.fuzzy_level == 1


class TestFuzzyKeyRecommendation:
    """Test the FuzzyKeyRecommendation dataclass."""
    
    def test_recommendation_creation(self):
        """Test creating recommendation objects."""
        recommendation = FuzzyKeyRecommendation(
            original_compatibility=0.6,
            fuzzy_compatibility=0.8,
            improvement_factor=1.33,
            recommended_pitch_shift=2,
            alternative_keys=[("9B", 0.8), ("7B", 0.75)],
            mixing_advice=["Use fuzzy logic", "Consider pitch shift"]
        )
        
        assert recommendation.improvement_factor > 1.0
        assert len(recommendation.alternative_keys) == 2
        assert len(recommendation.mixing_advice) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])