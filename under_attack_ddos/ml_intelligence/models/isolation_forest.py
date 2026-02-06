#!/usr/bin/env python3
"""
ML Model: Isolation Forest Wrapper
Part of 'under_attack_ddos' Defense System.

Responsibility: Detect anomalies in feature vectors.
"""

import random

class IsolationForestWrapper:
    def predict(self, feature_vector):
        """
        Returns -1 for anomaly, 1 for normal.
        feature_vector: [entropy, variance, jitter]
        """
        entropy, variance, jitter = feature_vector

        # 1. FIXED PACKET SIZE ATTACK (Low Entropy)
        # Constant payload size is a strong indicator of simple bots.
        if entropy < 0.05:
            return -1

        # 2. LOW-AND-SLOW / HEARTBEAT (Very low Jitter)
        # If jitter is extremely low, it suggests a perfectly timed bot loop.
        if jitter < 0.001 and variance < 0.0001:
             return -1

        # 3. BURST ATTACK (High Variance)
        # Unusually high variance in arrival times might indicate pulse-wave DDoS.
        if variance > 1.0:
            return -1

        return 1
