#!/usr/bin/env python3
"""
Metin2 Session Abuse Monitor
Part of Layer G (Game Protocol Defense)

Responsibility: Detects post-handshake anomalies including packet spam (opcode floods),
idle abuse, keep-alive floods, rapid channel switching, and payload variance (bot detection).
"""

import sys
import os
import json
import time
import logging
import argparse
import yaml
import math
from datetime import datetime, timezone
from collections import defaultdict

try:
    from scapy.all import sniff, IP, TCP, Raw
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "metin2_session_monitor"
LAYER = "game"
GAME = "metin2"
DEFAULT_GAME_PORT = 13000

# -----------------------------------------------------------------------------
# Session Monitor Class
# -----------------------------------------------------------------------------
class Metin2SessionMonitor:
    def __init__(self, config_path=None, interface=None, port_range=None, dry_run=False):
        self.config = self._load_config(config_path)
        self.interface = interface
        self.port_range = port_range or f"{DEFAULT_GAME_PORT}"
        self.dry_run = dry_run

        # State tracking
        self.sessions = defaultdict(lambda: {"pkt_count": 0, "last_ts": time.time(), "start_ts": time.time()})
        self.opcode_counts = defaultdict(lambda: defaultdict(int))
        self.port_history = defaultdict(set)

        # Payload size tracking for variance calculation
        # {src_ip: [len1, len2, ...]}
        # We only keep a small sample to save memory
        self.payload_samples = defaultdict(list)
        self.max_samples = 50

        self.start_window = time.time()
        self.window_size = 1.0

        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME} monitoring ports {self.port_range}. Dry-run: {dry_run}")

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
            src_ip = packet[IP].src
            dst_port = packet[TCP].dport
            now = time.time()

            # Session tracking
            sess = self.sessions[src_ip]
            sess["pkt_count"] += 1
            sess["last_ts"] = now

            # Channel/Port tracking
            self.port_history[src_ip].add(dst_port)

            # Payload Inspection
            if Raw in packet:
                payload = packet[Raw].load
                p_len = len(payload)
                if p_len > 0:
                    # Opcode Analysis
                    opcode = payload[0]
                    self.opcode_counts[src_ip][opcode] += 1

                    # Variance Sampling
                    if len(self.payload_samples[src_ip]) < self.max_samples:
                        self.payload_samples[src_ip].append(p_len)

    def calculate_variance(self, data):
        """Calculates standard deviation of a list."""
        if len(data) < 2: return 0.0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return math.sqrt(variance)

    def analyze_window(self):
        """Check accumulated metrics against thresholds."""
        now = time.time()
        duration = now - self.start_window
        if duration < 0.1: duration = 0.1

        # Load Thresholds
        max_pps = self.config.get("max_session_pps", 50)
        max_channel_switches = self.config.get("max_channel_switches", 5)
        idle_limit = self.config.get("idle_timeout", 300)
        grace_period = self.config.get("grace_period", 2.0)
        min_variance = self.config.get("min_payload_variance", 0.0) # 0 means disabled/strict

        # Opcode Rules
        fallback_opcode_pps = self.config.get("max_opcode_pps", 20)
        opcode_rules = self.config.get("opcode_rules", {})
        # Convert keys in config (int/str) to int if needed
        # YAML keys like 0x12 might be loaded as ints automatically.

        ips_to_purge = []

        for ip, sess in self.sessions.items():
            # 1. Idle Check
            idle_time = now - sess["last_ts"]
            if idle_time > idle_limit:
                ips_to_purge.append(ip)
                continue

            # 2. PPS Check
            session_age = now - sess["start_ts"]
            if session_age > grace_period:
                pps = sess["pkt_count"] / duration
                if pps > max_pps:
                    self.emit_event(ip, "pps_exceeded", pps, max_pps, "HIGH")

                # 3. Opcode Flood Check (Granular)
                if ip in self.opcode_counts:
                    for op, count in self.opcode_counts[ip].items():
                        op_pps = count / duration

                        # Determine threshold
                        # Try exact match or string representation
                        limit = opcode_rules.get(op)
                        if limit is None:
                            limit = opcode_rules.get(f"0x{op:02x}")
                        if limit is None:
                            limit = fallback_opcode_pps

                        if op_pps > limit:
                            self.emit_event(ip, "opcode_flood", op_pps, limit, "HIGH", {"opcode": f"0x{op:02x}"})

                # 4. Channel Switch Abuse
                if ip in self.port_history:
                    unique_ports = len(self.port_history[ip])
                    if unique_ports > max_channel_switches:
                         self.emit_event(ip, "channel_switch_abuse", unique_ports, max_channel_switches, "MEDIUM")

                # 5. Payload Variance (Bot Detection)
                # Only check if enough samples and PPS is significant (avoid FPs on idle clients)
                if len(self.payload_samples[ip]) > 10 and pps > 5:
                    std_dev = self.calculate_variance(self.payload_samples[ip])
                    # If variance is too low (e.g. 0 or close to 0), it's a fixed-packet bot
                    if std_dev < min_variance:
                        self.emit_event(ip, "bot_fixed_pattern", std_dev, min_variance, "MEDIUM")

            # Reset counters
            sess["pkt_count"] = 0

        # Reset window-scoped aggregators
        self.opcode_counts.clear()
        self.port_history.clear()
        self.payload_samples.clear()

        # Cleanup
        for ip in ips_to_purge:
            del self.sessions[ip]
            if ip in self.payload_samples: del self.payload_samples[ip]

        self.start_window = now

    def emit_event(self, src_ip, event_type, value, threshold, severity, extra_data=None):
        """Emits a structured JSON event."""
        data = {
            "value": round(value, 2),
            "threshold": threshold,
            "status": "simulated" if self.dry_run else "active"
        }
        if extra_data:
            data.update(extra_data)

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "game": GAME,
            "event": event_type,
            "src_ip": src_ip,
            "severity": severity,
            "data": data
        }
        print(json.dumps(event))
        sys.stdout.flush()
        logging.warning(f"ALERT: {event_type} from {src_ip} (Val: {value:.1f})")

    def run(self):
        """Main capture loop."""
        if "-" in self.port_range:
            bpf_filter = f"tcp dst portrange {self.port_range}"
        else:
            bpf_filter = f"tcp dst port {self.port_range}"

        logging.info(f"Starting session monitor with filter: '{bpf_filter}'...")
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
    parser = argparse.ArgumentParser(description="Metin2 Session Abuse Monitor")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--interface", help="Network interface to sniff")
    parser.add_argument("--port-range", default=str(DEFAULT_GAME_PORT), help="Port or Port Range (e.g., 13000-13099)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate events")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    monitor = Metin2SessionMonitor(args.config, args.interface, args.port_range, args.dry_run)

    if os.geteuid() != 0:
        logging.warning("Not running as root. Sniffing might fail.")

    monitor.run()

if __name__ == "__main__":
    main()
