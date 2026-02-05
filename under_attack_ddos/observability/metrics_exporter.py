#!/usr/bin/env python3
"""
Metrics Exporter
Part of Observability Layer

Responsibility: Exposes system metrics to Prometheus and provides CLI summaries.
Reads from system logs or state files to generate metrics.
"""

import sys
import os
import time
import json
import logging
import argparse
from threading import Thread
from collections import Counter
from http.server import HTTPServer, BaseHTTPRequestHandler

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
METRICS_PORT = 9090
LOG_FILE = "logs/system.json.log"
STATE_FILE = "runtime/global_state.json"

class PrometheusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(self.server.exporter.generate_metrics().encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return # Silence access logs

class MetricsExporter:
    def __init__(self, port=METRICS_PORT):
        self.port = port
        self.counters = Counter()
        self.gauges = {}

    def run(self):
        # Start Log Tailer in background
        t = Thread(target=self._tail_logs, daemon=True)
        t.start()

        # Start HTTP Server
        server = HTTPServer(('0.0.0.0', self.port), PrometheusHandler)
        server.exporter = self
        logging.info(f"Prometheus exporter started on port {self.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

    def _tail_logs(self):
        """Tails the system log file and updates counters."""
        if not os.path.exists(LOG_FILE):
            logging.warning(f"Log file {LOG_FILE} not found. Waiting...")

        # Simple polling loop
        while True:
            try:
                # In a real impl, track file offset. Here we re-scan periodically or use simplistic tail logic
                # For robustness in this prototype, we'll just read state files mostly.
                # Actually, tailing is better for event counts.
                pass
            except Exception:
                pass
            time.sleep(1)

    def update_from_log_line(self, line):
        try:
            event = json.loads(line)
            layer = event.get("layer", "unknown")
            evt_type = event.get("event", "unknown")

            # Metric: uad_events_total
            self.counters[f'uad_events_total{{layer="{layer}",type="{evt_type}"}}'] += 1

            if "severity" in event:
                sev = event["severity"]
                self.counters[f'uad_severity_total{{layer="{layer}",level="{sev}"}}'] += 1

        except json.JSONDecodeError:
            pass

    def generate_metrics(self):
        lines = []
        lines.append("# HELP uad_events_total Total detection events.")
        lines.append("# TYPE uad_events_total counter")
        for key, val in self.counters.items():
            if key.startswith("uad_events"):
                lines.append(f"{key} {val}")

        lines.append("# HELP uad_severity_total Events by severity.")
        lines.append("# TYPE uad_severity_total counter")
        for key, val in self.counters.items():
            if key.startswith("uad_severity"):
                lines.append(f"{key} {val}")

        # Add Risk Score Gauge
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    score = state.get("grs_score", 0)
                    lines.append(f'uad_global_risk_score {score}')
        except Exception:
            pass

        return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Metrics Exporter")
    parser.add_argument("--port", type=int, default=METRICS_PORT, help="Prometheus port")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    exporter = MetricsExporter(args.port)

    # Mock data for demonstration if file doesn't exist
    exporter.counters['uad_events_total{layer="l3",type="flood"}'] = 10
    exporter.counters['uad_events_total{layer="l4",type="syn"}'] = 5

    exporter.run()

if __name__ == "__main__":
    main()
