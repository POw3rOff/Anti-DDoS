#!/usr/bin/env python3
"""
State Tracker
Part of Enforcement Layer

Responsibility: Tracks active mitigations and their TTLs to ensure cleanup.
"""

import json
import os
import time
import fcntl
import logging

class StateTracker:
    def __init__(self, layer_name):
        self.state_file = f"runtime/enforcement/{layer_name}_state.json"
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

    def _get_lock(self, f):
        fcntl.flock(f, fcntl.LOCK_EX)

    def _release_lock(self, f):
        fcntl.flock(f, fcntl.LOCK_UN)

    def load_state(self):
        if not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file, 'r') as f:
                self._get_lock(f)
                data = json.load(f)
                self._release_lock(f)
                return data
        except Exception:
            return {}

    def save_state(self, state):
        tmp = f"{self.state_file}.tmp"
        with open(tmp, 'w') as f:
            self._get_lock(f)
            json.dump(state, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
            self._release_lock(f)
        os.replace(tmp, self.state_file)

    def add_entry(self, target, action, ttl):
        state = self.load_state()
        state[target] = {
            "action": action,
            "applied_at": time.time(),
            "expires_at": time.time() + ttl
        }
        self.save_state(state)

    def remove_entry(self, target):
        state = self.load_state()
        if target in state:
            del state[target]
            self.save_state(state)

    def get_expired(self):
        """Returns list of targets that have expired."""
        state = self.load_state()
        now = time.time()
        expired = []
        for target, info in state.items():
            if now > info["expires_at"]:
                expired.append((target, info["action"]))
        return expired
