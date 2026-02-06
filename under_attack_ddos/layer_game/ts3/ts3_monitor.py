#!/usr/bin/env python3
"""
TeamSpeak 3 Protocol Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects TeamSpeak 3 handshake floods and reflection attempts.
Protocol: TS3 (UDP).
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
SCRIPT_NAME = "ts3_monitor"
GAME_NAME = "TS3"

class TS3Monitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=9987, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        
        self.interface = interface
        self.port = int(port)
        
        # --- Thresholds & Stats ---
        self.handshake_counts = defaultdict(int) 
        self.last_reset = time.time()
        
        self.max_handshake_pps = self.config.get("max_handshake_pps", 5)

    def packet_callback(self, packet):
        """Processes UDP traffic on TS3 port."""
        if IP in packet and UDP in packet and Raw in packet:
            src_ip = packet[IP].src
            payload = packet[Raw].load

            # --- TS3 Handshake / Command Detection ---
            # TS3 packets have a header, usually starts with some specific bytes
            # Simple check for very common handshake/query patterns if possible
            # Here we just track general PPS for now as a baseline
            self.handshake_counts[src_ip] += 1

    def analyze(self):
        now = time.time()
        duration = now - self.last_reset
        if duration < 0.1: return

        for ip, count in list(self.handshake_counts.items()):
            pps = count / duration
            if pps > self.max_handshake_pps:
                self.emit_event("ts3_flood", ip, "HIGH", {
                    "pps": round(pps, 1),
                    "threshold": self.max_handshake_pps
                })

        self.handshake_counts.clear()
        self.last_reset = now

    def run(self):
        bpf_filter = f"udp port {self.port}"
        logging.info(f"Monitoring TeamSpeak 3 on {bpf_filter}...")
        
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
    parser = argparse.ArgumentParser(description="TeamSpeak 3 Protocol Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Interface to sniff")
    parser.add_argument("--port", type=int, default=9987, help="TS3 Port (Default: 9987)")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()

    if sys.platform != "win32" and os.geteuid() != 0:
        logging.warning("Not running as root. This might fail.")

    monitor = TS3Monitor(args.config, args.interface, args.port, args.dry_run)
    monitor.run()

if __name__ == "__main__":
    main()
 Boris? No, Antigravity.
