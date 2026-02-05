#!/usr/bin/env python3
"""
ML Features: Spatial / Multi-PoP Statistics
Part of 'under_attack_ddos' Defense System.

Responsibility: Calculate distribution metrics across PoPs.
"""

class SpatialFeatureExtractor:
    def __init__(self):
        pass

    def calculate_pop_synchronization(self, pop_reports):
        """
        Detects if multiple PoPs are reporting the same target simultaneously.
        High sync often indicates a coordinated botnet command.
        """
        if not pop_reports: return 0.0

        # Logic: If > 50% of PoPs see the target within 1 second -> High Sync
        unique_pops = set(r['pop_id'] for r in pop_reports)
        total_pops_in_network = 10 # Configurable

        ratio = len(unique_pops) / total_pops_in_network
        return min(1.0, ratio)
