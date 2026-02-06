
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Mock geoip2 if not installed
sys.modules["geoip2"] = MagicMock()
sys.modules["geoip2.database"] = MagicMock()
sys.modules["geoip2.errors"] = MagicMock()

from intelligence.enrichment import GeoIPEnricher

class TestGeoIPEnrichment(unittest.TestCase):
    
    @patch("intelligence.enrichment.HAS_GEOIP", True)
    @patch("intelligence.enrichment.os.path.exists")
    @patch("intelligence.enrichment.geoip2.database.Reader")
    def test_enrichment_success(self, mock_reader, mock_exists):
        mock_exists.return_value = True
        
        # Setup mock responses
        mock_city_reader = MagicMock()
        mock_city_resp = MagicMock()
        mock_city_resp.country.iso_code = "US"
        mock_city_resp.city.name = "Test City"
        mock_city_reader.city.return_value = mock_city_resp
        
        mock_asn_reader = MagicMock()
        mock_asn_resp = MagicMock()
        mock_asn_resp.autonomous_system_number = 12345
        mock_asn_resp.autonomous_system_organization = "Test Org"
        mock_asn_reader.asn.return_value = mock_asn_resp
        
        mock_reader.side_effect = [mock_city_reader, mock_asn_reader]
        
        enricher = GeoIPEnricher()
        data = enricher.enrich("1.2.3.4")
        
        self.assertEqual(data["country"], "US")
        self.assertEqual(data["city"], "Test City")
        self.assertEqual(data["asn"], "AS12345")
        self.assertEqual(data["org"], "Test Org")

    @patch("intelligence.enrichment.HAS_GEOIP", False)
    def test_missing_library(self):
        enricher = GeoIPEnricher()
        data = enricher.enrich("1.2.3.4")
        
        self.assertEqual(data["country"], "Unknown")
        self.assertEqual(data["asn"], "Unknown")

if __name__ == "__main__":
    unittest.main()
