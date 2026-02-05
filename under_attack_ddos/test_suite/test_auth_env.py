import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(PROJECT_ROOT)

# Mock scapy to avoid import errors in detectors
sys.modules['scapy.all'] = MagicMock()

# Import modules to test
# We import inside test methods or after sys.path is set
from under_attack_ddos.orchestration.under_attack_orchestrator import ConfigLoader as OrchConfigLoader, DEFAULT_CONFIG as ORCH_DEFAULT
from under_attack_ddos.layer3.spoofing_detector import ConfigLoader as SpoofConfigLoader
from under_attack_ddos.layer_game.universal_game_detector import TrafficAnalyzer

class TestAuthEnv(unittest.TestCase):
    def setUp(self):
        self.env_token = "SECURE_ENV_TOKEN_999"

    @patch.dict(os.environ, {"UAD_AUTH_TOKEN": "SECURE_ENV_TOKEN_999"})
    def test_orchestrator_config_env_override(self):
        """Test that Orchestrator ConfigLoader picks up UAD_AUTH_TOKEN."""
        # Load with empty list of paths to rely on defaults + env
        config = OrchConfigLoader.load([])
        self.assertEqual(config["security"]["auth_token"], self.env_token)

    @patch.dict(os.environ, {"UAD_AUTH_TOKEN": "SECURE_ENV_TOKEN_999"})
    def test_spoofing_detector_config_env_override(self):
        """Test that SpoofingDetector ConfigLoader picks up UAD_AUTH_TOKEN."""
        config = SpoofConfigLoader.load([])
        self.assertEqual(config["security"]["auth_token"], self.env_token)

    @patch.dict(os.environ, {"UAD_AUTH_TOKEN": "SECURE_ENV_TOKEN_999"})
    def test_universal_game_detector_env_override(self):
        """Test that Universal Game Detector TrafficAnalyzer picks up UAD_AUTH_TOKEN."""
        # Mock specs and config
        mock_config = {"security": {"auth_token": "default_insecure"}}
        analyzer = TrafficAnalyzer([], mock_config)
        self.assertEqual(analyzer.auth_token, self.env_token)

    def test_no_env_var_fallback(self):
        """Test fallback to config/default when env var is missing."""
        # Ensure env var is NOT set
        with patch.dict(os.environ, {}, clear=True):
             # Orchestrator
             config_orch = OrchConfigLoader.load([])
             # Should be 'default_insecure' from DEFAULT_CONFIG in script
             self.assertEqual(config_orch["security"]["auth_token"], "default_insecure")

             # TrafficAnalyzer
             mock_config = {"security": {"auth_token": "from_config"}}
             analyzer = TrafficAnalyzer([], mock_config)
             self.assertEqual(analyzer.auth_token, "from_config")

if __name__ == '__main__':
    unittest.main()
