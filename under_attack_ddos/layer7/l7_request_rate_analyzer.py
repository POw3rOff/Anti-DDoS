#!/usr/bin/env python3
"""
Layer 7 Request Rate Analyzer
Part of Anti-DDoS/under_attack_ddos/layer7/

Responsibility: Detects Application Layer (HTTP/API) rate abuse by analyzing
access logs (or log streams). Identifies "low-and-slow" attacks and burst patterns.
"""

import sys
import os
import json
import time
import argparse
import logging
import re
import yaml
from collections import defaultdict, deque
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Constants & Config
# -----------------------------------------------------------------------------
SCRIPT_NAME = "l7_request_rate_analyzer"
LAYER = "layer7"
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "l7_thresholds.yaml")

# Regex for Common Log Format (CLF) / Combined
# Example: 127.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
CLF_REGEX = re.compile(r'^(\S+) \S+ \S+ \[.*?\] "(.*?) (.*?) .*?" (\d+) (\S+)')

# -----------------------------------------------------------------------------
# Analyzer Class
# -----------------------------------------------------------------------------
class L7RequestRateAnalyzer:
    def __init__(self, config_path=None, input_format="json", dry_run=False):
        self.config = self._load_config(config_path)
        self.input_format = input_format
        self.dry_run = dry_run

        # State: {ip: deque([timestamps])}
        self.ip_history = defaultdict(deque)
        # State: {uri: deque([timestamps])} - For hot resource detection
        self.uri_history = defaultdict(deque)

        # Whitelists
        self.static_extensions = {'.css', '.js', '.png', '.jpg', '.gif', '.ico', '.woff', '.ttf'}

        self.window_size = 60 # 1 minute for RPM
        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME}. Format: {input_format}, Dry-run: {dry_run}")

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def _load_config(self, path):
        path = path or DEFAULT_CONFIG_PATH
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
        return {}

    def parse_line(self, line):
        """Extracts (ip, method, uri, status) from line."""
        line = line.strip()
        if not line: return None

        try:
            if self.input_format == "json":
                data = json.loads(line)
                # Adapt fields based on your JSON log schema
                # Assuming simple: client_ip, request_uri, method, status
                return (
                    data.get("client_ip") or data.get("remote_addr"),
                    data.get("method"),
                    data.get("request_uri") or data.get("uri"),
                    data.get("status")
                )
            elif self.input_format == "clf":
                match = CLF_REGEX.match(line)
                if match:
                    return match.group(1), match.group(2), match.group(3), match.group(4)
        except Exception:
            pass
        return None

    def analyze_request(self, ip, method, uri, status):
        """Core analysis logic."""
        now = time.time()

        # 0. Filter Static Assets (Optional - based on config)
        if any(uri.endswith(ext) for ext in self.static_extensions):
            return # Skip static asset counting for Rate Limiting (usually handled by CDN/Nginx efficiently)

        # 1. IP Rate Limiting (RPM)
        self.ip_history[ip].append(now)
        self._prune_history(self.ip_history[ip], now, self.window_size)

        rpm = len(self.ip_history[ip])
        ip_threshold = self.config.get("max_rpm_per_ip", 100)

        if rpm > ip_threshold:
            # Check if we already alerted recently? (Simple dedup logic: alert on multiples of threshold)
            if rpm % ip_threshold == 1:
                self.emit_event("rate_limit_exceeded", ip, "HIGH", {
                    "rpm": rpm,
                    "threshold": ip_threshold,
                    "target": uri
                })

        # 2. Burst Detection (e.g., > 10 reqs in 1 second)
        # Look at last 10 requests
        if rpm >= 10:
            last_10 = list(self.ip_history[ip])[-10:]
            duration = last_10[-1] - last_10[0]
            if duration < 1.0:
                 self.emit_event("burst_pattern_detected", ip, "MEDIUM", {
                    "pattern": "10_reqs_in_1s",
                    "duration": f"{duration:.3f}s"
                })

        # 3. Hot Resource Detection (Global)
        # Simplified: Just track count. In prod, maybe use heavy hitters sketch.
        self.uri_history[uri].append(now)
        self._prune_history(self.uri_history[uri], now, self.window_size)

        uri_rpm = len(self.uri_history[uri])
        uri_threshold = self.config.get("max_rpm_per_resource", 1000)

        if uri_rpm > uri_threshold and uri_rpm % 500 == 1:
             self.emit_event("resource_exhaustion_attempt", "GLOBAL", "MEDIUM", {
                 "target": uri,
                 "rpm": uri_rpm,
                 "threshold": uri_threshold
             })

    def _prune_history(self, deque_obj, now, window):
        while deque_obj and (now - deque_obj[0] > window):
            deque_obj.popleft()

    def emit_event(self, event_type, src_entity, severity, data=None):
        if data is None: data = {}
        data["status"] = "simulated" if self.dry_run else "active"

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "event": event_type,
            "source_entity": src_entity, # IP or "GLOBAL"
            "severity": severity,
            "data": data
        }
        print(json.dumps(event))
        sys.stdout.flush()
        if src_entity != "GLOBAL":
            logging.warning(f"ALERT: {event_type} from {src_entity} (Sev: {severity})")

    def run(self):
        logging.info("Starting L7 Analyzer (reading STDIN)...")
        try:
            for line in sys.stdin:
                parsed = self.parse_line(line)
                if parsed:
                    ip, method, uri, status = parsed
                    if ip and uri:
                        self.analyze_request(ip, method, uri, status)
        except KeyboardInterrupt:
            logging.info("Stopping...")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="L7 Request Rate Analyzer")
    parser.add_argument("--config", help="Path to l7_thresholds.yaml")
    parser.add_argument("--format", choices=["json", "clf"], default="json", help="Log format")
    parser.add_argument("--dry-run", action="store_true", help="Simulate alerts")

    args = parser.parse_args()

    analyzer = L7RequestRateAnalyzer(args.config, args.format, args.dry_run)
    analyzer.run()

if __name__ == "__main__":
    main()
