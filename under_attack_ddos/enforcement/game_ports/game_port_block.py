#!/usr/bin/env python3
"""
Game Port Block Enforcer
Part of Enforcement Layer

Responsibility: Blocks traffic to specific game ports for specific IPs.
Wraps iptables but scoped to game ports.
"""

import sys
import os
import logging
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.action_base import ActionBase
from common.state_tracker import StateTracker

CHAIN_NAME = "UAD_GAME_BLOCK"

class GamePortBlock(ActionBase):
    def __init__(self, dry_run=False):
        super().__init__("Game Port Blocker", dry_run)
        self.state = StateTracker("game_block")
        self._ensure_chain()

    def _ensure_chain(self):
        if self.dry_run: return
        res = subprocess.run(["iptables", "-L", CHAIN_NAME, "-n"], capture_output=True)
        if res.returncode != 0:
            subprocess.run(["iptables", "-N", CHAIN_NAME], check=True)
            # Insert logic here would depend on main chain structure

    def validate(self, target, params):
        return True

    def apply(self, target, params):
        ttl = params.get("ttl", 300)
        port = params.get("port", 11002)

        self.state.add_entry(target, "game_block", ttl)

        if self.dry_run:
            logging.info(f"[DRY-RUN] Block {target} on port {port}")
            return

        subprocess.run(
            ["iptables", "-A", CHAIN_NAME, "-s", target, "-p", "tcp", "--dport", str(port), "-j", "DROP"],
            check=False
        )
        logging.info(f"Blocked {target} on game port {port}")

    def revert(self, target, params):
        self.state.remove_entry(target)
        port = params.get("port", 11002)

        if self.dry_run:
            logging.info(f"[DRY-RUN] Unblock {target} on port {port}")
            return

        subprocess.run(
            ["iptables", "-D", CHAIN_NAME, "-s", target, "-p", "tcp", "--dport", str(port), "-j", "DROP"],
            check=False
        )
        logging.info(f"Unblocked {target} on game port")

if __name__ == "__main__":
    GamePortBlock().run_cli()
