
import unittest
import os
import json
import tempfile
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from ml_intelligence.models.isolation_forest import IsolationForestWrapper
# We can't easily import loader.py if bcc isn't installed on Windows, but we can verify the file exists and import defensively
# from ebpf.loader import eBPFManager 

class TestPersistence(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.test_dir, "history.json")
        
    def tearDown(self):
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        os.rmdir(self.test_dir)

    def test_ml_persistence(self):
        """Verify IsolationForestWrapper can save and load state."""
        model = IsolationForestWrapper()
        
        # 1. Add some history
        sample_feature = [0.5, 0.1, 0.005]
        model.history.append(sample_feature)
        
        # 2. Save
        success = model.save_state(self.history_file)
        self.assertTrue(success, "Failed to save state")
        self.assertTrue(os.path.exists(self.history_file), "State file not created")
        
        # 3. Create new instance and load
        new_model = IsolationForestWrapper()
        loaded = new_model.load_state(self.history_file)
        
        self.assertTrue(loaded, "Failed to load state")
        self.assertEqual(len(new_model.history), 1)
        self.assertEqual(new_model.history[0], sample_feature)

    @patch("ebpf.loader.BPF")
    @patch("ebpf.loader.os.path.exists")
    @patch("ebpf.loader.os.makedirs")
    def test_ebpf_pinning_logic(self, mock_makedirs, mock_exists, mock_bpf):
        """Verify eBPFManager tries to pin maps."""
        # Need to import inside test to avoid top-level failures if BCC missing
        try:
            from ebpf.loader import eBPFManager
        except ImportError:
            self.skipTest("BCC/Loader not importable")
            
        mock_args = MagicMock()
        mock_args.interface = "eth0"
        mock_args.dry_run = False
        
        manager = eBPFManager(mock_args)
        # Mock BPF object
        manager.bpf = MagicMock()
        
        # Mock map tables
        mock_table = MagicMock()
        manager.bpf.get_table.return_value = mock_table
        
        # Force existence check to False so it tries to create dir
        mock_exists.return_value = False
        
        manager.pin_maps()
        
        mock_makedirs.assert_called_with("/sys/fs/bpf/uad")
        # Check if get_table was called for our maps
        manager.bpf.get_table.assert_any_call("map_blacklist")
        # Check if pin was called
        mock_table.pin.assert_called()

if __name__ == "__main__":
    unittest.main()
