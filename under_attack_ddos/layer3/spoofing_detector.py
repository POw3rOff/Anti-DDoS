#!/usr/bin/env python3
"""
Spoofing Detector (Layer 3)
Part of 'under_attack_ddos' Defense System.

Responsibility: Detect potential IP spoofing by analyzing TTL consistency
and Bogon source addresses.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import threading
from collections import defaultdict
from datetime import datetime, timezone

# Third-party imports
try:
    from scapy.all import sniff, IP
    import yaml
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(4)

SCRIPT_NAME = "spoofing_detector"
LAYER = "layer3"

# Default config if file missing
DEFAULT_CONFIG = {
    "spoofing_detection": {
        "ttl_variance_threshold": 5,
        "bogon_alert_threshold": 1
    },
    "security": {
        "auth_token": "default_insecure"
    }
}

# Bogon ranges (simplified list of private/reserved ranges)
BOGON_RANGES = [
    ("10.0.0.0", "10.255.255.255"),
    ("172.16.0.0", "172.31.255.255"),
    ("192.168.0.0", "192.168.255.255"),
    ("127.0.0.0", "127.255.255.255"),
    ("0.0.0.0", "0.255.255.255"),
    ("100.64.0.0", "100.127.255.255"), # CGNAT - strictly speaking not bogon on WAN but usually valid, keeping for now
    ("169.254.0.0", "169.254.255.255"),
    ("224.0.0.0", "239.255.255.255"), # Multicast
    ("240.0.0.0", "255.255.255.255")  # Reserved
]

def ip_to_int(ip):
    parts = list(map(int, ip.split('.')))
    return (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]

PARSED_BOGONS = [(ip_to_int(start), ip_to_int(end)) for start, end in BOGON_RANGES]

class ConfigLoader:
    @staticmethod
    def load(paths):
        config = DEFAULT_CONFIG.copy()
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = yaml.safe_load(f)
                        if data:
                            # Merge logic (simplified)
                            if "spoofing_detection" in data:
                                config["spoofing_detection"].update(data["spoofing_detection"])
                            if "security" in data:
                                config["security"].update(data["security"])
                except Exception as e:
                    logging.error(f"Config load error {path}: {e}")
        return config

class SpoofAnalyzer:
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run
        self.ttl_tracker = defaultdict(list)
        self.lock = threading.Lock()
        self.running = True

        self.variance_threshold = config["spoofing_detection"].get("ttl_variance_threshold", 5)
        self.auth_token = config["security"].get("auth_token", "")

    def is_bogon(self, ip_str):
        try:
            ip_int = ip_to_int(ip_str)
            for start, end in PARSED_BOGONS:
                if start <= ip_int <= end:
                    return True
        except:
            pass
        return False

    def process_packet(self, pkt):
        if not self.running: return

        if IP in pkt:
            src_ip = pkt[IP].src
            ttl = pkt[IP].ttl

            # Check Bogon
            if self.is_bogon(src_ip):
                self._emit_event("bogon_ip_detected", src_ip, {"ttl": ttl}, "MEDIUM")
                return

            # Check TTL Variance
            with self.lock:
                self.ttl_tracker[src_ip].append(ttl)
                if len(self.ttl_tracker[src_ip]) > 10:
                    self.ttl_tracker[src_ip].pop(0)

                ttls = self.ttl_tracker[src_ip]
                if len(ttls) >= 5:
                    variance = max(ttls) - min(ttls)
                    if variance > self.variance_threshold:
                        # Heuristic: Valid paths rarely change TTL by > 5 hops rapidly
                        self._emit_event("spoofing_ttl_anomaly", src_ip,
                                         {"ttl_variance": variance, "samples": ttls},
                                         "HIGH")
                        # Clear to avoid flooding events
                        self.ttl_tracker[src_ip] = []

    def _emit_event(self, event_type, src_ip, data, severity):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "event": event_type,
            "source_entity": src_ip,
            "severity": severity,
            "data": data,
            "auth_token": self.auth_token
        }

        json_line = json.dumps(event)
        if self.dry_run:
            logging.info(f"[DRY-RUN] Would emit: {json_line}")
        else:
            print(json_line)
            sys.stdout.flush()

    def start_sniffing(self, interface):
        logging.info(f"Starting sniffing on {interface}...")
        try:
            sniff(iface=interface, prn=self.process_packet, store=0)
        except Exception as e:
            logging.error(f"Sniffing failed: {e}")

    def stop(self, signum=None, frame=None):
        self.running = False
        logging.info("Stopping...")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_NAME)
    parser.add_argument("--interface", default="eth0", help="Network interface to monitor")
    parser.add_argument("--config", default="config/hardening.yaml", help="Path to hardening config")
    parser.add_argument("--dry-run", action="store_true", help="Log only, no output")

    args = parser.parse_args()

    # Logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    if os.geteuid() != 0:
        logging.error("Root privileges required for sniffing.")
        sys.exit(1)

    # Load Config (Layered: default -> hardening.yaml)
    config = ConfigLoader.load(["config/thresholds.yaml", args.config])

    analyzer = SpoofAnalyzer(config, args.dry_run)

    signal.signal(signal.SIGINT, analyzer.stop)
    signal.signal(signal.SIGTERM, analyzer.stop)

    analyzer.start_sniffing(args.interface)

if __name__ == "__main__":
    main()
