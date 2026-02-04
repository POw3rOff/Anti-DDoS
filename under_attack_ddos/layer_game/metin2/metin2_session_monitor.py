#!/usr/bin/env python3
"""
Metin2 Session Abuse Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects post-handshake anomalies including packet spam,
idle abuse, and keep-alive floods.
"""

import sys
import os
import json
import time
import logging
import argparse
import yaml
from datetime import datetime, timezone
from collections import defaultdict

try:
    from scapy.all import sniff, IP, TCP
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "metin2_session_monitor"
LAYER = "game"
GAME = "metin2"
DEFAULT_GAME_PORT = 13000 # Default Metin2 Game Channel Port (Not Auth)

# -----------------------------------------------------------------------------
# Session Monitor Class
# -----------------------------------------------------------------------------
class Metin2SessionMonitor:
    def __init__(self, config_path=None, interface=None, port=DEFAULT_GAME_PORT, dry_run=False):
        self.config = self._load_config(config_path)
        self.interface = interface
        self.port = int(port)
        self.dry_run = dry_run

        # State: {src_ip: {pkt_count: int, last_ts: float, start_ts: float}}
        self.sessions = defaultdict(lambda: {"pkt_count": 0, "last_ts": time.time(), "start_ts": time.time()})

        self.start_window = time.time()
        self.window_size = 1.0

        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME} on port {self.port}. Dry-run: {dry_run}")

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def _load_config(self, path):
        if not path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, "config.yaml")
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def packet_callback(self, packet):
        """Callback for captured packets."""
        if IP in packet and TCP in packet:
            # Monitor traffic TO the game server port
            if packet[TCP].dport == self.port:
                src_ip = packet[IP].src
                now = time.time()

                sess = self.sessions[src_ip]
                sess["pkt_count"] += 1
                sess["last_ts"] = now

    def analyze_window(self):
        """Check accumulated metrics against thresholds."""
        now = time.time()
        duration = now - self.start_window
        if duration < 0.1: duration = 0.1

        max_pps = self.config.get("max_session_pps", 50)
        idle_limit = self.config.get("idle_timeout", 300)
        grace_period = self.config.get("grace_period", 2.0)

        ips_to_purge = []

        for ip, sess in self.sessions.items():
            # 1. Idle Check
            idle_time = now - sess["last_ts"]
            if idle_time > idle_limit:
                # Silent cleanup for idle sessions
                ips_to_purge.append(ip)
                continue

            # 2. PPS Check
            session_age = now - sess["start_ts"]
            if session_age > grace_period:
                pps = sess["pkt_count"] / duration
                if pps > max_pps:
                    self.emit_event(ip, "pps_exceeded", pps, "HIGH")

            # Reset counter for next window
            sess["pkt_count"] = 0

        # Cleanup
        for ip in ips_to_purge:
            del self.sessions[ip]

        self.start_window = now

    def emit_event(self, src_ip, metric, value, severity):
        """Emits a structured JSON event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "game": GAME,
            "event": "session_abuse",
            "src_ip": src_ip,
            "severity": severity,
            "data": {
                "metric": metric,
                "value": round(value, 2),
                "threshold": self.config.get("max_session_pps", 50),
                "status": "simulated" if self.dry_run else "active"
            }
        }
        print(json.dumps(event))
        sys.stdout.flush()
        logging.warning(f"ALERT: {metric} from {src_ip} ({value:.1f})")

    def run(self):
        """Main capture loop."""
        logging.info(f"Starting session monitor on port {self.port}...")
        try:
            while True:
                sniff(
                    filter=f"tcp dst port {self.port}",
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
    parser = argparse.ArgumentParser(description="Metin2 Session Abuse Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Network interface to sniff")
    parser.add_argument("--port", default=DEFAULT_GAME_PORT, type=int, help="Game server port")
    parser.add_argument("--dry-run", action="store_true", help="Simulate events")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    monitor = Metin2SessionMonitor(args.config, args.interface, args.port, args.dry_run)

    if os.geteuid() != 0:
        logging.warning("Not running as root. Sniffing might fail.")

    monitor.run()

if __name__ == "__main__":
    main()
