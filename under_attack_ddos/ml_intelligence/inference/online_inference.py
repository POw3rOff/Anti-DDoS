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
import os
import signal
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
        self.iso_wrapper = IsolationForestWrapper()
        
        # Persistence: Load history
        self.state_file = os.path.join(os.path.dirname(__file__), "ml_state.json")
        if self.iso_wrapper.load_state(self.state_file):
             logging.info(f"Loaded ML baseline history from {self.state_file}")

        self.ensemble = EnsembleModel([self.iso_wrapper])

        # Signal Handling for Graceful Shutdown
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        signal.signal(signal.SIGINT, self._shutdown_handler)

    def _shutdown_handler(self, signum, frame):
        logging.info("Stopping Inference Engine...")
        self.iso_wrapper.save_state(self.state_file)
        self.stop()
        sys.exit(0)
        
        # IP history for spatial analysis
        self.recent_ips = []
        self.max_ip_history = 1000

    def process_event(self, event):
        if self.echo:
            print(json.dumps(event))
            sys.stdout.flush()

        try:
            # Extract features
            # Support both 'source_entity' (standard) and 'ip' (some sensors)
            src_ip = event.get("source_entity", event.get("ip"))
            if not src_ip or src_ip == "global": return

            # Track IP distribution for spatial analysis
            self.recent_ips.append(src_ip)
            if len(self.recent_ips) > self.max_ip_history:
                self.recent_ips.pop(0)

            # Extract data metrics
            data = event.get("data", {})
            # Determine packet size or use a default
            pkt_size = data.get("len", data.get("pps_observed", 64)) 
            
            # Handle potential string values in JSON metrics
            if isinstance(pkt_size, str):
                try: pkt_size = int(pkt_size)
                except: pkt_size = 64

            # Timestamp extraction
            ts = event.get("timestamp")
            epoch = time.time()
            if ts:
                try:
                    # Handle Z suffix for UTC
                    if ts.endswith('Z'):
                        ts = ts.replace('Z', '+00:00')
                    epoch = datetime.fromisoformat(ts).timestamp()
                except (ValueError, TypeError):
                    pass

            # 1. Update Flow Stats & Calculate Features
            self.flow_extractor.update(src_ip, pkt_size, epoch)
            features = self.flow_extractor.calculate_features(src_ip)
            logging.debug(f"Features for {src_ip}: {features}")
            
            # 2. Ensemble Inference
            is_anomaly, model_conf = self.ensemble.evaluate(features)
            logging.debug(f"Is Anomaly: {is_anomaly}, Model Conf: {model_conf}")
            
            # 3. Spatial Check (Subnet Proximity)
            proximity = self.spatial_extractor.calculate_subnet_proximity(self.recent_ips)
            spatial_bonus = 0.0
            if proximity > 0.4:
                spatial_bonus = 0.15

            entropy, variance, jitter = features
            total_confidence = min(1.0, model_conf + spatial_bonus)
            logging.debug(f"Total Conf for {src_ip}: {total_confidence}")

            # 4. Final Decision & Emission
            if is_anomaly or total_confidence > 0.85:
                logging.debug(f"EMITTING ADVISORY for {src_ip}")
                reasons = []
                if entropy < 0.05: reasons.append("Fixed Packet Size (Low Entropy)")
                if jitter < 0.001: reasons.append("Robotic Heartbeat (Regular Intervals)")
                if model_conf > 0.7: reasons.append("Statistical Flow Anomaly")
                if proximity > 0.4: reasons.append(f"Subnet Campaign (Prox: {round(proximity,2)})")
                
                self.bridge.emit_advisory(src_ip, total_confidence, reasons)

        except Exception as e:
            logging.debug(f"Error processing event: {e}")

    def run_stdin(self):
        logging.info("ML Inference Engine Started...")
        while self.running:
            line = sys.stdin.readline()
            if not line: 
                logging.info("ML Engine: STDIN closed.")
                break
            try:
                event = json.loads(line)
                logging.debug(f"ML Engine: Received event for {event.get('source_entity')}")
                self.process_event(event)
                
                # Periodic Save (simple counter based)
                if int(time.time()) % 60 == 0: # Check roughly every minute (this is loose, but functional for loop)
                    pass # logic moved to cleaner place or just rely on shutdown for now to avoid IO thrashing

            except Exception as e:
                logging.error(f"ML Engine: Inference error: {e}")

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
