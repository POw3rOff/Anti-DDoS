#!/usr/bin/env python3
"""
FiveM (CitizenFX) Protocol Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects heartbeats floods and malformed Enet-based traffic.
Protocol: Enet (UDP) with CitizenFX specifics.
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
    from scapy.all import sniff, IP, UDP, Raw, conf
    if sys.platform == "win32":
        from scapy.all import L3RawSocket
        conf.L3socket = L3RawSocket
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# --- Identity ---
SCRIPT_NAME = "fivem_monitor"
GAME_NAME = "FiveM"

class FiveMMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=30120, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        
        self.interface = interface
        self.port = int(port)
        
        # --- Thresholds & Stats ---
        self.packet_counts = defaultdict(int) 
        self.last_reset = time.time()
        
        # FiveM specifics: CitizenFX usually has a specific UDP header for Enet
        self.max_pps = self.config.get("max_pps_per_ip", 50)
        self.query_counts = defaultdict(int)
        self.max_query_pps = self.config.get("max_query_pps", 5)

    def packet_callback(self, packet):
        """Processes UDP traffic on FiveM port with deeper inspection."""
        if IP in packet and UDP in packet:
            src_ip = packet[IP].src
            self.packet_counts[src_ip] += 1

            if Raw in packet:
                payload = packet[Raw].load
                # OOB Query detection
                if payload.startswith(b'\xff\xff\xff\xffgetinfo'):
                    self.query_counts = getattr(self, 'query_counts', defaultdict(int))
                    self.query_counts[src_ip] += 1
                
                # Malformed pack weights
                if len(payload) < 3:
                    self.packet_counts[src_ip] += 1 # Weighted

    def analyze(self):
        now = time.time()
        duration = now - self.last_reset
        if duration < 0.1: return

        ips = set(self.packet_counts.keys()) | set(self.query_counts.keys())

        for ip in ips:
            # 1. General UDP Flood
            pps = self.packet_counts[ip] / duration
            if pps > self.max_pps:
                self.emit_event("fivem_flood", ip, "HIGH", {
                    "pps": round(pps, 1),
                    "threshold": self.max_pps
                })
            
            # 2. Query/Reflection Flood
            q_pps = self.query_counts[ip] / duration
            if q_pps > self.max_query_pps:
                self.emit_event("fivem_query_flood", ip, "MEDIUM", {
                    "pps": round(q_pps, 1),
                    "threshold": self.max_query_pps
                })

        self.packet_counts.clear()
        self.query_counts.clear()
        self.last_reset = now


    def run(self):
        bpf_filter = f"udp port {self.port}"
        logging.info(f"Monitoring FiveM on {bpf_filter}...")
        
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
    parser = argparse.ArgumentParser(description="FiveM Protocol Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Interface to sniff")
    parser.add_argument("--port", type=int, default=30120, help="FiveM Port (Default: 30120)")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()

    if sys.platform != "win32" and os.geteuid() != 0:
        logging.warning("Not running as root. This might fail.")

    monitor = FiveMMonitor(args.config, args.interface, args.port, args.dry_run)
    monitor.run()

if __name__ == "__main__":
    main()
