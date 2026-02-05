#!/usr/bin/env python3
"""
Autotune Safety Guard
Part of 'under_attack_ddos' Defense System.

Responsibility: Enforce bounds and safety rules for kernel parameter tuning.
Prevents the system from locking itself out or becoming ineffective.
"""

import logging

# Hard Limits
LIMITS = {
    "icmp_pps": {"min": 100, "max": 10000, "default": 1000},
    "syn_pps":  {"min": 100, "max": 50000, "default": 500},
    "udp_pps":  {"min": 500, "max": 100000, "default": 2000},
    "game_pps": {"min": 50,  "max": 5000,   "default": 100}
}

class SafetyGuard:
    def __init__(self):
        pass

    def validate(self, param, value):
        """
        Validates and clamps a value to safe bounds.
        Returns (is_safe, clamped_value, reason)
        """
        rules = LIMITS.get(param)
        if not rules:
            return False, value, f"Unknown parameter: {param}"

        if value < rules["min"]:
            return True, rules["min"], f"Clamped to MIN {rules['min']}"

        if value > rules["max"]:
            return True, rules["max"], f"Clamped to MAX {rules['max']}"

        return True, value, "Value within bounds"

    def get_baseline(self, param):
        return LIMITS.get(param, {}).get("default")
