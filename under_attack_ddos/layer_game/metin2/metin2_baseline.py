#!/usr/bin/env python3
"""
Metin2 Behavioral Baseline Module
Part of Layer G (Game Protocol Defense)

Responsibility: Defines "normal" behavior metrics and provides validation logic
against the configured baseline. Used by other Metin2 detectors.
"""

import sys
import os
import json
import yaml
import logging
import argparse
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
MODULE_NAME = "metin2_baseline"
LAYER = "layer_game"
GAME = "metin2"

DEFAULT_CONFIG = {
    "max_login_pps": 5,
    "max_concurrent_sessions": 3,
    "min_session_duration": 60,
    "handshake_timeout": 5.0,
    "strict_handshake": True
}

# -----------------------------------------------------------------------------
# Baseline Class
# -----------------------------------------------------------------------------
class Metin2Baseline:
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self._setup_logging()

    def _load_config(self, path):
        if not path:
            # Try default location relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, "config.yaml")

        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return yaml.safe_load(f) or DEFAULT_CONFIG
            except Exception as e:
                logging.error(f"Failed to load config: {e}")

        logging.warning("Using default baseline configuration.")
        return DEFAULT_CONFIG

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO
        )

    def validate_login_rate(self, current_pps):
        """
        Checks if current login rate exceeds baseline.
        Returns: (is_anomaly: bool, details: dict)
        """
        threshold = self.config.get("max_login_pps", 5)
        is_anomaly = current_pps > threshold

        return is_anomaly, {
            "metric": "login_pps",
            "value": current_pps,
            "threshold": threshold,
            "severity": "HIGH" if current_pps > (threshold * 2) else "MEDIUM"
        }

    def validate_handshake_time(self, duration):
        """
        Checks if handshake completed within allowed window.
        Returns: (is_anomaly: bool, details: dict)
        """
        limit = self.config.get("handshake_timeout", 5.0)
        is_anomaly = duration > limit

        return is_anomaly, {
            "metric": "handshake_duration",
            "value": duration,
            "threshold": limit,
            "severity": "LOW"
        }

    def emit_event(self, event_type, details, src_ip="unknown"):
        """Emits a standard JSON event for the Orchestrator."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "game": GAME,
            "event": event_type,
            "source_entity": src_ip,
            "data": details
        }
        print(json.dumps(event))

# -----------------------------------------------------------------------------
# CLI for Testing
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Metin2 Baseline Validator")
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--test-pps", type=float, help="Test a PPS value against baseline")
    parser.add_argument("--test-handshake", type=float, help="Test a handshake duration against baseline")

    args = parser.parse_args()

    baseline = Metin2Baseline(args.config)

    if args.test_pps is not None:
        anomaly, details = baseline.validate_login_rate(args.test_pps)
        if anomaly:
            baseline.emit_event("baseline_violation", details)
        else:
            logging.info(f"PPS {args.test_pps} is within normal baseline.")

    if args.test_handshake is not None:
        anomaly, details = baseline.validate_handshake_time(args.test_handshake)
        if anomaly:
            baseline.emit_event("baseline_violation", details)
        else:
            logging.info(f"Duration {args.test_handshake}s is within normal baseline.")

if __name__ == "__main__":
    main()
