#!/usr/bin/env python3
"""
Generic Source Engine Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Protects all Source Engine games (CS:GO, TF2, L4D2, etc.) 
against A2S (Source Engine Query) reflection and floods.
Protocol: Source Engine Query (UDP).
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
SCRIPT_NAME = "source_monitor"
GAME_NAME = "SourceEngine"

class SourceMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=27015, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        
        self.interface = interface
        self.port = int(port)
        
        # --- Thresholds & Stats ---
        self.query_counts = defaultdict(int) 
        self.last_reset = time.time()
        
        self.max_query_pps = self.config.get("max_query_pps", 3)

    def packet_callback(self, packet):
        """Processes UDP traffic on Source Engine port."""
        if IP in packet and UDP in packet and Raw in packet:
            src_ip = packet[IP].src
            payload = packet[Raw].load

            # --- Source Engine Query (A2S_INFO) Detection ---
            # Prefix: 4x 0xFF, followed by 0x54 (A2S_INFO)
            if payload.startswith(b'\xff\xff\xff\xff\x54'):
                self.query_counts[src_ip] += 1

    def analyze(self):
        now = time.time()
        duration = now - self.last_reset
        if duration < 0.1: return

        for ip, count in list(self.query_counts.items()):
            pps = count / duration
            if pps > self.max_query_pps:
                self.emit_event("a2s_query_flood", ip, "HIGH", {
                    "pps": round(pps, 1),
                    "threshold": self.max_query_pps
                })

        self.query_counts.clear()
        self.last_reset = now

    def run(self):
        bpf_filter = f"udp port {self.port}"
        logging.info(f"Monitoring Source Engine on {bpf_filter}...")
        
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
    parser = argparse.ArgumentParser(description="Source Engine Protocol Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Interface to sniff")
    parser.add_argument("--port", type=int, default=27015, help="Source Port (Default: 27015)")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()

    if sys.platform != "win32" and os.geteuid() != 0:
        logging.warning("Not running as root. This might fail.")

    monitor = SourceMonitor(args.config, args.interface, args.port, args.dry_run)
    monitor.run()

if __name__ == "__main__":
    main()
