#!/usr/bin/env python3
"""
Layer G Game Correlation Engine
Part of Anti-DDoS/under_attack_ddos/layer_game/

Responsibility: Aggregates and correlates events from game-specific detectors
(e.g., Metin2) to identify sophisticated attack campaigns and reduce false positives.
"""

import sys
import os
import json
import time
import argparse
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Constants & Config
# -----------------------------------------------------------------------------
SCRIPT_NAME = "game_correlation_engine"
LAYER = "game_correlation"

# Event Weights for scoring
EVENT_WEIGHTS = {
    "auth_flood": 0.4,
    "protocol_violation": 0.6,
    "session_abuse": 0.5,
    "baseline_violation": 0.3
}

# -----------------------------------------------------------------------------
# Engine Class
# -----------------------------------------------------------------------------
class GameCorrelationEngine:
    def __init__(self, window_size=60, dry_run=False):
        self.window_size = window_size
        self.dry_run = dry_run

        # State: {src_ip: deque([events...])}
        self.event_buffer = defaultdict(deque)

        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME}. Window: {window_size}s. Dry-run: {dry_run}")

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def ingest_line(self, line):
        """Parse raw JSON line and ingest valid events."""
        try:
            if not line.strip(): return
            event = json.loads(line)

            # Basic validation
            if "src_ip" not in event or "event" not in event:
                return

            # Add reception timestamp for internal windowing
            event["_recv_ts"] = time.time()
            self._add_to_buffer(event)

        except json.JSONDecodeError:
            pass

    def _add_to_buffer(self, event):
        src_ip = event["src_ip"]
        self.event_buffer[src_ip].append(event)
        self._correlate(src_ip)

    def _correlate(self, src_ip):
        """Analyze the event buffer for a specific IP."""
        now = time.time()
        events = self.event_buffer[src_ip]

        # 1. Prune old events (Sliding Window)
        while events and (now - events[0]["_recv_ts"] > self.window_size):
            events.popleft()

        if not events:
            del self.event_buffer[src_ip]
            return

        # 2. Analyze current window
        signal_types = set()
        total_score = 0.0
        game_context = "unknown"

        for e in events:
            ev_type = e.get("event")
            signal_types.add(ev_type)
            total_score += EVENT_WEIGHTS.get(ev_type, 0.1)
            if "game" in e: game_context = e["game"]

        # 3. Decision Logic
        # Heuristic: Score > 1.0 or Multiple distinctive signal types
        is_attack = False
        confidence = 0.0
        severity = "LOW"

        # Case A: Multi-vector attack (e.g. Auth Flood + Protocol Violation)
        if len(signal_types) >= 2:
            is_attack = True
            confidence = 0.9
            severity = "CRITICAL" if "protocol_violation" in signal_types else "HIGH"

        # Case B: Sustained single-vector abuse
        elif total_score >= 2.0: # e.g. 5 auth_floods in window
            is_attack = True
            confidence = 0.7 + (min(total_score, 5.0) / 10.0) # Cap confidence boost
            severity = "HIGH"

        if is_attack:
            self._emit_alert(src_ip, game_context, list(signal_types), confidence, severity)
            # Optional: Clear buffer to suppress duplicate alerts for a short time?
            # For now, we rely on the orchestrator to dedup.

    def _emit_alert(self, src_ip, game, signals, confidence, severity):
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": "game",
            "game": game,
            "event": "correlated_attack",
            "src_ip": src_ip,
            "signals": signals,
            "confidence": round(confidence, 2),
            "severity": severity,
            "window": f"{self.window_size}s",
            "data": {
                "status": "simulated" if self.dry_run else "active"
            }
        }

        print(json.dumps(alert))
        sys.stdout.flush()
        logging.warning(f"CORRELATION: {game} attack from {src_ip} (Conf: {confidence:.2f})")

    def run_stdin(self):
        logging.info("Listening on STDIN...")
        try:
            for line in sys.stdin:
                self.ingest_line(line)
        except KeyboardInterrupt:
            logging.info("Stopping...")

    def run_file(self, path):
        logging.info(f"Tailing files in {path}...")
        # Simple implementation: Scan once or tail (simulated tail logic)
        # In production this would use inotify
        pass

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Layer G Correlation Engine")
    parser.add_argument("--input", choices=["stdin", "files"], default="stdin", help="Input mode")
    parser.add_argument("--events-path", help="Path to runtime events (file mode)")
    parser.add_argument("--window", type=int, default=60, help="Correlation window in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Simulate alerts")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    engine = GameCorrelationEngine(args.window, args.dry_run)

    if args.input == "stdin":
        engine.run_stdin()
    else:
        logging.error("File mode not yet implemented in this version.")
        sys.exit(1)

if __name__ == "__main__":
    main()
