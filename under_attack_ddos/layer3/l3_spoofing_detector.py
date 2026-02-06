#!/usr/bin/env python3
"""
Layer 3 Spoofing Detector
Part of 'under_attack_ddos' Defense System.

Responsibility: Detects IP spoofing (Bogons, Martians) and randomized source IP floods.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import math
from collections import defaultdict
from datetime import datetime, timezone
import ipaddress

# Third-party imports
try:
    import yaml
    from scapy.all import sniff, IP
except ImportError as e:
    print(f"CRITICAL: Missing required dependencies: {e}", file=sys.stderr)
    print("Please install: pip install pyyaml scapy", file=sys.stderr)
    sys.exit(4)

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "l3_spoofing_detector"
LAYER = "layer3"
RESPONSIBILITY = "Detect IP spoofing and Bogons"

# Default configuration
DEFAULT_CONFIG = {
    "layer3": {
        "spoofing": {
            "entropy_threshold": 0.9,
            "sample_size": 1000,
            "martian_check": True
        }
    }
}

# RFC 1918 and other reserved ranges (Bogons)
BOGON_RANGES = [
    "0.0.0.0/8",          # Current network
    "10.0.0.0/8",         # Private network
    "100.64.0.0/10",      # Carrier-grade NAT
    "127.0.0.0/8",        # Loopback
    "169.254.0.0/16",     # Link-local
    "172.16.0.0/12",      # Private network
    "192.0.0.0/24",       # IETF Protocol Assignments
    "192.0.2.0/24",       # TEST-NET-1
    "192.88.99.0/24",     # 6to4 Relay Anycast
    "192.168.0.0/16",     # Private network
    "198.18.0.0/15",      # Network benchmark
    "198.51.100.0/24",    # TEST-NET-2
    "203.0.113.0/24",     # TEST-NET-3
    "224.0.0.0/4",        # Multicast
    "240.0.0.0/4",        # Reserved (Class E)
    "255.255.255.255/32"  # Broadcast
]

# Pre-compile networks for faster checking
BOGON_NETWORKS = [ipaddress.ip_network(cidr) for cidr in BOGON_RANGES]

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ConfigLoader:
    @staticmethod
    def load(path):
        if not os.path.exists(path):
            logging.warning(f"Config file not found: {path}. Using defaults.")
            return DEFAULT_CONFIG

        try:
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            # Minimal merge logic
            return user_config
        except Exception as e:
            logging.error(f"Failed to parse config: {e}")
            sys.exit(2)

class SpoofingDetector:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.running = True
        self.ip_buffer = []
        self.start_time = time.time()

        # Load settings
        self.spoof_conf = self.config.get("layer3", {}).get("spoofing", {})
        self.sample_size = self.spoof_conf.get("sample_size", 1000)
        self.entropy_threshold = self.spoof_conf.get("entropy_threshold", 0.9)

        logging.info(f"Initialized {SCRIPT_NAME}. Mode: {args.mode}. Sample Size: {self.sample_size}")

    def is_bogon(self, ip_str):
        try:
            ip = ipaddress.ip_address(ip_str)
            # Check global bogon list
            for net in BOGON_NETWORKS:
                if ip in net:
                    return True
            return False
        except ValueError:
            return False # Invalid IP is not necessarily a bogon in this context, but filtered elsewhere

    def calculate_entropy(self, ips):
        if not ips:
            return 0.0

        total = len(ips)
        counts = defaultdict(int)
        for ip in ips:
            counts[ip] += 1

        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)

        # Normalize entropy (0 to 1)
        # Max entropy is log2(total) if all IPs are unique
        if total <= 1:
            return 0.0
        max_entropy = math.log2(total)
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def packet_callback(self, packet):
        """Called for each captured packet."""
        if IP in packet:
            src_ip = packet[IP].src

            # 1. Immediate Bogon Check
            if self.spoof_conf.get("martian_check", True) and self.is_bogon(src_ip):
                self._emit_alert("spoofed_ip_detected", {
                    "source_ip": src_ip,
                    "reason": "bogon_check_failed",
                    "status": "bogon"
                }, severity="CRITICAL")
                return

            # 2. Buffer for Entropy Check
            self.ip_buffer.append(src_ip)

            # 3. Analyze Batch if Full
            if len(self.ip_buffer) >= self.sample_size:
                self.analyze_batch()

    def analyze_batch(self):
        """Analyze accumulated IPs for randomness (spoofing)."""
        unique_ips = len(set(self.ip_buffer))
        entropy = self.calculate_entropy(self.ip_buffer)

        # High entropy means highly randomized IPs -> likely spoofing flood
        # Low entropy means few IPs -> likely simple flood (handled by other tools)

        if entropy > self.entropy_threshold:
             self._emit_alert("random_spoofing_detected", {
                "sample_size": len(self.ip_buffer),
                "unique_ips": unique_ips,
                "entropy": round(entropy, 4),
                "threshold": self.entropy_threshold
            }, severity="HIGH")

        # Clear buffer
        self.ip_buffer = []

    def _emit_alert(self, event_type, data, severity="MEDIUM"):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "event": event_type,
            "severity": severity,
            "source_entity": data.get("source_ip", "batch"),
            "data": data
        }

        if self.args.dry_run:
            event["status"] = "simulated"
            logging.info(f"[DRY-RUN] Alert: {event_type} - {data}")
        else:
            event["status"] = "active"

        if self.args.json:
            print(json.dumps(event))
            sys.stdout.flush()
        else:
            logging.warning(f"ALERT: {event_type} (Sev: {severity})")

    def run(self):
        """Main Loop"""
        logging.info(f"Starting capture loop. Buffer limit: {self.sample_size}")

        try:
            # We use sniff with a count limit or simply loop indefinitely if we handle buffering
            # Here we let scapy run and callback handle logic
            sniff(prn=self.packet_callback, store=0)

            # Note: sniff blocks unless stopped or count reached.
            # If args.once is set, we might want to limit count or time, but let's rely on signal for now
            # or use timeout in loop if we want periodic checks (not needed for this logic)

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logging.error(f"Runtime error: {e}", exc_info=True)
            sys.exit(1)

    def stop(self, signum=None, frame=None):
        logging.info("Stopping...")
        self.running = False
        sys.exit(0)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)

    # Required Flags
    parser.add_argument("--config", default="config/l3_spoofing.yaml", help="Path to YAML configuration")
    parser.add_argument("--mode", default="monitor", choices=["normal", "monitor", "under_attack"], help="Execution mode")

    # Optional Flags
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions")
    parser.add_argument("--daemon", action="store_true", help="Run as background service")
    parser.add_argument("--once", action="store_true", help="Run single pass and exit")
    parser.add_argument("--json", action="store_true", help="Output JSON events to STDOUT")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")

    args = parser.parse_args()

    # Validation
    if args.daemon and args.once:
        print("Error: --daemon and --once are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    # Logging Setup
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        stream=sys.stderr
    )

    # Root Check
    if os.geteuid() != 0 and not args.dry_run:
        logging.warning("Not running as root. Sniffing might fail.")

    # Initialization
    logging.info(f"Starting {SCRIPT_NAME} v1.0.0")
    config = ConfigLoader.load(args.config)

    detector = SpoofingDetector(args, config)

    # Signal Handling
    signal.signal(signal.SIGINT, detector.stop)
    signal.signal(signal.SIGTERM, detector.stop)

    # Execution
    detector.run()

if __name__ == "__main__":
    main()
