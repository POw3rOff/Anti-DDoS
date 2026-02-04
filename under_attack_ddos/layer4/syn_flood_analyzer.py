#!/usr/bin/env python3
"""
Layer 4 TCP SYN Flood Analyzer
Part of 'under_attack_ddos' Defense System.

Responsibility: Detects abnormal rates of TCP SYN packets per source IP.
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

# Third-party imports
try:
    import yaml
    from scapy.all import sniff, IP, TCP
except ImportError as e:
    print(f"CRITICAL: Missing required dependencies: {e}", file=sys.stderr)
    print("Please install: pip install pyyaml scapy", file=sys.stderr)
    sys.exit(4)

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "l4_syn_flood_analyzer"
LAYER = "layer4"
RESPONSIBILITY = "Detect TCP SYN floods and state exhaustion attempts"

# Default configuration (Fail-safe)
DEFAULT_CONFIG = {
    "layer4": {
        "syn_flood": {
            "syn_rate_pps": 200,  # Global baseline per source
            "burst_tolerance": 1.5
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
            return user_config
        except Exception as e:
            logging.error(f"Failed to parse config: {e}")
            sys.exit(2)

class SynFloodAnalyzer:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.running = True
        self.syn_counts = defaultdict(int)

        # Load thresholds
        l4_conf = self.config.get("layer4", {}).get("syn_flood", {})
        base_pps = l4_conf.get("syn_rate_pps", 200)

        # Adjust based on mode
        if self.args.mode == "under_attack":
            self.pps_threshold = base_pps * 0.5  # Stricter
        elif self.args.mode == "monitor":
            self.pps_threshold = base_pps * 2.0  # Looser (reduce noise)
        else:
            self.pps_threshold = base_pps

        logging.info(f"Initialized {SCRIPT_NAME}. Mode: {args.mode}. SYN Threshold: {self.pps_threshold} PPS")

    def packet_callback(self, packet):
        """Called for each captured packet. BPF ensures we only get TCP SYNs."""
        if IP in packet:
            src_ip = packet[IP].src
            self.syn_counts[src_ip] += 1

    def analyze_window(self, duration):
        """Analyzes the accumulated SYN counts."""
        now = datetime.now(timezone.utc).isoformat()
        events = []

        for ip, count in self.syn_counts.items():
            pps = count / duration

            if pps > self.pps_threshold:
                # Calculate Severity
                if pps > (self.pps_threshold * 5):
                    severity = "CRITICAL"
                    confidence = "HIGH"
                elif pps > (self.pps_threshold * 2):
                    severity = "HIGH"
                    confidence = "MEDIUM"
                else:
                    severity = "MEDIUM"
                    confidence = "LOW"

                event = {
                    "timestamp": now,
                    "layer": LAYER,
                    "detector": SCRIPT_NAME,
                    "event": "syn_flood_detected",
                    "severity": severity,
                    "confidence": confidence,
                    "source_entity": ip,
                    "data": {
                        "syn_rate_pps": round(pps, 2),
                        "pps_threshold": self.pps_threshold,
                        "total_syns": count,
                        "duration": round(duration, 2)
                    }
                }

                if self.args.dry_run:
                    event["status"] = "simulated"
                    logging.info(f"[DRY-RUN] Would flag SYN flood from {ip} ({pps:.2f} PPS)")
                else:
                    event["status"] = "active"

                events.append(event)

        # Output events
        if self.args.json and events:
            for e in events:
                print(json.dumps(e))
        elif events:
            for e in events:
                logging.warning(f"ALERT: {e['event']} from {e['source_entity']} (PPS: {e['data']['syn_rate_pps']})")

        # Reset counters
        self.syn_counts.clear()

    def run(self):
        """Main Loop"""
        window_size = 5.0  # Seconds
        if self.args.mode == "under_attack":
            window_size = 2.0

        # BPF Filter: TCP (proto 6) and SYN flag set (0x02)
        # "tcp[13] & 2 != 0" checks if the SYN bit is set in the flags field
        bpf_filter = "tcp[13] & 2 != 0"

        logging.info(f"Starting capture loop. Window: {window_size}s. Filter: '{bpf_filter}'")

        try:
            while self.running:
                start_loop = time.time()

                # Sniff packets
                # count=0 means infinite (controlled by timeout)
                # store=0 prevents memory leaks
                sniff(filter=bpf_filter, prn=self.packet_callback, store=0, timeout=window_size)

                # Analyze
                duration = time.time() - start_loop
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
        stream=sys.stderr
    )

    # Root Check
    if os.geteuid() != 0 and not args.dry_run:
        logging.warning("Not running as root. Sniffing may fail.")

    # Initialization
    logging.info(f"Starting {SCRIPT_NAME} v1.0.0")
    config = ConfigLoader.load(args.config)

    analyzer = SynFloodAnalyzer(args, config)

    # Signal Handling
    signal.signal(signal.SIGINT, analyzer.stop)
    signal.signal(signal.SIGTERM, analyzer.stop)

    # Execution
    analyzer.run()

if __name__ == "__main__":
    main()
