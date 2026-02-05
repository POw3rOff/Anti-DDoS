#!/usr/bin/env python3
"""
Edge Daemon
Part of 'under_attack_ddos' Defense System.

Responsibility: Main loop for the Edge PoP.
Orchestrates detection, local enforcement, and communication with Core.
"""

import time
import logging
import argparse
import sys
import json
from .local_detector import LocalDetector
from .xdp_controller import XDPController

class EdgeDaemon:
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run
        self.detector = LocalDetector()
        self.enforcer = XDPController(dry_run)
        self.running = True
        self.pop_id = config.get("pop_id", "unknown_pop")

    def run(self):
        logging.info(f"Edge Daemon started on PoP: {self.pop_id}")

        while self.running:
            # 1. Gather Sensor Data (Simulated ingestion)
            # In prod, this reads from a queue or socket

            # 2. Local Detection
            alerts = self.detector.get_pending_alerts()

            for alert in alerts:
                logging.info(f"Local Alert: {alert}")

                # 3. Fast-Path Enforcement (Edge Autonomy)
                if alert['confidence'] > 0.8:
                    self.enforcer.block_ip(alert['src_ip'], ttl_seconds=300)

                # 4. Signal Core (Simulated emit)
                self._emit_to_core(alert)

            time.sleep(1.0)

    def _emit_to_core(self, alert):
        msg = {
            "origin": self.pop_id,
            "type": "alert",
            "payload": alert
        }
        # In prod, this pushes to Redis/Kafka/HTTP
        if self.dry_run:
            logging.info(f"[DRY-RUN] To Core: {json.dumps(msg)}")

    def stop(self, *args):
        self.running = False

def main():
    parser = argparse.ArgumentParser(description="Edge Daemon")
    parser.add_argument("--pop-id", required=True, help="ID of this Edge PoP")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    config = {"pop_id": args.pop_id}
    daemon = EdgeDaemon(config, args.dry_run)

    try:
        daemon.run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
