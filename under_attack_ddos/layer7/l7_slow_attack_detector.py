#!/usr/bin/env python3
"""
Layer 7 Slow Attack Detector (Slowloris/Slow Read)
Part of under_attack_ddos/layer7/

Responsibility: Identifies connections that hold sockets open for excessive duration
with low throughput. Uses upstream response time and request duration logs.
"""

import sys
import os
import json
import argparse
import logging
import yaml
from collections import defaultdict
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "l7_slow_attack_detector"
LAYER = "layer7"
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "l7_thresholds.yaml")

# -----------------------------------------------------------------------------
# Detector Class
# -----------------------------------------------------------------------------
class L7SlowAttackDetector:
    def __init__(self, config_path=None, dry_run=False):
        self.config = self._load_config(config_path)
        self.dry_run = dry_run

        # Load thresholds
        self.max_duration = self.config.get("max_connection_duration", 60)
        self.min_rate = self.config.get("min_data_rate", 10)

        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME}. Max Duration: {self.max_duration}s")

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def _load_config(self, path):
        path = path or DEFAULT_CONFIG_PATH
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
        return {}

    def parse_line(self, line):
        """
        Expects JSON logs with 'request_time' (Nginx) or 'duration' fields.
        And 'bytes_sent' / 'body_bytes_sent'.
        """
        try:
            line = line.strip()
            if not line: return None
            data = json.loads(line)

            # Normalize fields
            ip = data.get("client_ip") or data.get("remote_addr")

            # Duration (Seconds)
            duration = data.get("request_time") or data.get("duration", 0)
            duration = float(duration)

            # Size (Bytes)
            size = data.get("body_bytes_sent") or data.get("bytes_sent", 0)
            size = int(size)

            return ip, duration, size
        except Exception:
            return None

    def analyze_request(self, ip, duration, size):
        if not ip: return

        # 1. Slow Connection Check
        if duration > self.max_duration:
            # Calculate Rate (Bytes/Sec)
            rate = size / duration if duration > 0 else 0

            # If rate is effectively zero or very low, it's suspicious
            if rate < self.min_rate:
                self.emit_event("slow_loris_suspected", ip, "HIGH", {
                    "duration": f"{duration:.2f}s",
                    "bytes_sent": size,
                    "rate": f"{rate:.2f} B/s",
                    "threshold_rate": self.min_rate
                })

    def emit_event(self, event_type, src_ip, severity, data):
        data["status"] = "simulated" if self.dry_run else "active"
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "event": event_type,
            "source_entity": src_ip,
            "severity": severity,
            "data": data
        }
        print(json.dumps(event))
        sys.stdout.flush()
        logging.warning(f"ALERT: {event_type} from {src_ip} ({data['duration']})")

    def run(self):
        logging.info("Starting Slow Attack Detector (reading STDIN)...")
        try:
            for line in sys.stdin:
                parsed = self.parse_line(line)
                if parsed:
                    self.analyze_request(*parsed)
        except KeyboardInterrupt:
            logging.info("Stopping...")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="L7 Slow Attack Detector")
    parser.add_argument("--config", help="Path to config yaml")
    parser.add_argument("--dry-run", action="store_true", help="Simulate alerts")

    args = parser.parse_args()

    detector = L7SlowAttackDetector(args.config, args.dry_run)
    detector.run()

if __name__ == "__main__":
    main()
