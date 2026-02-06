#!/usr/bin/env python3
"""
SAMP (San Andreas Multiplayer) Protocol Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects Join floods and malformed RakNet packets.
Protocol: RakNet (UDP).
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
    from scapy.all import sniff, IP, UDP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# --- Identity ---
SCRIPT_NAME = "samp_monitor"
GAME_NAME = "SAMP"

class SAMPMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=7777, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        
        self.interface = interface
        self.port = int(port)
        
        # --- Thresholds & Stats ---
        self.join_counts = defaultdict(int) 
        self.query_counts = defaultdict(int)
        self.last_reset = time.time()
        
        self.max_join_pps = self.config.get("max_join_pps", 2)
        self.max_query_pps = self.config.get("max_query_pps", 5)

    def packet_callback(self, packet):
        """Processes UDP traffic on SAMP port."""
        if IP in packet and UDP in packet and Raw in packet:
            src_ip = packet[IP].src
            payload = packet[Raw].load

            # --- SAMP / RakNet Packet Detection ---
            # SAMP Query usually starts with 'SAMP' followed by IP (4 bytes) and Port (2 bytes)
            if payload.startswith(b'SAMP'):
                self.query_counts[src_ip] += 1
                return

            # join packet detection (simplistic)
            # RakNet connection request usually starts with certain byte IDs
            if len(payload) > 0:
                packet_id = payload[0]
                # ID_CONNECTION_REQUEST = 0x09 (Example for RakNet)
                if packet_id == 0x09:
                    self.join_counts[src_ip] += 1

    def analyze(self):
        now = time.time()
        duration = now - self.last_reset
        if duration < 0.1: return

        for ip in list(set(self.join_counts.keys()) | set(self.query_counts.keys())):
            j_pps = self.join_counts[ip] / duration
            if j_pps > self.max_join_pps:
                self.emit_event("samp_join_flood", ip, "HIGH", {
                    "pps": round(j_pps, 1),
                    "threshold": self.max_join_pps
                })

            q_pps = self.query_counts[ip] / duration
            if q_pps > self.max_query_pps:
                self.emit_event("samp_query_flood", ip, "MEDIUM", {
                    "pps": round(q_pps, 1),
                    "threshold": self.max_query_pps
                })

        self.join_counts.clear()
        self.query_counts.clear()
        self.last_reset = now

    def run(self):
        bpf_filter = f"udp port {self.port}"
        logging.info(f"Monitoring SAMP on {bpf_filter}...")
        
        try:
            while True:
                sniff(
                    filter=bpf_filter,
                    prn=self.packet_callback,
                    store=0,
                    timeout=5.0,
                    iface=self.interface
                )
                self.analyze()
        except KeyboardInterrupt:
            logging.info("Exiting...")

def main():
    parser = argparse.ArgumentParser(description="SAMP Protocol Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Interface to sniff")
    parser.add_argument("--port", type=int, default=7777, help="SAMP Port (Default: 7777)")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()

    if sys.platform != "win32" and os.geteuid() != 0:
        logging.warning("Not running as root. This might fail.")

    monitor = SAMPMonitor(args.config, args.interface, args.port, args.dry_run)
    monitor.run()

if __name__ == "__main__":
    main()
 Boris? No, Antigravity.
