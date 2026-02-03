#!/usr/bin/env python3
"""
http_timing_attack_detector.py
Layer 7 Anti-DDoS Script: Analyzes request timing for mechanical patterns.

Purpose:
Detects automated attack tools that send requests at fixed intervals (e.g., every 1000ms)
or using simple randomization functions that differ from human behavior.

Logic:
1. Tracks inter-arrival times (IAT) for each IP.
2. Calculates Standard Deviation of IATs.
   - Near Zero = Fixed rate attack (e.g., Low Orbit Ion Cannon in default mode).
3. Calculates Burstiness.

Usage:
    python3 http_timing_attack_detector.py < log_stream.json
"""

import sys
import json
import time
import math
from collections import defaultdict, deque

# Configuration
WINDOW_SIZE = 20           # Number of requests to keep for analysis
MIN_REQUESTS = 5           # Minimum requests before verdict
FIXED_RATE_THRESHOLD = 0.05 # Standard Deviation threshold (seconds) for "fixed rate"
FAST_RATE_THRESHOLD = 0.5  # Mean IAT threshold (seconds) for "too fast"

class TimingAnalyzer:
    def __init__(self):
        # ip -> deque of timestamps
        self.history = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))

    def analyze(self, ip, timestamp):
        timestamps = self.history[ip]
        timestamps.append(timestamp)

        if len(timestamps) < MIN_REQUESTS:
            return None

        # Calculate Inter-Arrival Times (IAT)
        iats = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]

        if not iats:
            return None

        # 1. Calculate Mean IAT
        mean_iat = sum(iats) / len(iats)

        # 2. Calculate Standard Deviation
        variance = sum((x - mean_iat) ** 2 for x in iats) / len(iats)
        std_dev = math.sqrt(variance)

        # Verdict Logic
        verdict = "NORMAL"
        confidence = 0
        details = []

        # Check for Fixed Rate (Mechanical)
        if std_dev < FIXED_RATE_THRESHOLD:
            verdict = "BOT_FIXED_RATE"
            confidence = 90
            details.append(f"Fixed rate detected: std_dev={std_dev:.4f}s")

        # Check for High Frequency (Flood)
        if mean_iat < FAST_RATE_THRESHOLD:
            if verdict == "NORMAL":
                verdict = "BOT_HIGH_FREQ"
            else:
                verdict += "_AND_HIGH_FREQ"
            confidence = max(confidence, 80)
            details.append(f"High frequency: mean_iat={mean_iat:.4f}s")

        if verdict != "NORMAL":
            return {
                "ip": ip,
                "verdict": verdict,
                "confidence": confidence,
                "metrics": {
                    "mean_iat": mean_iat,
                    "std_dev": std_dev
                },
                "details": details
            }
        return None

def main():
    analyzer = TimingAnalyzer()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            ip = record.get("ip")
            ts = record.get("timestamp", time.time())

            if ip:
                result = analyzer.analyze(ip, ts)
                if result:
                    print(json.dumps(result))
                    sys.stdout.flush()
        except json.JSONDecodeError:
            pass
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
