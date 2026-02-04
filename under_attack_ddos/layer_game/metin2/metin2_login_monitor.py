#!/usr/bin/env python3
"""
Metin2 Login Flood Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects excessive authentication attempts (login floods) by monitoring
network traffic or logs and validating against the Metin2 behavioral baseline.
"""

import sys
import os
import json
import time
import logging
import argparse
from datetime import datetime, timezone
from collections import defaultdict

# Add parent directory to path to allow importing baseline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from metin2.metin2_baseline import Metin2Baseline
    from scapy.all import sniff, IP, TCP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies or baseline module: {e}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "metin2_login_monitor"
LAYER = "game"
GAME = "metin2"

# Metin2 default auth port (can be overridden)
DEFAULT_AUTH_PORT = 11002

# -----------------------------------------------------------------------------
# Monitor Class
# -----------------------------------------------------------------------------
class Metin2LoginMonitor:
    def __init__(self, config_path=None, interface=None, dry_run=False):
        self.baseline = Metin2Baseline(config_path)
        self.interface = interface
        self.dry_run = dry_run
        self.login_counts = defaultdict(int)
        self.start_time = time.time()
        self.window_size = 1.0  # Check every second

        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME}. Dry-run: {dry_run}")

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def packet_callback(self, packet):
        """
        Callback for Scapy sniffer.
        Detects potential AUTH_LOGIN packets based on port and payload heuristics.
        """
        if IP in packet and TCP in packet:
            # Check if packet is destined for Auth Port
            if packet[TCP].dport == DEFAULT_AUTH_PORT:
                # Heuristic: Metin2 Login packets usually have specific length or headers
                # For this monitor, we count connections/payloads to the auth port
                if Raw in packet:
                    self.login_counts[packet[IP].src] += 1

    def analyze_window(self):
        """Analyzes accumulated login attempts against baseline."""
        now = time.time()
        duration = now - self.start_time
        if duration < 0.1: duration = 0.1

        for ip, count in self.login_counts.items():
            pps = count / duration

            # Use Baseline module to validate
            is_anomaly, details = self.baseline.validate_login_rate(pps)

            if is_anomaly:
                self.emit_event(ip, details)

        # Reset for next window
        self.login_counts.clear()
        self.start_time = time.time()

    def emit_event(self, src_ip, details):
        """Emits a structured JSON event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "game": GAME,
            "event": "auth_flood",
            "src_ip": src_ip,
            "severity": details["severity"],
            "data": {
                "pps_observed": round(details["value"], 2),
                "pps_threshold": details["threshold"],
                "status": "simulated" if self.dry_run else "active"
            }
        }

        # STDOUT for Orchestrator
        print(json.dumps(event))
        sys.stdout.flush()

        # STDERR for operator logs
        logging.warning(f"ALERT: Auth flood from {src_ip} ({details['value']:.1f} PPS)")

    def run(self):
        """Main capture loop."""
        logging.info(f"Starting capture on port {DEFAULT_AUTH_PORT}...")

        try:
            while True:
                # Capture for window_size seconds
                sniff(
                    filter=f"tcp dst port {DEFAULT_AUTH_PORT}",
                    prn=self.packet_callback,
                    store=0,
                    timeout=self.window_size,
                    iface=self.interface
                )
                self.analyze_window()
        except KeyboardInterrupt:
            logging.info("Stopping...")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Metin2 Login Flood Detector")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Network interface to sniff")
    parser.add_argument("--dry-run", action="store_true", help="Simulate events without action")
    parser.add_argument("--test-ip", help="Simulate a flood from this IP (No sniffing)")
    parser.add_argument("--test-pps", type=float, default=10.0, help="PPS for test simulation")

    args = parser.parse_args()

    monitor = Metin2LoginMonitor(args.config, args.interface, args.dry_run)

    if args.test_ip:
        # Simulation Mode
        logging.info(f"Simulating flood from {args.test_ip} with {args.test_pps} PPS")
        monitor.login_counts[args.test_ip] = int(args.test_pps)
        monitor.analyze_window()
    else:
        # Live Mode
        if os.geteuid() != 0:
            logging.warning("Not running as root. Sniffing might fail.")
        monitor.run()

if __name__ == "__main__":
    main()
