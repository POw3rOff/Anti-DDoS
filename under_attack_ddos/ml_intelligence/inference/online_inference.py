#!/usr/bin/env python3
"""
ML: Online Inference
Part of 'under_attack_ddos' Defense System.

Responsibility: Stream processing loop.
"""

import sys
import json
import logging
import time
from datetime import datetime
from ml_intelligence.features.flow_features import FlowFeatureExtractor
from ml_intelligence.features.spatial_features import SpatialFeatureExtractor
from ml_intelligence.models.isolation_forest import IsolationForestWrapper
from ml_intelligence.models.ensemble import EnsembleModel
from ml_intelligence.bridge.ml_to_orchestrator import MLBridge

class OnlineInference:
    def __init__(self, bridge, echo=False):
        self.bridge = bridge
        self.echo = echo
        self.flow_extractor = FlowFeatureExtractor()
        self.spatial_extractor = SpatialFeatureExtractor()
        self.running = True

        # Init models
        iso = IsolationForestWrapper()
        self.ensemble = EnsembleModel([iso])
        
        # IP history for spatial analysis
        self.recent_ips = []
        self.max_ip_history = 1000

    def process_event(self, event):
        if self.echo:
            print(json.dumps(event))
            sys.stdout.flush()

        # Extract features
        src_ip = event.get("source_entity")
        if not src_ip or src_ip == "global": return

        # Track IP distribution
        self.recent_ips.append(src_ip)
        if len(self.recent_ips) > self.max_ip_history:
            self.recent_ips.pop(0)

        # Mocking packet size extraction from event data
        data = event.get("data", {})
        pkt_size = data.get("len", data.get("pps_observed", 64)) 
        ts = event.get("timestamp")
        
        # Convert timestamp to epoch
        epoch = time.time()
        if ts:
            try:
                epoch = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
            except ValueError:
                pass

        self.flow_extractor.update(src_ip, pkt_size, epoch)
        features = self.flow_extractor.calculate_features(src_ip)
        
        # Inference
        is_anomaly, model_conf = self.ensemble.evaluate(features)
        
        # Spatial Check (Subnet Proximity)
        # We look at the distribution of the last N IPs seen globally
        proximity = self.spatial_extractor.calculate_subnet_proximity(self.recent_ips)
        spatial_bonus = 0.0
        if proximity > 0.4: # >40% of traffic from same /24
            spatial_bonus = 0.15

        entropy, variance, jitter = features
        total_confidence = min(1.0, model_conf + spatial_bonus)

        if is_anomaly or total_confidence > 0.85:
            reasons = []
            if entropy < 0.05: reasons.append("Fixed Packet Size (Low Entropy)")
            if jitter < 0.001: reasons.append("Robotic Heartbeat (Regular Intervals)")
            if model_conf > 0.7: reasons.append("Statistical Flow Anomaly")
            if proximity > 0.4: reasons.append(f"Subnet Campaign Detected (Prox: {round(proximity,2)})")
            
            self.bridge.emit_advisory(src_ip, total_confidence, reasons)

    def run_stdin(self):
        logging.info("ML Inference Engine Started...")
        for line in sys.stdin:
            if not self.running: break
            try:
                event = json.loads(line)
                self.process_event(event)
            except Exception as e:
                logging.debug(f"Inference error: {e}")

    def stop(self):
        self.running = False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ML Online Inference")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")
    parser.add_argument("--echo", action="store_true", help="Echo input events to STDOUT (for piping)")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format='%(asctime)s [%(levelname)s] %(message)s')
    
    bridge = MLBridge()
    inference = OnlineInference(bridge, echo=args.echo)
    inference.run_stdin()

if __name__ == "__main__":
    main()
