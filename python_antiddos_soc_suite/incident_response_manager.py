import time
import json
import uuid

class IncidentResponseManager:
    def __init__(self):
        self.active_incidents = {}
        self.incident_history = []

    def create_incident(self, trigger_type, description, severity):
        incident_id = str(uuid.uuid4())
        incident = {
            'id': incident_id,
            'start_time': time.time(),
            'status': 'OPEN',
            'trigger': trigger_type,
            'description': description,
            'severity': severity,
            'mitigations': []
        }
        self.active_incidents[incident_id] = incident
        return incident_id

    def log_mitigation(self, incident_id, action, target):
        if incident_id in self.active_incidents:
            self.active_incidents[incident_id]['mitigations'].append({
                'timestamp': time.time(),
                'action': action,
                'target': target
            })

    def close_incident(self, incident_id, resolution_notes):
        if incident_id in self.active_incidents:
            incident = self.active_incidents.pop(incident_id)
            incident['end_time'] = time.time()
            incident['status'] = 'CLOSED'
            incident['resolution'] = resolution_notes
            self.incident_history.append(incident)
            return incident
        return None

    def get_active_incidents(self):
        return list(self.active_incidents.values())

if __name__ == "__main__":
    manager = IncidentResponseManager()
    id = manager.create_incident("Anomaly", "Spike in traffic", "HIGH")
    print(f"Created incident: {id}")
    manager.log_mitigation(id, "BLOCK", "1.2.3.4")
    print(manager.get_active_incidents())