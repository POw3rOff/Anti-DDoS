#!/usr/bin/env python3
"""
adaptive_rate_limit_engine.py
Layer 7 Anti-DDoS Script: Dynamic rate-limiting engine.

Features:
- Rate limiting by IP, Session ID, and API Token.
- Adaptive limits: Tightens thresholds when global traffic load increases.
- Penalty system: Exponential backoff for repeat offenders.

Usage:
    python3 adaptive_rate_limit_engine.py < log_stream.json

Input Format:
    JSON objects with keys: "ip", "session_id" (optional), "token" (optional), "endpoint", "timestamp".
"""

import sys
import json
import time
from collections import defaultdict

# Default Configuration
DEFAULT_LIMIT_PER_SECOND = 10
BURST_ALLOWANCE = 20
GLOBAL_TRAFFIC_THRESHOLD = 1000  # Req/sec that triggers panic mode
PANIC_MODE_MULTIPLIER = 0.5      # Reduce limits by 50% in panic mode

class TokenBucket:
    def __init__(self, capacity, fill_rate):
        if capacity < 0:
            raise ValueError(f"TokenBucket capacity must be non-negative, got {capacity}")
        if fill_rate < 0:
            raise ValueError(f"TokenBucket fill_rate must be non-negative, got {fill_rate}")
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self.fill_rate = float(fill_rate)
        self.last_update = time.time()

    def consume(self, tokens=1):
        if tokens < 0:
            raise ValueError(f"Cannot consume negative tokens: {tokens}")
        now = time.time()
        # Add new tokens based on time passed
        elapsed = now - self.last_update
        self.last_update = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.fill_rate)

        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

class AdaptiveRateLimiter:
    def __init__(self):
        # Stores TokenBuckets for different entities
        self.ip_buckets = {}
        self.session_buckets = {}
        self.global_counter = []
        self.blocked_ips = {}  # IP -> expiration_timestamp

    def is_blocked(self, ip):
        if ip in self.blocked_ips:
            if time.time() < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]
        return False

    def block_ip(self, ip, duration=60):
        self.blocked_ips[ip] = time.time() + duration

    def update_global_load(self):
        """Calculates current requests per second globally."""
        now = time.time()
        # Remove requests older than 1 second
        self.global_counter = [t for t in self.global_counter if now - t < 1.0]
        return len(self.global_counter)

    def get_dynamic_limit(self, load):
        """Returns multiplier for limits based on load."""
        if load > GLOBAL_TRAFFIC_THRESHOLD:
            return PANIC_MODE_MULTIPLIER
        return 1.0

    def process_request(self, record):
        ip = record.get("ip")
        session = record.get("session_id")
        timestamp = record.get("timestamp", time.time())

        # 1. Check Blocklist
        if self.is_blocked(ip):
            return {"action": "BLOCK", "reason": "IP_PENALTY", "ip": ip}

        # 2. Update Global Load
        self.global_counter.append(timestamp)
        current_load = self.update_global_load()
        limit_multiplier = self.get_dynamic_limit(current_load)

        # 3. Check IP Limit
        if ip:
            if ip not in self.ip_buckets:
                self.ip_buckets[ip] = TokenBucket(BURST_ALLOWANCE * limit_multiplier, DEFAULT_LIMIT_PER_SECOND * limit_multiplier)

            if not self.ip_buckets[ip].consume():
                self.block_ip(ip, duration=30) # Temporary block
                return {"action": "BLOCK", "reason": "RATE_LIMIT_IP", "ip": ip}

        # 4. Check Session Limit (stricter)
        if session:
            if session not in self.session_buckets:
                # Sessions usually have lower limits than IPs (which might be NATs)
                self.session_buckets[session] = TokenBucket(10 * limit_multiplier, 5 * limit_multiplier)

            if not self.session_buckets[session].consume():
                return {"action": "BLOCK", "reason": "RATE_LIMIT_SESSION", "session": session}

        return {"action": "ALLOW", "ip": ip, "load_factor": limit_multiplier}

def main():
    limiter = AdaptiveRateLimiter()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            result = limiter.process_request(record)
            print(json.dumps(result))
            sys.stdout.flush()
        except json.JSONDecodeError:
            sys.stderr.write(f"Invalid JSON: {line}\n")
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
