import os
import shutil
import tempfile
import unittest
from core.metadata_writer import write_metadata
import mutagen
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.wave import WAVE

# Archivos de muestra reales en /Volumes/KINGSTON/Audio
SAMPLES = {
    'mp3': '/Volumes/KINGSTON/Audio/The Tamperer feat. Maya - Feel It (Original Mix).mp3',
    'flac': '/Volumes/KINGSTON/Audio/Alice Cooper - School\'s Out_PN.flac',
    'm4a': '/Volumes/KINGSTON/Audio/Coldplay - A Sky Full Of Stars (DJ Beats).m4a',
    'wav': None,  # No hay wav en la carpeta, omitir test
}

METADATA = {
    'title': 'Test Title',
    'artist': 'Test Artist',
    'album': 'Test Album',
    'genre': 'Test Genre',
    'year': '2024',
    'comments': 'Test comments',
    'key': '8A',
    'bpm': 128,
}

class TestMetadataWriter(unittest.TestCase):
    def setUp(self):
        self.temp_files = {}
        for fmt, src in SAMPLES.items():
            if src and os.path.exists(src):
                fd, temp_path = tempfile.mkstemp(suffix='.' + fmt)
                os.close(fd)
                shutil.copy(src, temp_path)
                self.temp_files[fmt] = temp_path
            else:
                self.temp_files[fmt] = None

    def tearDown(self):
        for temp in self.temp_files.values():
            if temp and os.path.exists(temp):
                os.remove(temp)
            # Borrar json auxiliar si existe
            json_path = os.path.splitext(temp)[0] + '.json' if temp else None
            if json_path and os.path.exists(json_path):
                os.remove(json_path)

    def test_write_and_read_mp3(self):
        path = self.temp_files['mp3']
        if not path:
            self.skipTest('No sample mp3 file found')
        self.assertTrue(write_metadata(path, METADATA))
        audio = ID3(path)
        self.assertEqual(str(audio.get('TIT2')), METADATA['title'])
        self.assertEqual(str(audio.get('TPE1')), METADATA['artist'])
        self.assertEqual(str(audio.get('TALB')), METADATA['album'])
        self.assertEqual(str(audio.get('TCON')), METADATA['genre'])
        comment_frame = audio.getall('COMM')
        self.assertTrue(comment_frame)
        self.assertIn(METADATA['comments'], comment_frame[0].text)
        self.assertEqual(str(audio.get('TKEY')), METADATA['key'])
        self.assertIn(str(METADATA['bpm']), str(audio))

    def test_write_and_read_flac(self):
        path = self.temp_files['flac']
        if not path:
            self.skipTest('No sample flac file found')
        self.assertTrue(write_metadata(path, METADATA))
        audio = FLAC(path)
        self.assertEqual(audio.get('TITLE', [''])[0], METADATA['title'])
        self.assertEqual(audio.get('ARTIST', [''])[0], METADATA['artist'])
        self.assertEqual(audio.get('ALBUM', [''])[0], METADATA['album'])
        self.assertEqual(audio.get('GENRE', [''])[0], METADATA['genre'])
        self.assertEqual(audio.get('COMMENT', [''])[0], METADATA['comments'])
        self.assertEqual(audio.get('INITIALKEY', [''])[0], METADATA['key'])
        self.assertEqual(audio.get('BPM', [''])[0], str(METADATA['bpm']))

    def test_write_and_read_m4a(self):
        path = self.temp_files['m4a']
        if not path:
            self.skipTest('No sample m4a file found')
        self.assertTrue(write_metadata(path, METADATA))
        audio = MP4(path)
        self.assertEqual(audio.get('\xa9nam', [''])[0], METADATA['title'])
        self.assertEqual(audio.get('\xa9ART', [''])[0], METADATA['artist'])
        self.assertEqual(audio.get('\xa9alb', [''])[0], METADATA['album'])
        self.assertEqual(audio.get('\xa9gen', [''])[0], METADATA['genre'])
        self.assertEqual(audio.get('\xa9cmt', [''])[0], METADATA['comments'])
        self.assertIn(b'8A', audio.get('----:com.apple.iTunes:initialkey', [b''])[0])
        self.assertEqual(audio.get('tmpo', [0])[0], METADATA['bpm'])

    def test_write_and_read_wav(self):
        path = self.temp_files['wav']
        if not path:
            self.skipTest('No sample wav file found')
        self.assertTrue(write_metadata(path, METADATA))
        audio = WAVE(path)
        self.assertEqual(audio.get('INAM', ''), METADATA['title'])
        self.assertEqual(audio.get('IART', ''), METADATA['artist'])
        self.assertEqual(audio.get('IGNR', ''), METADATA['genre'])
        self.assertEqual(audio.get('ICMT', ''), METADATA['comments'])
        # Verifica que el .json auxiliar existe y contiene los campos extra
        json_path = os.path.splitext(path)[0] + '.json'
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, 'r', encoding='utf-8') as f:
            data = f.read()
            self.assertIn('album', data)
            self.assertIn('year', data)
            self.assertIn('key', data)
            self.assertIn('bpm', data)

if __name__ == '__main__':
    unittest.main() 