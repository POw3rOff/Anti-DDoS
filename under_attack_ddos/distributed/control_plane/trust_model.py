#!/usr/bin/env python3
"""
Control Plane: Trust Model
Part of 'under_attack_ddos' Defense System.

Responsibility: Assigns and manages Trust Scores for Edge PoPs.
Prevents compromised or noisy PoPs from triggering global bans.
"""

class TrustModel:
    def __init__(self):
        # pop_id -> score (0-100)
        self.scores = {}
        self.default_score = 50

    def register_pop(self, pop_id):
        if pop_id not in self.scores:
            self.scores[pop_id] = self.default_score

    def evaluate_signal(self, pop_id, signal_data):
        """
        Returns a weight (0.0-1.0) for the signal based on PoP trust.
        """
        score = self.scores.get(pop_id, self.default_score)

        # Simple linear weight for now
        weight = score / 100.0
        return weight

    def update_score(self, pop_id, delta):
        current = self.scores.get(pop_id, self.default_score)
        new_score = max(0, min(100, current + delta))
        self.scores[pop_id] = new_score
