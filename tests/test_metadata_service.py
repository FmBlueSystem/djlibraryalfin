import unittest
from unittest.mock import patch
from services.metadata_service import MetadataService

class TestMetadataService(unittest.TestCase):
    @patch('core.metadata_enricher._search_musicbrainz', return_value={'genre': 'Rock'})
    @patch('core.metadata_enricher._search_spotify', return_value={'year': 1990})
    @patch('core.metadata_enricher._search_discogs', return_value={'album': 'Demo'})
    def test_enrich_combines_sources(self, mock_d, mock_s, mock_mb):
        service = MetadataService()
        info = {'title': 'Test', 'artist': 'Band'}
        result = service.enrich(info)
        self.assertEqual(result['genre'], 'Rock')
        self.assertEqual(result['year'], 1990)
        self.assertEqual(result['album'], 'Demo')

if __name__ == '__main__':
    unittest.main()
