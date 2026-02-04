
import sys
import os
import unittest
from unittest.mock import MagicMock
from collections import defaultdict

# Add repo root to path to import the script
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(repo_root)

# Mock scapy before importing the module
sys.modules['scapy.all'] = MagicMock()
from scapy.all import IP, TCP

# Now import the module
# We need to load it from source file because it is not a proper package
import importlib.util
spec = importlib.util.spec_from_file_location("syn_flood_analyzer",
    os.path.join(repo_root, "under_attack_ddos/layer4/syn_flood_analyzer.py"))
syn_flood_analyzer = importlib.util.module_from_spec(spec)
sys.modules["syn_flood_analyzer"] = syn_flood_analyzer
spec.loader.exec_module(syn_flood_analyzer)

class TestSynFloodAnalyzer(unittest.TestCase):
    def setUp(self):
        self.args = MagicMock()
        self.args.mode = "normal"
        self.args.dry_run = True
        self.args.json = True

        self.config = {
            "layer4": {
                "syn_flood": {
                    "syn_rate_pps": 100
                }
            }
        }

        self.analyzer = syn_flood_analyzer.SynFloodAnalyzer(self.args, self.config)

    def test_packet_callback_ipv4(self):
        # Setup mock packet with IP layer
        packet = MagicMock()
        ip_layer = MagicMock()
        ip_layer.src = "192.168.1.100"

        # Determine behavior based on implementation details (access via __getitem__ or getlayer)
        # Old implementation uses: if IP in packet: packet[IP].src
        # New implementation uses: packet.getlayer(IP).src

        # We need to support both for the test to be valid before and after

        # Configure __contains__ for 'if IP in packet'
        packet.__contains__.side_effect = lambda layer: layer == IP

        # Configure __getitem__ for 'packet[IP]'
        packet.__getitem__.side_effect = lambda layer: ip_layer if layer == IP else None

        # Configure getlayer for 'packet.getlayer(IP)'
        packet.getlayer.side_effect = lambda layer: ip_layer if layer == IP else None

        # Call callback
        self.analyzer.packet_callback(packet)

        # Verify count
        self.assertEqual(self.analyzer.syn_counts["192.168.1.100"], 1)

    def test_packet_callback_non_ip(self):
        # Setup mock packet WITHOUT IP layer (e.g. IPv6 or raw Ethernet)
        packet = MagicMock()

        # Configure __contains__
        packet.__contains__.return_value = False

        # Configure getlayer
        packet.getlayer.return_value = None

        # Call callback
        self.analyzer.packet_callback(packet)

        # Verify count is empty
        self.assertEqual(len(self.analyzer.syn_counts), 0)

if __name__ == '__main__':
    unittest.main()
