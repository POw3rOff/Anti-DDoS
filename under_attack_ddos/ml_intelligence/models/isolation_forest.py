#!/usr/bin/env python3
"""
ML Model: Isolation Forest Wrapper
Part of 'under_attack_ddos' Defense System.

Responsibility: Detect anomalies in feature vectors.
"""

import random
import json
import os
import statistics

import statistics

class IsolationForestWrapper:
    def __init__(self):
        # Baseline history for dynamic thresholding
        self.history = []
        self.max_history = 500

    def predict(self, feature_vector):
        """
        Returns -1 for anomaly, 1 for normal.
        feature_vector: [entropy, variance, jitter]
        """
        entropy, variance, jitter = feature_vector

        # 1. HARD LIMITS (Sanity Checks)
        if entropy < 0.05: return -1 # Fixed packet size
        if jitter < 0.0001: return -1 # Robotic heartbeat

        # 2. DYNAMIC THRESHOLDING (Z-Score)
        # If we have enough history, check for significant deviations
        if len(self.history) >= 30:
            # We track 'variance' as the primary indicator of PPS volatility
            variances = [h[1] for h in self.history]
            mean_v = statistics.mean(variances)
            stdev_v = statistics.stdev(variances)
            
            # If current variance is > 3 standard deviations from mean -> Anomaly
            if stdev_v > 0 and (variance - mean_v) / stdev_v > 3.0:
                return -1

        # Update History
        self.history.append(feature_vector)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return 1

    def save_state(self, filepath):
        """Saves current baseline history to disk."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.history, f)
            return True
        except Exception as e:
            # logging not imported in this class file usually, but we can print or ignore
            print(f"Failed to save state: {e}")
            return False

    def load_state(self, filepath):
        """Loads baseline history from disk."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Validate dimension
                    self.history = [x for x in data if len(x) == 3]
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Failed to load state: {e}")
            return False
