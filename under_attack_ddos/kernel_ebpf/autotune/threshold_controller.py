#!/usr/bin/env python3
"""
Autotune Threshold Controller
Part of 'under_attack_ddos' Defense System.

Responsibility: Actuator. Writes values to the pinned BPF config_map.
"""

import sys
import os
import argparse
import logging
import subprocess
from .safety_guard import SafetyGuard

# Config Map Index Mappings (Must match maps.h)
MAP_INDICES = {
    "icmp_pps": 0,
    "syn_pps":  1,
    "udp_pps":  2,
    "game_pps": 3
}

MAP_PATH = "/sys/fs/bpf/under_attack_ddos/config_map"

class ThresholdController:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.guard = SafetyGuard()
        self.current_values = {} # Cache

        # Init cache with defaults
        for k in MAP_INDICES.keys():
            self.current_values[k] = self.guard.get_baseline(k)

    def apply_update(self, param, value):
        if param not in MAP_INDICES:
            logging.error(f"Unknown param: {param}")
            return

        # 1. Safety Check
        is_safe, safe_val, reason = self.guard.validate(param, value)
        if not is_safe:
            logging.error(f"Update rejected: {reason}")
            return

        if safe_val != value:
            logging.warning(f"Value adjusted by SafetyGuard: {value} -> {safe_val} ({reason})")

        # 2. Apply
        idx = MAP_INDICES[param]
        self._write_bpf_map(idx, safe_val)
        self.current_values[param] = safe_val

    def _write_bpf_map(self, idx, val):
        if self.dry_run:
            logging.info(f"[DRY-RUN] BPF Map Update: idx={idx} val={val}")
            return

        # Use bpftool to update map
        # bpftool map update pinned <path> key <key> value <val>
        # Key/Val are usually hex bytes. For Array: key is index (4 bytes), value is u32 (4 bytes).

        # Helper to fmt as hex bytes space separated
        key_hex = " ".join([f"{b:02x}" for b in idx.to_bytes(4, 'little')])
        val_hex = " ".join([f"{b:02x}" for b in val.to_bytes(4, 'little')])

        cmd = [
            "bpftool", "map", "update", "pinned", MAP_PATH,
            "key", "hex", key_hex,
            "value", "hex", val_hex
        ]

        try:
            # We construct string for logging/cmd
            # Subprocess expects list of args. Key/Val arguments for bpftool are distinct.
            # actually bpftool expects: key hex 00 00 00 00 value hex 00 00 00 00

            full_cmd = ["bpftool", "map", "update", "pinned", MAP_PATH, "key", "hex"] + key_hex.split() + ["value", "hex"] + val_hex.split()

            subprocess.check_call(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info(f"Updated BPF Map: idx {idx} -> {val}")
        except Exception as e:
            logging.error(f"Failed to update BPF map: {e}")

def main():
    parser = argparse.ArgumentParser(description="eBPF Threshold Controller")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--set", nargs=2, metavar=('PARAM', 'VALUE'), help="Set parameter manually")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    controller = ThresholdController(args.dry_run)

    if args.set:
        param, val = args.set
        try:
            controller.apply_update(param, int(val))
        except ValueError:
            logging.error("Value must be integer")

if __name__ == "__main__":
    main()
