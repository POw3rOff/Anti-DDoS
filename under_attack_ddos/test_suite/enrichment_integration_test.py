
import unittest
import sys
import os
import json
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# 1. Mock geoip2 BEFORE importing analyzer modules to handle the imports inside them
sys.modules["geoip2"] = MagicMock()
sys.modules["geoip2.database"] = MagicMock()
sys.modules["geoip2.errors"] = MagicMock()

# 2. Mock GeoIPEnricher to return fixed data
class MockEnricher:
    def __init__(self, *args): pass
    def enrich(self, ip):
        if ip == "8.8.8.8":
            return {"country": "US", "city": "Mountain View", "asn": "AS15169", "org": "Google"}
        return {"country": "Unknown", "city": "Unknown", "asn": "Unknown", "org": "Unknown"}

# Patch the enrichment module
with patch("intelligence.enrichment.GeoIPEnricher", MockEnricher):
    from layer_game.common.game_protocol_parser import GameProtocolParser
    from layer3.ip_flood_analyzer import IPFloodAnalyzer
    from layer4.syn_flood_analyzer import SynFloodAnalyzer

class TestEnrichmentIntegration(unittest.TestCase):
    
    def test_game_protocol_parser_enrichment(self):
        """Verify GameProtocolParser injects context."""
        # Config mock
        parser = GameProtocolParser("test_script", "test_game", dry_run=True)
        # Mock sys.stdout
        with patch("sys.stdout") as mock_stdout:
            parser.emit_event("test_event", "8.8.8.8", "HIGH", {})
            
            # Check calls
            self.assertTrue(mock_stdout.flush.called)
            # Retrieve print arguments 
            # (Note: print calls write to stdout, but we mocked sys.stdout. 
            # Actually print writes to sys.stdout.write usually. 
            # Ideally we patch 'builtins.print' or capture stdout)
            
        with patch("builtins.print") as mock_print:
            parser.emit_event("test_event", "8.8.8.8", "HIGH", {})
            args, _ = mock_print.call_args
            event_json = args[0]
            event = json.loads(event_json)
            
            self.assertIn("context", event)
            self.assertEqual(event["context"]["country"], "US")
            self.assertEqual(event["context"]["asn"], "AS15169")

    def test_l3_analyzer_enrichment(self):
        """Verify IPFloodAnalyzer injects context."""
        mock_args = MagicMock()
        mock_args.mode = "monitor"
        mock_args.dry_run = True # Important so it prints to log/stdout via logic
        mock_args.json = True # Force JSON output
        mock_args.ebpf = False
        
        analyzer = IPFloodAnalyzer(mock_args, {})
        analyzer.packet_counts["8.8.8.8"] = 10000 
        
        with patch("builtins.print") as mock_print:
            analyzer.analyze_window(1.0) # 10000 PPS > threshold
            
            args, _ = mock_print.call_args
            event_json = args[0]
            event = json.loads(event_json)
            
            self.assertIn("context", event)
            self.assertEqual(event["context"]["country"], "US")

    def test_l4_analyzer_enrichment(self):
        """Verify SynFloodAnalyzer injects context."""
        mock_args = MagicMock()
        mock_args.mode = "monitor"
        mock_args.dry_run = True
        mock_args.json = True
        mock_args.ebpf = False
        
        analyzer = SynFloodAnalyzer(mock_args, {})
        analyzer.syn_counts["8.8.8.8"] = 5000
        
        with patch("builtins.print") as mock_print:
            analyzer.analyze_window(1.0)
            
            args, _ = mock_print.call_args
            event_json = args[0]
            event = json.loads(event_json)
            
            self.assertIn("context", event)
            self.assertEqual(event["context"]["org"], "Google")

if __name__ == "__main__":
    unittest.main()
