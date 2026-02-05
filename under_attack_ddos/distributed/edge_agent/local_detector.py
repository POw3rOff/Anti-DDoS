#!/usr/bin/env python3
"""
Edge Agent: Local Detector
Part of 'under_attack_ddos' Defense System.

Responsibility: Aggregates signals from local sensors (L3/L4/Game)
and produces summarized alerts for the Edge Daemon.
"""

import time
import logging

class LocalDetector:
    def __init__(self):
        self.alerts = []

    def ingest_sensor_data(self, data):
        """
        Ingests raw data from collectors (e.g. parsed from logs or queues).
        data: { 'src_ip': '...', 'pps': 50000, 'layer': 'l4' }
        """
        # Simple thresholding logic for the Edge
        if data.get('pps', 0) > 10000:
            self.alerts.append({
                "type": "volumetric_anomaly",
                "src_ip": data['src_ip'],
                "confidence": 0.9,
                "timestamp": time.time()
            })

    def get_pending_alerts(self):
        """Returns and clears pending alerts."""
        res = self.alerts[:]
        self.alerts = []
        return res
