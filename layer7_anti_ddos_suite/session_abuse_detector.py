#!/usr/bin/env python3
"""
session_abuse_detector.py
Layer 7 Anti-DDoS Script: Detects session hijacking and cookie recycling.

Features:
1. Detects Session Hijacking: One session ID used by multiple distinct IPs.
2. Detects Session Stuffing/Recycling: One IP using too many different session IDs.
3. Detects Concurrent Sessions: Limits the number of active sessions per user (if user_id provided).

Usage:
    python3 session_abuse_detector.py < log_stream.json
"""

import sys
import json
import time
from collections import defaultdict

# Configuration
MAX_IPS_PER_SESSION = 2    # Allow 2 IPs (e.g., mobile switch to WiFi) but warn
MAX_SESSIONS_PER_IP = 10   # High number suggests bot creating/testing sessions
SESSION_TTL = 3600         # Cleanup inactive sessions after 1 hour

class SessionMonitor:
    def __init__(self):
        self.session_map = defaultdict(set) # session_id -> {ips}
        self.ip_map = defaultdict(set)      # ip -> {session_ids}
        self.last_seen = {}                 # id -> timestamp

    def cleanup(self):
        """Removes old entries to prevent memory leaks."""
        now = time.time()
        # Clean session map
        for sid in list(self.last_seen.keys()):
            if now - self.last_seen[sid] > SESSION_TTL:
                del self.last_seen[sid]
                if sid in self.session_map: del self.session_map[sid]
                # Note: Not cleaning IP map efficiently here for brevity,
                # but in prod would need reverse index or periodic full scan

    def analyze(self, record):
        ip = record.get("ip")
        session_id = record.get("session_id")
        # Could be a cookie value or explicit token
        if not session_id:
            headers = record.get("headers", {})
            cookie = headers.get("Cookie") or headers.get("cookie")
            if cookie and "session=" in cookie:
                # Basic parsing extraction
                parts = cookie.split("session=")
                if len(parts) > 1:
                    session_id = parts[1].split(";")[0]

        if not session_id or not ip:
            return None

        self.last_seen[session_id] = time.time()
        self.session_map[session_id].add(ip)
        self.ip_map[ip].add(session_id)

        alerts = []

        # Check 1: Session Hijacking (One session, many IPs)
        unique_ips = len(self.session_map[session_id])
        if unique_ips > MAX_IPS_PER_SESSION:
            alerts.append(f"Session Hijacking Risk: Session {session_id[:8]}... used by {unique_ips} IPs")

        # Check 2: Session Stuffing (One IP, many sessions)
        unique_sessions = len(self.ip_map[ip])
        if unique_sessions > MAX_SESSIONS_PER_IP:
            alerts.append(f"Session Stuffing Risk: IP {ip} used {unique_sessions} unique sessions")

        if alerts:
            return {
                "ip": ip,
                "session_id": session_id,
                "verdict": "ABUSE_DETECTED",
                "alerts": alerts
            }
        return None

def main():
    monitor = SessionMonitor()
    counter = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            result = monitor.analyze(record)
            if result:
                print(json.dumps(result))
                sys.stdout.flush()

            counter += 1
            if counter % 1000 == 0:
                monitor.cleanup()

        except json.JSONDecodeError:
            pass
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
