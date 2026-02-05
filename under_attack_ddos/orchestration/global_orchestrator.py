#!/usr/bin/env python3
"""
Global Orchestrator
Part of 'under_attack_ddos' Defense System.

Responsibility: Central authority for mitigation decisions.
Receives intent from 'under_attack_orchestrator', 'distributed_sync_agent',
and other detectors to issue concrete enforcement commands.
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
from datetime import datetime, timezone

# Third-party imports
try:
    import yaml
except ImportError as e:
    print(f"CRITICAL: Missing dependencies: {e}", file=sys.stderr)
    sys.exit(4)

SCRIPT_NAME = "global_orchestrator"

class GlobalOrchestrator:
    def __init__(self, config_path, dry_run=False):
        self.config_path = config_path
        self.dry_run = dry_run
        self.running = True
        self.queue = queue.Queue()

        # Load policies
        self.policies = self._load_config()

    def _load_config(self):
        # Simplified policy loader
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def ingest_loop(self):
        """Read JSON events from STDIN (piped from detectors/orchestrators)."""
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line: break

                event = json.loads(line)
                self.queue.put(event)
            except json.JSONDecodeError:
                continue
            except Exception:
                break

    def process_loop(self):
        """Process events and dispatch commands."""
        while self.running:
            try:
                event = self.queue.get(timeout=1.0)
                self._handle_event(event)
            except queue.Empty:
                continue

    def _handle_event(self, event):
        # Dispatch logic
        layer = event.get("layer")
        evt_type = event.get("event")
        src = event.get("source_entity")
        data = event.get("data", {})

        # Distributed / Game Layer Handling
        if layer == "distributed":
            if evt_type == "edge_mitigation_triggered":
                self._dispatch_mitigation("iptables_block", src, {"duration": 300, "reason": "edge_sync"})
                return

        if layer == "layer_game":
            severity = event.get("severity")
            if severity in ["HIGH", "CRITICAL"]:
                # Game specific mitigation
                game = data.get("game")
                proto = data.get("protocol")
                self._dispatch_mitigation("game_port_block", src, {"game": game, "protocol": proto, "duration": 60})
                return

        # Legacy/Standard Handling
        if event.get("state") == "UNDER_ATTACK":
            # Global mode change
            logging.warning("SYSTEM UNDER ATTACK - Escalating defenses")
            # In real impl, this would trigger mode switching scripts
            return

    def _dispatch_mitigation(self, action_type, target, params):
        command = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action_type,
            "target": target,
            "params": params
        }

        json_cmd = json.dumps(command)
        if self.dry_run:
            logging.info(f"[DRY-RUN] Dispatch: {json_cmd}")
        else:
            # Write to enforcement queue file or similar.
            # For this prototype, we log to stdout which might be picked up by a dispatcher
            # But usually Orchestrator -> Dispatcher via IPC.
            logging.info(f"DISPATCH >>> {json_cmd}")
            # Ensure separate output stream if needed, usually orchestrator writes to a specific pipe
            # Here we just log.

    def stop(self, *args):
        self.running = False
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_NAME)
    parser.add_argument("--config", default="config/orchestrator.yaml")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    orch = GlobalOrchestrator(args.config, args.dry_run)
    signal.signal(signal.SIGINT, orch.stop)
    signal.signal(signal.SIGTERM, orch.stop)

    # Input thread
    t = threading.Thread(target=orch.ingest_loop, daemon=True)
    t.start()

    orch.process_loop()

if __name__ == "__main__":
    main()
