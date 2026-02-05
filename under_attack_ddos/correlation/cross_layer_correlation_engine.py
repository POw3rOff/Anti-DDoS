#!/usr/bin/env python3
"""
Cross-Layer Correlation Engine
Part of Anti-DDoS/under_attack_ddos/correlation/

Responsibility: Aggregates events from L3, L4, L7, and Game layers to identify
complex attack campaigns (e.g. Multi-Vector, Distributed Botnets).
"""

import sys
import os
import json
import time
import argparse
import logging
import yaml
from collections import defaultdict, deque
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Constants & Config
# -----------------------------------------------------------------------------
SCRIPT_NAME = "cross_layer_correlation_engine"
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "correlation_rules.yaml")

# -----------------------------------------------------------------------------
# Engine Class
# -----------------------------------------------------------------------------
class CrossLayerCorrelationEngine:
    def __init__(self, config_path=None, dry_run=False):
        self.config = self._load_config(config_path)
        self.dry_run = dry_run

        # Windows
        self.micro_window = 10.0 # seconds
        self.macro_window = 300.0 # 5 minutes

        # State: {entity_key: deque([events])}
        # Entity Key can be IP (1.2.3.4) or Subnet (1.2.3.0/24)
        self.entity_buffer = defaultdict(deque)

        # Subnet Aggregation State: {subnet_cidr: score}
        self.subnet_scores = defaultdict(float)

        self._setup_logging()
        logging.info(f"Initialized {SCRIPT_NAME}. Dry-run: {dry_run}")

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def _load_config(self, path):
        path = path or DEFAULT_CONFIG_PATH
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}

    def get_subnet(self, ip):
        """Returns /24 subnet for an IP. Simplified."""
        if ":" in ip: return None # Skip IPv6 for now or implement better logic
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return None

    def ingest_line(self, line):
        try:
            if not line.strip(): return
            event = json.loads(line)

            # Normalize fields
            # We expect: timestamp, layer, event, src_ip/source_entity, severity

            src = event.get("src_ip") or event.get("source_entity")
            if not src: return

            # Skip GLOBAL events for entity correlation (but maybe use for DEFCON level)
            if src == "GLOBAL": return

            event["_recv_ts"] = time.time()

            # Add to IP buffer
            self.entity_buffer[src].append(event)
            self._correlate_entity(src)

            # Add to Subnet buffer (Simplified: just update score for now)
            subnet = self.get_subnet(src)
            if subnet:
                self._update_subnet_score(subnet, event)

        except json.JSONDecodeError:
            pass

    def _correlate_entity(self, ip):
        """Analyze IP history for Multi-Vector attacks."""
        now = time.time()
        events = self.entity_buffer[ip]

        # Prune Macro Window
        while events and (now - events[0]["_recv_ts"] > self.macro_window):
            events.popleft()

        if not events:
            del self.entity_buffer[ip]
            return

        # Check for Multi-Layer
        layers_seen = set()
        severity_sum = 0

        for e in events:
            layers_seen.add(e.get("layer", "unknown"))
            # Simple severity mapping: LOW=1, MEDIUM=5, HIGH=10, CRITICAL=20
            sev = e.get("severity", "LOW")
            score = 1
            if sev == "MEDIUM": score = 5
            elif sev == "HIGH": score = 10
            elif sev == "CRITICAL": score = 20
            severity_sum += score

        # Rule: Multi-Vector Attacker
        # If seen in > 1 layer (e.g. L4 + L7) AND severity sum > 15
        if len(layers_seen) > 1 and severity_sum > 15:
            self.emit_campaign("Multi-Vector Attacker", ip, "HIGH", {
                "layers": list(layers_seen),
                "score": severity_sum
            })
            # Clear buffer to avoid spam? Or rely on orchestrator.
            # events.clear()

    def _update_subnet_score(self, subnet, event):
        # Todo: Implement proper sliding window for subnets.
        # For now, just a placeholder.
        pass

    def emit_campaign(self, campaign_type, target, confidence, details):
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "campaign_alert",
            "campaign_name": campaign_type,
            "target_entity": target,
            "confidence": confidence,
            "details": details,
            "data": {
                "status": "simulated" if self.dry_run else "active"
            }
        }
        print(json.dumps(alert))
        sys.stdout.flush()
        logging.warning(f"CAMPAIGN: {campaign_type} against {target} (Conf: {confidence})")

    def run(self):
        logging.info("Starting Correlation Engine (reading STDIN)...")
        try:
            for line in sys.stdin:
                self.ingest_line(line)
        except KeyboardInterrupt:
            logging.info("Stopping...")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Cross-Layer Correlation Engine")
    parser.add_argument("--config", help="Path to correlation_rules.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Simulate alerts")

    args = parser.parse_args()

    engine = CrossLayerCorrelationEngine(args.config, args.dry_run)
    engine.run()

if __name__ == "__main__":
    main()
