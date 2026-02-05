#!/usr/bin/env python3
"""
Global Orchestrator
Part of Anti-DDoS/under_attack_ddos/

Responsibility: The Central Brain. Consumes mitigation intents from ALL layers
(L3, L4, L7, G), correlates them, and decides authoritative enforcement actions.
"""

import sys
import os
import json
import time
import argparse
import logging
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Constants & Config
# -----------------------------------------------------------------------------
SCRIPT_NAME = "global_orchestrator"
LAYER = "control_plane"

# Decision Matrices
# Maps (Aggregate Severity, Confidence) -> Enforcement Level
DECISION_MATRIX = {
    "LOW": "OBSERVE",
    "MEDIUM": "SOFT",
    "HIGH": "HARD",
    "CRITICAL": "ISOLATE"
}

# Action Mapping
ACTIONS = {
    "OBSERVE": "log_only",
    "SOFT": "rate_limit",
    "HARD": "block_temp",
    "ISOLATE": "blackhole_routing"
}

# -----------------------------------------------------------------------------
# Orchestrator Class
# -----------------------------------------------------------------------------
class GlobalOrchestrator:
    def __init__(self, mode="observe", policy="balanced", dry_run=False):
        self.mode = mode
        self.policy = policy
        self.dry_run = dry_run

        # State: {src_ip: {"score": float, "layers": set(), "intents": []}}
        self.ip_state = defaultdict(lambda: {"score": 0.0, "layers": set(), "intents": []})
        self.cleanup_interval = 60
        self.last_cleanup = time.time()

        self._setup_logging()
        self._ensure_dirs()
        logging.info(f"Initialized {SCRIPT_NAME}. Mode: {mode}. Policy: {policy}. Dry-run: {dry_run}")

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def _ensure_dirs(self):
        os.makedirs("runtime/enforcement", exist_ok=True)

    def ingest_intent(self, line):
        """Parse normalized intent JSON."""
        try:
            if not line.strip(): return
            intent = json.loads(line)

            src_ip = intent.get("src_ip")
            if not src_ip: return

            self._update_state(src_ip, intent)
            self._evaluate_enforcement(src_ip)

        except json.JSONDecodeError:
            pass

    def _update_state(self, src_ip, intent):
        state = self.ip_state[src_ip]

        # Add intent
        state["intents"].append(intent)
        state["layers"].add(intent.get("source_layer", "unknown"))

        # Recalculate Score
        # Simple additive model + Multiplier for multi-layer
        severity_score = {
            "LOW": 10, "MEDIUM": 30, "HIGH": 60, "CRITICAL": 90
        }.get(intent.get("severity", "LOW"), 10)

        confidence = intent.get("confidence", 0.5)

        impact = severity_score * confidence

        # Multi-layer multiplier
        if len(state["layers"]) > 1:
            impact *= 1.5

        state["score"] += impact
        # Cap score
        state["score"] = min(state["score"], 150.0)

    def _evaluate_enforcement(self, src_ip):
        state = self.ip_state[src_ip]
        score = state["score"]

        # Determine Severity Level based on Score
        level = "LOW"
        if score > 120: level = "CRITICAL"
        elif score > 80: level = "HIGH"
        elif score > 40: level = "MEDIUM"

        decision = DECISION_MATRIX.get(level, "OBSERVE")
        action = ACTIONS.get(decision, "log_only")

        # Policy Adjustments
        if self.policy == "strict" and level == "MEDIUM":
            action = "block_temp" # Escalate
        elif self.policy == "permissive" and level == "HIGH":
            action = "rate_limit" # De-escalate

        # Emit Command
        if decision != "OBSERVE":
            self._emit_enforcement(src_ip, action, level, state["layers"])

    def _emit_enforcement(self, src_ip, action, level, layers):
        command = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "src_ip": src_ip,
            "ttl": 300 if level == "MEDIUM" else 900,
            "reason": f"score_exceeded_{level.lower()}",
            "confidence": 0.9, # Simplified
            "layers": list(layers),
            "data": {
                "status": "simulated" if self.dry_run or self.mode == "observe" else "active"
            }
        }

        # Write to file for Enforcement Agents to pick up
        fname = f"runtime/enforcement/{src_ip}_{int(time.time())}.json"
        try:
            with open(fname, 'w') as f:
                json.dump(command, f)
        except Exception as e:
            logging.error(f"Failed to write enforcement: {e}")

        logging.warning(f"DECISION: {action} for {src_ip} (Layers: {list(layers)})")

    def run_stdin(self):
        logging.info("Listening on STDIN...")
        try:
            for line in sys.stdin:
                self.ingest_intent(line)
        except KeyboardInterrupt:
            logging.info("Stopping...")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Global Security Orchestrator")
    parser.add_argument("--input", choices=["stdin", "files"], default="stdin", help="Input mode")
    parser.add_argument("--mode", choices=["observe", "active"], default="observe", help="Operational mode")
    parser.add_argument("--policy", choices=["strict", "balanced", "permissive"], default="balanced", help="Enforcement policy")
    parser.add_argument("--dry-run", action="store_true", help="Simulate enforcement")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    orch = GlobalOrchestrator(args.mode, args.policy, args.dry_run)

    if args.input == "stdin":
        orch.run_stdin()
    else:
        logging.error("File input mode not implemented yet.")
        sys.exit(1)

if __name__ == "__main__":
    main()
