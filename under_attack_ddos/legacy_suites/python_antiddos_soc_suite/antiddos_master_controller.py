import time
import logging
import threading

# Import all suite components
from collector_http_logs import HTTPLogCollector
from collector_api_metrics import APIMetricsCollector
from behavior_baseline_engine import BehaviorBaselineEngine
from anomaly_detection_engine import AnomalyDetectionEngine
from bot_correlation_engine import BotCorrelationEngine
from risk_scoring_engine import RiskScoringEngine
from decision_engine import DecisionEngine
from mitigation_executor import MitigationExecutor
from incident_response_manager import IncidentResponseManager
from soc_dashboard_backend import SOCDashboardBackend
from alerting_notification_engine import AlertingNotificationEngine

class AntiDDOSMasterController:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
        self.logger = logging.getLogger("MasterController")

        # Initialize Collectors
        self.log_collector = HTTPLogCollector(simulate=True)
        self.api_collector = APIMetricsCollector()

        # Initialize Analysis Engines
        self.baseline_engine = BehaviorBaselineEngine(window_size=50)
        self.anomaly_engine = AnomalyDetectionEngine(threshold_sigma=2.5)
        self.bot_engine = BotCorrelationEngine()

        # Initialize Intelligence Engines
        self.risk_engine = RiskScoringEngine(decay_rate=0.5)
        self.decision_engine = DecisionEngine()

        # Initialize Response Engines
        self.mitigation_executor = MitigationExecutor(dry_run=True)
        self.incident_manager = IncidentResponseManager()

        # Initialize Observability
        self.alerter = AlertingNotificationEngine()
        self.dashboard = SOCDashboardBackend(port=8080)

        self.running = False

    def start(self):
        self.logger.info("Starting Anti-DDoS SOC Suite...")
        self.running = True

        # Start Dashboard
        self.dashboard.start()

        # Main Control Loop
        self.control_loop()

    def stop(self):
        self.logger.info("Stopping Anti-DDoS SOC Suite...")
        self.running = False
        self.dashboard.stop()

    def control_loop(self):
        log_generator = self.log_collector.collect()

        try:
            while self.running:
                # 1. Collection
                try:
                    log_entry = next(log_generator)
                except StopIteration:
                    break

                ip = log_entry['ip']

                # 2. Analysis
                # Update baseline with dummy RPS (calculating real RPS would require more state)
                # For simulation, we'll assume 1 req = instantaneous RPS impact
                current_rps_estimate = 10 # Mock
                self.baseline_engine.update(current_rps_estimate)

                baseline = self.baseline_engine.get_baseline()
                is_anomaly, z_score = self.anomaly_engine.detect_anomaly(
                    current_rps_estimate,
                    baseline['mean_rps'],
                    baseline['stdev_rps']
                )

                self.bot_engine.analyze_request(log_entry)

                # 3. Intelligence
                risk_points = 0
                if is_anomaly:
                    risk_points += 10

                if log_entry['status'] >= 500:
                    risk_points += 5

                # Update Risk Score
                current_score = self.risk_engine.update_score(ip, risk_points)

                # Decide Action
                action, reason = self.decision_engine.decide(ip, current_score)

                # 4. Response
                if action != 'MONITOR':
                    self.logger.warning(f"Taking action {action} on {ip} (Score: {current_score:.2f})")
                    self.mitigation_executor.execute_action(action, ip, reason)

                    # Log Incident if severe
                    if action == 'BLOCK':
                        incident_id = self.incident_manager.create_incident(
                            "High Risk IP",
                            f"Blocked {ip} due to score {current_score}",
                            "HIGH"
                        )
                        self.incident_manager.log_mitigation(incident_id, action, ip)
                        self.alerter.send_alert("WARNING", f"Mitigation Triggered: {action}", f"Applied to {ip}")

                # 5. Periodic Tasks (every ~100 requests or time interval)
                # ... (Botnet correlation checks, etc.)

                # Sleep to simulate traffic pacing
                time.sleep(0.05)

        except KeyboardInterrupt:
            self.stop()

if __name__ == "__main__":
    controller = AntiDDOSMasterController()
    try:
        controller.start()
    except KeyboardInterrupt:
        controller.stop()