#!/usr/bin/env python3
"""
ML Features: Flow Statistics
Part of 'under_attack_ddos' Defense System.

Responsibility: Calculate statistical features from traffic flows.
"""

import math
import time
from collections import defaultdict

class FlowFeatureExtractor:
    def __init__(self):
        # ip -> {"sizes": [...], "times": [...]}
        self.windows = defaultdict(lambda: {"sizes": [], "times": []})
        self.max_window = 100

    def update(self, src_ip, packet_size, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        
        win = self.windows[src_ip]
        win["sizes"].append(packet_size)
        win["times"].append(timestamp)

        if len(win["sizes"]) > self.max_window:
            win["sizes"].pop(0)
            win["times"].pop(0)

    def calculate_features(self, src_ip):
        """Returns a feature vector: [entropy, variance, jitter]"""
        win = self.windows.get(src_ip)
        if not win or len(win["sizes"]) < 10:
            return [0.0, 0.0, 0.0]

        # 1. Entropy of sizes
        entropy = self._calculate_entropy(win["sizes"])

        # 2. Inter-arrival dynamics
        intervals = [win["times"][i] - win["times"][i-1] for i in range(1, len(win["times"]))]
        if not intervals:
            return [round(entropy, 3), 0.0, 0.0]

        mean_interval = sum(intervals) / len(intervals)
        
        # Variance of intervals (how much the timing varies)
        variance = sum((x - mean_interval)**2 for x in intervals) / len(intervals)

        # Jitter (standard deviation of intervals)
        # Low jitter indicates robotic, highly regular timing.
        jitter = math.sqrt(variance)

        return [round(entropy, 4), round(variance, 6), round(jitter, 6)]

    def _calculate_entropy(self, sizes):
        if not sizes: return 0.0
        counts = defaultdict(int)
        for s in sizes:
            counts[s] += 1
        entropy = 0.0
        total = len(sizes)
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return entropy
