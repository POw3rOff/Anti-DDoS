#!/usr/bin/env python3
"""
Layer G Game Mitigation Bridge
Part of Anti-DDoS/under_attack_ddos/layer_game/

Responsibility: Translates game-specific correlated attacks into generic
mitigation intents for the central Orchestrator. Ideally piped from
game_correlation_engine.py.
"""

import sys
import json
import argparse
import logging
import time
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Constants & Config
# -----------------------------------------------------------------------------
SCRIPT_NAME = "game_mitigation_bridge"
LAYER = "layer_game"  # Standardized for global orchestrator

# Mitigation Policy Definitions
POLICIES = {
    "passive": {
        "HIGH": {"action": "log_only", "ttl": 0},
        "CRITICAL": {"action": "rate_limit_ip", "ttl": 60}
    },
    "balanced": {
        "HIGH": {"action": "rate_limit_ip", "ttl": 300},
        "CRITICAL": {"action": "temporary_blackhole", "ttl": 300}
    },
    "aggressive": {
        "HIGH": {"action": "temporary_blackhole", "ttl": 600},
        "CRITICAL": {"action": "escalate_to_l3", "ttl": 3600}
    }
}

class MitigationBridge:
    def __init__(self, policy_name="balanced", dry_run=False):
        self.policy_name = policy_name
        self.policy = POLICIES.get(policy_name, POLICIES["balanced"])
        self.dry_run = dry_run

        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME}. Policy: {policy_name}. Dry-run: {dry_run}")

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def process_event(self, line):
        """Ingest raw event line, validate, and translate."""
        try:
            if not line.strip(): return
            event = json.loads(line)

            # Filter: Only process correlated attacks from Layer G
            if event.get("event") != "correlated_attack":
                return
            if event.get("layer") != "game":
                return

            self._translate_intent(event)

        except json.JSONDecodeError:
            pass

    def _translate_intent(self, event):
        """Map game event to generic mitigation intent."""
        severity = event.get("severity", "LOW")
        src_ip = event.get("src_ip")
        confidence = event.get("confidence", 0.0)
        game = event.get("game", "unknown")

        # 1. Determine Action based on Policy
        rule = self.policy.get(severity)
        if not rule:
            # Severity too low for action in this policy
            return

        action = rule["action"]
        ttl = rule["ttl"]

        # 2. Contextual Overrides
        # If confidence is exceptionally high, escalate
        if confidence > 0.95 and action == "rate_limit_ip":
            action = "temporary_blackhole"
            ttl *= 2

        # 3. Construct Intent Object
        intent = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": LAYER,
            "event": f"game_mitigation_intent",
            "source_entity": src_ip,
            "severity": severity,
            "data": {
                "game": game,
                "protocol": "unknown", # Correlated events might aggregate protocols
                "action_type": action,
                "ttl": ttl,
                "original_signals": event.get("signals", []),
                "policy_used": self.policy_name
            }
        }

        self._emit_intent(intent)

    def _emit_intent(self, intent):
        """Output to STDOUT for the Orchestrator."""
        print(json.dumps(intent))
        sys.stdout.flush()

        logging.warning(f"MITIGATION INTENT: {intent['data']['action_type']} for {intent['source_entity']} (TTL: {intent['data']['ttl']}s)")

    def run_stdin(self):
        logging.info("Listening on STDIN...")
        try:
            for line in sys.stdin:
                self.process_event(line)
        except KeyboardInterrupt:
            logging.info("Stopping...")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Layer G Mitigation Bridge")
    parser.add_argument("--input", choices=["stdin"], default="stdin", help="Input mode")
    parser.add_argument("--policy", choices=["passive", "balanced", "aggressive"], default="balanced", help="Mitigation policy profile")
    parser.add_argument("--dry-run", action="store_true", help="Simulate intents")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    bridge = MitigationBridge(args.policy, args.dry_run)

    if args.input == "stdin":
        bridge.run_stdin()

if __name__ == "__main__":
    main()
