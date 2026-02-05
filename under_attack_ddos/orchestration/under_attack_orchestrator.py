#!/usr/bin/env python3
"""
Under Attack Orchestrator (Hardened)
Part of 'under_attack_ddos' Defense System.

Responsibility: Central correlation and decision engine.
Consumes detector events, calculates risk scores, and determines system state.
NO mitigation actions are performed here.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import threading
import queue
from collections import defaultdict, deque
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
RESPONSIBILITY = "Correlate events and determine global attack state"

# Default configuration (Fail-safe)
DEFAULT_CONFIG = {
    "orchestrator": {
        "window_size_seconds": 30,
        "cleanup_interval_seconds": 60,
        "weights": {"layer3": 0.4, "layer4": 0.3, "layer7": 0.3},
        "cross_layer_multiplier": 1.5,
        "thresholds": {
            "normal": {"max": 29},
            "monitor": {"min": 30, "max": 59},
            "under_attack": {"min": 60, "max": 89},
            "escalated": {"min": 90}
        },
        "cooldown_seconds": 300
    },
    "security": {
        "auth_token": "default_insecure"
    },
    "input_protection": {
        "max_events_per_second": 1000,
        "internal_queue_size": 5000,
        "max_event_age_seconds": 5
    }
}

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ConfigLoader:
    @staticmethod
    def load(paths):
        config = DEFAULT_CONFIG.copy()
        # Ensure sub-dicts exist
        if "security" not in config: config["security"] = {}
        if "input_protection" not in config: config["input_protection"] = {}

        for path in paths:
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    if not data: continue

                    # Deep merge (simplified)
                    for section in ["orchestrator", "security", "input_protection"]:
                        if section in data:
                            if section not in config: config[section] = {}
                            config[section].update(data[section])
            except Exception as e:
                logging.error(f"Failed to parse config {path}: {e}")
                sys.exit(2)

        # Override with Environment Variables (Security)
        env_token = os.environ.get("UAD_AUTH_TOKEN")
        if env_token:
            if "security" not in config: config["security"] = {}
            config["security"]["auth_token"] = env_token

        ConfigLoader._validate_config(config)
        return config

    @staticmethod
    def _validate_config(config):
        """Enforces critical business rules on the loaded configuration."""
        try:
            # 1. Orchestrator Window & Intervals
            orc = config.get("orchestrator", {})
            if orc.get("window_size_seconds", 30) <= 0:
                raise ValueError("orchestrator.window_size_seconds must be > 0")

            # 2. Weights
            weights = orc.get("weights", {})
            for k, v in weights.items():
                if v < 0:
                    raise ValueError(f"orchestrator.weights.{k} must be >= 0")

            # 3. Input Protection
            inp = config.get("input_protection", {})
            if inp.get("max_events_per_second", 1000) <= 0:
                raise ValueError("input_protection.max_events_per_second must be > 0")

        except ValueError as e:
            logging.error(f"Configuration Validation Error: {e}")
            sys.exit(3)

class RateLimiter:
    """Token bucket rate limiter."""
    def __init__(self, rate_per_second):
        self.rate = rate_per_second
        self.tokens = rate_per_second
        self.last_update = time.time()
        self.lock = threading.Lock()

    def allow(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Refill
            self.tokens += elapsed * self.rate
            if self.tokens > self.rate:
                self.tokens = self.rate

            # Consume
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

class EventIngestor(threading.Thread):
    """Reads events from input source and pushes to processing queue with validation."""
    def __init__(self, input_type, source, event_queue, config):
        super().__init__(daemon=True)
        self.input_type = input_type
        self.source = source
        self.event_queue = event_queue
        self.config = config
        self.running = True

        # Hardening
        self.auth_token = config["security"].get("auth_token")
        self.rate_limiter = RateLimiter(config["input_protection"]["max_events_per_second"])
        self.max_age = config["input_protection"]["max_event_age_seconds"]

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
        if not line.strip(): return

        # 1. Rate Limit Check
        if not self.rate_limiter.allow():
            # Drop silently or log periodically (logging every drop is bad for DoS)
            return

        try:
            event = json.loads(line)

            # 2. Auth Check
            if self.auth_token and self.auth_token != "default_insecure":
                token = event.get("auth_token")
                if token != self.auth_token:
                    logging.warning(f"Dropped unauthorized event from {event.get('source_entity')}")
                    return

            # 3. Age Check (optional, if timestamp present)
            # 4. Enqueue with limits
            try:
                self.event_queue.put(event, block=False)
            except queue.Full:
                logging.warning("Event queue FULL. Dropping event.")

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
        self.lock = threading.Lock()

        self.current_state = "NORMAL"
        self.last_attack_time = 0

    def ingest(self, event):
        """Add event to buffer and prune old events."""
        with self.lock:
            now = time.time()
            # Normalize event timestamp
            event["_recv_time"] = now

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

            # Calculate score per source
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

                # Cap source score
                src_score = min(src_score, 100.0)

                # Add to total (weighted average or max - adopting MAX strategy for safety)
                total_score = max(total_score, src_score)

                if src_score > 30:
                    active_sources.append({"ip": src, "score": round(src_score, 1)})

            # Determine State
            new_state = self._map_score_to_state(total_score)

            # Hysteresis / Cooldown
            now = time.time()
            if total_score >= 60: # Threshold for UNDER_ATTACK
                self.last_attack_time = now

            if new_state == "NORMAL" and (now - self.last_attack_time < self.config["cooldown_seconds"]):
                # Hold state if in cooldown
                return None

            if new_state != self.current_state:
                self.current_state = new_state
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "state": self.current_state,
                    "score": round(total_score, 1),
                    "affected_sources": active_sources,
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

        # Hardened Queue
        max_q = config["input_protection"].get("internal_queue_size", 5000)
        self.queue = queue.Queue(maxsize=max_q)

        # Components
        source = args.input_file if args.input == 'file' else None
        self.ingestor = EventIngestor(args.input, source, self.queue, config)
        self.engine = CorrelationEngine(config)

    def run(self):
        logging.info(f"Starting {SCRIPT_NAME}. Mode: {self.args.mode}")
        logging.info(f"Security: Rate Limit={self.ingestor.rate_limiter.rate}/s, Queue={self.queue.maxsize}")

        # Start Ingestor
        self.ingestor.start()

        try:
            while self.running:
                # 1. Process Queue (Non-blocking)
                try:
                    while True:
                        event = self.queue.get_nowait()
                        self.engine.ingest(event)
                except queue.Empty:
                    pass

                # 2. Evaluate State (Periodic)
                decision = self.engine.evaluate_risk()
                if decision:
                    self._emit_decision(decision)

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
        # Output to STDOUT (piped to mitigation usually)
        print(json.dumps(decision))
        sys.stdout.flush()

        # Log to STDERR
        logging.info(f"STATE CHANGE >>> {decision['state']} (Score: {decision['score']})")

    def stop(self, signum=None, frame=None):
        logging.info("Stopping...")
        self.running = False
        self.ingestor.stop()

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)

    # Required Flags
    parser.add_argument("--config", required=True, help="Path to YAML configuration")
    parser.add_argument("--hardening-config", default="config/hardening.yaml", help="Path to hardening config")
    parser.add_argument("--input", default="stdin", choices=["stdin", "file"], help="Input source")
    parser.add_argument("--input-file", help="Path to input file (if input=file)")

    # Optional Flags
    parser.add_argument("--mode", default="normal", choices=["normal", "monitor", "under_attack"], help="Initial mode")
    parser.add_argument("--daemon", action="store_true", help="Run as background service")
    parser.add_argument("--once", action="store_true", help="Run single pass and exit")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")

    args = parser.parse_args()

    if args.input == "file" and not args.input_file:
        print("Error: --input-file required when input is 'file'", file=sys.stderr)
        sys.exit(1)

    # Logging Setup
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        stream=sys.stderr
    )

    # Initialization
    logging.info(f"Starting {SCRIPT_NAME} v1.0.1 (Hardened)")

    # Load Main + Hardening Configs
    config = ConfigLoader.load([args.config, args.hardening_config])

    orchestrator = Orchestrator(args, config)

    # Signal Handling
    signal.signal(signal.SIGINT, orchestrator.stop)
    signal.signal(signal.SIGTERM, orchestrator.stop)

    # Execution
    orchestrator.run()

if __name__ == "__main__":
    main()
