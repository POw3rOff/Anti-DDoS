#!/usr/bin/env python3
"""
Minecraft Protocol Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects Handshake floods, Status ping floods, and large packet attacks.
Protocol: Minecraft Java/Bedrock (Focusing on Java Handshake/SLP).
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
SCRIPT_NAME = "minecraft_monitor"
GAME_NAME = "Minecraft"

class MinecraftMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=25565, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME_NAME, config_path, dry_run)
        
        self.interface = interface
        self.port = int(port)
        
        # --- Thresholds & Stats ---
        self.handshake_counts = defaultdict(int) 
        self.status_ping_counts = defaultdict(int)
        self.large_packet_counts = defaultdict(int)
        
        # Sliding Windows (History of PPS)
        self.pps_history = defaultdict(lambda: {"handshake": [], "status": []})
        self.window_size = 5 # 5 intervals of 5 seconds = 25s window
        
        self.last_reset = time.time()
        
        # Defaults
        self.max_handshake_pps = self.config.get("max_handshake_pps", 2)
        self.max_status_pps = self.config.get("max_status_pps", 5)
        self.max_packet_size = self.config.get("max_packet_size", 1500)

    def packet_callback(self, packet):
        """Processes TCP traffic on Minecraft port."""
        if IP in packet and TCP in packet:
            src_ip = packet[IP].src
            
            # Check packet size
            if len(packet) > self.max_packet_size:
                self.large_packet_counts[src_ip] += 1

            if Raw in packet:
                payload = packet[Raw].load
                
                # --- Basic Minecraft Handshake / SLP Detection ---
                if len(payload) > 2:
                    # Minecraft Java: [VarInt len] [ID]. Usually 0x00 for handshake.
                    # Simple check: payload[1] is frequently 0x00 for ID 0.
                    packet_id = payload[1] 
                    
                    if packet_id == 0x00: 
                        if len(payload) < 10:
                            self.status_ping_counts[src_ip] += 1
                        else:
                            self.handshake_counts[src_ip] += 1

    def analyze(self):
        """Analyzes behavior windows using sliding averages."""
        now = time.time()
        duration = now - self.last_reset
        if duration < 1.0: return # Minimum 1s window

        ips = set(self.handshake_counts.keys()) | set(self.status_ping_counts.keys()) | set(self.large_packet_counts.keys()) | set(self.pps_history.keys())

        for ip in list(ips):
            # Calculate current PPS
            h_pps = self.handshake_counts[ip] / duration
            s_pps = self.status_ping_counts[ip] / duration
            
            # Update History
            hist = self.pps_history[ip]
            hist["handshake"].append(h_pps)
            hist["status"].append(s_pps)
            
            if len(hist["handshake"]) > self.window_size:
                hist["handshake"].pop(0)
                hist["status"].pop(0)

            # Average PPS over window
            avg_h = sum(hist["handshake"]) / len(hist["handshake"])
            avg_s = sum(hist["status"]) / len(hist["status"])

            # 1. Handshake Flood (Trigger on average exceed)
            if avg_h > self.max_handshake_pps:
                self.emit_event("mc_handshake_flood", ip, "HIGH", {
                    "avg_pps": round(avg_h, 1),
                    "current_pps": round(h_pps, 1),
                    "threshold": self.max_handshake_pps,
                    "window": f"{self.window_size * 5}s"
                })

            # 2. Status/Ping Flood
            if avg_s > self.max_status_pps:
                self.emit_event("mc_status_flood", ip, "MEDIUM", {
                    "avg_pps": round(avg_s, 1),
                    "current_pps": round(s_pps, 1),
                    "threshold": self.max_status_pps
                })

            # 3. Large Packets (Still immediate)
            if self.large_packet_counts[ip] > 20:
                self.emit_event("mc_oversized_packets", ip, "LOW", {
                    "count": self.large_packet_counts[ip],
                    "limit": 20
                })

            # Housekeeping for inactive IPs
            if h_pps == 0 and s_pps == 0 and sum(hist["handshake"]) == 0:
                del self.pps_history[ip]

        # Pruning
        self.handshake_counts.clear()
        self.status_ping_counts.clear()
        self.large_packet_counts.clear()
        self.last_reset = now

    def run(self):
        bpf_filter = f"tcp port {self.port}"
        logging.info(f"Monitoring Minecraft on {bpf_filter}...")
        
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
    parser = argparse.ArgumentParser(description="Minecraft Protocol Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Interface to sniff")
    parser.add_argument("--port", type=int, default=25565, help="Minecraft Port (Default: 25565)")
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()

    if sys.platform != "win32" and os.geteuid() != 0:
        logging.warning("Not running as root. This might fail.")

    monitor = MinecraftMonitor(args.config, args.interface, args.port, args.dry_run)
    monitor.run()

if __name__ == "__main__":
    main()
