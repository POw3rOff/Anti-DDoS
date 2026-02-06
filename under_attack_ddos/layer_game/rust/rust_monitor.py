#!/usr/bin/env python3
"""
Rust Game Protocol Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Defends Rust servers against RakNet handshake floods,
A2S query spam, and RCON brute-force attempts.
"""

import sys
import os
import time
import logging
import argparse
import binascii
from collections import defaultdict

# Add layer_game directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from common.game_protocol_parser import GameProtocolParser
    from scapy.all import sniff, IP, UDP, TCP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "rust_monitor"
GAME = "rust"
DEFAULT_GAME_PORT = 28015
DEFAULT_RCON_PORT = 28016

# RakNet Packet IDs
ID_OPEN_CONNECTION_REQUEST_1 = 0x05
ID_OPEN_CONNECTION_REQUEST_2 = 0x07

# -----------------------------------------------------------------------------
# Monitor Class
# -----------------------------------------------------------------------------
class RustMonitor(GameProtocolParser):
    def __init__(self, config_path=None, interface=None, dry_run=False):
        super().__init__(SCRIPT_NAME, GAME, config_path, dry_run)

        self.interface = interface

        # Counters
        self.handshake_counts = defaultdict(int)
        self.query_counts = defaultdict(int)
        self.rcon_attempts = defaultdict(int)

        self.start_window = time.time()
        self.window_size = 1.0

        # Load specific config sections
        self.hs_conf = self.config.get("handshake_flood", {})
        self.query_conf = self.config.get("query_flood", {})
        self.rcon_conf = self.config.get("rcon_protection", {})

    def packet_callback(self, packet):
        """Callback for captured packets."""
        if IP not in packet: return

        src_ip = packet[IP].src

        # UDP Traffic (Game + Query)
        if UDP in packet and Raw in packet:
            payload = packet[Raw].load
            if len(payload) == 0: return

            byte0 = payload[0]

            # 1. RakNet Handshake Check
            if byte0 in [ID_OPEN_CONNECTION_REQUEST_1, ID_OPEN_CONNECTION_REQUEST_2]:
                self.handshake_counts[src_ip] += 1

            # 2. A2S Query Check (Header: FF FF FF FF)
            elif payload.startswith(b'\xff\xff\xff\xff'):
                self.query_counts[src_ip] += 1

        # TCP Traffic (RCON)
        elif TCP in packet and packet[TCP].dport == self.rcon_conf.get("port", DEFAULT_RCON_PORT):
             # Simple heuristic: excessive small packets on RCON port could indicate brute force or fuzzing
             # Real RCON auth detection requires payload parsing which might be encrypted/complex
             # Here we track connection attempts (SYN)
             if packet[TCP].flags & 0x02: # SYN
                 self.rcon_attempts[src_ip] += 1

    def analyze_window(self):
        """Check accumulated metrics against thresholds."""
        now = time.time()
        duration = now - self.start_window
        if duration < 0.1: duration = 0.1

        ips_to_purge = []

        # 1. Handshake Analysis
        hs_limit = self.hs_conf.get("max_pps", 10)
        for ip, count in self.handshake_counts.items():
            pps = count / duration
            if pps > hs_limit:
                self.emit_event("raknet_handshake_flood", ip, "HIGH", {
                    "pps": round(pps, 2),
                    "threshold": hs_limit
                })
            ips_to_purge.append(ip)

        # 2. Query Analysis
        q_limit = self.query_conf.get("max_pps", 20)
        for ip, count in self.query_counts.items():
            pps = count / duration
            if pps > q_limit:
                 self.emit_event("a2s_query_flood", ip, "MEDIUM", {
                    "pps": round(pps, 2),
                    "threshold": q_limit
                })
            ips_to_purge.append(ip)

        # 3. RCON Analysis
        # RCON limits are usually lower (connections per second)
        rcon_limit = 5
        for ip, count in self.rcon_attempts.items():
            cps = count / duration
            if cps > rcon_limit:
                self.emit_event("rcon_brute_force_attempt", ip, "CRITICAL", {
                    "cps": round(cps, 2),
                    "threshold": rcon_limit
                })
            ips_to_purge.append(ip)

        # Cleanup
        for ip in set(ips_to_purge):
            if ip in self.handshake_counts: del self.handshake_counts[ip]
            if ip in self.query_counts: del self.query_counts[ip]
            if ip in self.rcon_attempts: del self.rcon_attempts[ip]

        self.start_window = now

    def run(self):
        """Main capture loop."""
        game_port = DEFAULT_GAME_PORT
        rcon_port = self.rcon_conf.get("port", DEFAULT_RCON_PORT)

        # BPF Filter: UDP game port OR TCP RCON port
        bpf_filter = f"(udp port {game_port}) or (tcp port {rcon_port})"

        logging.info(f"Starting Rust Monitor with filter: '{bpf_filter}'...")
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
    parser = argparse.ArgumentParser(description="Rust Game Protocol Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Network interface to sniff")
    parser.add_argument("--dry-run", action="store_true", help="Simulate events")

    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")

    monitor = RustMonitor(config_path, args.interface, args.dry_run)

    if os.geteuid() != 0:
        logging.warning("Not running as root. Sniffing might fail.")

    monitor.run()

if __name__ == "__main__":
    main()
