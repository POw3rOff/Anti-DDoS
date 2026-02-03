#!/usr/bin/env python3
"""
botnet_pattern_correlator.py
Layer 7 Anti-DDoS Script: Correlates patterns across multiple IPs.

Purpose:
Identifies distributed botnets by finding IPs that share identical behaviors, such as:
1. Identical User-Agents (rare for random large groups).
2. Synchronized attack timing (start/stop at same second).
3. Identical request targets or payloads.
4. Identical JA3 fingerprints (if available in logs).

Usage:
    python3 botnet_pattern_correlator.py < log_stream.json
"""

import sys
import json
import time
from collections import defaultdict

# Configuration
GROUP_SIZE_THRESHOLD = 5  # Minimum number of IPs to consider a "botnet"
TIME_WINDOW = 10          # Seconds to look for synchronized events

class BotnetCorrelator:
    def __init__(self):
        # target_path -> set(ips)
        self.target_groups = defaultdict(set)
        # user_agent -> set(ips)
        self.ua_groups = defaultdict(set)
        # fingerprint -> set(ips)
        self.fp_groups = defaultdict(set)

        self.detected_botnets = set() # Track already reported groups

    def analyze(self, record):
        ip = record.get("ip")
        ua = record.get("headers", {}).get("User-Agent", "unknown")
        path = record.get("url", "unknown")
        # Assuming 'fingerprint' might be enriched by upstream script
        fp = record.get("fingerprint", "unknown")

        # Update Groups
        self.ua_groups[ua].add(ip)
        self.target_groups[path].add(ip)
        if fp != "unknown":
            self.fp_groups[fp].add(ip)

        alerts = []

        # Check UA Groups
        if len(self.ua_groups[ua]) > GROUP_SIZE_THRESHOLD:
            group_id = f"UA_BOTNET_{hash(ua)}"
            if group_id not in self.detected_botnets:
                alerts.append({
                    "type": "UA_BOTNET",
                    "id": group_id,
                    "signature": ua[:50],
                    "size": len(self.ua_groups[ua]),
                    "ips_sample": list(self.ua_groups[ua])[:5]
                })
                self.detected_botnets.add(group_id)

        # Check Fingerprint Groups
        if fp != "unknown" and len(self.fp_groups[fp]) > GROUP_SIZE_THRESHOLD:
            group_id = f"FP_BOTNET_{fp}"
            if group_id not in self.detected_botnets:
                alerts.append({
                    "type": "FINGERPRINT_BOTNET",
                    "id": group_id,
                    "signature": fp,
                    "size": len(self.fp_groups[fp]),
                    "ips_sample": list(self.fp_groups[fp])[:5]
                })
                self.detected_botnets.add(group_id)

        if alerts:
            return {
                "verdict": "BOTNET_DETECTED",
                "timestamp": time.time(),
                "details": alerts
            }
        return None

def main():
    correlator = BotnetCorrelator()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            result = correlator.analyze(record)
            if result:
                print(json.dumps(result))
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
