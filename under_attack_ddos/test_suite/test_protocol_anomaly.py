import unittest
import sys
import os
import time
from unittest.mock import MagicMock

# Setup paths to prioritize layer_game/common over common/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
layer_game_dir = os.path.join(project_root, "layer_game")

# Prepend layer_game to sys.path so 'common' resolves to layer_game/common
if layer_game_dir not in sys.path:
    sys.path.insert(0, layer_game_dir)

# Also need project root for other imports potentially, but insert it after
if project_root not in sys.path:
    sys.path.append(project_root)

# Mock scapy before importing
sys.modules['scapy.all'] = MagicMock()
from scapy.all import IP, TCP, Raw

# Now import the module under test
from metin2.metin2_protocol_anomaly import Metin2ProtocolAnomaly

class TestMetin2ProtocolAnomaly(unittest.TestCase):
    def setUp(self):
        # Mock config
        self.config_path = os.path.join(layer_game_dir, "metin2", "config.yaml")
        # Ensure config loading doesn't fail if file missing, or mock it

    def test_packet_callback_optimization(self):
        """Test that packet_callback correctly extracts layers and calls analyze."""
        detector = Metin2ProtocolAnomaly(config_path=None, dry_run=True)
        # Mock the analyze method to verify it receives layer objects
        detector._analyze_client_packet = MagicMock()

        # Create a mock packet
        pkt = MagicMock()

        # Mock getlayer behavior
        ip_layer = MagicMock()
        ip_layer.src = "192.168.1.50"

        tcp_layer = MagicMock()
        tcp_layer.dport = 11002

        raw_layer = MagicMock()
        raw_layer.load = b"test_payload"

        def getlayer_side_effect(layer_type):
            if layer_type == IP: return ip_layer
            if layer_type == TCP: return tcp_layer
            if layer_type == Raw: return raw_layer
            return None

        pkt.getlayer.side_effect = getlayer_side_effect

        # Call the callback
        detector.packet_callback(pkt)

        # Verify getlayer was called
        pkt.getlayer.assert_any_call(IP)
        pkt.getlayer.assert_any_call(TCP)
        pkt.getlayer.assert_any_call(Raw)

        # Verify _analyze_client_packet was called with the layers
        detector._analyze_client_packet.assert_called_once_with(ip_layer, raw_layer)

    def test_analyze_client_packet_logic(self):
        """Test the logic inside _analyze_client_packet with passed layers."""
        detector = Metin2ProtocolAnomaly(config_path=None, dry_run=True)
        # Mock baseline to avoid actual validation logic dependencies or config issues
        detector.baseline = MagicMock()
        detector.baseline.validate_handshake_time.return_value = (False, {})
        detector.baseline.config = {"handshake_timeout": 5.0}

        ip_layer = MagicMock()
        ip_layer.src = "192.168.1.60"

        raw_layer = MagicMock()
        # Simulate INIT packet (too short)
        raw_layer.load = b"\x01\x02"

        # Capture emitted events
        detector.emit_event = MagicMock()

        detector._analyze_client_packet(ip_layer, raw_layer)

        # Should detect malformed packet (len < 4 in STATE_INIT)
        # Check args passed to emit_event
        args, _ = detector.emit_event.call_args
        self.assertEqual(args[0], "malformed_packet")
        self.assertEqual(args[1], "192.168.1.60")

if __name__ == '__main__':
    unittest.main()
