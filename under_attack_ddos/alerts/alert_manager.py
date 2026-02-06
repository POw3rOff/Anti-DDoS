#!/usr/bin/env python3
"""
Alert Manager for under_attack_ddos system.
Part of Phase 7: Orchestration & Observability.

Responsibility: Consumes critical events and routes them to notification channels.
"""

import logging
import json
import time
import os
from datetime import datetime, timezone
from collections import deque
from intelligence.enrichment import GeoIPEnricher
try:
    import requests
except ImportError:
    requests = None

class AlertManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.alert_log = "logs/alerts.log"
        os.makedirs(os.path.dirname(self.alert_log), exist_ok=True)
        self.history = deque(maxlen=100)
        self.dedup_window = 60 # seconds
        self.last_alerts = {} # {alert_key: timestamp}
        self.enricher = GeoIPEnricher()
        self.discord_url = self.config.get("discord_webhook_url", "")

    def process_event(self, event):
        """Processes an event and triggers alerts if it meets severity criteria."""
        severity = event.get("severity", "INFO")
        event_type = event.get("type", event.get("event", "unknown"))
        
        # Enrich IP Context
        target_ip = event.get("target_entity")
        if target_ip and target_ip != "global":
            enrichment = self.enricher.enrich(target_ip)
            if enrichment.get("country") != "Unknown":
                event["context"] = enrichment

        # We only alert on MEDIUM, HIGH, CRITICAL or specific event types
        if severity not in ["MEDIUM", "HIGH", "CRITICAL"] and event_type not in ["state_change", "mitigation_directive", "ml_advisory"]:
            return

        # Deduplication key
        dedup_key = f"{event_type}:{event.get('target_entity', 'global')}"
        now = time.time()
        
        if dedup_key in self.last_alerts:
            if now - self.last_alerts[dedup_key] < self.dedup_window:
                return # Silent drop

        self.last_alerts[dedup_key] = now
        self._trigger_alert(event)

    def _trigger_alert(self, event):
        """Routes the alert to configured channels."""
        alert_msg = self._format_alert(event)
        
        # 1. Log to alert-specific file
        try:
            with open(self.alert_log, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logging.error(f"Failed to write to alert log: {e}")

        # 2. Log to system logs
        logging.warning(f"ALERT TRIGGERED: {alert_msg}")

        # 3. Send to Discord
        if self.discord_url and requests:
            self._send_discord_alert(event, alert_msg)

        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "msg": alert_msg,
            "severity": event.get("severity", "INFO")
        })

    def _format_alert(self, event):
        """Creates a human-readable alert message."""
        etype = event.get("type", event.get("event", "unknown"))
        target = event.get("target_entity", event.get("source_entity", "global"))
        
        if etype == "state_change":
            return f"SYSTEM STATE CHANGE: {event.get('state')} (Score: {event.get('score')})"
        elif etype == "mitigation_directive":
            return f"MITIGATION ACTIVE: {event.get('action')} on {target} ({event.get('justification')})"
        elif etype == "ml_advisory":
            return f"ML ANOMALY DETECTED: {target} (Confidence: {event.get('confidence')})"
        
        return f"CRITICAL EVENT [{etype}] on {target}" + self._format_enrichment(event)

    def _format_enrichment(self, event):
        ctx = event.get("context", {})
        if not ctx: return ""
        return f" [{ctx.get('country', '??')} {ctx.get('asn', '')}]"

    def get_recent_alerts(self, limit=5):
        return list(self.history)[-limit:]

    def _send_discord_alert(self, event, formatted_msg):
        """Sends a rich embed to Discord."""
        try:
            severity = event.get("severity", "INFO")
            color = 0x00ff41 # Green (Info)
            
            if severity == "MEDIUM":
                color = 0xffaa00 # Orange
            elif severity in ["HIGH", "CRITICAL", "ESCALATED", "UNDER_ATTACK"]:
                color = 0xff0000 # Red
            
            payload = {
                "username": "UAD SENTINEL",
                "avatar_url": "https://i.imgur.com/4M34hi2.png",
                "embeds": [{
                    "title": f"🚨 {severity} ALERT",
                    "description": formatted_msg,
                    "color": color,
                    "fields": [
                        {"name": "Target", "value": event.get("target_entity", "N/A"), "inline": True},
                        {"name": "Type", "value": event.get("type", "Unknown"), "inline": True},
                        {"name": "Timestamp", "value": datetime.now().strftime("%H:%M:%S UTC"), "inline": True}
                    ],
                    "footer": {"text": "Under Attack DDoS Protection System"}
                }]
            }
            
            requests.post(self.discord_url, json=payload, timeout=2)
        except Exception as e:
            logging.error(f"Discord Alert Failed: {e}")
