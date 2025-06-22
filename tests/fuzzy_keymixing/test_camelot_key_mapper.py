# tests/fuzzy_keymixing/test_camelot_key_mapper.py

import pytest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from core.camelot_key_mapper import (
    CamelotKeyMapper,
    KeyFormat,
    KeyInfo,
    get_camelot_key_mapper,
    convert_to_camelot,
    convert_to_traditional,
    analyze_key_complete,
    get_traditional_compatible_keys
)


class TestCamelotKeyMapper:
    """Test suite for CamelotKeyMapper component."""
    
    @pytest.fixture
    def mapper(self):
        """Create fresh mapper instance for each test."""
        return CamelotKeyMapper()
    
    def test_mapper_initialization(self, mapper):
        """Test that mapper initializes correctly."""
        assert mapper is not None
        assert len(mapper.camelot_master_map) == 24  # 12 major + 12 minor
        assert len(mapper.reverse_maps) > 0
        assert len(mapper.key_patterns) > 0
    
    def test_master_mapping_completeness(self, mapper):
        """Test that master mapping contains all 24 Camelot keys."""
        expected_keys = []
        for i in range(1, 13):
            expected_keys.extend([f"{i}A", f"{i}B"])
        
        assert len(mapper.camelot_master_map) == 24
        for key in expected_keys:
            assert key in mapper.camelot_master_map
    
    def test_camelot_format_detection(self, mapper):
        """Test detection of Camelot format keys."""
        camelot_keys = ["1A", "12B", "8A", "5B"]
        
        for key in camelot_keys:
            detected = mapper._detect_key_format(key)
            assert detected == KeyFormat.CAMELOT
    
    def test_open_key_format_detection(self, mapper):
        """Test detection of OpenKey format keys."""
        open_keys = ["1m", "12d", "8m", "5d"]
        
        for key in open_keys:
            detected = mapper._detect_key_format(key)
            assert detected == KeyFormat.OPEN_KEY
    
    def test_traditional_format_detection(self, mapper):
        """Test detection of traditional format keys."""
        traditional_keys = ["C Major", "A Minor", "F# Major", "Bb Minor"]
        
        for key in traditional_keys:
            detected = mapper._detect_key_format(key)
            assert detected == KeyFormat.TRADITIONAL
    
    def test_simplified_format_detection(self, mapper):
        """Test detection of simplified format keys."""
        simplified_keys = ["C", "Am", "F#m", "Bb"]
        
        for key in simplified_keys:
            detected = mapper._detect_key_format(key)
            assert detected == KeyFormat.SIMPLIFIED
    
    def test_camelot_to_camelot_conversion(self, mapper):
        """Test converting Camelot to Camelot (identity)."""
        test_keys = ["8B", "5A", "12B", "1A"]
        
        for key in test_keys:
            result = mapper.convert_key(key, KeyFormat.CAMELOT)
            assert result == key
    
    def test_camelot_to_traditional_conversion(self, mapper):
        """Test converting Camelot to traditional format."""
        test_cases = [
            ("8B", "C Major"),
            ("8A", "A Minor"),
            ("9B", "G Major"),
            ("9A", "E Minor"),
            ("7B", "F Major"),
            ("7A", "D Minor"),
        ]
        
        for camelot, expected_traditional in test_cases:
            result = mapper.convert_key(camelot, KeyFormat.TRADITIONAL)
            assert result == expected_traditional
    
    def test_traditional_to_camelot_conversion(self, mapper):
        """Test converting traditional to Camelot format."""
        test_cases = [
            ("C Major", "8B"),
            ("A Minor", "8A"),
            ("G Major", "9B"),
            ("E Minor", "9A"),
            ("F Major", "7B"),
            ("D Minor", "7A"),
        ]
        
        for traditional, expected_camelot in test_cases:
            result = mapper.convert_key(traditional, KeyFormat.CAMELOT)
            assert result == expected_camelot
    
    def test_open_key_to_camelot_conversion(self, mapper):
        """Test converting OpenKey to Camelot format."""
        test_cases = [
            ("8d", "8B"),  # C Major
            ("8m", "8A"),  # A Minor
            ("9d", "9B"),  # G Major
            ("9m", "9A"),  # E Minor
        ]
        
        for open_key, expected_camelot in test_cases:
            result = mapper.convert_key(open_key, KeyFormat.CAMELOT)
            assert result == expected_camelot
    
    def test_simplified_to_camelot_conversion(self, mapper):
        """Test converting simplified to Camelot format."""
        test_cases = [
            ("C", "8B"),    # C Major
            ("Am", "8A"),   # A Minor
            ("G", "9B"),    # G Major
            ("Em", "9A"),   # E Minor
        ]
        
        for simplified, expected_camelot in test_cases:
            result = mapper.convert_key(simplified, KeyFormat.CAMELOT)
            assert result == expected_camelot
    
    def test_enharmonic_equivalents(self, mapper):
        """Test handling of enharmonic equivalent keys."""
        enharmonic_pairs = [
            ("C# Major", "Db Major"),
            ("F# Major", "Gb Major"),
            ("A# Minor", "Bb Minor"),
            ("D# Minor", "Eb Minor"),
        ]
        
        for key1, key2 in enharmonic_pairs:
            camelot1 = mapper.convert_key(key1, KeyFormat.CAMELOT)
            camelot2 = mapper.convert_key(key2, KeyFormat.CAMELOT)
            assert camelot1 == camelot2  # Should map to same Camelot key
    
    def test_batch_conversion(self, mapper):
        """Test batch conversion functionality."""
        keys = ["C Major", "A Minor", "G Major", "E Minor"]
        results = mapper.batch_convert(keys, KeyFormat.CAMELOT)
        
        assert len(results) == 4
        assert results["C Major"] == "8B"
        assert results["A Minor"] == "8A"
        assert results["G Major"] == "9B"
        assert results["E Minor"] == "9A"
    
    def test_key_analysis_complete(self, mapper):
        """Test complete key analysis functionality."""
        test_key = "C Major"
        key_info = mapper.analyze_key(test_key)
        
        assert key_info is not None
        assert key_info.original_input == test_key
        assert key_info.camelot == "8B"
        assert key_info.traditional == "C Major"
        assert key_info.simplified == "C"
        assert key_info.note == "C"
        assert key_info.mode == "major"
        assert key_info.sharps_flats == 0
    
    def test_compatible_keys_generation(self, mapper):
        """Test generation of compatible keys."""
        test_key = "8B"  # C Major
        compatible = mapper.get_compatible_keys(test_key)
        
        assert len(compatible) > 0
        assert "8B" in compatible  # Same key
        assert "8A" in compatible  # Relative minor
        assert "7B" in compatible or "9B" in compatible  # Adjacent keys
    
    def test_key_relationships(self, mapper):
        """Test key relationship analysis."""
        test_key = "8B"  # C Major
        relationships = mapper.get_key_relationships(test_key)
        
        assert "same_key" in relationships
        assert "relative" in relationships
        assert "adjacent" in relationships
        assert "fifth_circle" in relationships
        
        assert "8B" in relationships["same_key"]
        assert "8A" in relationships["relative"]
    
    def test_key_validation(self, mapper):
        """Test key validation functionality."""
        # Valid key
        valid_result = mapper.validate_key("C Major")
        assert valid_result["valid"] is True
        assert valid_result["camelot"] == "8B"
        
        # Invalid key
        invalid_result = mapper.validate_key("Invalid Key")
        assert invalid_result["valid"] is False
        assert "suggestions" in invalid_result
    
    def test_supported_formats_info(self, mapper):
        """Test getting supported formats information."""
        formats = mapper.get_supported_formats()
        
        assert "camelot" in formats
        assert "open_key" in formats
        assert "traditional" in formats
        assert "simplified" in formats
        assert "examples" in formats
    
    def test_edge_cases(self, mapper):
        """Test edge cases and error handling."""
        # Empty string
        result = mapper.convert_key("", KeyFormat.CAMELOT)
        assert result is None
        
        # None input
        result = mapper.convert_key(None, KeyFormat.CAMELOT)
        assert result is None
        
        # Invalid format
        result = mapper.convert_key("InvalidKey", KeyFormat.CAMELOT)
        assert result is None
    
    def test_case_insensitive_handling(self, mapper):
        """Test case insensitive key handling."""
        test_cases = [
            ("c major", "8B"),
            ("A MINOR", "8A"),
            ("g Major", "9B"),
            ("e minor", "9A"),
        ]
        
        for input_key, expected in test_cases:
            result = mapper.convert_key(input_key, KeyFormat.CAMELOT)
            assert result == expected
    
    def test_whitespace_handling(self, mapper):
        """Test handling of extra whitespace."""
        test_cases = [
            ("  C Major  ", "8B"),
            (" A Minor ", "8A"),
            ("C  Major", "8B"),  # Extra space
        ]
        
        for input_key, expected in test_cases:
            result = mapper.convert_key(input_key, KeyFormat.CAMELOT)
            assert result == expected
    
    def test_singleton_instance(self):
        """Test that singleton pattern works correctly."""
        mapper1 = get_camelot_key_mapper()
        mapper2 = get_camelot_key_mapper()
        
        assert mapper1 is mapper2  # Same instance
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly."""
        # Test convert_to_camelot
        result = convert_to_camelot("C Major")
        assert result == "8B"
        
        # Test convert_to_traditional
        result = convert_to_traditional("8B")
        assert result == "C Major"
        
        # Test analyze_key_complete
        key_info = analyze_key_complete("C Major")
        assert key_info is not None
        assert key_info.camelot == "8B"
        
        # Test get_traditional_compatible_keys
        compatible = get_traditional_compatible_keys("8B")
        assert len(compatible) > 0
        assert "8A" in compatible


class TestKeyFormat:
    """Test the KeyFormat enum."""
    
    def test_key_format_values(self):
        """Test that KeyFormat enum has expected values."""
        assert KeyFormat.CAMELOT.value == "camelot"
        assert KeyFormat.OPEN_KEY.value == "open_key"
        assert KeyFormat.TRADITIONAL.value == "traditional"
        assert KeyFormat.SIMPLIFIED.value == "simplified"


class TestKeyInfo:
    """Test the KeyInfo dataclass."""
    
    def test_key_info_creation(self):
        """Test creating KeyInfo objects."""
        key_info = KeyInfo(
            original_input="C Major",
            camelot="8B",
            open_key="8d",
            traditional="C Major",
            simplified="C",
            note="C",
            mode="major",
            sharps_flats=0,
            enharmonic_equivalent=None,
            circle_of_fifths_position=8
        )
        
        assert key_info.original_input == "C Major"
        assert key_info.camelot == "8B"
        assert key_info.note == "C"
        assert key_info.mode == "major"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])