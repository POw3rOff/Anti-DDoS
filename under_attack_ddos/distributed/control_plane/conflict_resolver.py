#!/usr/bin/env python3
"""
Control Plane: Conflict Resolver
Part of 'under_attack_ddos' Defense System.

Responsibility: Decides the "Global Truth" when PoPs disagree.
"""

class ConflictResolver:
    def __init__(self, trust_model):
        self.trust_model = trust_model

    def resolve(self, target_ip, reports):
        """
        reports: list of { 'pop_id': str, 'action': 'BLOCK'|'ALLOW' }
        Returns: Final Action or None (indecisive)
        """
        block_score = 0.0
        allow_score = 0.0

        for r in reports:
            weight = self.trust_model.evaluate_signal(r['pop_id'], None)
            if r['action'] == 'BLOCK':
                block_score += weight
            elif r['action'] == 'ALLOW':
                allow_score += weight

        # Consensus threshold
        if block_score > 2.0: # Requires at least 2 perfect PoPs or 3 average ones
            return "BLOCK"

        if allow_score > block_score:
            return "ALLOW"

        return None
