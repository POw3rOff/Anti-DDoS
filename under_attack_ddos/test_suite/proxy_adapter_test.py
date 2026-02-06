
import unittest
import os
import sys
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from mitigation.proxy_adapter import ProxyAdapter

class TestProxyAdapter(unittest.TestCase):
    def setUp(self):
        self.test_config = "web_security/test_denylist.conf"
        # Cleanup before test
        if os.path.exists(self.test_config):
            os.remove(self.test_config)
            
    def tearDown(self):
        # Cleanup after test
        if os.path.exists(self.test_config):
            os.remove(self.test_config)

    def test_initialization(self):
        adapter = ProxyAdapter(config_path=self.test_config)
        self.assertTrue(os.path.exists(self.test_config))
        with open(self.test_config, 'r') as f:
            self.assertIn("# Dynamic Denylist", f.read())

    def test_block_ip(self):
        adapter = ProxyAdapter(config_path=self.test_config)
        adapter.block_ip("192.168.1.100")
        
        with open(self.test_config, 'r') as f:
            content = f.read()
            self.assertIn("192.168.1.100 1;", content)
            
        # Test dedup
        adapter.block_ip("192.168.1.100")
        with open(self.test_config, 'r') as f:
            content = f.read()
            # Should only appear once if we checked the set, but file append might duplicate if restart
            # The class uses a set for runtime dedup
            self.assertEqual(content.count("192.168.1.100 1;"), 1)

if __name__ == "__main__":
    unittest.main()
