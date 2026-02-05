#!/usr/bin/env python3
"""
Persistence Manager
Part of Enforcement Layer

Responsibility: Ensures active mitigations survive reboots and crashes.
Manages the `active_actions.json` state file.
"""

import json
import os
import time
import fcntl
import logging
from datetime import datetime, timezone

STATE_FILE = "runtime/state/active_actions.json"
HISTORY_FILE = "runtime/state/history.log"

class PersistenceManager:
    def __init__(self):
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

    def _get_lock(self, f):
        fcntl.flock(f, fcntl.LOCK_EX)

    def _release_lock(self, f):
        fcntl.flock(f, fcntl.LOCK_UN)

    def load_active(self):
        """Loads non-expired actions."""
        if not os.path.exists(STATE_FILE):
            return {}

        try:
            with open(STATE_FILE, 'r') as f:
                self._get_lock(f)
                data = json.load(f)
                self._release_lock(f)

            # Filter expired
            now = time.time()
            active = {k: v for k, v in data.items() if v["expires_at"] > now}

            # If we filtered something, save back (lazy cleanup)
            if len(active) != len(data):
                self._save_atomic(active)

            return active
        except Exception as e:
            logging.error(f"Failed to load persistence state: {e}")
            return {}

    def save_action(self, target, action, ttl, layer):
        """Records a new mitigation action."""
        active = self.load_active()
        now = time.time()

        entry = {
            "action": action,
            "layer": layer,
            "applied_at": now,
            "expires_at": now + ttl,
            "details": {"target": target, "ttl": ttl}
        }

        active[target] = entry
        self._save_atomic(active)
        self._audit(f"APPLY {action} on {target} (TTL: {ttl})")

    def remove_action(self, target):
        """Removes a mitigation action."""
        active = self.load_active()
        if target in active:
            action = active[target]["action"]
            del active[target]
            self._save_atomic(active)
            self._audit(f"REVERT {action} on {target}")

    def _save_atomic(self, data):
        tmp = f"{STATE_FILE}.tmp"
        try:
            with open(tmp, 'w') as f:
                self._get_lock(f)
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
                self._release_lock(f)
            os.replace(tmp, STATE_FILE)
        except Exception as e:
            logging.error(f"Persistence save failed: {e}")

    def _audit(self, message):
        """Appends to history log."""
        ts = datetime.now(timezone.utc).isoformat()
        try:
            with open(HISTORY_FILE, 'a') as f:
                f.write(f"[{ts}] {message}\n")
        except Exception:
            pass
