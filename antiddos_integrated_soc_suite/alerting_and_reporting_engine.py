#!/usr/bin/env python3
import datetime

class AlertingAndReportingEngine:
    """
    Motor de notificação e alertas para o SOC.
    """
    def send_alert(self, incident, channel="console"):
        """
        Envia alerta sobre incidente.
        """
        timestamp = datetime.datetime.fromtimestamp(incident.get("start_time", 0)).strftime('%Y-%m-%d %H:%M:%S')
        severity = incident.get("severity", "INFO")
        msg = (
            f"[{severity}] ALERT - Incident {incident.get('id')} "
            f"detected on {incident.get('ip')} at {timestamp}. "
            f"Type: {incident.get('classification')}"
        )

        if channel == "console":
            print(f"[91m{msg}[0m") # Red text
        elif channel == "syslog":
            # Simulação de syslog
            pass
        elif channel == "email":
            # Simulação de envio
            pass

        return msg

    def generate_daily_report(self, history):
        """Gera relatório textual de incidentes passados."""
        report = "--- Daily Anti-DDoS Report ---" + chr(10)
        report += f"Total Incidents: {len(history)}" + chr(10)
        for inc in history:
            report += f" - [{inc['id']}] {inc['ip']}: {inc['classification']} (Duration: {inc.get('end_time',0) - inc['start_time']:.1f}s)" + chr(10)
        return report
