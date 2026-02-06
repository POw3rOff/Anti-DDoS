#!/usr/bin/env python3

class AttackClassificationEngine:
    """
    Classifica o tipo de ataque com base nos alertas correlacionados.
    """
    def classify(self, alert_data):
        """
        Recebe dados do CrossLayerCorrelationEngine e retorna classificação textual.
        """
        scores = alert_data.get("scores", {})
        l4 = scores.get("l4_score", 0)
        l7 = scores.get("l7_score", 0)

        classification = "Unknown Anomaly"
        severity = "Low"

        if l4 > 100 and l7 < 10:
            classification = "L4 Volumetric / SYN Flood"
            severity = "High"
        elif l7 > 50 and l4 < 10:
            classification = "L7 HTTP Flood / Abuse"
            severity = "Medium"
        elif l4 > 20 and l7 > 20:
            classification = "Multi-Vector Attack (Hybrid)"
            severity = "Critical"
        elif l7 > 100:
            classification = "L7 Massive Flood"
            severity = "Critical"

        return {
            "classification": classification,
            "severity": severity
        }
