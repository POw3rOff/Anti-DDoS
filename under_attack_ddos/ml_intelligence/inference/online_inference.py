#!/usr/bin/env python3
"""
ML: Online Inference
Part of 'under_attack_ddos' Defense System.

Responsibility: Stream processing loop.
"""

import sys
import json
import logging
from ..features.flow_features import FlowFeatureExtractor
from ..models.isolation_forest import IsolationForestWrapper
from ..models.ensemble import EnsembleModel

class OnlineInference:
    def __init__(self, bridge):
        self.bridge = bridge
        self.flow_extractor = FlowFeatureExtractor()

        # Init models
        iso = IsolationForestWrapper()
        self.ensemble = EnsembleModel([iso])

    def process_event(self, event):
        # Extract features
        src_ip = event.get("source_entity")
        # Mocking packet size extraction from event data
        pkt_size = event.get("data", {}).get("len", 64)

        self.flow_extractor.update(src_ip, pkt_size)
        entropy = self.flow_extractor.calculate_entropy(src_ip)

        # Feature Vector
        features = [entropy]

        # Inference
        is_anomaly, confidence = self.ensemble.evaluate(features)

        if is_anomaly:
            self.bridge.emit_advisory(src_ip, confidence, ["Low Entropy"])

    def run_stdin(self):
        logging.info("ML Inference Engine Started...")
        for line in sys.stdin:
            try:
                event = json.loads(line)
                self.process_event(event)
            except Exception:
                pass
