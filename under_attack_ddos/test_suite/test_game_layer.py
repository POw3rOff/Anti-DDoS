import unittest
import sys
import os
import json
import logging
from io import StringIO
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)
# Add layer_game to path for imports
sys.path.append(os.path.join(PROJECT_ROOT, "layer_game"))

# Mock scapy before importing monitors
sys.modules['scapy.all'] = MagicMock()
from scapy.all import IP, TCP, Raw

from layer_game.common.game_protocol_parser import GameProtocolParser
from layer_game.metin2.metin2_login_monitor import Metin2LoginMonitor

class TestGameLayer(unittest.TestCase):
    def setUp(self):
        # Suppress logging during tests
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_parser_emit_event(self):
        """Test if GameProtocolParser emits valid JSON."""
        # Create concrete class for testing abstract base
        class TestParser(GameProtocolParser):
            def run(self): pass

        parser = TestParser("test_script", "test_game", dry_run=True)

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        parser.emit_event("test_event", "127.0.0.1", "LOW", {"foo": "bar"})

        sys.stdout = sys.__stdout__ # Reset

        output = captured_output.getvalue().strip()
        self.assertTrue(output)

        event = json.loads(output)
        self.assertEqual(event["event"], "test_event")
        self.assertEqual(event["src_ip"], "127.0.0.1")
        self.assertEqual(event["severity"], "LOW")
        self.assertEqual(event["data"]["foo"], "bar")
        self.assertEqual(event["data"]["status"], "simulated")

    def test_login_monitor_logic(self):
        """Test Metin2LoginMonitor packet processing and logic."""
        monitor = Metin2LoginMonitor(dry_run=True)
        # Mock config
        monitor.baseline.config = {"max_login_pps": 2, "global_login_pps": 10}

        # Simulate packets
        pkt = MagicMock()
        pkt.__contains__.side_effect = lambda x: True # Contains IP, TCP, Raw
        pkt[IP].src = "192.168.1.100"
        pkt[TCP].dport = 11002

        # Feed 5 packets (Flood)
        for _ in range(5):
            monitor.packet_callback(pkt)

        self.assertEqual(monitor.login_counts["192.168.1.100"], 5)
        self.assertEqual(monitor.global_login_count, 5)

        # Capture emission
        captured_output = StringIO()
        sys.stdout = captured_output

        # Force analysis window to be > 0.1s
        monitor.start_time = time.time() - 1.0
        monitor.analyze_window()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        self.assertIn("auth_flood", output)
        self.assertIn("192.168.1.100", output)

if __name__ == '__main__':
    import time # Needed inside test method
    unittest.main()
