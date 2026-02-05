#!/usr/bin/env python3
"""
Layer 4 UDP Flood Monitor
Part of 'under_attack_ddos' Defense System.

Responsibility: Detects volumetric UDP floods and amplification reflection attacks
by monitoring system-wide UDP statistics and queue sizes.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    pass # Config might be optional or handle gracefully

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "l4_udp_flood_monitor"
LAYER = "layer4"
RESPONSIBILITY = "Detect UDP floods via system counters"
PROC_NET_SNMP = "/proc/net/snmp"
PROC_NET_UDP = "/proc/net/udp"

DEFAULT_CONFIG = {
    "layer4": {
        "udp_flood": {
            "pps_max": 20000,
            "drop_rate_max": 100
        }
    }
}

# -----------------------------------------------------------------------------
# Monitor Class
# -----------------------------------------------------------------------------
class UdpFloodMonitor:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.running = True

        # Load Thresholds
        l4 = self.config.get("layer4", {}).get("udp_flood", {})
        self.pps_threshold = l4.get("pps_max", 20000)
        self.drop_threshold = l4.get("drop_rate_max", 100)

        if self.args.mode == "under_attack":
            self.pps_threshold *= 0.8

        self.last_snmp = self._read_snmp()
        self.last_ts = time.time()

        logging.info(f"Initialized {SCRIPT_NAME}. Threshold: {self.pps_threshold} PPS")

    def _read_snmp(self):
        """Parses /proc/net/snmp for UDP stats"""
        stats = {}
        try:
            with open(PROC_NET_SNMP, 'r') as f:
                lines = f.readlines()

            # Find Udp: lines
            # Example:
            # Udp: InDatagrams NoPorts InErrors OutDatagrams RcvbufErrors SndbufErrors InCsumErrors IgnoredMulti
            # Udp: 1234 5 0 1234 0 0 0 0

            header = None
            for line in lines:
                parts = line.split()
                if not parts: continue
                if parts[0] == "Udp:" and not header:
                    header = parts
                elif parts[0] == "Udp:" and header:
                    # Values
                    for i, field in enumerate(header):
                        if i == 0: continue # Skip "Udp:"
                        if i < len(parts):
                            stats[field] = int(parts[i])
                    break
        except Exception as e:
            logging.error(f"Failed to read SNMP: {e}")
        return stats

    def _read_udp_queues(self):
        """Parses /proc/net/udp for queue sizes (checking for saturation)"""
        # This is more expensive (one line per socket), so use carefully.
        # We might just sample average queue size.
        # For this version, we will focus on SNMP stats which are global.
        pass

    def analyze(self):
        curr_snmp = self._read_snmp()
        curr_ts = time.time()

        if not self.last_snmp or not curr_snmp:
            self.last_snmp = curr_snmp
            self.last_ts = curr_ts
            return

        delta_t = curr_ts - self.last_ts
        if delta_t <= 0: return

        # Calculate Rates
        in_datagrams = curr_snmp.get("InDatagrams", 0) - self.last_snmp.get("InDatagrams", 0)
        in_errors = curr_snmp.get("InErrors", 0) - self.last_snmp.get("InErrors", 0)
        rcv_buf_errors = curr_snmp.get("RcvbufErrors", 0) - self.last_snmp.get("RcvbufErrors", 0)

        pps = in_datagrams / delta_t
        drop_rate = (in_errors + rcv_buf_errors) / delta_t

        events = []

        # Check PPS
        if pps > self.pps_threshold:
            events.append({
                "event": "udp_flood_detected",
                "severity": "HIGH",
                "data": {"udp_pps": int(pps), "threshold": self.pps_threshold}
            })

        # Check Drop Rate (Buffer Overflow)
        if drop_rate > self.drop_threshold:
             events.append({
                "event": "udp_buffer_overflow",
                "severity": "MEDIUM",
                "data": {"drop_rate": int(drop_rate), "threshold": self.drop_threshold}
            })

        self._emit(events)

        self.last_snmp = curr_snmp
        self.last_ts = curr_ts

    def _emit(self, events):
        now = datetime.now(timezone.utc).isoformat()
        for e in events:
            full_event = {
                "timestamp": now,
                "layer": LAYER,
                "detector": SCRIPT_NAME,
                "source_entity": "GLOBAL",
                **e
            }
            if self.args.dry_run:
                full_event["data"]["status"] = "simulated"
                logging.info(f"[DRY-RUN] {e['event']} (PPS: {e['data'].get('udp_pps')})")
            else:
                full_event["data"]["status"] = "active"

            if self.args.json:
                print(json.dumps(full_event))
            else:
                logging.warning(f"ALERT: {e['event']}")

    def run(self):
        interval = 1.0
        logging.info(f"Starting UDP monitor. Interval: {interval}s")
        try:
            while self.running:
                self.analyze()
                time.sleep(interval)
                if self.args.once: self.running = False
        except KeyboardInterrupt:
            self.stop()

    def stop(self, signum=None, frame=None):
        logging.info("Stopping...")
        self.running = False

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)
    parser.add_argument("--config", help="Path to YAML configuration")
    parser.add_argument("--mode", required=True, choices=["normal", "monitor", "under_attack"], help="Execution mode")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions")
    parser.add_argument("--once", action="store_true", help="Run single pass and exit")
    parser.add_argument("--json", action="store_true", help="Output JSON events to STDOUT")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        stream=sys.stderr
    )

    # Load Config
    config = DEFAULT_CONFIG
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f) or DEFAULT_CONFIG
        except Exception as e:
            logging.error(f"Config load error: {e}")

    monitor = UdpFloodMonitor(args, config)
    signal.signal(signal.SIGINT, monitor.stop)
    signal.signal(signal.SIGTERM, monitor.stop)

    monitor.run()

if __name__ == "__main__":
    main()
