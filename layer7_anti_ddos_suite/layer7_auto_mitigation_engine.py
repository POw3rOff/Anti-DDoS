#!/usr/bin/env python3
"""
layer7_auto_mitigation_engine.py
Layer 7 Anti-DDoS Script: Auto Mitigation Engine.

Purpose:
Aggregates alerts from all other detection scripts and decides on mitigation actions.
Supports actions:
- BLOCK: Drop traffic via Firewall/Fail2Ban integration.
- CAPTCHA: Flag IP for CAPTCHA challenge (upstream).
- RATE_LIMIT: Degrade service quality / bandwidth.
- GREYLIST: Temporarily block and re-evaluate.

Usage:
    python3 layer7_auto_mitigation_engine.py < alerts_stream.json

Integration:
    Outputs valid JSON commands that can be consumed by a local enforcement agent
    (e.g., a script that runs `iptables` or updates Nginx configs).
"""

import sys
import json
import time
from collections import defaultdict

# Mitigation Thresholds (Score based)
THRESHOLD_BLOCK = 100
THRESHOLD_CAPTCHA = 50
THRESHOLD_RATE_LIMIT = 20

# Durations (Seconds)
BLOCK_DURATION = 3600
CAPTCHA_DURATION = 300

class MitigationEngine:
    def __init__(self):
        self.ip_scores = defaultdict(int)
        self.active_mitigations = {} # ip -> {action, expire_time}

    def process_alert(self, alert):
        ip = alert.get("ip")
        if not ip:
            return None

        # Calculate Score Impact
        verdict = alert.get("verdict", "UNKNOWN")
        impact = 0

        if verdict == "BOT": impact = 50
        elif verdict == "BOTNET_DETECTED": impact = 100
        elif verdict == "ABUSE": impact = 60
        elif verdict == "SCHEMA_VIOLATION": impact = 40
        elif verdict == "SUSPICIOUS": impact = 20

        # Accumulate Score
        self.ip_scores[ip] += impact
        current_score = self.ip_scores[ip]

        # Determine Action
        action = "MONITOR"
        duration = 0

        if current_score >= THRESHOLD_BLOCK:
            action = "BLOCK"
            duration = BLOCK_DURATION
        elif current_score >= THRESHOLD_CAPTCHA:
            action = "CAPTCHA"
            duration = CAPTCHA_DURATION
        elif current_score >= THRESHOLD_RATE_LIMIT:
            action = "RATE_LIMIT"
            duration = CAPTCHA_DURATION

        # Check if already mitigated with same or stronger action
        if ip in self.active_mitigations:
            current_mitigation = self.active_mitigations[ip]
            if current_mitigation["action"] == action and time.time() < current_mitigation["expire_time"]:
                return None # Already active
            if action == "MONITOR":
                return None # Don't downgrade automatically yet

        # Apply Mitigation
        self.active_mitigations[ip] = {
            "action": action,
            "expire_time": time.time() + duration
        }

        return {
            "timestamp": time.time(),
            "ip": ip,
            "action": action,
            "reason": verdict,
            "score": current_score,
            "duration": duration,
            "command": self._generate_command(ip, action, duration)
        }

    def _generate_command(self, ip, action, duration):
        """Generates shell-compatible command description for enforcement agents."""
        if action == "BLOCK":
            return f"iptables -A INPUT -s {ip} -j DROP # Expires in {duration}s"
        elif action == "CAPTCHA":
            return f"echo {ip} >> /etc/nginx/captcha_list.txt"
        elif action == "RATE_LIMIT":
            return f"echo {ip} >> /etc/nginx/ratelimit_list.txt"
        return "noop"

def main():
    engine = MitigationEngine()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            alert = json.loads(line)
            decision = engine.process_alert(alert)
            if decision:
                print(json.dumps(decision))
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
