#!/usr/bin/env python3
"""
Mitigation Controller
Part of 'under_attack_ddos' Defense System.

Responsibility: Reacts to decisions from the Orchestrator.
Level 1 Safe Mode: No packet dropping, only alerts and posture changes.
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
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "mitigation_controller"
LAYER = "mitigation"
RESPONSIBILITY = "Safe-mode response logic and alerting"

# Default configuration (Fail-safe)
DEFAULT_CONFIG = {
    "mitigation": {
        "dry_run_default": True,
        "auto_escalate": True,
        "states": {
            "normal": {"risk_max": 29},
            "defensive": {"risk_min": 30, "risk_max": 59},
            "high_alert": {"risk_min": 60}
        },
        "alerts": {
            "enabled": True,
            "log_file": "logs/mitigation_events.json.log"
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

class AlertManager:
    def __init__(self, config):
        self.config = config
        self.log_path = config.get("alerts", {}).get("log_file", None)

    def send(self, level, message, details=None):
        """Dispatches alert to configured channels."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }

        # 1. JSON Log File
        if self.log_path:
            try:
                # Ensure directory exists
                log_dir = os.path.dirname(self.log_path)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)

                with open(self.log_path, 'a') as f:
                    f.write(json.dumps(payload) + "\n")
            except Exception as e:
                logging.error(f"Failed to write alert log: {e}")

        # 2. Webhook (Placeholder)
        webhook = self.config.get("alerts", {}).get("webhook_url")
        if webhook:
            logging.info(f"Would POST to webhook: {webhook}")

        # 3. STDOUT (for operator visibility)
        print(f"ALERT [{level}]: {message}", file=sys.stdout)

class ControllerEngine:
    def __init__(self, args, config):
        self.args = args
        self.config = config.get("mitigation", DEFAULT_CONFIG["mitigation"])
        self.alerter = AlertManager(self.config)

        self.current_state = "NORMAL"
        self.last_state_change = time.time()
        self.running = True

    def process_decision(self, decision):
        """Evaluates an Orchestrator Decision."""
        score = decision.get("score", 0)
        orch_state = decision.get("state", "NORMAL")

        # Determine Target Mitigation State
        target_state = self._map_risk_to_state(score)

        if target_state != self.current_state:
            self._transition(target_state, decision)
        else:
            # Just log significant events if state is stable
            if score > 50:
                logging.info(f"Sustained Risk: {score} (State: {self.current_state})")

    def _map_risk_to_state(self, score):
        states = self.config["states"]
        if score >= states["high_alert"]["risk_min"]: return "HIGH_ALERT"
        if score >= states["defensive"]["risk_min"]: return "DEFENSIVE"
        return "NORMAL"

    def _transition(self, new_state, context):
        now = time.time()

        # Cooldown check (only prevents downgrades)
        if self._is_downgrade(new_state) and (now - self.last_state_change < self.config["cooldown_seconds"]):
            logging.info(f"Cooldown active. Holding {self.current_state} despite lower risk.")
            return

        old_state = self.current_state
        self.current_state = new_state
        self.last_state_change = now

        msg = f"Transition: {old_state} -> {new_state}"
        logging.warning(msg)

        # Trigger Alerts
        level = "INFO" if new_state == "NORMAL" else "CRITICAL"
        self.alerter.send(level, msg, details=context)

        # Execute Safe Actions
        self._execute_posture(new_state)

    def _is_downgrade(self, new_state):
        # Simple hierarchy: NORMAL < DEFENSIVE < HIGH_ALERT
        ranks = {"NORMAL": 0, "DEFENSIVE": 1, "HIGH_ALERT": 2}
        return ranks.get(new_state, 0) < ranks.get(self.current_state, 0)

    def _execute_posture(self, state):
        """Applies reversible configuration flags."""
        if self.args.dry_run:
            logging.info(f"[DRY-RUN] Would apply posture: {state}")
            return

        if state == "HIGH_ALERT":
            logging.info("ACTION: Suggesting aggressive rate limits.")
            logging.info("ACTION: Recommending CAPTCHA on all login endpoints.")
        elif state == "DEFENSIVE":
            logging.info("ACTION: Suggesting stricter monitoring logging.")
        elif state == "NORMAL":
            logging.info("ACTION: Resetting recommendations to baseline.")

    def run_loop(self, input_source):
        logging.info(f"Starting {SCRIPT_NAME}. Waiting for decisions...")

        try:
            if input_source == 'stdin':
                for line in sys.stdin:
                    if not self.running: break
                    self._handle_input(line)
            else:
                # File tail mode
                with open(input_source, 'r') as f:
                    f.seek(0, 2)
                    while self.running:
                        line = f.readline()
                        if not line:
                            time.sleep(0.1)
                            continue
                        self._handle_input(line)

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logging.error(f"Runtime error: {e}", exc_info=True)
            sys.exit(1)

    def _handle_input(self, line):
        try:
            if not line.strip(): return
            decision = json.loads(line)
            self.process_decision(decision)
        except json.JSONDecodeError:
            pass

    def stop(self, signum=None, frame=None):
        logging.info("Stopping...")
        self.running = False

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)

    # Required Flags
    parser.add_argument("--config", required=True, help="Path to YAML configuration")

    # Optional Flags
    parser.add_argument("--mode", default="normal", help="Initial mode (override)")
    parser.add_argument("--input", default="stdin", choices=["stdin", "file"], help="Input source")
    parser.add_argument("--input-file", help="Path to input file (if input=file)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions")
    parser.add_argument("--daemon", action="store_true", help="Run as background service")
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
    logging.info(f"Starting {SCRIPT_NAME} v1.0.0")
    config = ConfigLoader.load(args.config)

    controller = ControllerEngine(args, config)

    # Signal Handling
    signal.signal(signal.SIGINT, controller.stop)
    signal.signal(signal.SIGTERM, controller.stop)

    # Execution
    controller.run_loop(args.input if args.input == 'stdin' else args.input_file)

if __name__ == "__main__":
    main()
