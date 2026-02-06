#!/usr/bin/env python3
import time
import sys

# Import Modules
from sensor_layer3_collector import SensorLayer3Collector
from sensor_layer4_collector import SensorLayer4Collector
from sensor_layer7_collector import SensorLayer7Collector
from event_normalizer import EventNormalizer
from context_enrichment_engine import ContextEnrichmentEngine
from baseline_learning_engine import BaselineLearningEngine
from cross_layer_correlation_engine import CrossLayerCorrelationEngine
from attack_classification_engine import AttackClassificationEngine
from risk_scoring_engine import RiskScoringEngine
from decision_policy_engine import DecisionPolicyEngine
from layered_mitigation_executor import LayeredMitigationExecutor
from adaptive_throttling_engine import AdaptiveThrottlingEngine
from incident_lifecycle_manager import IncidentLifecycleManager
from soc_dashboard_backend import SocDashboardBackend
from alerting_and_reporting_engine import AlertingAndReportingEngine

class AntiDDOSMasterPipeline:
    """
    Orquestrador Principal do Pipeline Anti-DDoS Integrado (SOC-Style).
    Coordena o fluxo de dados desde a coleta até a mitigação e reporte.
    """
    def __init__(self):
        print("[INIT] Initializing Anti-DDoS Pipeline Modules...")

        # 1. Sensors
        self.sensor_l3 = SensorLayer3Collector()
        self.sensor_l4 = SensorLayer4Collector()
        self.sensor_l7 = SensorLayer7Collector()

        # 2. Normalization & Enrichment
        self.normalizer = EventNormalizer()
        self.enricher = ContextEnrichmentEngine()

        # 3. Analysis
        self.baseline_engine = BaselineLearningEngine()
        self.correlation_engine = CrossLayerCorrelationEngine()
        self.classifier = AttackClassificationEngine()

        # 4. Decision
        self.risk_engine = RiskScoringEngine()
        self.policy_engine = DecisionPolicyEngine()

        # 5. Mitigation
        self.mitigation_executor = LayeredMitigationExecutor(dry_run=True)
        self.throttling_engine = AdaptiveThrottlingEngine()

        # 6. SOC
        self.incident_manager = IncidentLifecycleManager()
        self.dashboard = SocDashboardBackend()
        self.alerter = AlertingAndReportingEngine()

        print("[INIT] All modules ready.")

    def run_cycle(self):
        """Executa um ciclo completo de detecção e mitigação."""
        cycle_start = time.time()

        # --- A. COLETA ---
        raw_l3 = self.sensor_l3.collect()
        raw_l4 = self.sensor_l4.collect()
        raw_l7 = self.sensor_l7.collect()

        # --- B. NORMALIZAÇÃO ---
        events = []
        events.extend(self.normalizer.normalize(raw_l3))
        events.extend(self.normalizer.normalize(raw_l4))
        events.extend(self.normalizer.normalize(raw_l7))

        # --- C. ENRIQUECIMENTO ---
        for evt in events:
            if evt.get("src_ip"):
                self.enricher.enrich_event(evt)

        # --- D. ANÁLISE & CORRELAÇÃO ---
        # Update baseline stats (simplified)
        snapshot = {
            "l3_packets": raw_l3.get("traffic", {}).get("rx_packets", 0),
            "l4_conn": raw_l4.get("udp_connections", 0), # Simplificado
            "l7_reqs": len(raw_l7.get("events", []))
        }
        self.baseline_engine.update(snapshot)

        # Ingest events for correlation
        self.correlation_engine.ingest_events(events)
        alerts = self.correlation_engine.get_correlated_alerts()

        # --- E. DECISÃO & MITIGAÇÃO ---
        mitigated_count = 0
        for alert in alerts:
            ip = alert["ip"]

            # Classify
            classification_data = self.classifier.classify(alert)

            # Score
            # Need to re-fetch context if needed, but correlation stores scores
            risk_score = self.risk_engine.calculate_risk(
                {"severity": classification_data["severity"], "scores": alert["scores"]},
                context_data=self.enricher.enrich_event({"src_ip": ip}).get("enrichment")
            )

            # Decision
            decision = self.policy_engine.decide(risk_score, {"ip": ip})

            # Execute
            result = self.mitigation_executor.execute_decision(decision, ip)
            if decision["action"] != "NONE":
                print(f"[ACTION] {ip}: {result}")
                mitigated_count += 1

                # Update SOC Incident
                incident = self.incident_manager.create_or_update_incident({
                    "classification": classification_data["classification"],
                    "severity": classification_data["severity"]
                }, ip)

                # Alert
                if incident["status"] == "Open":
                    self.alerter.send_alert(incident)

        # --- F. SOC & MANUTENÇÃO ---
        resolved_count = self.incident_manager.check_resolutions()
        if resolved_count > 0:
            print(f"[SOC] Resolved {resolved_count} incidents.")

        self.dashboard.update_dashboard({
            "active_incidents_count": self.incident_manager.get_active_count(),
            "mitigated_count": mitigated_count,
            "throughput": snapshot
        })

        duration = time.time() - cycle_start
        # print(f"[CYCLE] Completed in {duration:.3f}s. Analyzed {len(events)} events. Active Incidents: {self.incident_manager.get_active_count()}")

    def start(self):
        print("[START] Starting Pipeline Loop (Press Ctrl+C to stop)...")
        try:
            while True:
                self.run_cycle()
                time.sleep(2) # 2 segundos entre ciclos
        except KeyboardInterrupt:
            print(chr(10) + "[STOP] Pipeline stopping...")
            print(self.alerter.generate_daily_report(self.incident_manager.history))

if __name__ == "__main__":
    pipeline = AntiDDOSMasterPipeline()
    pipeline.start()
