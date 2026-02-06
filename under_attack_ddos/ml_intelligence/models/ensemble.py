#!/usr/bin/env python3
"""
ML Model: Ensemble
Part of 'under_attack_ddos' Defense System.

Responsibility: Combine outputs from different models.
"""

class EnsembleModel:
    def __init__(self, models):
        self.models = models

    def evaluate(self, features):
        votes = []
        for model in self.models:
            votes.append(model.predict(features))

        # Majority vote
        anomalies = votes.count(-1)
        if anomalies > len(self.models) / 2:
            return True, 0.8 # Is Anomaly, Confidence

        return False, 0.0
