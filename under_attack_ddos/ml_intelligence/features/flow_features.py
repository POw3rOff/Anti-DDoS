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
        # ip -> [packet_sizes...]
        self.windows = defaultdict(list)

    def update(self, src_ip, packet_size):
        self.windows[src_ip].append(packet_size)
        if len(self.windows[src_ip]) > 100:
            self.windows[src_ip].pop(0)

    def calculate_entropy(self, src_ip):
        """Calculates Shannon entropy of packet sizes."""
        sizes = self.windows.get(src_ip, [])
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
