#!/usr/bin/env python3
"""
Intelligence & Decision Engine
Part of 'under_attack_ddos' Defense System.

Responsibility: Calculates Global Risk Score (GRS), manages defense states, 
evaluates confidence, and generates mitigation directives.
"""

import time
import logging
from datetime import datetime, timezone
from collections import defaultdict

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "intelligence_engine"
LAYER = "intelligence"

class IntelligenceEngine:
    def __init__(self, config):
        self.config = config.get("orchestrator", {})
        self.weights = self.config.get("weights", {
            "layer3": 0.4,
            "layer4": 0.3,
            "layer7": 0.3,
            "layer_game": 0.5,
            "correlation": 1.0
        })
        self.thresholds = self.config.get("thresholds", {
            "normal": {"max": 29},
            "monitor": {"min": 30, "max": 59},
            "under_attack": {"min": 60, "max": 89},
            "escalated": {"min": 90}
        })
        self.cross_layer_multiplier = self.config.get("cross_layer_multiplier", 1.5)
        self.cooldown_seconds = self.config.get("cooldown_seconds", 300)

        self.current_state = "NORMAL"
        self.last_attack_time = 0
        self.grs_score = 0.0

    def calculate_grs(self, source_events, active_campaigns):
        """
        Calculates Global Risk Score based on event density and campaigns.
        
        :param source_events: Dict {ip: [events...]}
        :param active_campaigns: List of campaign objects
        :return: (grs, active_sources, active_layers)
        """
        total_score = 0.0
        active_sources = []
        global_active_layers = set()

        for src, events in source_events.items():
            if not events: continue

            src_score = 0.0
            layers_seen = set()

            for e in events:
                layer = e.get("layer", "unknown")
                severity = e.get("severity", "LOW")

                # Base score mapping
                base_val = 10
                if severity == "MEDIUM": base_val = 30
                elif severity == "HIGH": base_val = 60
                elif severity == "CRITICAL": base_val = 90

                weight = self.weights.get(layer, 0.1)
                src_score += (base_val * weight)
                layers_seen.add(layer)
                global_active_layers.add(layer)

            # Cross-layer multiplier for this specific source
            if len(layers_seen) > 1:
                src_score *= self.cross_layer_multiplier

            src_score = min(src_score, 100.0)
            total_score = max(total_score, src_score)

            if src_score > 30:
                active_sources.append({
                    "ip": src, 
                    "score": round(src_score, 1),
                    "layers": list(layers_seen)
                })

        # Campaign alerts boost total score significantly
        if active_campaigns:
            for camp in active_campaigns:
                global_active_layers.add("correlation")
                if camp.get("confidence") == "HIGH":
                    total_score = max(total_score, 95.0)
                else:
                    total_score = max(total_score, 80.0)

        self.grs_score = round(total_score, 1)
        return self.grs_score, active_sources, global_active_layers

    def determine_state(self, grs):
        """Maps GRS to operational state with hysteresis."""
        now = time.time()
        new_state = self._map_score_to_state(grs)

        # Update last attack time if score is significant
        if grs >= 60:
            self.last_attack_time = now

        # Cooldown period check: Don't revert to NORMAL too quickly
        if new_state == "NORMAL" and self.current_state != "NORMAL":
            if (now - self.last_attack_time) < self.cooldown_seconds:
                return self.current_state # Hold present state

        if new_state != self.current_state:
            old_state = self.current_state
            self.current_state = new_state
            logging.info(f"STATE TRANSITION: {old_state} -> {new_state} (GRS: {grs})")
            return new_state

        return None

    def generate_directives(self, grs, active_sources, active_campaigns):
        """Produces a list of mitigation directives."""
        directives = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Global State Directive
        directives.append({
            "timestamp": now_iso,
            "type": "state_change",
            "state": self.current_state,
            "score": grs,
            "confidence": "HIGH" if grs > 60 else "MEDIUM"
        })

        # 2. Targeted Mitigation Directives (High Confidence Only)
        for src in active_sources:
            # We block if score is high or if we are in critical defense modes
            is_critical_state = self.current_state in ["UNDER_ATTACK", "ESCALATED"]
            if src["score"] >= 80 or (is_critical_state and src["score"] >= 60):
                directives.append({
                    "timestamp": now_iso,
                    "type": "mitigation_directive",
                    "action": "block_ip",
                    "target": src["ip"],
                    "params": {"ttl": 300},
                    "justification": f"High risk score ({src['score']}) on layers {src['layers']}"
                })

        return directives

    def _map_score_to_state(self, score):
        t = self.thresholds
        if score >= t["escalated"]["min"]: return "ESCALATED"
        if score >= t["under_attack"]["min"]: return "UNDER_ATTACK"
        if score >= t["monitor"]["min"]: return "MONITOR"
        return "NORMAL"
