#!/usr/bin/env python3
"""
Under Attack Mode Controller
Part of 'under_attack_ddos' Defense System.

Responsibility: Manual and authoritative state management for the system.
Act as the "Panic Button" and "Safety Override" interface.
"""

import sys
import os
import json
import time
import argparse
import fcntl
import logging
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "under_attack_mode"
LAYER = "orchestration"
RESPONSIBILITY = "Global state control"

RUNTIME_DIR = "runtime"
STATE_FILE = os.path.join(RUNTIME_DIR, "global_state.json")
LOCK_FILE = os.path.join(RUNTIME_DIR, "state.lock")
OVERRIDE_FILE = os.path.join(RUNTIME_DIR, "OVERRIDE.lock")

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class StateManager:
    def __init__(self):
        self._ensure_runtime_dir()

    def _ensure_runtime_dir(self):
        if not os.path.exists(RUNTIME_DIR):
            os.makedirs(RUNTIME_DIR, exist_ok=True)

    def _get_lock(self):
        """Acquire a file lock to ensure atomic updates."""
        try:
            lock_fd = open(LOCK_FILE, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            return lock_fd
        except IOError as e:
            logging.error(f"Could not acquire lock: {e}")
            sys.exit(1)

    def _release_lock(self, lock_fd):
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()

    def read_state(self):
        """Reads the current state JSON."""
        if not os.path.exists(STATE_FILE):
            return {
                "mode": "NORMAL",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "reason": "system_init",
                "manual_override": False
            }

        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error("State file corrupted. Resetting.")
            return self.read_state() # Recursive reset logic essentially, or just return default.
            # Ideally return default to avoid infinite recursion if read_state fail
            return {"mode": "NORMAL", "updated_at": datetime.now(timezone.utc).isoformat(), "error": "corrupted"}

    def write_state(self, state):
        """Writes the state JSON atomically."""
        lock = self._get_lock()
        try:
            state["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Check for override lock presence
            if os.path.exists(OVERRIDE_FILE):
                state["manual_override"] = True
            else:
                state["manual_override"] = False

            # Atomic write via temp file
            tmp_file = f"{STATE_FILE}.tmp"
            with open(tmp_file, 'w') as f:
                json.dump(state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp_file, STATE_FILE)
            logging.info(f"State updated: {state['mode']}")
        finally:
            self._release_lock(lock)

    def set_override(self, enabled):
        """Creates or removes the override lock file."""
        if enabled:
            with open(OVERRIDE_FILE, 'w') as f:
                f.write(datetime.now(timezone.utc).isoformat())
            logging.warning("MANUAL OVERRIDE ENABLED. Automated changes disabled.")
        else:
            if os.path.exists(OVERRIDE_FILE):
                os.remove(OVERRIDE_FILE)
            logging.info("Manual override disabled.")

    def get_status(self):
        state = self.read_state()
        override = os.path.exists(OVERRIDE_FILE)

        print("-" * 40)
        print(f"SYSTEM STATUS: {state.get('mode', 'UNKNOWN')}")
        print("-" * 40)
        print(f"Last Updated : {state.get('updated_at')}")
        print(f"Override     : {'ACTIVE' if override else 'Inactive'}")
        print(f"Reason       : {state.get('reason', 'N/A')}")
        print("-" * 40)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to execute")

    # Status
    subparsers.add_parser("status", help="Show current system mode")

    # Enable (Manual Trigger)
    enable_parser = subparsers.add_parser("enable", help="Manually trigger UNDER_ATTACK mode")
    enable_parser.add_argument("--reason", default="manual_intervention", help="Reason for activation")

    # Disable (Return to Normal)
    disable_parser = subparsers.add_parser("disable", help="Return to NORMAL mode")
    disable_parser.add_argument("--reason", default="manual_reset", help="Reason for reset")

    # Force (Override)
    force_parser = subparsers.add_parser("force", help="Set specific mode and lock system")
    force_parser.add_argument("mode", choices=["NORMAL", "UNDER_ATTACK"], help="Mode to force")
    force_parser.add_argument("--lock", action="store_true", help="Create override lock to prevent auto-changes")
    force_parser.add_argument("--unlock", action="store_true", help="Remove override lock")

    args = parser.parse_args()

    # Logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', stream=sys.stderr)

    manager = StateManager()

    if args.command == "status":
        manager.get_status()

    elif args.command == "enable":
        state = manager.read_state()
        state["mode"] = "UNDER_ATTACK"
        state["reason"] = args.reason
        manager.write_state(state)

    elif args.command == "disable":
        state = manager.read_state()
        state["mode"] = "NORMAL"
        state["reason"] = args.reason
        manager.write_state(state)

    elif args.command == "force":
        if args.unlock:
            manager.set_override(False)

        state = manager.read_state()
        state["mode"] = args.mode
        state["reason"] = "forced_by_admin"
        manager.write_state(state)

        if args.lock:
            manager.set_override(True)

if __name__ == "__main__":
    main()
