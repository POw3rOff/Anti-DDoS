#!/usr/bin/env python3
"""
Autotune Policy Model
Part of 'under_attack_ddos' Defense System.

Responsibility: Decide how to adjust thresholds based on system state.
"""

class PolicyModel:
    def __init__(self):
        pass

    def suggest_tuning(self, current_state, metrics):
        """
        Returns a dict of adjustments: {param: new_value}
        metrics: { 'cpu_load': 0.0-1.0, 'dropped_pps': int, 'current_pps': int }
        """
        adjustments = {}

        # Logic: If CPU is high, raise thresholds to reduce processing overhead (shed load)
        # Wait, actually: If CPU is high due to *processing* legitimate traffic, we might want strict filtering.
        # But if CPU is high due to *analyzing* too many alerts, we might want to RAISE thresholds to alert less.
        # XDP context: Processing in XDP is cheap. But creating events is expensive.
        # So if we are creating too many events (high alerts), raise threshold.

        cpu = metrics.get("cpu_load", 0.0)

        # Example Logic
        if cpu > 0.8:
            # High Load: Reduce sensitivity (Raise thresholds) to survive
            adjustments["syn_pps"] = "increase_10%"
            adjustments["udp_pps"] = "increase_10%"
        elif cpu < 0.2:
            # Low Load: Increase sensitivity (Lower thresholds) to catch low-and-slow
            adjustments["syn_pps"] = "decrease_5%"

        return adjustments

    def calculate_new_value(self, current_val, adjustment_str):
        if not current_val: return current_val

        if adjustment_str == "increase_10%":
            return int(current_val * 1.1)
        if adjustment_str == "decrease_5%":
            return int(current_val * 0.95)

        return current_val
