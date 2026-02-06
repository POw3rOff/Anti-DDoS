#!/usr/bin/env python3
"""
ML: Online Inference
Part of 'under_attack_ddos' Defense System.

Responsibility: Stream processing loop.
"""

import sys
import json
import logging
from ml_intelligence.features.flow_features import FlowFeatureExtractor
from ml_intelligence.models.isolation_forest import IsolationForestWrapper
from ml_intelligence.models.ensemble import EnsembleModel
from ml_intelligence.bridge.ml_to_orchestrator import MLBridge

class OnlineInference:
    def __init__(self, bridge):
        self.bridge = bridge
        self.flow_extractor = FlowFeatureExtractor()
        self.running = True

        # Init models
        iso = IsolationForestWrapper()
        self.ensemble = EnsembleModel([iso])

    def process_event(self, event):
        # Extract features
        src_ip = event.get("source_entity")
        if not src_ip or src_ip == "global": return

        # Mocking packet size extraction from event data
        data = event.get("data", {})
        pkt_size = data.get("len", data.get("pps_observed", 64)) 
        ts = event.get("timestamp")
        
        # Convert timestamp to epoch if possible
        epoch = None
        if ts:
            try:
                epoch = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
            except ValueError:
                epoch = time.time()

        self.flow_extractor.update(src_ip, pkt_size, epoch)
        features = self.flow_extractor.calculate_features(src_ip)
        logging.debug(f"IP: {src_ip} Features: {features}")

        # Inference
        is_anomaly, confidence = self.ensemble.evaluate(features)
        logging.debug(f"IP: {src_ip} IsAnomaly: {is_anomaly} Conf: {confidence}")

        if is_anomaly:
            reasons = []
            entropy, variance, jitter = features
            if entropy < 0.05: reasons.append("Fixed Packet Size (Low Entropy)")
            if jitter < 0.001: reasons.append("Robotic Heartbeat (Low Jitter)")
            if variance > 1.0: reasons.append("Pulse Wave Pattern (High Variance)")
            
            self.bridge.emit_advisory(src_ip, confidence, reasons)

    def run_stdin(self):
        logging.info("ML Inference Engine Started...")
        for line in sys.stdin:
            if not self.running: break
            try:
                event = json.loads(line)
                self.process_event(event)
            except Exception:
                pass

    def stop(self):
        self.running = False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ML Online Inference")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format='%(asctime)s [%(levelname)s] %(message)s')
    
    bridge = MLBridge()
    inference = OnlineInference(bridge)
    inference.run_stdin()

if __name__ == "__main__":
    main()
