#!/usr/bin/env python3
import time
import uuid

class IncidentLifecycleManager:
    """
    Gere o ciclo de vida dos incidentes (Open -> Mitigating -> Resolved).
    """
    def __init__(self):
        self.active_incidents = {}
        self.history = []

    def create_or_update_incident(self, attack_data, ip):
        """Cria novo incidente ou atualiza existente para o IP alvo."""
        if ip in self.active_incidents:
            incident = self.active_incidents[ip]
            incident["last_update"] = time.time()
            incident["status"] = "Mitigating"
            # Atualiza severidade se piorou
            return incident

        # Novo Incidente
        incident_id = str(uuid.uuid4())[:8]
        incident = {
            "id": incident_id,
            "ip": ip,
            "start_time": time.time(),
            "last_update": time.time(),
            "classification": attack_data.get("classification", "Unknown"),
            "severity": attack_data.get("severity", "Low"),
            "status": "Open"
        }
        self.active_incidents[ip] = incident
        return incident

    def check_resolutions(self, timeout=60):
        """Fecha incidentes que não tiveram atividade recente."""
        now = time.time()
        resolved_ips = []

        for ip, inc in self.active_incidents.items():
            if now - inc["last_update"] > timeout:
                inc["status"] = "Resolved"
                inc["end_time"] = now
                self.history.append(inc)
                resolved_ips.append(ip)

        for ip in resolved_ips:
            del self.active_incidents[ip]

        return len(resolved_ips)

    def get_active_count(self):
        return len(self.active_incidents)
