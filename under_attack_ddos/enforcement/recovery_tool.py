#!/usr/bin/env python3
"""
Recovery Tool
Part of Enforcement Layer

Responsibility: Re-applies active mitigations after a system reboot/crash.
Reads from runtime/state/active_actions.json and invokes dispatchers.
"""

import sys
import os
import logging
import time
import subprocess

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enforcement.common.persistence import PersistenceManager
from enforcement.dispatcher import MODULE_MAP

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logging.info("Starting Recovery Process...")

    pm = PersistenceManager()
    active_actions = pm.load_active()

    if not active_actions:
        logging.info("No active actions found to recover.")
        return

    recovered_count = 0

    for target, info in active_actions.items():
        # Check if expired
        ttl_remaining = info["expires_at"] - time.time()
        if ttl_remaining <= 0:
            logging.info(f"Skipping expired: {target}")
            continue

        # Determine module
        # Note: We need to map 'description' back to action key or store key.
        # Ideally persistence should store the 'action_key' (e.g. 'block_temp') not description.
        # For this prototype, we assume the 'action' field in JSON matches MODULE_MAP keys if possible,
        # or we rely on the fact that ActionBase stores the class description.

        # FIX: The current persistence saves "action" as description.
        # We need a way to map description back or ensure 'action' is the key.
        # Assuming for now 'block_temp' maps to iptables.

        # Heuristic mapping for recovery
        module_script = None
        if "IPTables" in info["action"]:
            module_script = MODULE_MAP["block_temp"]
        elif "Game Port" in info["action"]:
            module_script = MODULE_MAP["game_block"]
        elif "Traffic Control" in info["action"]:
            module_script = MODULE_MAP["rate_limit"]

        if module_script:
            logging.info(f"Recovering: {target} via {module_script} (TTL: {int(ttl_remaining)}s)")

            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), module_script)

            subprocess.run([
                sys.executable, script_path,
                "--target", target,
                "--apply",
                "--ttl", str(int(ttl_remaining))
            ], check=False)

            recovered_count += 1
        else:
            logging.warning(f"Unknown action type for recovery: {info['action']}")

    logging.info(f"Recovery Complete. Restored {recovered_count} rules.")

if __name__ == "__main__":
    main()
