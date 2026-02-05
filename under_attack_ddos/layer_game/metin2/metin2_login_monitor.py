#!/usr/bin/env python3
"""
Metin2 Login Flood Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects excessive authentication attempts (login floods) by monitoring
network traffic or logs. Handles single-source floods and distributed (global) floods.
"""

import sys
import os
import json
import time
import logging
import argparse
from datetime import datetime, timezone
from collections import defaultdict

# Add layer_game directory to path to allow importing common and metin2 modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from common.game_protocol_parser import GameProtocolParser
    from metin2.metin2_baseline import Metin2Baseline
    from scapy.all import sniff, IP, TCP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies or modules: {e}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "metin2_login_monitor"
GAME = "metin2"
DEFAULT_AUTH_PORT = 11002

# -----------------------------------------------------------------------------
# Monitor Class
# -----------------------------------------------------------------------------
class Metin2LoginMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, dry_run=False):
        # Initialize base class (handles logging and config loading)
        super().__init__(SCRIPT_NAME, GAME, config_path, dry_run)

        self.baseline = Metin2Baseline(config_path)
        self.interface = interface

        self.login_counts = defaultdict(int)
        self.global_login_count = 0
        self.start_time = time.time()
        self.window_size = 1.0  # Check every second

    def packet_callback(self, packet):
        """
        Callback for Scapy sniffer.
        Detects potential AUTH_LOGIN packets based on port and payload heuristics.
        """
        if IP in packet and TCP in packet:
            # Check if packet is destined for Auth Port
            if packet[TCP].dport == DEFAULT_AUTH_PORT:
                if Raw in packet:
                    self.login_counts[packet[IP].src] += 1
                    self.global_login_count += 1

    def analyze_window(self):
        """Analyzes accumulated login attempts against baseline."""
        now = time.time()
        duration = now - self.start_time
        if duration < 0.1: duration = 0.1

        # 1. Per-IP Analysis
        for ip, count in self.login_counts.items():
            pps = count / duration
            is_anomaly, details = self.baseline.validate_login_rate(pps)

            if is_anomaly:
                # Construct data payload for event
                data = {
                    "pps_observed": round(details["value"], 2),
                    "pps_threshold": details["threshold"],
                    "status": "simulated" if self.dry_run else "active"
                }
                self.emit_event("auth_flood", ip, details["severity"], data)

        # 2. Global Distributed Flood Analysis
        global_pps = self.global_login_count / duration
        global_threshold = self.baseline.config.get("global_login_pps", 200)

        if global_pps > global_threshold:
            self.emit_event("distributed_auth_flood", "GLOBAL", "CRITICAL", {
                "value": round(global_pps, 2),
                "threshold": global_threshold,
                "unique_ips": len(self.login_counts),
                "status": "simulated" if self.dry_run else "active"
            })

        # Reset for next window
        self.login_counts.clear()
        self.global_login_count = 0
        self.start_time = time.time()

    def run(self):
        """Main capture loop."""
        logging.info(f"Starting capture on port {DEFAULT_AUTH_PORT}...")
        try:
            while True:
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

    # Pass config path to default if not provided, to ensure it loads from correct place
    config_path = args.config
    if not config_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")

    monitor = Metin2LoginMonitor(config_path, args.interface, args.dry_run)

    if args.test_ip:
        # Simulation Mode
        logging.info(f"Simulating flood from {args.test_ip} with {args.test_pps} PPS")
        monitor.login_counts[args.test_ip] = int(args.test_pps)
        monitor.global_login_count = int(args.test_pps)
        monitor.analyze_window()
    else:
        # Live Mode
        if os.geteuid() != 0:
            logging.warning("Not running as root. Sniffing might fail.")
        monitor.run()

if __name__ == "__main__":
    main()
