#!/usr/bin/env python3
"""
Enforcement Dispatcher
Part of Enforcement Layer

Responsibility: Watches runtime/enforcement/ for new commands and routes them
to the appropriate enforcement module (Firewall, TC, etc.).
"""

import sys
import os
import json
import time
import logging
import argparse
import subprocess
from datetime import datetime

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
WATCH_DIR = "runtime/enforcement"
PROCESSED_DIR = "runtime/enforcement/processed"

# Mapping: Action -> Module Script
MODULE_MAP = {
    "block_temp": "firewall/iptables_block.py",
    "rate_limit": "traffic_control/tc_rate_limit.py",
    "game_block": "game_ports/game_port_block.py"
}

# -----------------------------------------------------------------------------
# Dispatcher Class
# -----------------------------------------------------------------------------
class Dispatcher:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self._setup_logging()
        self._ensure_dirs()

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def _ensure_dirs(self):
        os.makedirs(WATCH_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DIR, exist_ok=True)

    def run(self):
        logging.info("Dispatcher started. Watching for commands...")
        try:
            while True:
                self._scan_and_dispatch()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Stopping...")

    def _scan_and_dispatch(self):
        for fname in os.listdir(WATCH_DIR):
            if not fname.endswith(".json"): continue

            fpath = os.path.join(WATCH_DIR, fname)
            try:
                with open(fpath, 'r') as f:
                    command = json.load(f)

                self._dispatch(command)

                # Move to processed
                os.rename(fpath, os.path.join(PROCESSED_DIR, fname))

            except Exception as e:
                logging.error(f"Failed to process {fname}: {e}")

    def _dispatch(self, cmd):
        action = cmd.get("action")
        target = cmd.get("src_ip")
        ttl = cmd.get("ttl", 300)

        module = MODULE_MAP.get(action)
        if not module:
            logging.warning(f"Unknown action: {action}")
            return

        # Construct CLI call
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, module)

        cli_args = [
            sys.executable, script_path,
            "--target", target,
            "--apply",
            "--ttl", str(ttl)
        ]

        if self.dry_run:
            cli_args.append("--dry-run")

        logging.info(f"Dispatching: {action} -> {target}")

        if not self.dry_run:
            # Fire and forget (or wait?) - Waiting ensures sequentiality
            subprocess.run(cli_args, check=False)
        else:
            logging.info(f"[DRY-RUN] Exec: {' '.join(cli_args)}")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enforcement Dispatcher")
    parser.add_argument("--dry-run", action="store_true", help="Simulate dispatch")
    args = parser.parse_args()

    Dispatcher(args.dry_run).run()
