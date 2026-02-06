#!/usr/bin/env python3
"""
Rust Session Abuse Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects post-handshake anomalies in Rust (RakNet) sessions,
including entity spam, voice chat floods, and packet stuffing.
"""

import sys
import os
import time
import logging
import argparse
import math
from collections import defaultdict

# Add layer_game directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from common.game_protocol_parser import GameProtocolParser
    from scapy.all import sniff, IP, UDP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "rust_session_monitor"
GAME = "rust"
DEFAULT_GAME_PORT = 28015

# RakNet Data Packet ID Range (Approximate, usually 0x80-0x8F for data frames)
RAKNET_DATA_FRAME_START = 0x80
RAKNET_DATA_FRAME_END = 0x8F

# -----------------------------------------------------------------------------
# Session Monitor Class
# -----------------------------------------------------------------------------
class RustSessionMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, port=None, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME, config_path, dry_run)

        self.interface = interface
        self.port = int(port) if port else DEFAULT_GAME_PORT

        # State tracking
        self.sessions = defaultdict(lambda: {"pkt_count": 0, "bytes": 0, "last_ts": time.time()})
        self.entity_update_counts = defaultdict(int) # Heuristic tracking

        self.start_window = time.time()
        self.window_size = 1.0

    def packet_callback(self, packet):
        """Callback for captured packets."""
        if IP in packet and UDP in packet:
            # Filter for Game Port (Dst = Server)
            if packet[UDP].dport != self.port: return

            src_ip = packet[IP].src
            now = time.time()

            # Session tracking
            sess = self.sessions[src_ip]
            sess["pkt_count"] += 1
            sess["last_ts"] = now

            if Raw in packet:
                payload = packet[Raw].load
                p_len = len(payload)
                sess["bytes"] += p_len

                if p_len > 0:
                    byte0 = payload[0]
                    # Check if it's a data frame (RakNet)
                    if RAKNET_DATA_FRAME_START <= byte0 <= RAKNET_DATA_FRAME_END:
                         # Heuristic: Large packets often contain multiple messages or entity updates
                         if p_len > 1000:
                             self.entity_update_counts[src_ip] += 1

    def analyze_window(self):
        """Check accumulated metrics against thresholds."""
        now = time.time()
        duration = now - self.start_window
        if duration < 0.1: duration = 0.1

        # Load Thresholds
        session_conf = self.config.get("session_abuse", {})
        max_pps = session_conf.get("max_pps", 100)
        max_mbps = session_conf.get("max_mbps", 1.0)
        max_entity_updates = session_conf.get("max_entity_updates_pps", 20)

        ips_to_purge = []

        for ip, sess in self.sessions.items():
            # 1. PPS Check
            pps = sess["pkt_count"] / duration
            if pps > max_pps:
                self.emit_event("session_pps_flood", ip, "HIGH", {
                    "value": round(pps, 2),
                    "threshold": max_pps
                })

            # 2. Bandwidth Check (Mbps)
            mbps = (sess["bytes"] * 8) / (1024 * 1024) / duration
            if mbps > max_mbps:
                 self.emit_event("session_bandwidth_flood", ip, "MEDIUM", {
                    "value": round(mbps, 2),
                    "threshold": max_mbps
                })

            # 3. Entity/Large Packet Spam
            if ip in self.entity_update_counts:
                updates_pps = self.entity_update_counts[ip] / duration
                if updates_pps > max_entity_updates:
                     self.emit_event("entity_spam_detected", ip, "HIGH", {
                        "value": round(updates_pps, 2),
                        "threshold": max_entity_updates,
                        "desc": "excessive_large_packets"
                    })

            # Reset per-window counters
            sess["pkt_count"] = 0
            sess["bytes"] = 0

            # Idle cleanup
            if now - sess["last_ts"] > 60:
                ips_to_purge.append(ip)

        self.entity_update_counts.clear()

        # Cleanup
        for ip in ips_to_purge:
            del self.sessions[ip]

        self.start_window = now

    def run(self):
        """Main capture loop."""
        bpf_filter = f"udp port {self.port}"

        logging.info(f"Starting Rust Session Monitor with filter: '{bpf_filter}'...")
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
    parser = argparse.ArgumentParser(description="Rust Session Abuse Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Network interface to sniff")
    parser.add_argument("--port", type=int, default=DEFAULT_GAME_PORT, help="Game Port")
    parser.add_argument("--dry-run", action="store_true", help="Simulate events")

    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")

    monitor = RustSessionMonitor(config_path, args.interface, args.port, args.dry_run)

    if os.geteuid() != 0:
        logging.warning("Not running as root. Sniffing might fail.")

    monitor.run()

if __name__ == "__main__":
    main()
