#!/usr/bin/env python3
"""
RakNet Protocol Monitor (Rust / Minecraft Bedrock)
Part of Layer G
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
except ImportError:
    # Fallback/Mock for dry-run if dependencies missing
    GameProtocolParser = object 

# --- Identity ---
SCRIPT_NAME = "raknet_monitor"
GAME_NAME = "Rust_RakNet"

class RakNetMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=19132, dry_run=False):
        if GameProtocolParser != object:
            super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        else:
            self.config = {}
            self.dry_run = dry_run

        self.interface = interface
        self.port = int(port)
        
        self.ping_counts = defaultdict(int)
        self.window_start = time.time()
        self.window_size = 1.0
        
        # Thresholds
        self.max_pings_pps = 10 

    def packet_callback(self, packet):
        if IP in packet and UDP in packet:
            if Raw in packet:
                payload = packet[Raw].load
                if len(payload) > 0:
                    # RakNet Unconnected Ping is 0x01 or 0x02
                    pid = payload[0]
                    if pid in [0x01, 0x02]:
                        src_ip = packet[IP].src
                        self.ping_counts[src_ip] += 1

    def analyze(self):
        now = time.time()
        if now - self.window_start >= self.window_size:
            for ip, count in self.ping_counts.items():
                rate = count / self.window_size
                if rate > self.max_pings_pps:
                    self.emit_event("raknet_ping_flood", ip, "MEDIUM", {
                        "pps": round(rate, 1),
                        "threshold": self.max_pings_pps
                    })
            
            self.ping_counts.clear()
            self.window_start = now

    def emit_event(self, event_type, src_ip, severity, details):
        import json
        from datetime import datetime, timezone
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": "game",
            "game": "rust",
            "event": event_type,
            "src_ip": src_ip,
            "severity": severity,
            "details": details
        }
        print(json.dumps(alert))
        sys.stdout.flush()

    def run(self):
        bpf_filter = f"udp port {self.port}"
        logging.info(f"Monitoring RakNet on {bpf_filter}...")
        try:
            from scapy.all import sniff
            while True:
                sniff(
                    filter=bpf_filter,
                    prn=self.packet_callback,
                    store=0,
                    timeout=1.0,
                    iface=self.interface
                )
                self.analyze()
        except ImportError:
            logging.error("Scapy not found.")
        except KeyboardInterrupt:
            pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface")
    parser.add_argument("--port", type=int, default=19132)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    monitor = RakNetMonitor(None, args.interface, args.port, args.dry_run)
    monitor.run()

if __name__ == "__main__":
    main()
