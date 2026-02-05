#!/usr/bin/env python3
"""
Distributed Sync Agent
Part of 'under_attack_ddos' Defense System.

Responsibility: Synchronize attack state between Edge (LB) and Core (Game Host) nodes.
Uses Redis Pub/Sub for low-latency communication.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import threading
import socket
from datetime import datetime, timezone

# Third-party imports
try:
    import redis
    import yaml
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(4)

SCRIPT_NAME = "distributed_sync_agent"

class SyncAgent:
    def __init__(self, config, role):
        self.config = config.get("distributed", {})
        self.role = role
        self.running = True

        # Redis Setup
        conf = self.config.get("communication", {})
        self.r = redis.Redis(
            host=conf.get("redis_host", "localhost"),
            port=conf.get("redis_port", 6379),
            decode_responses=True
        )
        self.channel = conf.get("channel", "ddos_sync")
        self.hostname = socket.gethostname()

    def publish_state(self, state_data):
        """Send local state/alerts to the cluster."""
        msg = {
            "origin": self.hostname,
            "role": self.role,
            "timestamp": time.time(),
            "data": state_data
        }
        try:
            self.r.publish(self.channel, json.dumps(msg))
            logging.debug(f"Published: {msg}")
        except Exception as e:
            logging.error(f"Publish failed: {e}")

    def listen(self):
        """Subscribe to cluster updates."""
        pubsub = self.r.pubsub()
        pubsub.subscribe(self.channel)

        logging.info(f"Listening on channel '{self.channel}' as {self.role}...")

        while self.running:
            try:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    self._handle_message(message['data'])
            except Exception as e:
                logging.error(f"Listen error: {e}")
                time.sleep(1)

    def _handle_message(self, raw_json):
        try:
            msg = json.loads(raw_json)
            origin = msg.get("origin")
            if origin == self.hostname: return # Ignore self

            sender_role = msg.get("role")
            data = msg.get("data")

            # Logic:
            # If I am Edge and Core says "Help!", I block.
            # If I am Core and Edge says "Blocking X", I log it.

            if self.role == "edge" and sender_role == "core":
                if data.get("action") == "request_mitigation":
                    target_ip = data.get("target_ip")
                    logging.info(f"CORE REQUEST: Blocking {target_ip} at EDGE.")
                    # In real impl, this would write to mitigation queue
                    print(json.dumps({
                        "layer": "distributed",
                        "event": "edge_mitigation_triggered",
                        "source_entity": target_ip,
                        "severity": "HIGH",
                        "data": {"reason": "core_request", "origin": origin}
                    }))
                    sys.stdout.flush()

        except Exception as e:
            logging.error(f"Msg parse error: {e}")

    def stop(self, *args):
        self.running = False

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_NAME)
    parser.add_argument("--config", required=True, help="Path to games.yaml")
    parser.add_argument("--role", choices=["edge", "core"], required=True, help="Node role")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    # Load config
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Config load failed: {e}")
        sys.exit(1)

    agent = SyncAgent(config, args.role)

    signal.signal(signal.SIGINT, agent.stop)
    signal.signal(signal.SIGTERM, agent.stop)

    # Start listener thread
    t = threading.Thread(target=agent.listen)
    t.start()

    # Main loop could read from stdin to publish local alerts
    # For now, just keep alive
    while agent.running:
        time.sleep(1)

if __name__ == "__main__":
    main()
