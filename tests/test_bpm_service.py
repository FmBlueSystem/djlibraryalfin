import unittest
import numpy as np
import soundfile as sf
import tempfile
import os
from services.bpm_service import BPMService

class TestBPMService(unittest.TestCase):
    def setUp(self):
        sr = 22050
        bpm = 120
        duration = 5
        click_times = np.arange(0, duration, 60 / bpm)
        y = np.zeros(int(sr * duration))
        click_samples = (click_times * sr).astype(int)
        y[click_samples] = 1.0
        fd, self.temp_path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        sf.write(self.temp_path, y, sr)

    def tearDown(self):
        os.remove(self.temp_path)

    def test_analyze_returns_bpm(self):
        service = BPMService()
        result = service.analyze(self.temp_path)
        self.assertIn('bpm', result)
        self.assertIsNotNone(result['bpm'])
        self.assertTrue(110 <= result['bpm'] <= 130)

if __name__ == '__main__':
    unittest.main()
