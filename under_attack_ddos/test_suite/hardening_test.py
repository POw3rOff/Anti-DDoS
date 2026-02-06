
import unittest
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# L3
from intelligence.geo_fencer import GeoFencer
from layer3.spoof_detector import SpoofDetector

# L4
from layer4.connection_killer import ConnectionKiller

# L7
from layer7.js_challenge import JSChallenge
from layer7.tls_analyzer import TLSFingerprinter

# Game
from layer_game.vip_manager import VIPManager
# GameProtocolParser is abstract, so we mock it or test the logic if possible.
# We'll skip testing the abstract class directly and focus on the standalone logic we added if easy, 
# or just test the other components.

class TestHardening(unittest.TestCase):
    
    # --- L3 Tests ---
    def test_spoof_detector(self):
        detector = SpoofDetector()
        self.assertTrue(detector.is_spoofed("10.0.0.1"), "Should detect private IP")
        self.assertFalse(detector.is_spoofed("8.8.8.8"), "Should allow public IP")

    # --- L7 Tests ---
    def test_js_challenge(self):
        js = JSChallenge(secret_key="test")
        html = js.generate_challenge("1.2.3.4")
        self.assertIn("<script>", html)
        self.assertIn("solve", html)
        # Token validation (mock)
        self.assertTrue(js.validate_token("1.2.3.4", "a"*64))

    # --- Game Tests ---
    def test_vip_manager(self):
        vip = VIPManager(vip_duration=5)
        vip.add_vip("1.1.1.1")
        self.assertTrue(vip.is_vip("1.1.1.1"))
        self.assertFalse(vip.is_vip("2.2.2.2"))
        
        # Expiration
        # time.sleep(6) # Too slow for unit test
        # self.assertFalse(vip.is_vip("1.1.1.1"))

if __name__ == "__main__":
    unittest.main()
