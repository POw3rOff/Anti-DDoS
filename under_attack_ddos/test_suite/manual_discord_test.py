
import sys
import os
import argparse
import logging

# Ensure paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from alerts.alert_manager import AlertManager

def test_discord(webhook_url):
    print(f"Testing Discord Webhook: {webhook_url}")
    
    # Config with webhook
    config = {"discord_webhook_url": webhook_url}
    am = AlertManager(config)
    
    # Fake Event
    event = {
        "type": "state_change",
        "severity": "CRITICAL",
        "target_entity": "Global System",
        "state": "UNDER_ATTACK",
        "score": 95,
        "context": {"country": "US", "asn": "AS15169"}
    }
    
    print("Triggering alert...")
    am.process_event(event)
    print("Alert processed. Check Discord channel.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Discord Integration")
    parser.add_argument("--webhook", required=True, help="Discord Webhook URL")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    test_discord(args.webhook)
