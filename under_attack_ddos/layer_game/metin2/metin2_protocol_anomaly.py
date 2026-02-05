#!/usr/bin/env python3
"""
Metin2 Protocol Anomaly Detector
Part of Layer G (Game Protocol Defense)

Responsibility: Detects protocol violations, handshake timing anomalies,
zombie connections (slowloris-style), and sequence disorders.
"""

import sys
import os
import json
import time
import logging
import argparse
from datetime import datetime, timezone
from collections import defaultdict

# Add layer_game directory to path
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
SCRIPT_NAME = "metin2_protocol_anomaly"
GAME = "metin2"
DEFAULT_AUTH_PORT = 11002

# Simplified Metin2 Handshake States
STATE_INIT = 0
STATE_HEADER_SENT = 1
STATE_KEY_EXCHANGE = 2
STATE_AUTH_SENT = 3

# -----------------------------------------------------------------------------
# Anomaly Detector Class
# -----------------------------------------------------------------------------
class Metin2ProtocolAnomaly(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME, config_path, dry_run)

        self.baseline = Metin2Baseline(config_path)
        self.interface = interface

        # Track client states: {src_ip: {"state": int, "ts": float}}
        self.client_states = defaultdict(lambda: {"state": STATE_INIT, "ts": time.time()})
        self.cleanup_interval = 2.0
        self.last_cleanup = time.time()

    def packet_callback(self, packet):
        """
        Callback for Scapy sniffer.
        Analyzes TCP payload to infer protocol state and detect violations.
        """
        # Optimization: Use getlayer to avoid repeated traversal
        ip_layer = packet.getlayer(IP)
        tcp_layer = packet.getlayer(TCP)
        raw_layer = packet.getlayer(Raw)

        if ip_layer and tcp_layer and raw_layer:
            # Check destination port (Client -> Server)
            if tcp_layer.dport == DEFAULT_AUTH_PORT:
                self._analyze_client_packet(ip_layer, raw_layer)

        # Periodic cleanup of stale states
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self._cleanup_states()

    def _analyze_client_packet(self, ip_layer, raw_layer):
        src_ip = ip_layer.src
        payload = raw_layer.load

        # Heuristic State Machine
        current_state = self.client_states[src_ip]["state"]
        last_ts = self.client_states[src_ip]["ts"]
        now = time.time()

        # 1. Timing Check (Baseline Validation)
        duration = now - last_ts
        is_anomaly, details = self.baseline.validate_handshake_time(duration)
        if is_anomaly:
            self.emit_event("timing_anomaly", src_ip, "HIGH", details)
            del self.client_states[src_ip]
            return

        # 2. Sequence/Header Validation (Heuristic)
        pkt_len = len(payload)

        if current_state == STATE_INIT:
            if pkt_len < 4:
                self.emit_event("malformed_packet", src_ip, "HIGH", {"len": pkt_len, "reason": "too_short_init"})
            else:
                self.client_states[src_ip] = {"state": STATE_HEADER_SENT, "ts": now}

        elif current_state == STATE_HEADER_SENT:
            self.client_states[src_ip] = {"state": STATE_KEY_EXCHANGE, "ts": now}

        elif current_state == STATE_KEY_EXCHANGE:
            self.client_states[src_ip] = {"state": STATE_AUTH_SENT, "ts": now}

        self.client_states[src_ip]["ts"] = now

    def _cleanup_states(self):
        """Remove clients that timed out or disconnected."""
        now = time.time()
        timeout = self.baseline.config.get("handshake_timeout", 5.0)

        to_remove = []
        for ip, data in self.client_states.items():
            age = now - data["ts"]
            if age > timeout:
                if data["state"] < STATE_AUTH_SENT:
                     self.emit_event("zombie_connection", ip, "HIGH", {
                         "state": data["state"],
                         "duration": round(age, 2)
                     })
                to_remove.append(ip)

        for ip in to_remove:
            del self.client_states[ip]

        self.last_cleanup = now

    def run(self):
        """Main capture loop."""
        logging.info(f"Starting protocol monitor on port {DEFAULT_AUTH_PORT}...")
        try:
            sniff(
                filter=f"tcp dst port {DEFAULT_AUTH_PORT}",
                prn=self.packet_callback,
                store=0,
                iface=self.interface
            )
        except KeyboardInterrupt:
            logging.info("Stopping...")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Metin2 Protocol Anomaly Detector")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Network interface to sniff")
    parser.add_argument("--dry-run", action="store_true", help="Simulate events")

    # Test Flags
    parser.add_argument("--test-ip", help="Simulate anomalous packet from IP")
    parser.add_argument("--test-type", choices=["timing", "malformed", "zombie"], help="Type of anomaly to simulate")

    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")

    detector = Metin2ProtocolAnomaly(config_path, args.interface, args.dry_run)

    if args.test_ip and args.test_type:
        logging.info(f"Simulating {args.test_type} from {args.test_ip}")
        if args.test_type == "timing":
            detector.emit_event("timing_anomaly", args.test_ip, "HIGH", {"duration": 10.0, "limit": 5.0})
        elif args.test_type == "malformed":
            detector.emit_event("malformed_packet", args.test_ip, "HIGH", {"len": 2, "reason": "too_short"})
        elif args.test_type == "zombie":
             detector.emit_event("zombie_connection", args.test_ip, "HIGH", {"state": 1, "duration": 6.0})
    else:
        if os.geteuid() != 0:
            logging.warning("Not running as root. Sniffing might fail.")
        detector.run()

if __name__ == "__main__":
    main()
