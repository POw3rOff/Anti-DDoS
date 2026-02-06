#!/usr/bin/env python3
"""
Game Monitor Boilerplate Template
Part of Layer G (Game Protocol Defense)

This template serves as a starting point for implementing new game-specific
protocol monitors.
"""

import sys
import os
import json
import logging
import argparse
import time
from collections import defaultdict

# Add layer_game directory to path to allow importing 'common'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from common.game_protocol_parser import GameProtocolParser
    # Import scapy for packet capture
    from scapy.all import sniff, IP, TCP, UDP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# --- Identity ---
SCRIPT_NAME = "game_monitor_template"
GAME_NAME = "example_game"

class ExampleGameMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=None, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        
        self.interface = interface
        self.port = int(port) if port else None
        
        # --- Metrics & State ---
        self.packet_counts = defaultdict(int)
        self.last_analysis_time = time.time()
        self.analysis_interval = 2.0 # Analyze every 2 seconds

    def packet_callback(self, packet):
        """
        Process each captured packet.
        Refine the BPF filter in run() to minimize CPU overhead.
        """
        if IP in packet:
            src_ip = packet[IP].src
            
            # 1. Basic Rate Tracking
            self.packet_counts[src_ip] += 1
            
            # 2. Protocol-Specific Logic
            if Raw in packet:
                payload = packet[Raw].load
                self.process_payload(src_ip, payload)

    def process_payload(self, src_ip, payload):
        """
        Implement Deep Packet Inspection (DPI) here.
        Example: Detect malformed headers or known exploit signatures.
        """
        pass

    def analyze_behavior(self):
        """
        Analyze accumulated metrics over the window.
        """
        now = time.time()
        duration = now - self.last_analysis_time
        
        threshold = self.config.get("max_pps", 100)
        
        for ip, count in list(self.packet_counts.items()):
            pps = count / duration
            if pps > threshold:
                self.emit_event("high_pps_detected", ip, "MEDIUM", {
                    "pps": round(pps, 2),
                    "threshold": threshold
                })
        
        # Reset counters
        self.packet_counts.clear()
        self.last_analysis_time = now

    def run(self):
        """Main capture loop."""
        bpf_filter = f"port {self.port}" if self.port else "ip"
        
        logging.info(f"Starting {GAME_NAME} monitor on '{self.interface or 'default'}'...")
        
        try:
            while True:
                sniff(
                    filter=bpf_filter,
                    prn=self.packet_callback,
                    store=0,
                    timeout=self.analysis_interval,
                    iface=self.interface
                )
                self.analyze_behavior()
        except KeyboardInterrupt:
            logging.info("Shutting down...")

def main():
    parser = argparse.ArgumentParser(description=f"{GAME_NAME} Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Interface to sniff")
    parser.add_argument("--port", type=int, help="Game port")
    parser.add_argument("--dry-run", action="store_true", help="Simulate alerts")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        logging.warning("Not running as root. Scapy may fail.")

    monitor = ExampleGameMonitor(
        config_path=args.config,
        interface=args.interface,
        port=args.port,
        dry_run=args.dry_run
    )
    monitor.run()

if __name__ == "__main__":
    main()
