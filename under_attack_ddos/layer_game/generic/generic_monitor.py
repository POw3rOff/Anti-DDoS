#!/usr/bin/env python3
"""
Generic Game Protocol Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Defends games that don't have a dedicated plugin using
configurable signatures (Hex/Regex) and behavior heuristics (Query Floods).
Supports Source Engine (A2S), RakNet, and text-based protocols.
"""

import sys
import os
import json
import time
import logging
import argparse
import re
import binascii
from collections import defaultdict
from datetime import datetime, timezone

# Add layer_game directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from common.game_protocol_parser import GameProtocolParser
    from scapy.all import sniff, IP, TCP, UDP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "generic_game_monitor"
GAME = "generic"

# -----------------------------------------------------------------------------
# Monitor Class
# -----------------------------------------------------------------------------
class GenericGameMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=None, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME, config_path, dry_run)

        self.interface = interface
        self.port = int(port) if port else None

        # Parse Config Rules
        self.signatures = self._parse_signatures()
        self.regex_rules = self._parse_regex_rules()

        # State Tracking
        self.query_counts = defaultdict(lambda: defaultdict(int)) # {ip: {sig_name: count}}
        self.pps_counts = defaultdict(int)

        self.start_window = time.time()
        self.window_size = 1.0

    def _parse_signatures(self):
        """Converts hex strings in config to byte objects."""
        sigs = []
        raw_sigs = self.config.get("query_flood", {}).get("signatures", [])
        for s in raw_sigs:
            try:
                # Remove spaces and 0x prefix
                clean_hex = s["hex_start"].replace(" ", "").replace("0x", "")
                byte_seq = binascii.unhexlify(clean_hex)
                sigs.append({
                    "name": s["name"],
                    "bytes": byte_seq,
                    "max_pps": s["max_pps"]
                })
            except Exception as e:
                logging.error(f"Invalid hex signature {s.get('name')}: {e}")
        return sigs

    def _parse_regex_rules(self):
        """Compiles regex rules."""
        rules = []
        raw_rules = self.config.get("payload_rules", [])
        for r in raw_rules:
            try:
                rules.append({
                    "name": r["name"],
                    "pattern": re.compile(r["regex"].encode()), # Compile as bytes regex
                    "max_pps": r["max_pps"],
                    "severity": r.get("severity", "MEDIUM")
                })
            except Exception as e:
                logging.error(f"Invalid regex rule {r.get('name')}: {e}")
        return rules

    def packet_callback(self, packet):
        """Callback for captured packets."""
        if IP in packet:
            src_ip = packet[IP].src
            # Filter by port if specified
            if self.port:
                if TCP in packet and packet[TCP].dport != self.port: return
                if UDP in packet and packet[UDP].dport != self.port: return

            self.pps_counts[src_ip] += 1

            if Raw in packet:
                payload = packet[Raw].load

                # 1. Hex Signature Matching (Query Floods)
                for sig in self.signatures:
                    if payload.startswith(sig["bytes"]):
                        self.query_counts[src_ip][sig["name"]] += 1

                # 2. Regex Payload Analysis
                for rule in self.regex_rules:
                    if rule["pattern"].search(payload):
                         self.query_counts[src_ip][rule["name"]] += 1

    def analyze_window(self):
        """Check accumulated metrics against thresholds."""
        now = time.time()
        duration = now - self.start_window
        if duration < 0.1: duration = 0.1

        # Global Thresholds
        global_max_pps = self.config.get("max_pps_per_ip", 100)

        ips_to_purge = []

        for ip, total_pkt in self.pps_counts.items():
            # 1. General Volumetric
            pps = total_pkt / duration
            if pps > global_max_pps:
                self.emit_event("volumetric_flood", ip, "HIGH", {
                    "pps": round(pps, 2),
                    "threshold": global_max_pps
                })

            # 2. Signature/Rule Checks
            if ip in self.query_counts:
                for rule_name, count in self.query_counts[ip].items():
                    rule_pps = count / duration

                    # Find limit
                    limit = 0
                    severity = "MEDIUM"

                    # Search in Hex Sigs
                    for s in self.signatures:
                        if s["name"] == rule_name:
                            limit = s["max_pps"]
                            severity = "HIGH" # Query floods usually impactful
                            break

                    # Search in Regex Rules
                    if limit == 0:
                        for r in self.regex_rules:
                            if r["name"] == rule_name:
                                limit = r["max_pps"]
                                severity = r["severity"]
                                break

                    if rule_pps > limit:
                        self.emit_event("signature_match", ip, severity, {
                            "rule": rule_name,
                            "pps": round(rule_pps, 2),
                            "threshold": limit
                        })

            ips_to_purge.append(ip)

        # Cleanup
        for ip in ips_to_purge:
            del self.pps_counts[ip]
            if ip in self.query_counts: del self.query_counts[ip]

        self.start_window = now

    def run(self):
        """Main capture loop."""
        bpf_filter = f"port {self.port}" if self.port else "ip"

        logging.info(f"Starting Generic Monitor on filter '{bpf_filter}'...")
        try:
            while True:
                sniff(
                    filter=bpf_filter,
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
    parser = argparse.ArgumentParser(description="Generic Game Protocol Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Network interface to sniff")
    parser.add_argument("--port", type=int, help="Target Game Port (UDP/TCP)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate events")

    args = parser.parse_args()

    # Resolve default config
    config_path = args.config
    if not config_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")

    monitor = GenericGameMonitor(config_path, args.interface, args.port, args.dry_run)

    if os.geteuid() != 0:
        logging.warning("Not running as root. Sniffing might fail.")

    monitor.run()

if __name__ == "__main__":
    main()
