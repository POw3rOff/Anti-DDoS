
import unittest
import os
import sys

# Ensure paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from ebpf.xdp_loader import XDPLoader, MockTable

class TestEBPFSimulation(unittest.TestCase):
    def test_mock_initialization(self):
        # Force simulation mode
        loader = XDPLoader(mode="simulate")
        self.assertTrue(loader.simulation)
        self.assertIsInstance(loader.blacklist, MockTable)
        self.assertIsInstance(loader.stats, MockTable)

    def test_add_remove_ban(self):
        loader = XDPLoader(mode="simulate")
        ip = "192.168.1.100"
        ip_int = loader.ip_to_int(ip)

        # Ban
        loader.add_banned_ip(ip)
        self.assertEqual(loader.blacklist.lookup(ip_int), 0)

        # Unban
        loader.remove_banned_ip(ip)
        self.assertIsNone(loader.blacklist.lookup(ip_int))

    def test_stats(self):
        loader = XDPLoader(mode="simulate")
        stats = loader.get_stats()
        self.assertEqual(stats["dropped"], 0)
        self.assertEqual(stats["passed"], 0)

        # Simulate update
        loader.stats[0] = 50 
        self.assertEqual(loader.get_stats()["dropped"], 50)

if __name__ == "__main__":
    unittest.main()
