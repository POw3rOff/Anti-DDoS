#!/usr/bin/env python3
"""
ML Features: Flow Statistics
Part of 'under_attack_ddos' Defense System.

Responsibility: Calculate statistical features from traffic flows.
"""

import math
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
        """Returns a feature vector: [entropy, pps_variance, jitter]"""
        win = self.windows.get(src_ip)
        if not win or len(win["sizes"]) < 10:
            return [0.0, 0.0, 0.0]

        # 1. Entropy of sizes
        entropy = self._calculate_entropy(win["sizes"])

        # 2. PPS Variance (approximated within window)
        dur = win["times"][-1] - win["times"][0]
        pps = len(win["sizes"]) / max(dur, 0.001)
        # For variance, we look at inter-arrival times
        intervals = [win["times"][i] - win["times"][i-1] for i in range(1, len(win["times"]))]
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval)**2 for x in intervals) / len(intervals)

        # 3. Jitter (standard deviation of intervals)
        jitter = math.sqrt(variance)

        return [round(entropy, 3), round(variance, 6), round(jitter, 6)]

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
