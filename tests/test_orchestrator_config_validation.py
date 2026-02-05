import sys
import os
import unittest
from unittest.mock import patch, mock_open

# Add the directory containing the script to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../under_attack_ddos/orchestration')))

try:
    import under_attack_orchestrator as uao
except ImportError:
    pass

class TestConfigValidation(unittest.TestCase):
    def test_negative_values_raise_error(self):
        # We construct a config that SHOULD fail
        mock_yaml_data = {
            "orchestrator": {
                "window_size_seconds": -10,
                "weights": {"layer3": -0.5}
            },
            "input_protection": {
                "max_events_per_second": -100
            }
        }

        with patch("builtins.open", mock_open(read_data="data")), \
             patch("yaml.safe_load", return_value=mock_yaml_data), \
             patch("os.path.exists", return_value=True), \
             patch("logging.error") as mock_log: # Suppress error logging during test

            # Now we expect SystemExit with code 3
            with self.assertRaises(SystemExit) as cm:
                uao.ConfigLoader.load(["dummy_path.yaml"])

            self.assertEqual(cm.exception.code, 3)
            print("VALIDATION VERIFIED: SystemExit(3) raised as expected.")

    def test_valid_config_passes(self):
         mock_yaml_data = {
            "orchestrator": {
                "window_size_seconds": 30,
                "weights": {"layer3": 0.5}
            },
            "input_protection": {
                "max_events_per_second": 1000
            }
        }

         with patch("builtins.open", mock_open(read_data="data")), \
             patch("yaml.safe_load", return_value=mock_yaml_data), \
             patch("os.path.exists", return_value=True):

            config = uao.ConfigLoader.load(["dummy_path.yaml"])
            self.assertEqual(config["orchestrator"]["window_size_seconds"], 30)
            print("VALIDATION VERIFIED: Valid config passes.")

if __name__ == '__main__':
    unittest.main()
