#!/usr/bin/env python3
"""
Under Attack Orchestrator
Part of 'under_attack_ddos' Defense System.

Responsibility: Consumes events from all detection layers, calculates Global Risk Score (GRS),
and determines the system's Operational Mode. Now supports Campaign Alerts.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import queue
import threading
from collections import defaultdict
from datetime import datetime, timezone

# Third-party imports
try:
    import yaml
except ImportError as e:
    print(f"CRITICAL: Missing required dependencies: {e}", file=sys.stderr)
    print("Please install: pip install pyyaml", file=sys.stderr)
    sys.exit(4)

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "under_attack_orchestrator"
LAYER = "orchestration"
RESPONSIBILITY = "Global State Management & Decision Making"

# Default configuration (Fail-safe)
DEFAULT_CONFIG = {
    "orchestrator": {
        "window_size_seconds": 30,
        "weights": {
            "layer3": 0.4,
            "layer4": 0.3,
            "layer7": 0.3,
            "layer_game": 0.5,
            "correlation": 1.0  # High weight for pre-correlated alerts
        },
        "cross_layer_multiplier": 1.5,
        "thresholds": {
            "normal": {"max": 29},
            "monitor": {"min": 30, "max": 59},
            "under_attack": {"min": 60, "max": 89},
            "escalated": {"min": 90}
        },
        "cooldown_seconds": 300
    }
}

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ConfigLoader:
    @staticmethod
    def load(path):
        if not os.path.exists(path):
            logging.error(f"Config file not found: {path}")
            return DEFAULT_CONFIG

        try:
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            return user_config
        except Exception as e:
            logging.error(f"Failed to parse config: {e}")
            sys.exit(2)

class EventIngestor(threading.Thread):
    """Reads events from input source and pushes to processing queue."""
    def __init__(self, input_type, source, event_queue):
        super().__init__(daemon=True)
        self.input_type = input_type
        self.source = source
        self.event_queue = event_queue
        self.running = True

    def run(self):
        logging.info(f"Ingestor started. Source: {self.input_type}")
        if self.input_type == 'file':
            self._tail_file()
        elif self.input_type == 'stdin':
            self._read_stdin()

    def _tail_file(self):
        try:
            with open(self.source, 'r') as f:
                f.seek(0, 2) # Go to end
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    self._process_line(line)
        except Exception as e:
            logging.error(f"File ingest error: {e}")

    def _read_stdin(self):
        try:
            for line in sys.stdin:
                if not self.running: break
                self._process_line(line)
        except Exception as e:
            logging.error(f"Stdin ingest error: {e}")

    def _process_line(self, line):
        try:
            if not line.strip(): return
            event = json.loads(line)
            self.event_queue.put(event)
        except json.JSONDecodeError:
            logging.warning(f"Invalid JSON received: {line[:50]}...")

    def stop(self):
        self.running = False

class CorrelationEngine:
    def __init__(self, config):
        self.config = config.get("orchestrator", DEFAULT_CONFIG["orchestrator"])
        self.window_size = self.config["window_size_seconds"]
        self.weights = self.config["weights"]

        # In-memory state: {source_ip: [events...]}
        self.event_buffer = defaultdict(list)
        # Campaign State: [campaign_alerts...]
        self.active_campaigns = []

        self.lock = threading.Lock()

        self.current_state = "NORMAL"
        self.last_attack_time = 0

    def ingest(self, event):
        """Add event to buffer and prune old events."""
        with self.lock:
            now = time.time()
            event["_recv_time"] = now

            # Special handling for Campaign Alerts (from Cross-Layer Engine)
            if event.get("type") == "campaign_alert":
                self.active_campaigns.append(event)
                # Keep campaigns active for macro window (e.g. 5 mins)
                self.active_campaigns = [c for c in self.active_campaigns if now - c["_recv_time"] <= 300]
                return

            src = event.get("source_entity", "unknown")
            self.event_buffer[src].append(event)

            # Prune old events for this source
            self.event_buffer[src] = [e for e in self.event_buffer[src]
                                      if now - e["_recv_time"] <= self.window_size]

    def evaluate_risk(self):
        """Calculate Global Risk Score (GRS) and per-source risks."""
        with self.lock:
            total_score = 0.0
            active_sources = []
            active_layers = set()

            # 1. Evaluate Source-based Risks
            for src, events in self.event_buffer.items():
                if not events: continue

                src_score = 0.0
                layers_seen = set()

                for e in events:
                    layer = e.get("layer", "unknown")
                    severity = e.get("severity", "LOW")

                    # Base score mapping
                    base_val = 10
                    if severity == "MEDIUM": base_val = 30
                    elif severity == "HIGH": base_val = 60
                    elif severity == "CRITICAL": base_val = 90

                    weight = self.weights.get(layer, 0.1)
                    src_score += (base_val * weight)
                    layers_seen.add(layer)
                    active_layers.add(layer)

                # Cross-layer multiplier
                if len(layers_seen) > 1:
                    src_score *= self.config["cross_layer_multiplier"]

                src_score = min(src_score, 100.0)
                total_score = max(total_score, src_score)

                if src_score > 30:
                    active_sources.append({"ip": src, "score": round(src_score, 1)})

            # 2. Evaluate Campaign Alerts (High Priority)
            if self.active_campaigns:
                # If we have an active campaign, score is at least 80 (UNDER_ATTACK)
                # If confidence is HIGH, bump to 95 (ESCALATED)
                for camp in self.active_campaigns:
                    if camp.get("confidence") == "HIGH":
                        total_score = max(total_score, 95.0)
                    else:
                        total_score = max(total_score, 80.0)

                    active_layers.add("correlation")

            # Determine State
            new_state = self._map_score_to_state(total_score)

            # Hysteresis / Cooldown
            now = time.time()
            if total_score >= 60: # Threshold for UNDER_ATTACK
                self.last_attack_time = now

            if new_state == "NORMAL" and (now - self.last_attack_time < self.config["cooldown_seconds"]):
                return None # Hold state

            if new_state != self.current_state:
                self.current_state = new_state
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "state": self.current_state,
                    "score": round(total_score, 1),
                    "affected_sources": active_sources,
                    "active_campaigns": [c.get("campaign_name") for c in self.active_campaigns],
                    "active_layers": list(active_layers),
                    "confidence": "HIGH" if len(active_layers) > 1 else "MEDIUM",
                    "decision_id": f"dec-{int(now)}"
                }

            return None

    def _map_score_to_state(self, score):
        t = self.config["thresholds"]
        if score >= t["escalated"]["min"]: return "ESCALATED"
        if score >= t["under_attack"]["min"]: return "UNDER_ATTACK"
        if score >= t["monitor"]["min"]: return "MONITOR"
        return "NORMAL"

class Orchestrator:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.running = True
        self.queue = queue.Queue()

        # Components
        source = args.input_file if args.input == 'file' else None
        self.ingestor = EventIngestor(args.input, source, self.queue)
        self.engine = CorrelationEngine(config)

        # State dump file
        self.state_file = "runtime/global_state.json"
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

    def run(self):
        logging.info(f"Starting {SCRIPT_NAME}. Mode: {self.args.mode}")

        self.ingestor.start()

        try:
            while self.running:
                # 1. Process Queue
                try:
                    while True:
                        event = self.queue.get_nowait()
                        self.engine.ingest(event)
                except queue.Empty:
                    pass

                # 2. Evaluate State
                decision = self.engine.evaluate_risk()
                if decision:
                    self._emit_decision(decision)
                    self._update_state_file(decision)

                # 3. Sleep
                time.sleep(1.0)

                if self.args.once and self.queue.empty():
                    self.running = False

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logging.error(f"Runtime error: {e}", exc_info=True)
            sys.exit(1)

    def _emit_decision(self, decision):
        print(json.dumps(decision))
        sys.stdout.flush()
        logging.info(f"STATE CHANGE >>> {decision['state']} (Score: {decision['score']})")

    def _update_state_file(self, decision):
        """Writes current state to runtime file for Dashboard."""
        try:
            with open(self.state_file, 'w') as f:
                # Map decision to simple state
                state_dump = {
                    "mode": decision["state"],
                    "grs_score": decision["score"],
                    "last_update": decision["timestamp"],
                    "campaigns": decision.get("active_campaigns", [])
                }
                json.dump(state_dump, f)
        except Exception as e:
            logging.error(f"Failed to write state file: {e}")

    def stop(self, signum=None, frame=None):
        logging.info("Stopping...")
        self.running = False
        self.ingestor.stop()

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)
    parser.add_argument("--config", required=True, help="Path to YAML configuration")
    parser.add_argument("--input", default="stdin", choices=["stdin", "file"], help="Input source")
    parser.add_argument("--input-file", help="Path to input file (if input=file)")
    parser.add_argument("--mode", default="normal", choices=["normal", "monitor", "under_attack"], help="Initial mode")
    parser.add_argument("--daemon", action="store_true", help="Run as background service")
    parser.add_argument("--once", action="store_true", help="Run single pass and exit")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")

    args = parser.parse_args()

    if args.input == "file" and not args.input_file:
        print("Error: --input-file required when input is 'file'", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        stream=sys.stderr
    )

    config = ConfigLoader.load(args.config)
    orchestrator = Orchestrator(args, config)

    signal.signal(signal.SIGINT, orchestrator.stop)
    signal.signal(signal.SIGTERM, orchestrator.stop)

    orchestrator.run()

if __name__ == "__main__":
    main()
