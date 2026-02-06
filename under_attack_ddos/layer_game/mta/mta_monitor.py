#!/usr/bin/env python3
"""
MTA (Multi Theft Auto) Protocol Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Protects against Enet-based sync floods.
Protocol: Enet (UDP) variant.
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
SCRIPT_NAME = "mta_monitor"
GAME_NAME = "MTA"

class MTAMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=22003, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        
        self.interface = interface
        self.port = int(port)
        
        # --- Thresholds & Stats ---
        self.packet_counts = defaultdict(int) 
        self.last_reset = time.time()
        
        self.max_pps = self.config.get("max_pps_per_ip", 50)
        self.ase_counts = defaultdict(int)
        self.max_ase_pps = 5

    def packet_callback(self, packet):
        """Processes UDP traffic on MTA port."""
        if IP in packet and UDP in packet:
            src_ip = packet[IP].src
            self.packet_counts[src_ip] += 1
            
            if Raw in packet:
                payload = packet[Raw].load
                # ASE Query: 's' (0x73) usually at start of payload for ASE protocol
                # MTA ASE port is usually BasePort + 123
                # But here we inspect payload for simple signature
                if len(payload) > 0 and payload[0] == 0x73:
                    self.ase_counts[src_ip] += 1

    def analyze(self):
        now = time.time()
        duration = now - self.last_reset
        if duration < 0.1: return

        for ip, count in list(self.packet_counts.items()):
            pps = count / duration
            if pps > self.max_pps:
                self.emit_event("mta_flood", ip, "HIGH", {
                    "pps": round(pps, 1),
                    "threshold": self.max_pps
                })
        
        for ip, count in list(self.ase_counts.items()):
            pps = count / duration
            if pps > self.max_ase_pps:
                self.emit_event("mta_ase_flood", ip, "MEDIUM", {
                    "pps": round(pps, 1),
                    "threshold": self.max_ase_pps
                })

        self.packet_counts.clear()
        self.ase_counts.clear()
        self.last_reset = now

    def run(self):
        bpf_filter = f"udp port {self.port}"
        logging.info(f"Monitoring MTA on {bpf_filter}...")
        
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
    parser = argparse.ArgumentParser(description="MTA Protocol Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Interface to sniff")
    parser.add_argument("--port", type=int, default=22003, help="MTA Port (Default: 22003)")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()

    if sys.platform != "win32" and os.geteuid() != 0:
        logging.warning("Not running as root. This might fail.")

    monitor = MTAMonitor(args.config, args.interface, args.port, args.dry_run)
    monitor.run()

if __name__ == "__main__":
    main()
