
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Robust Mocking of dependencies BEFORE import
mock_pcap = MagicMock()
mock_xdp = MagicMock()
sys.modules["forensics.pcap_recorder"] = MagicMock()
sys.modules["forensics.pcap_recorder"].PcapRecorder = MagicMock(return_value=mock_pcap)

# Ensure paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Now import Orchestrator
from orchestration.under_attack_orchestrator import Orchestrator
from ebpf.xdp_loader import XDPLoader # Real loader class for isinstance check

class MockArgs:
    def __init__(self):
        self.mode = "simulate"
        self.log_level = "INFO"
        self.dry_run = True

class TestOrchestratorXDP(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        mock_pcap.reset_mock()
        
    @patch("orchestration.under_attack_orchestrator.ConfigManager")
    @patch("orchestration.under_attack_orchestrator.AlertManager")
    @patch("orchestration.under_attack_orchestrator.IntelligenceEngine")
    def test_xdp_initialization(self, MockIE, MockAM, MockCM):
        # Mock Config
        mock_config = MagicMock()
        mock_config.get_config.return_value = {"ebpf_support": True}
        MockCM.return_value = mock_config

        # Force simulation mode for the REAL XDPLoader if we use it, 
        # OR we check that the orchestrator instantiates it.
        # Since we imported the real Orchestrator, it will import the real XDPLoader (since we didn't mock ebpf.xdp_loader in sys.modules yet)
        
        args = MockArgs()
        orch = Orchestrator(args)
        
        # Verify XDP is initialized
        self.assertTrue(orch.ebpf_enabled)
        # It should be an instance of the class we imported, usually.
        # But if the orchestrator imports it, it is the real one.
        self.assertIsInstance(orch.xdp, XDPLoader)
        self.assertTrue(orch.xdp.simulation)

    @patch("orchestration.under_attack_orchestrator.ConfigManager")
    @patch("orchestration.under_attack_orchestrator.AlertManager")
    @patch("orchestration.under_attack_orchestrator.IntelligenceEngine")
    def test_mitigation_ban(self, MockIE, MockAM, MockCM):
        args = MockArgs()
        orch = Orchestrator(args)
        
        # Manually inject a mock XDP loader for verification of calls
        orch.xdp = MagicMock()
        orch.ebpf_enabled = True

        directive = {
            "type": "mitigation_directive",
            "action": "ban_ip",
            "target": "10.0.0.1",
            "justification": "Test Ban"
        }
        
        orch._emit_directive(directive)
        
        # Verify add_banned_ip was called
        orch.xdp.add_banned_ip.assert_called_with("10.0.0.1")

if __name__ == "__main__":
    unittest.main()
