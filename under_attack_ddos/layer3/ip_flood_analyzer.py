#!/usr/bin/env python3
"""
Layer 3 IP Flood Analyzer
Part of 'under_attack_ddos' Defense System.

Responsibility: Detects abnormal IP packet rates per source IP and subnet.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
from collections import defaultdict
from datetime import datetime, timezone

# Third-party imports (assumed available in production environment)
try:
    import yaml
    from scapy.all import sniff, IP
except ImportError as e:
    print(f"CRITICAL: Missing required dependencies: {e}", file=sys.stderr)
    print("Please install: pip install pyyaml scapy", file=sys.stderr)
    sys.exit(4)

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "l3_ip_flood_analyzer"
LAYER = "layer3"
RESPONSIBILITY = "Detect volumetric IP floods per source"

# Default configuration (Fail-safe)
DEFAULT_CONFIG = {
    "layer3": {
        "source_ip_pps": {
            "normal": 1000,
            "under_attack": 200
        },
        "subnet_pps": {
            "normal": 5000,
            "under_attack": 1000
        }
    }
}

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ConfigLoader:
    @staticmethod
    def load(path):
        if not os.path.exists(path):
            logging.error(f"Config file not found: {path}")
            return DEFAULT_CONFIG

        try:
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f) or {}

            # Simple merge (User config overrides defaults)
            # In a real implementation, do a deep merge
            return user_config
        except Exception as e:
            logging.error(f"Failed to parse config: {e}")
            sys.exit(2)

class IPFloodAnalyzer:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.running = True
        self.packet_counts = defaultdict(int)
        self.start_time = time.time()

        # Determine thresholds based on mode
        l3_conf = self.config.get("layer3", {}).get("source_ip_pps", {})
        if self.args.mode == "under_attack":
            self.pps_threshold = l3_conf.get("under_attack", 200)
        else:
            self.pps_threshold = l3_conf.get("normal", 1000)

        logging.info(f"Initialized {SCRIPT_NAME}. Mode: {args.mode}. PPS Threshold: {self.pps_threshold}")

    def packet_callback(self, packet):
        """Called for each captured packet."""
        if IP in packet:
            src_ip = packet[IP].src
            self.packet_counts[src_ip] += 1

    def analyze_window(self, duration):
        """Analyzes the accumulated packet counts."""
        now = datetime.now(timezone.utc).isoformat()
        events = []

        for ip, count in self.packet_counts.items():
            pps = count / duration

            if pps > self.pps_threshold:
                severity = "HIGH" if pps > (self.pps_threshold * 2) else "MEDIUM"

                event = {
                    "timestamp": now,
                    "layer": LAYER,
                    "event": "ip_flood_detected",
                    "severity": severity,
                    "source_entity": ip,
                    "data": {
                        "pps_observed": round(pps, 2),
                        "pps_threshold": self.pps_threshold,
                        "total_packets": count,
                        "duration": round(duration, 2)
                    }
                }

                # Dry-run check
                if self.args.dry_run:
                    event["status"] = "simulated"
                    logging.info(f"[DRY-RUN] Would flag IP {ip} (PPS: {pps:.2f})")
                else:
                    event["status"] = "active"

                events.append(event)

        # Output events
        if self.args.json and events:
            for e in events:
                print(json.dumps(e))
        elif events:
            for e in events:
                logging.warning(f"ALERT: {e['event']} from {e['source_entity']} (PPS: {e['data']['pps_observed']})")

        # Reset counters for next window
        self.packet_counts.clear()

    def run(self):
        """Main Loop"""
        window_size = 5.0 # Seconds

        if self.args.mode == "under_attack":
            window_size = 1.0 # Aggressive sampling

        logging.info(f"Starting capture loop. Window size: {window_size}s")

        try:
            while self.running:
                start_loop = time.time()

                # Sniff packets for 'window_size' seconds
                # store=0 to avoid memory leak
                sniff(prn=self.packet_callback, store=0, timeout=window_size)

                # Analyze
                duration = time.time() - start_loop
                # Correct duration in case sniffing stopped early or took longer
                if duration < 0.1: duration = 0.1

                self.analyze_window(duration)

                if self.args.once:
                    self.running = False

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logging.error(f"Runtime error: {e}", exc_info=True)
            sys.exit(1)

    def stop(self, signum=None, frame=None):
        logging.info("Stopping...")
        self.running = False

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)

    # Required Flags
    parser.add_argument("--config", required=True, help="Path to YAML configuration")
    parser.add_argument("--mode", required=True, choices=["normal", "monitor", "under_attack"], help="Execution mode")

    # Optional Flags
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions")
    parser.add_argument("--daemon", action="store_true", help="Run as background service")
    parser.add_argument("--once", action="store_true", help="Run single pass and exit")
    parser.add_argument("--json", action="store_true", help="Output JSON events to STDOUT")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")

    args = parser.parse_args()

    # Validation
    if args.daemon and args.once:
        print("Error: --daemon and --once are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    # Logging Setup
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        stream=sys.stderr # Logs go to stderr
    )

    # Root Check (Scapy needs root for sniffing)
    if os.geteuid() != 0 and not args.dry_run:
        # Note: In dry-run we might allow non-root if reading from pcap (future feature),
        # but for live sniffing we need privileges.
        logging.warning("Not running as root. Sniffing might fail or show limited packets.")

    # Initialization
    logging.info(f"Starting {SCRIPT_NAME} v1.0.0")
    config = ConfigLoader.load(args.config)

    analyzer = IPFloodAnalyzer(args, config)

    # Signal Handling
    signal.signal(signal.SIGINT, analyzer.stop)
    signal.signal(signal.SIGTERM, analyzer.stop)

    # Execution
    analyzer.run()

if __name__ == "__main__":
    main()
