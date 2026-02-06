#!/usr/bin/env python3
"""
websocket_flood_protector.py
Layer 7 Anti-DDoS Script: Detects WebSocket floods.

Purpose:
Analyzes WebSocket traffic logs (Connect, Message, Disconnect events) to detect:
1. Connection Floods (Handshake spam).
2. Message Floods (Too many frames per second).
3. Payload Abuse (Large payloads).

Usage:
    python3 websocket_flood_protector.py < ws_logs.json

Input Format:
    {"event": "CONNECT|MESSAGE|DISCONNECT", "ip": "...", "session_id": "...", "timestamp": ..., "payload_size": ...}
"""

import sys
import json
import time
from collections import defaultdict, deque

# Configuration
MAX_CONN_RATE = 5          # Connections per second per IP
MAX_MSG_RATE = 20          # Messages per second per session
MAX_PAYLOAD_SIZE = 65536   # 64KB max payload regular

class WebSocketMonitor:
    def __init__(self):
        # ip -> deque of connect timestamps
        self.conn_history = defaultdict(lambda: deque(maxlen=10))
        # session -> deque of message timestamps
        self.msg_history = defaultdict(lambda: deque(maxlen=50))
        self.active_sessions = set()

    def process_event(self, record):
        event = record.get("event")
        ip = record.get("ip")
        session = record.get("session_id")
        timestamp = record.get("timestamp", time.time())
        size = record.get("payload_size", 0)

        alerts = []

        if event == "CONNECT":
            self.active_sessions.add(session)
            # Check Connection Rate
            self.conn_history[ip].append(timestamp)
            if len(self.conn_history[ip]) >= MAX_CONN_RATE:
                duration = self.conn_history[ip][-1] - self.conn_history[ip][0]
                if duration < 1.0: # X connections in < 1 second
                    alerts.append(f"WS Connection Flood: {len(self.conn_history[ip])} conns in {duration:.2f}s from {ip}")

        elif event == "MESSAGE":
            if session not in self.active_sessions:
                # Zombie message or missed connect event
                pass

            # Check Payload Size
            if size > MAX_PAYLOAD_SIZE:
                alerts.append(f"WS Large Payload: {size} bytes from {ip}")

            # Check Message Rate
            self.msg_history[session].append(timestamp)
            if len(self.msg_history[session]) >= MAX_MSG_RATE:
                duration = self.msg_history[session][-1] - self.msg_history[session][0]
                if duration < 1.0:
                    alerts.append(f"WS Message Flood: {len(self.msg_history[session])} msgs in {duration:.2f}s from session {session}")

        elif event == "DISCONNECT":
            if session in self.active_sessions:
                self.active_sessions.remove(session)

        if alerts:
            return {
                "ip": ip,
                "session_id": session,
                "verdict": "ABUSE",
                "alerts": alerts
            }
        return None

def main():
    monitor = WebSocketMonitor()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            result = monitor.process_event(record)
            if result:
                print(json.dumps(result))
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
