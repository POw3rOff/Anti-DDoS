#!/usr/bin/env python3
"""
UAD Prometheus Metrics Exporter
Part of 'under_attack_ddos' Defense System.

Responsibility: Scraping internal state and exposing it as Prometheus metrics.
"""

import os
import time
import json
import logging
import argparse
from prometheus_client import start_http_server, Gauge, Counter

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "metrics_exporter"
STATE_FILE = "runtime/global_state.json"

# -----------------------------------------------------------------------------
# Metrics Definitions
# -----------------------------------------------------------------------------
GRS_SCORE = Gauge("uad_global_risk_score", "Current Global Risk Score (0-100)")
DEFENSE_MODE = Gauge("uad_defense_mode", "Current Defense Mode (0=NORMAL, 1=MONITOR, 2=UNDER_ATTACK, 3=ESCALATED)")
ACTIVE_CAMPAIGNS = Gauge("uad_active_campaigns_count", "Number of currently active multi-vector campaigns")
MITIGATION_DIRECTIVES = Counter("uad_mitigation_directives_total", "Total number of mitigation actions issued", ["type", "action"])

MODE_MAP = {
    "NORMAL": 0,
    "MONITOR": 1,
    "UNDER_ATTACK": 2,
    "ESCALATED": 3
}

# -----------------------------------------------------------------------------
# Exporter Class
# -----------------------------------------------------------------------------

class UADMetricsExporter:
    def __init__(self, port):
        self.port = port
        self.running = True

    def run(self):
        logging.info(f"Starting Prometheus exporter on port {self.port}...")
        start_http_server(self.port)
        
        while self.running:
            try:
                self._update_metrics()
            except Exception as e:
                logging.error(f"Error updating metrics: {e}")
            time.sleep(5)

    def _update_metrics(self):
        if not os.path.exists(STATE_FILE):
            return

        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            
            # 1. Update GRS
            GRS_SCORE.set(state.get("grs_score", 0.0))
            
            # 2. Update Mode
            mode_str = state.get("mode", "NORMAL")
            DEFENSE_MODE.set(MODE_MAP.get(mode_str, 0))
            
            # 3. Update Campaigns
            campaigns = state.get("campaigns", [])
            ACTIVE_CAMPAIGNS.set(len(campaigns))
            
            # Note: Counters like MITIGATION_DIRECTIVES are harder to update 
            # from a state file unless it contains a total_directives field.
            # For now, GRS and Mode are the most critical signals.
            
        except json.JSONDecodeError:
            pass # File might be half-written

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UAD Prometheus Exporter")
    parser.add_argument("--port", type=int, default=9100, help="Exporter port")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level),
                        format='%(asctime)s [%(levelname)s] %(message)s')

    exporter = UADMetricsExporter(args.port)
    try:
        exporter.run()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
