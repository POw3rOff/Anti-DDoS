#!/usr/bin/env python3
"""
http_behavior_fingerprinting.py
Layer 7 Anti-DDoS Script: Creates fingerprints of HTTP clients to distinguish bots from humans.

This script analyzes HTTP request logs to generate a fingerprint based on:
1. Header ordering (if available in input)
2. Presence of specific headers
3. Timing between requests (if session tracking is enabled)
4. User-Agent consistency

Usage:
    python3 http_behavior_fingerprinting.py < log_file.json
    OR
    tail -F access.json | python3 http_behavior_fingerprinting.py

Input Format:
    JSON objects, one per line, with at least:
    {
        "ip": "1.2.3.4",
        "timestamp": 1678888888,
        "headers": {"User-Agent": "...", "Accept": "...", ...},
        "method": "GET",
        "url": "/path"
    }
    Note: For strict header order fingerprinting, 'headers' should be a list of [key, value] tuples,
    or the log source must preserve JSON object key order (Python 3.7+ does, but many JSON serializers don't).
"""

import sys
import json
import hashlib
import time
from collections import defaultdict

# Configuration
# Threshold for inter-arrival time variance (machines are regular, humans are bursty)
REGULARITY_THRESHOLD = 0.1
# Known bot user agents (simple substring match)
BOT_KEYWORDS = ["bot", "crawl", "spider", "curl", "wget", "python", "java"]

class HTTPFingerprinter:
    def __init__(self):
        self.client_history = defaultdict(list)
        self.suspicious_ips = set()

    def generate_fingerprint(self, headers):
        """Generates a hash based on header names and their order."""
        if isinstance(headers, dict):
            header_keys = list(headers.keys())
        elif isinstance(headers, list):
            header_keys = [h[0] for h in headers]
        else:
            return "unknown"

        # Normalize to lowercase for consistency
        header_keys = [k.lower() for k in header_keys]
        fingerprint_str = "|".join(header_keys)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    def analyze_timing(self, ip, timestamp):
        """Analyzes inter-arrival times for regularity."""
        history = self.client_history[ip]
        history.append(timestamp)

        # Keep only last 10 requests
        if len(history) > 10:
            history.pop(0)

        if len(history) < 5:
            return "insufficient_data"

        intervals = [history[i] - history[i-1] for i in range(1, len(history))]
        avg_interval = sum(intervals) / len(intervals)

        if avg_interval == 0:
            return "machine_burst"

        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        cv = std_dev / avg_interval if avg_interval > 0 else 0 # Coefficient of Variation

        # Low CV implies high regularity (bot-like)
        if cv < REGULARITY_THRESHOLD:
            return "machine_regular"
        return "human_irregular"

    def process_request(self, record):
        ip = record.get("ip", "unknown")
        headers = record.get("headers", {})
        user_agent = ""

        if isinstance(headers, dict):
            user_agent = headers.get("User-Agent", "")
        elif isinstance(headers, list):
            for k, v in headers:
                if k.lower() == "user-agent":
                    user_agent = v
                    break

        fingerprint = self.generate_fingerprint(headers)
        timing_verdict = self.analyze_timing(ip, record.get("timestamp", time.time()))

        is_bot_ua = any(keyword in user_agent.lower() for keyword in BOT_KEYWORDS)

        result = {
            "ip": ip,
            "fingerprint": fingerprint,
            "timing_analysis": timing_verdict,
            "bot_user_agent": is_bot_ua,
            "verdict": "HUMAN"
        }

        # Scoring Logic
        score = 0
        if is_bot_ua: score += 50
        if timing_verdict == "machine_regular": score += 30
        if timing_verdict == "machine_burst": score += 40

        if score > 40:
            result["verdict"] = "BOT"
            self.suspicious_ips.add(ip)

        return result

def main():
    fingerprinter = HTTPFingerprinter()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            analysis = fingerprinter.process_request(record)
            print(json.dumps(analysis))
            sys.stdout.flush()
        except json.JSONDecodeError:
            sys.stderr.write(f"Invalid JSON: {line}\n")
        except Exception as e:
            sys.stderr.write(f"Error processing line: {e}\n")

if __name__ == "__main__":
    main()
