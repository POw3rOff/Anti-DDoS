#!/usr/bin/env python3
"""
Metin2 Protocol Anomaly Detector
Part of Layer G (Game Protocol Defense)

Responsibility: Detects protocol violations, handshake timing anomalies,
and sequence disorders in the Metin2 authentication flow.
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
SCRIPT_NAME = "metin2_protocol_anomaly"
LAYER = "game"
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
class Metin2ProtocolAnomaly:
    def __init__(self, config_path=None, interface=None, dry_run=False):
        self.baseline = Metin2Baseline(config_path)
        self.interface = interface
        self.dry_run = dry_run

        # Track client states: {src_ip: {"state": int, "ts": float}}
        self.client_states = defaultdict(lambda: {"state": STATE_INIT, "ts": time.time()})
        self.cleanup_interval = 10.0
        self.last_cleanup = time.time()

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
        Analyzes TCP payload to infer protocol state and detect violations.
        """
        if IP in packet and TCP in packet and Raw in packet:
            # Check destination port (Client -> Server)
            if packet[TCP].dport == DEFAULT_AUTH_PORT:
                self._analyze_client_packet(packet)

        # Periodic cleanup of stale states
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self._cleanup_states()

    def _analyze_client_packet(self, packet):
        src_ip = packet[IP].src
        payload = packet[Raw].load

        # Heuristic State Machine (Simplified for passive monitoring)
        current_state = self.client_states[src_ip]["state"]
        last_ts = self.client_states[src_ip]["ts"]
        now = time.time()

        # 1. Timing Check (Baseline Validation)
        duration = now - last_ts
        is_anomaly, details = self.baseline.validate_handshake_time(duration)
        if is_anomaly:
            self.emit_event(src_ip, "timing_anomaly", details)
            # Reset state on failure
            del self.client_states[src_ip]
            return

        # 2. Sequence/Header Validation (Heuristic)
        # Metin2 packets often start with specific headers.
        # Example: 0x32 (Header), 0x45 (Key), 0x98 (Auth) - *Hypothetical for defense*

        # Logic: If client sends AUTH packet without HEADER/KEY first -> Violation
        # NOTE: Without a full dissector, we assume length-based heuristics here.
        pkt_len = len(payload)

        if current_state == STATE_INIT:
            # Expecting Initial Handshake (e.g., specific length)
            if pkt_len < 4: # Too small, likely garbage/fuzzing
                self.emit_event(src_ip, "malformed_packet", {"len": pkt_len, "reason": "too_short_init"})
            else:
                self.client_states[src_ip] = {"state": STATE_HEADER_SENT, "ts": now}

        elif current_state == STATE_HEADER_SENT:
            # Expecting Key Exchange
            self.client_states[src_ip] = {"state": STATE_KEY_EXCHANGE, "ts": now}

        # Update timestamp for timeout tracking
        self.client_states[src_ip]["ts"] = now

    def _cleanup_states(self):
        """Remove clients that timed out or disconnected."""
        now = time.time()
        timeout = self.baseline.config.get("handshake_timeout", 5.0)

        to_remove = []
        for ip, data in self.client_states.items():
            if now - data["ts"] > timeout:
                # Optional: Flag as "zombie connection" or "slow read"
                to_remove.append(ip)

        for ip in to_remove:
            del self.client_states[ip]

        self.last_cleanup = now

    def emit_event(self, src_ip, event_type, details):
        """Emits a structured JSON event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "game": GAME,
            "event": event_type,
            "src_ip": src_ip,
            "severity": "HIGH",
            "data": {
                "details": details,
                "status": "simulated" if self.dry_run else "active"
            }
        }

        print(json.dumps(event))
        sys.stdout.flush()
        logging.warning(f"ALERT: Protocol violation from {src_ip}: {event_type}")

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
    parser.add_argument("--test-type", choices=["timing", "malformed"], help="Type of anomaly to simulate")

    args = parser.parse_args()

    detector = Metin2ProtocolAnomaly(args.config, args.interface, args.dry_run)

    if args.test_ip and args.test_type:
        logging.info(f"Simulating {args.test_type} from {args.test_ip}")
        if args.test_type == "timing":
            detector.emit_event(args.test_ip, "timing_anomaly", {"duration": 10.0, "limit": 5.0})
        elif args.test_type == "malformed":
            detector.emit_event(args.test_ip, "malformed_packet", {"len": 2, "reason": "too_short"})
    else:
        if os.geteuid() != 0:
            logging.warning("Not running as root. Sniffing might fail.")
        detector.run()

if __name__ == "__main__":
    main()
