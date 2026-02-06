#!/usr/bin/env python3

class DecisionPolicyEngine:
    """
    Toma a decisão final de mitigação com base no Risco e Políticas.
    """
    def decide(self, risk_score, entity_info):
        """
        Retorna a ação recomendada: 'BLOCK', 'THROTTLE', 'CHALLENGE', 'LOG', 'NONE'
        """

        # Regra de ouro: Whitelist (risco muito baixo ou forçado a 0)
        if risk_score <= 10:
            return {"action": "NONE", "reason": "Low Risk"}

        # Níveis de mitigação progressiva
        if risk_score >= 90:
            return {"action": "BLOCK", "duration": 3600, "reason": "Critical Risk"}

        if risk_score >= 70:
            return {"action": "BLOCK", "duration": 300, "reason": "High Risk"}

        if risk_score >= 50:
            return {"action": "CHALLENGE", "type": "JS_Challenge", "reason": "Medium Risk"}

        if risk_score >= 30:
            return {"action": "THROTTLE", "rate": "1r/s", "reason": "Low-Medium Risk"}

        return {"action": "LOG", "reason": "Observation"}
