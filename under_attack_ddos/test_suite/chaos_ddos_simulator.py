#!/usr/bin/env python3
"""
Chaos DDoS Simulator
Part of 'under_attack_ddos' Defense System.

Responsibility: Generates synthetic events to test the Orchestrator and Correlation Engine without real network traffic.
"""

import sys
import os
import json
import time
import random
import argparse
import logging
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "chaos_ddos_simulator"
LAYER = "test_suite"
RESPONSIBILITY = "Inject synthetic threats"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class EventGenerator:
    def __init__(self, target_file):
        self.target_file = target_file

    def emit(self, event):
        """Appends event to the input file watched by Orchestrator."""
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        event["simulator"] = True

        try:
            with open(self.target_file, 'a') as f:
                f.write(json.dumps(event) + "\n")
            logging.info(f"Injected: {event['layer']} / {event['event']}")
        except Exception as e:
            logging.error(f"Injection failed: {e}")

    def generate_l3_flood(self, duration=10):
        logging.info(f"Starting L3 UDP Flood Simulation ({duration}s)...")
        end_time = time.time() + duration
        while time.time() < end_time:
            event = {
                "layer": "layer3",
                "event": "bandwidth_spike_detected",
                "severity": "CRITICAL",
                "source_entity": f"192.168.1.{random.randint(1, 254)}",
                "data": {"mbps": random.randint(800, 1200)}
            }
            self.emit(event)
            time.sleep(0.5)

    def generate_l4_syn_flood(self, duration=10):
        logging.info(f"Starting L4 SYN Flood Simulation ({duration}s)...")
        end_time = time.time() + duration
        while time.time() < end_time:
            event = {
                "layer": "layer4",
                "event": "syn_flood_detected",
                "severity": "HIGH",
                "source_entity": "203.0.113.5",
                "data": {"syn_rate_pps": random.randint(500, 2000)}
            }
            self.emit(event)
            time.sleep(0.2)

    def generate_l7_slowloris(self, duration=10):
        logging.info(f"Starting L7 Slowloris Simulation ({duration}s)...")
        end_time = time.time() + duration
        while time.time() < end_time:
            event = {
                "layer": "layer7",
                "event": "slow_loris_suspected",
                "severity": "MEDIUM",
                "source_entity": f"10.0.0.{random.randint(10, 50)}",
                "data": {"duration_sec": 120}
            }
            self.emit(event)
            time.sleep(1.0)

    def generate_multi_vector(self, duration=10):
        logging.info(f"Starting Multi-Vector Campaign ({duration}s)...")
        end_time = time.time() + duration
        while time.time() < end_time:
            if random.random() < 0.5:
                self.generate_l3_flood(duration=0.1)
            else:
                self.generate_l7_slowloris(duration=0.1)
            time.sleep(0.5)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)

    # Required Flags
    parser.add_argument("--target", default="events.pipe", help="File to write events to")

    # Scenarios
    subparsers = parser.add_subparsers(dest="scenario", required=True, help="Attack Scenario")

    subparsers.add_parser("l3_flood", help="Simulate Volumetric L3 Attack")
    subparsers.add_parser("l4_syn", help="Simulate TCP SYN Flood")
    subparsers.add_parser("l7_slow", help="Simulate Slowloris")
    subparsers.add_parser("multi_vector", help="Simulate Coordinated Attack")

    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")

    args = parser.parse_args()

    # Logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    generator = EventGenerator(args.target)

    if args.scenario == "l3_flood":
        generator.generate_l3_flood(args.duration)
    elif args.scenario == "l4_syn":
        generator.generate_l4_syn_flood(args.duration)
    elif args.scenario == "l7_slow":
        generator.generate_l7_slowloris(args.duration)
    elif args.scenario == "multi_vector":
        generator.generate_multi_vector(args.duration)

if __name__ == "__main__":
    main()
