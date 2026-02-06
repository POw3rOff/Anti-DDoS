#!/usr/bin/env python3
"""
Layer 7 Behavioral Fingerprinter
Part of under_attack_ddos/layer7/

Responsibility: Builds a reputation score for active sessions based on navigation patterns.
Detects non-human flows (e.g., accessing /login without /index, zero dwell time).
"""

import sys
import os
import json
import time
import argparse
import logging
import yaml
from collections import defaultdict, deque
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "l7_behavioral_fingerprinter"
LAYER = "layer7"
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "l7_thresholds.yaml")

# -----------------------------------------------------------------------------
# Fingerprinter Class
# -----------------------------------------------------------------------------
class L7BehavioralFingerprinter:
    def __init__(self, config_path=None, dry_run=False):
        self.config = self._load_config(config_path)
        self.dry_run = dry_run

        # Session State: {ip: {"path_history": deque, "last_ts": float, "score": int}}
        self.sessions = defaultdict(lambda: {
            "path_history": deque(maxlen=10),
            "last_ts": 0,
            "score": 0, # 0 = Good, 100 = Bot
            "is_flagged": False
        })

        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME}. Dry-run: {dry_run}")

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
        """Expects JSON log lines."""
        try:
            line = line.strip()
            if not line: return None
            data = json.loads(line)
            return (
                data.get("client_ip") or data.get("remote_addr"),
                data.get("request_uri") or data.get("uri"),
                data.get("http_user_agent") or data.get("user_agent", "")
            )
        except Exception:
            return None

    def analyze_request(self, ip, uri, ua):
        if not ip or not uri: return

        now = time.time()
        session = self.sessions[ip]

        # 1. Dwell Time Check (Too fast = Bot)
        dwell_time = now - session["last_ts"] if session["last_ts"] > 0 else 1.0

        # Update State
        session["last_ts"] = now
        session["path_history"].append(uri)

        # Skip if already flagged to reduce noise
        if session["is_flagged"]:
            # Decay flag after 5 mins? For now, just skip.
            if now - session["last_ts"] > 300:
                session["is_flagged"] = False
                session["score"] = 0
            else:
                return

        # --- HEURISTICS ---

        # Rule 1: Machine Speed (Dwell time < 50ms consistently)
        if dwell_time < 0.05:
            session["score"] += 20
        elif dwell_time < 0.2:
            session["score"] += 5
        else:
            # Reward human speed
            session["score"] = max(0, session["score"] - 5)

        # Rule 2: Entry Point Anomaly
        # Visiting sensitive page immediately without history
        if len(session["path_history"]) == 1:
            if "/login" in uri or "/admin" in uri or "/checkout" in uri:
                session["score"] += 40 # High suspicion

        # Rule 3: Linear/Cyclic Browsing (Repeatedly hitting same URL)
        if len(session["path_history"]) >= 5:
            # Check if last 5 are identical
            if len(set(session["path_history"])) == 1:
                session["score"] += 30

        # Rule 4: Headless Browser Check (Simple UA)
        if "HeadlessChrome" in ua or "PhantomJS" in ua or "python-requests" in ua:
            session["score"] += 100

        # --- EVALUATION ---
        if session["score"] >= 80:
            self.emit_event("suspicious_bot_fingerprint", ip, "HIGH", {
                "score": session["score"],
                "reason": self._determine_reason(session, dwell_time, ua),
                "history": list(session["path_history"])
            })
            session["is_flagged"] = True

    def _determine_reason(self, session, dwell, ua):
        if "Headless" in ua or "python" in ua: return "user_agent_blacklist"
        if len(set(session["path_history"])) == 1: return "cyclic_browsing"
        if len(session["path_history"]) == 1: return "direct_sensitive_entry"
        if dwell < 0.1: return "inhuman_speed"
        return "accumulated_risk"

    def emit_event(self, event_type, src_ip, severity, data):
        data["status"] = "simulated" if self.dry_run else "active"
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "event": event_type,
            "source_entity": src_ip,
            "severity": severity,
            "data": data
        }
        print(json.dumps(event))
        sys.stdout.flush()
        logging.warning(f"ALERT: {event_type} from {src_ip} (Score: {data['score']})")

    def run(self):
        logging.info("Starting Behavioral Fingerprinter (reading STDIN)...")
        try:
            for line in sys.stdin:
                parsed = self.parse_line(line)
                if parsed:
                    self.analyze_request(*parsed)
        except KeyboardInterrupt:
            logging.info("Stopping...")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="L7 Behavioral Fingerprinter")
    parser.add_argument("--config", help="Path to config yaml")
    parser.add_argument("--dry-run", action="store_true", help="Simulate alerts")

    args = parser.parse_args()

    fingerprinter = L7BehavioralFingerprinter(args.config, args.dry_run)
    fingerprinter.run()

if __name__ == "__main__":
    main()
