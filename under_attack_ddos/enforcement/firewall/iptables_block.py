#!/usr/bin/env python3
"""
IPTables Block Enforcer
Part of Enforcement Layer

Responsibility: Manages temporary IP blocks using iptables.
"""

import sys
import os
import logging
import subprocess

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.action_base import ActionBase
from common.state_tracker import StateTracker

CHAIN_NAME = "UAD_BLOCKLIST"

class IPTablesBlock(ActionBase):
    def __init__(self, dry_run=False):
        super().__init__("IPTables IP Blocker", dry_run)
        self.state = StateTracker("iptables_block")
        self._ensure_chain()

    def _ensure_chain(self):
        """Idempotent chain creation."""
        if self.dry_run: return

        # Check if chain exists
        res = subprocess.run(["iptables", "-L", CHAIN_NAME, "-n"], capture_output=True)
        if res.returncode != 0:
            # Create chain
            subprocess.run(["iptables", "-N", CHAIN_NAME], check=True)
            # Insert at top of INPUT
            subprocess.run(["iptables", "-I", "INPUT", "1", "-j", CHAIN_NAME], check=True)

    def validate(self, target, params):
        # Basic IP validation could go here
        return True

    def apply(self, target, params):
        ttl = params.get("ttl", 300)

        # Add tracking
        self.state.add_entry(target, "block_temp", ttl)

        if self.dry_run:
            logging.info(f"[DRY-RUN] iptables -A {CHAIN_NAME} -s {target} -j DROP")
            return

        # Check existence to avoid duplicates
        check = subprocess.run(
            ["iptables", "-C", CHAIN_NAME, "-s", target, "-j", "DROP"],
            capture_output=True
        )

        if check.returncode != 0:
            subprocess.run(
                ["iptables", "-A", CHAIN_NAME, "-s", target, "-j", "DROP"],
                check=True
            )
            logging.info(f"Blocked {target} for {ttl}s")
        else:
            logging.info(f"Already blocked: {target}")

    def revert(self, target, params):
        self.state.remove_entry(target)

        if self.dry_run:
            logging.info(f"[DRY-RUN] iptables -D {CHAIN_NAME} -s {target} -j DROP")
            return

        # Delete rule
        subprocess.run(
            ["iptables", "-D", CHAIN_NAME, "-s", target, "-j", "DROP"],
            check=False # Ignore errors if already gone
        )
        logging.info(f"Unblocked {target}")

if __name__ == "__main__":
    IPTablesBlock().run_cli()
