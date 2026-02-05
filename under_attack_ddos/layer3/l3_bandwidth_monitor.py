#!/usr/bin/env python3
"""
Layer 3 Bandwidth Monitor
Part of 'under_attack_ddos' Defense System.

Responsibility: Detects volumetric attacks by monitoring ingress/egress bandwidth
usage and packet-per-second (PPS) rates on network interfaces using /proc/net/dev.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
from datetime import datetime, timezone

# Third-party imports
try:
    import yaml
except ImportError as e:
    print(f"CRITICAL: Missing required dependencies: {e}", file=sys.stderr)
    print("Please install: pip install pyyaml", file=sys.stderr)
    sys.exit(4)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "l3_bandwidth_monitor"
LAYER = "layer3"
RESPONSIBILITY = "Monitor interface Bandwidth and PPS"
PROC_NET_DEV = "/proc/net/dev"

# Default configuration (Fail-safe)
DEFAULT_CONFIG = {
    "layer3": {
        "bandwidth_ingress_mbps": {"warning": 500, "critical": 850},
        "pps_ingress": {"warning": 50000, "critical": 100000}
    }
}

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ConfigLoader:
    @staticmethod
    def load(path):
        if not path or not os.path.exists(path):
            return DEFAULT_CONFIG
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return DEFAULT_CONFIG

class BandwidthMonitor:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.running = True
        self.interfaces = {} # {iface: {last_ts, last_bytes_rx, last_pkts_rx}}

        # Load Thresholds
        l3 = self.config.get("layer3", {})
        self.bw_warn = l3.get("bandwidth_ingress_mbps", {}).get("warning", 500)
        self.bw_crit = l3.get("bandwidth_ingress_mbps", {}).get("critical", 850)
        self.pps_warn = l3.get("pps_ingress", {}).get("warning", 50000)
        self.pps_crit = l3.get("pps_ingress", {}).get("critical", 100000)

        # Mode adjustment
        if self.args.mode == "under_attack":
            self.pps_warn *= 0.8
            self.bw_warn *= 0.8

        logging.info(f"Initialized {SCRIPT_NAME}. thresholds: {self.bw_warn}Mbps / {self.pps_warn}PPS")

    def _read_stats(self):
        """Parses /proc/net/dev"""
        stats = {}
        try:
            with open(PROC_NET_DEV, 'r') as f:
                lines = f.readlines()

            # Skip header lines (first 2)
            for line in lines[2:]:
                parts = line.split(':')
                if len(parts) < 2: continue

                iface = parts[0].strip()
                # Skip loopback
                if iface == "lo": continue

                fields = parts[1].split()
                # Fields: bytes_rx, packets_rx, errs, drop, fifo, frame, compressed, multicast, bytes_tx, ...
                bytes_rx = int(fields[0])
                pkts_rx = int(fields[1])
                bytes_tx = int(fields[8])
                pkts_tx = int(fields[9])

                stats[iface] = {
                    "rx_bytes": bytes_rx,
                    "rx_pkts": pkts_rx,
                    "tx_bytes": bytes_tx,
                    "tx_pkts": pkts_tx,
                    "ts": time.time()
                }
        except Exception as e:
            logging.error(f"Failed to read {PROC_NET_DEV}: {e}")
        return stats

    def analyze(self):
        current_stats = self._read_stats()

        for iface, curr in current_stats.items():
            if iface not in self.interfaces:
                self.interfaces[iface] = curr
                continue

            prev = self.interfaces[iface]
            delta_t = curr["ts"] - prev["ts"]
            if delta_t <= 0: continue

            # RX Stats
            delta_bytes_rx = curr["rx_bytes"] - prev["rx_bytes"]
            delta_pkts_rx = curr["rx_pkts"] - prev["rx_pkts"]

            mbps_rx = (delta_bytes_rx * 8) / (1024 * 1024) / delta_t
            pps_rx = delta_pkts_rx / delta_t

            self._check_thresholds(iface, mbps_rx, pps_rx)

            # Update state
            self.interfaces[iface] = curr

    def _check_thresholds(self, iface, mbps, pps):
        events = []
        now = datetime.now(timezone.utc).isoformat()

        # Check Bandwidth
        if mbps > self.bw_warn:
            sev = "CRITICAL" if mbps > self.bw_crit else "HIGH"
            events.append({
                "event": "bandwidth_spike_detected",
                "severity": sev,
                "data": {"mbps": round(mbps, 2), "threshold": self.bw_warn, "direction": "ingress"}
            })

        # Check PPS
        if pps > self.pps_warn:
            sev = "CRITICAL" if pps > self.pps_crit else "HIGH"
            events.append({
                "event": "pps_spike_detected",
                "severity": sev,
                "data": {"pps": int(pps), "threshold": self.pps_warn, "direction": "ingress"}
            })

        for e in events:
            full_event = {
                "timestamp": now,
                "layer": LAYER,
                "detector": SCRIPT_NAME,
                "source_entity": iface,
                **e
            }
            if self.args.dry_run:
                full_event["data"]["status"] = "simulated"
                logging.info(f"[DRY-RUN] {e['event']} on {iface}: {e['data']}")
            else:
                full_event["data"]["status"] = "active"

            if self.args.json:
                print(json.dumps(full_event))
            else:
                logging.warning(f"ALERT: {e['event']} on {iface} (Sev: {e['severity']})")

    def run(self):
        # Polling interval (1s is standard for rate monitoring)
        interval = 1.0
        logging.info(f"Starting monitor loop. Interval: {interval}s")

        try:
            while self.running:
                self.analyze()
                time.sleep(interval)
                if self.args.once:
                    self.running = False
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

    config = ConfigLoader.load(args.config)
    monitor = BandwidthMonitor(args, config)

    signal.signal(signal.SIGINT, monitor.stop)
    signal.signal(signal.SIGTERM, monitor.stop)

    monitor.run()

if __name__ == "__main__":
    main()
