#!/usr/bin/env python3
"""
Universal Game Detector
Part of 'under_attack_ddos' Defense System.

Responsibility: Detect anomalies in game traffic based on YAML definitions.
Supports multiple games (Metin2, Rust, FiveM, CS:GO) via a unified inspection engine.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import threading
import re
from datetime import datetime, timezone
from collections import defaultdict

# Third-party imports
try:
    from scapy.all import sniff, IP, TCP, UDP, Raw
    import yaml
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(4)

SCRIPT_NAME = "universal_game_detector"
LAYER = "layer_game"

class ConfigLoader:
    @staticmethod
    def load(path):
        if not os.path.exists(path):
            logging.error(f"Config not found: {path}")
            return {}
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"Config parse error: {e}")
            return {}

class ProtocolSpec:
    def __init__(self, game_name, proto_def):
        self.game = game_name
        self.name = proto_def.get("name")
        self.transport = proto_def.get("transport").upper()
        self.checks = set(proto_def.get("checks", []))
        self.regex = re.compile(proto_def["regex"].encode()) if "regex" in proto_def else None

        # Parse Ports "11000-11005" or "27015"
        pr = str(proto_def.get("port_range", "0"))
        if '-' in pr:
            s, e = map(int, pr.split('-'))
            self.ports = range(s, e + 1)
        else:
            self.ports = [int(pr)]

class TrafficAnalyzer:
    def __init__(self, specs, config, dry_run=False):
        self.specs = specs # List of ProtocolSpec
        self.config = config
        self.dry_run = dry_run
        self.running = True

        # Port map for fast lookup: { (proto, port) : [ProtocolSpec...] }
        self.port_map = defaultdict(list)
        for spec in specs:
            for p in spec.ports:
                self.port_map[(spec.transport, p)].append(spec)

        # Counters
        self.counters = defaultdict(int) # (src_ip, spec_name) -> count
        self.lock = threading.Lock()

        # Hardening
        self.auth_token = config.get("security", {}).get("auth_token", "default_insecure")

    def process_packet(self, pkt):
        if not self.running: return
        if IP not in pkt: return

        proto = "TCP" if TCP in pkt else "UDP" if UDP in pkt else None
        if not proto: return

        dst_port = pkt[proto].dport
        specs = self.port_map.get((proto, dst_port))

        if not specs: return

        src_ip = pkt[IP].src
        payload = bytes(pkt[Raw].load) if Raw in pkt else b""

        for spec in specs:
            self._analyze(spec, src_ip, payload)

    def _analyze(self, spec, src_ip, payload):
        # 1. Regex/Payload Check
        if spec.regex and spec.regex.match(payload):
            # Known attack signature match (e.g., A2S_INFO flood pattern)
            self._emit_event(spec, "signature_match", src_ip, "HIGH", {"pattern": spec.name})
            return

        # 2. Rate Check (Simplified for prototype)
        # In a real system, we'd use sliding windows or leaky buckets here.
        # This simple counter resets every second via _reset_loop
        key = (src_ip, spec.name)
        with self.lock:
            self.counters[key] += 1
            count = self.counters[key]

        # Thresholds (hardcoded for prototype, should come from thresholds.yaml)
        if count == 50: # 50 PPS per source per protocol
             self._emit_event(spec, "rate_anomaly", src_ip, "MEDIUM", {"pps": count})

    def _emit_event(self, spec, risk_type, src, severity, data):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "event": f"{spec.game}_{risk_type}",
            "source_entity": src,
            "severity": severity,
            "data": {**data, "protocol": spec.name, "game": spec.game},
            "auth_token": self.auth_token
        }
        json_line = json.dumps(event)
        if self.dry_run:
            logging.info(f"[DRY-RUN] {json_line}")
        else:
            print(json_line)
            sys.stdout.flush()

    def reset_loop(self):
        while self.running:
            time.sleep(1.0)
            with self.lock:
                self.counters.clear()

    def start_sniffing(self, interface):
        # Build filter
        # "tcp portrange 11000-11005 or udp port 27015"
        # Scapy filter logic omitted for brevity, sniffing all and filtering in python for prototype stability
        logging.info(f"Sniffing on {interface} for {len(self.specs)} game protocols...")
        try:
            sniff(iface=interface, prn=self.process_packet, store=0)
        except Exception as e:
            logging.error(f"Sniffing error: {e}")

    def stop(self, *args):
        self.running = False
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_NAME)
    parser.add_argument("--config", required=True, help="Path to games.yaml")
    parser.add_argument("--hardening", default="config/hardening.yaml", help="Path to hardening.yaml")
    parser.add_argument("--interface", default="eth0", help="Interface")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    if os.geteuid() != 0:
        logging.error("Root required.")
        sys.exit(1)

    # Load Configs
    games_conf = ConfigLoader.load(args.config)
    hard_conf = ConfigLoader.load(args.hardening)

    # Parse Specs
    specs = []
    for game, data in games_conf.get("games", {}).items():
        for p in data.get("protocols", []):
            specs.append(ProtocolSpec(game, p))

    analyzer = TrafficAnalyzer(specs, hard_conf, args.dry_run)

    # Reset thread
    t = threading.Thread(target=analyzer.reset_loop, daemon=True)
    t.start()

    signal.signal(signal.SIGINT, analyzer.stop)
    signal.signal(signal.SIGTERM, analyzer.stop)

    analyzer.start_sniffing(args.interface)

if __name__ == "__main__":
    main()
