
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from alerts.alert_manager import AlertManager

class TestAlertManager(unittest.TestCase):
    @patch("alerts.alert_manager.requests")
    def test_discord_alert(self, mock_requests):
        # Config with mock URL
        config = {"discord_webhook_url": "http://discord.fake/api"}
        am = AlertManager(config)
        
        # Test Event
        event = {
            "type": "state_change",
            "severity": "CRITICAL",
            "target_entity": "TestNode",
            "state": "UNDER_ATTACK"
        }
        
        # Process
        am.process_event(event)
        
        # Verify Post
        self.assertTrue(mock_requests.post.called)
        args, kwargs = mock_requests.post.call_args
        
        self.assertEqual(args[0], "http://discord.fake/api")
        payload = kwargs["json"]
        self.assertEqual(payload["username"], "UAD SENTINEL")
        self.assertIn("CRITICAL ALERT", payload["embeds"][0]["title"])
        self.assertEqual(payload["embeds"][0]["color"], 0xff0000)

if __name__ == "__main__":
    unittest.main()
