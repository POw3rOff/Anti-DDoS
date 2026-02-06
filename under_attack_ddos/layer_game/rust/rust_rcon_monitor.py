#!/usr/bin/env python3
"""
Rust RCON Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects RCON brute-force and malformed packet attacks on Rust servers.
Protocol: RCON over TCP (Valve Source RCON variant).
"""

import sys
import os
import logging
import argparse
import time
from collections import defaultdict

# Add layer_game directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from common.game_protocol_parser import GameProtocolParser
    from scapy.all import sniff, IP, TCP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# --- Identity ---
SCRIPT_NAME = "rust_rcon_monitor"
GAME_NAME = "Rust"

class RustRCONMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=28016, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        
        self.interface = interface
        self.port = int(port)
        
        # --- Thresholds & Stats ---
        self.login_attempts = defaultdict(int) 
        self.bad_packet_counts = defaultdict(int)
        self.last_reset = time.time()
        
        # Defaults
        self.max_login_pps = self.config.get("max_login_pps", 1)
        self.max_bad_packets = self.config.get("max_bad_packets", 5)

    def packet_callback(self, packet):
        """Processes TCP traffic on Rust RCON port."""
        if IP in packet and TCP in packet and Raw in packet:
            src_ip = packet[IP].src
            payload = packet[Raw].load

            # --- Minimal Source RCON Packet Validation ---
            # Header: Length (4 bytes), RequestID (4 bytes), Type (4 bytes), Body (null term), Suffix (null term)
            # Min length = 4+4+4+1+1 = 14 bytes
            if len(payload) < 14:
                self.bad_packet_counts[src_ip] += 1
                return

            try:
                # Type 3 = SERVERDATA_AUTH
                # In Source RCON, the type field starts at offset 8 (0-indexed)
                packet_type = int.from_bytes(payload[8:12], byteorder='little')
                
                if packet_type == 3:
                    self.login_attempts[src_ip] += 1
                    logging.debug(f"Login attempt from {src_ip}")
            except Exception:
                self.bad_packet_counts[src_ip] += 1

    def analyze(self):
        """Analyzes behavior windows."""
        now = time.time()
        duration = now - self.last_reset
        if duration < 0.1: return

        for ip in list(self.login_attempts.keys()):
            lps = self.login_attempts[ip] / duration
            if lps > self.max_login_pps:
                self.emit_event("rcon_brute_force", ip, "HIGH", {
                    "login_pps": round(lps, 1),
                    "threshold": self.max_login_pps
                })

        for ip in list(self.bad_packet_counts.keys()):
            if self.bad_packet_counts[ip] > self.max_bad_packets:
                self.emit_event("rcon_malformed_packets", ip, "MEDIUM", {
                    "count": self.bad_packet_counts[ip]
                })

        # Pruning
        self.login_attempts.clear()
        self.bad_packet_counts.clear()
        self.last_reset = now

    def run(self):
        bpf_filter = f"tcp port {self.port}"
        logging.info(f"Monitoring Rust RCON on {bpf_filter}...")
        
        try:
            while True:
                sniff(
                    filter=bpf_filter,
                    prn=self.packet_callback,
                    store=0,
                    timeout=5.0, # 5 second analysis window
                    iface=self.interface
                )
                self.analyze()
        except KeyboardInterrupt:
            logging.info("Exiting...")

def main():
    parser = argparse.ArgumentParser(description="Rust RCON Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Interface to sniff")
    parser.add_argument("--port", type=int, default=28016, help="Rust RCON Port (Default: 28016)")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()

    # Elevation check
    if sys.platform != "win32" and os.geteuid() != 0:
        logging.warning("Not running as root. This might fail.")

    monitor = RustRCONMonitor(args.config, args.interface, args.port, args.dry_run)
    monitor.run()

if __name__ == "__main__":
    main()
