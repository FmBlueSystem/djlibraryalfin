# tests/fuzzy_keymixing/test_performance/test_fuzzy_performance.py

import pytest
import time
import sys
import os
import json
from typing import List, Dict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from core.fuzzy_key_analyzer import get_fuzzy_key_analyzer
from core.camelot_key_mapper import get_camelot_key_mapper
from core.pitch_shift_recommender import get_pitch_shift_recommender
from core.dj_transition_analyzer import get_dj_transition_analyzer


class TestFuzzyPerformance:
    """Performance benchmarks for Fuzzy Keymixing components."""
    
    @pytest.fixture
    def test_keys(self):
        """Load test keys dataset."""
        fixtures_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "test_keys_dataset.json")
        with open(fixtures_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def sample_tracks(self):
        """Load sample tracks dataset."""
        fixtures_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_tracks.json")
        with open(fixtures_path, 'r') as f:
            return json.load(f)
    
    def test_fuzzy_analyzer_speed(self, test_keys):
        """Benchmark FuzzyKeyAnalyzer performance."""
        fuzzy_analyzer = get_fuzzy_key_analyzer()
        camelot_keys = test_keys["camelot_keys"]
        
        # Test single analysis speed
        start_time = time.time()
        result = fuzzy_analyzer.analyze_fuzzy_compatibility("8B", "8A")
        single_analysis_time = time.time() - start_time
        
        assert result is not None
        assert single_analysis_time < 0.01  # Should be under 10ms
        
        # Test batch analysis speed
        start_time = time.time()
        for i in range(0, min(10, len(camelot_keys))):
            for j in range(0, min(10, len(camelot_keys))):
                if i != j:
                    result = fuzzy_analyzer.analyze_fuzzy_compatibility(camelot_keys[i], camelot_keys[j])
                    assert result is not None
        
        batch_time = time.time() - start_time
        analyses_count = min(10, len(camelot_keys)) * (min(10, len(camelot_keys)) - 1)
        avg_time_per_analysis = batch_time / analyses_count
        
        assert avg_time_per_analysis < 0.005  # Should be under 5ms per analysis
        
        print(f"FuzzyKeyAnalyzer: {avg_time_per_analysis*1000:.2f}ms per analysis")
    
    def test_key_mapper_speed(self, test_keys):
        """Benchmark CamelotKeyMapper performance."""
        key_mapper = get_camelot_key_mapper()
        traditional_keys = test_keys["traditional_keys"]
        
        # Test single conversion speed
        start_time = time.time()
        result = key_mapper.convert_key("C Major")
        single_conversion_time = time.time() - start_time
        
        assert result == "8B"
        assert single_conversion_time < 0.001  # Should be under 1ms
        
        # Test batch conversion speed
        start_time = time.time()
        for key in traditional_keys:
            result = key_mapper.convert_key(key)
            assert result is not None
        
        batch_time = time.time() - start_time
        avg_time_per_conversion = batch_time / len(traditional_keys)
        
        assert avg_time_per_conversion < 0.001  # Should be under 1ms per conversion
        
        print(f"CamelotKeyMapper: {avg_time_per_conversion*1000:.2f}ms per conversion")
    
    def test_pitch_recommender_speed(self, test_keys):
        """Benchmark PitchShiftRecommender performance."""
        pitch_recommender = get_pitch_shift_recommender()
        test_pairs = [
            ("C Major", "D Major"),
            ("A Minor", "B Minor"),
            ("G Major", "F# Major"),
            ("F Major", "Bb Major"),
            ("E Minor", "C Minor")
        ]
        
        # Test recommendation speed
        times = []
        for key1, key2 in test_pairs:
            start_time = time.time()
            result = pitch_recommender.recommend_pitch_shift(key1, key2)
            analysis_time = time.time() - start_time
            times.append(analysis_time)
            
            assert result is not None
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 0.02  # Should average under 20ms
        assert max_time < 0.05  # No single analysis should take over 50ms
        
        print(f"PitchShiftRecommender: {avg_time*1000:.2f}ms average, {max_time*1000:.2f}ms max")
    
    def test_transition_analyzer_speed(self, sample_tracks):
        """Benchmark DJTransitionAnalyzer performance."""
        transition_analyzer = get_dj_transition_analyzer()
        
        # Test single transition analysis
        track1 = sample_tracks[0]
        track2 = sample_tracks[1]
        
        start_time = time.time()
        result = transition_analyzer.analyze_transition(track1, track2)
        single_analysis_time = time.time() - start_time
        
        assert result is not None
        assert single_analysis_time < 0.05  # Should be under 50ms
        
        # Test multiple transition analyses
        times = []
        for i in range(len(sample_tracks) - 1):
            start_time = time.time()
            result = transition_analyzer.analyze_transition(sample_tracks[i], sample_tracks[i + 1])
            analysis_time = time.time() - start_time
            times.append(analysis_time)
            
            assert result is not None
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 0.03  # Should average under 30ms
        assert max_time < 0.1   # No single analysis should take over 100ms
        
        print(f"DJTransitionAnalyzer: {avg_time*1000:.2f}ms average, {max_time*1000:.2f}ms max")
    
    def test_memory_usage(self, test_keys):
        """Test memory usage of fuzzy components."""
        import tracemalloc
        
        # Start memory tracing
        tracemalloc.start()
        
        # Initialize components
        fuzzy_analyzer = get_fuzzy_key_analyzer()
        key_mapper = get_camelot_key_mapper()
        pitch_recommender = get_pitch_shift_recommender()
        transition_analyzer = get_dj_transition_analyzer()
        
        # Take initial memory snapshot
        initial_memory = tracemalloc.take_snapshot()
        
        # Perform multiple operations
        camelot_keys = test_keys["camelot_keys"]
        for i in range(0, min(24, len(camelot_keys)), 2):
            for j in range(1, min(24, len(camelot_keys)), 2):
                # Fuzzy analysis
                fuzzy_analyzer.analyze_fuzzy_compatibility(camelot_keys[i], camelot_keys[j])
                
                # Key conversion
                key_mapper.convert_key(camelot_keys[i])
                
                # Pitch recommendation
                if i < len(test_keys["traditional_keys"]) and j < len(test_keys["traditional_keys"]):
                    pitch_recommender.recommend_pitch_shift(
                        test_keys["traditional_keys"][i], 
                        test_keys["traditional_keys"][j]
                    )
        
        # Take final memory snapshot
        final_memory = tracemalloc.take_snapshot()
        
        # Calculate memory difference
        top_stats = final_memory.compare_to(initial_memory, 'lineno')
        total_size_diff = sum(stat.size_diff for stat in top_stats)
        
        # Memory growth should be reasonable (under 10MB for extensive operations)
        assert total_size_diff < 10 * 1024 * 1024  # 10MB
        
        tracemalloc.stop()
        
        print(f"Memory usage: {total_size_diff / 1024:.2f} KB growth")
    
    def test_scalability_simulation(self):
        """Test scalability with simulated large datasets."""
        fuzzy_analyzer = get_fuzzy_key_analyzer()
        
        # Simulate different library sizes
        library_sizes = [100, 500, 1000]
        
        for size in library_sizes:
            # Generate test keys by cycling through available keys
            test_keys = []
            camelot_keys = [f"{i}{letter}" for i in range(1, 13) for letter in ['A', 'B']]
            
            for i in range(size):
                test_keys.append(camelot_keys[i % len(camelot_keys)])
            
            # Time analysis of subset
            subset_size = min(50, size)  # Test with subset to keep test time reasonable
            start_time = time.time()
            
            for i in range(0, subset_size, 5):
                for j in range(1, subset_size, 5):
                    if i != j:
                        fuzzy_analyzer.analyze_fuzzy_compatibility(test_keys[i], test_keys[j])
            
            analysis_time = time.time() - start_time
            analyses_performed = (subset_size // 5) * ((subset_size // 5) - 1)
            
            if analyses_performed > 0:
                avg_time_per_analysis = analysis_time / analyses_performed
                
                # Performance should scale reasonably
                assert avg_time_per_analysis < 0.01  # Under 10ms per analysis
                
                print(f"Library size {size}: {avg_time_per_analysis*1000:.2f}ms per analysis")
    
    def test_traditional_vs_fuzzy_performance(self, test_keys):
        """Compare performance of traditional vs fuzzy analysis."""
        fuzzy_analyzer = get_fuzzy_key_analyzer()
        test_pairs = [
            ("C Major", "A Minor"),
            ("G Major", "E Minor"), 
            ("D Major", "B Minor"),
            ("F Major", "D Minor"),
            ("Bb Major", "G Minor")
        ]
        
        # Test traditional analysis (max_fuzziness=1)
        traditional_times = []
        for key1, key2 in test_pairs:
            start_time = time.time()
            result = fuzzy_analyzer.analyze_fuzzy_compatibility(key1, key2, max_fuzziness=1)
            analysis_time = time.time() - start_time
            traditional_times.append(analysis_time)
            assert result is not None
        
        avg_traditional_time = sum(traditional_times) / len(traditional_times)
        
        # Test fuzzy analysis (max_fuzziness=4)
        fuzzy_times = []
        for key1, key2 in test_pairs:
            start_time = time.time()
            result = fuzzy_analyzer.analyze_fuzzy_compatibility(key1, key2, max_fuzziness=4)
            analysis_time = time.time() - start_time
            fuzzy_times.append(analysis_time)
            assert result is not None
        
        avg_fuzzy_time = sum(fuzzy_times) / len(fuzzy_times)
        
        # Fuzzy should not be more than 3x slower than traditional
        performance_ratio = avg_fuzzy_time / avg_traditional_time if avg_traditional_time > 0 else 1
        assert performance_ratio < 3.0
        
        print(f"Traditional: {avg_traditional_time*1000:.2f}ms, Fuzzy: {avg_fuzzy_time*1000:.2f}ms")
        print(f"Performance ratio: {performance_ratio:.2f}x")
    
    def test_concurrent_access_performance(self, test_keys):
        """Test performance under concurrent access simulation."""
        import threading
        
        fuzzy_analyzer = get_fuzzy_key_analyzer()
        camelot_keys = test_keys["camelot_keys"][:8]  # Use subset for test
        
        results = []
        times = []
        
        def worker_thread(thread_id):
            thread_start = time.time()
            thread_results = []
            
            for i in range(len(camelot_keys)):
                for j in range(len(camelot_keys)):
                    if i != j:
                        result = fuzzy_analyzer.analyze_fuzzy_compatibility(camelot_keys[i], camelot_keys[j])
                        thread_results.append(result)
            
            thread_time = time.time() - thread_start
            results.extend(thread_results)
            times.append(thread_time)
        
        # Create multiple threads
        threads = []
        num_threads = 3
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # All analyses should complete successfully
        expected_results_per_thread = len(camelot_keys) * (len(camelot_keys) - 1)
        assert len(results) == num_threads * expected_results_per_thread
        
        # Performance should not degrade significantly under concurrent access
        avg_thread_time = sum(times) / len(times)
        assert avg_thread_time < total_time * 1.5  # Allowing for some overhead
        
        print(f"Concurrent access: {total_time:.2f}s total, {avg_thread_time:.2f}s avg per thread")


class TestPerformanceRegression:
    """Test for performance regression detection."""
    
    def test_baseline_performance_benchmarks(self, test_keys=None):
        """Establish baseline performance benchmarks."""
        if test_keys is None:
            test_keys = {
                "camelot_keys": [f"{i}{letter}" for i in range(1, 13) for letter in ['A', 'B']],
                "traditional_keys": ["C Major", "A Minor", "G Major", "E Minor", "D Major", "B Minor"]
            }
        
        # Benchmark data structure
        benchmarks = {
            "fuzzy_analysis": [],
            "key_conversion": [],
            "pitch_recommendation": [],
            "transition_analysis": []
        }
        
        # Fuzzy analysis benchmark
        fuzzy_analyzer = get_fuzzy_key_analyzer()
        for _ in range(10):
            start_time = time.time()
            fuzzy_analyzer.analyze_fuzzy_compatibility("8B", "8A")
            benchmarks["fuzzy_analysis"].append(time.time() - start_time)
        
        # Key conversion benchmark
        key_mapper = get_camelot_key_mapper()
        for _ in range(10):
            start_time = time.time()
            key_mapper.convert_key("C Major")
            benchmarks["key_conversion"].append(time.time() - start_time)
        
        # Pitch recommendation benchmark
        pitch_recommender = get_pitch_shift_recommender()
        for _ in range(10):
            start_time = time.time()
            pitch_recommender.recommend_pitch_shift("C Major", "D Major")
            benchmarks["pitch_recommendation"].append(time.time() - start_time)
        
        # Transition analysis benchmark
        transition_analyzer = get_dj_transition_analyzer()
        track1 = {"key": "C Major", "bpm": 128, "energy": 0.8, "title": "Test 1"}
        track2 = {"key": "A Minor", "bpm": 128, "energy": 0.8, "title": "Test 2"}
        
        for _ in range(10):
            start_time = time.time()
            transition_analyzer.analyze_transition(track1, track2)
            benchmarks["transition_analysis"].append(time.time() - start_time)
        
        # Calculate and assert reasonable performance
        for operation, times in benchmarks.items():
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            # Define reasonable thresholds
            thresholds = {
                "fuzzy_analysis": 0.01,      # 10ms
                "key_conversion": 0.001,     # 1ms
                "pitch_recommendation": 0.02, # 20ms
                "transition_analysis": 0.05   # 50ms
            }
            
            assert avg_time < thresholds[operation], f"{operation} too slow: {avg_time*1000:.2f}ms"
            assert max_time < thresholds[operation] * 2, f"{operation} max time too slow: {max_time*1000:.2f}ms"
            
            print(f"{operation}: {avg_time*1000:.2f}ms avg, {max_time*1000:.2f}ms max")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print outputs