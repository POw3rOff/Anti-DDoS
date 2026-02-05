#!/usr/bin/env python3
"""
Attack Simulation Framework
Part of Test Suite

Responsibility: Controlled execution of synthetic attacks and PCAP replays
to validate the Anti-DDoS pipeline without generating real-world damage.
"""

import sys
import os
import json
import time
import argparse
import logging
import yaml
import random
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
SCRIPT_NAME = "attack_framework"
OUTPUT_DIR = "runtime/simulations/"

class AttackSimulator:
    def __init__(self, target_file, pcap_file=None):
        self.target_file = target_file
        self.pcap_file = pcap_file
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    def run_scenario(self, config_path):
        """Runs a synthetic scenario defined in YAML."""
        if not os.path.exists(config_path):
            logging.error(f"Scenario not found: {config_path}")
            return

        with open(config_path, 'r') as f:
            scenario = yaml.safe_load(f)

        logging.info(f"Starting Scenario: {scenario.get('name', 'Unknown')}")

        for event_def in scenario.get("events", []):
            count = event_def.get("count", 1)
            interval = event_def.get("interval", 1.0)

            for _ in range(count):
                event = self._build_event(event_def)
                self._emit(event)
                time.sleep(interval)

    def replay_pcap(self):
        """
        Simulates events based on a PCAP file.
        Does NOT replay packets on the wire, but generates EVENTS as if detectors saw them.
        """
        if not self.pcap_file:
            logging.error("No PCAP file provided")
            return

        logging.info(f"Replaying PCAP metadata from {self.pcap_file} (Simulation)")
        try:
            from scapy.all import rdpcap, IP, TCP, UDP
            packets = rdpcap(self.pcap_file)

            # Simple heuristic: Aggregate by second and emit flood events if high
            counts = {}
            start_ts = packets[0].time

            for pkt in packets:
                if IP not in pkt: continue

                ts_bucket = int(pkt.time)
                src = pkt[IP].src

                if ts_bucket not in counts: counts[ts_bucket] = 0
                counts[ts_bucket] += 1

                # Emit every 100 packets as a burst event
                if counts[ts_bucket] % 100 == 0:
                    event = {
                        "layer": "layer3",
                        "event": "bandwidth_spike_detected",
                        "src_ip": src,
                        "data": {"pps": counts[ts_bucket]}
                    }
                    self._emit(event)
                    time.sleep(0.01) # fast replay

        except ImportError:
            logging.error("Scapy not installed. Cannot replay PCAP.")
        except Exception as e:
            logging.error(f"Replay failed: {e}")

    def _build_event(self, definition):
        """Constructs a standard JSON event from YAML definition."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": f"layer{definition.get('layer', 3)}",
            "event": definition.get("type", "unknown_attack"),
            "source_entity": f"192.168.1.{random.randint(50, 150)}",
            "severity": definition.get("data", {}).get("severity", "MEDIUM"),
            "data": definition.get("data", {}),
            "simulator": True
        }

    def _emit(self, event):
        """Writes event to the target pipe/file."""
        try:
            # Ensure dir exists
            os.makedirs(os.path.dirname(self.target_file), exist_ok=True)

            with open(self.target_file, 'a') as f:
                f.write(json.dumps(event) + "\n")
            print(json.dumps(event)) # Also to stdout
        except Exception as e:
            logging.error(f"Emit failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Red Team Attack Simulator")
    parser.add_argument("--scenario", help="Path to YAML scenario file")
    parser.add_argument("--pcap", help="Path to PCAP file for replay")
    parser.add_argument("--target", default="runtime/simulations/live_events.json", help="Output file")
    parser.add_argument("--simulate", action="store_true", required=True, help="Safety flag")

    args = parser.parse_args()

    sim = AttackSimulator(args.target, args.pcap)

    if args.scenario:
        sim.run_scenario(args.scenario)
    elif args.pcap:
        sim.replay_pcap()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
