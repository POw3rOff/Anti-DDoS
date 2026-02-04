#!/usr/bin/env python3

class RiskScoringEngine:
    """
    Calcula o risco (0-100) de uma entidade (IP) baseada em múltiplos fatores.
    """
    def calculate_risk(self, alert_data, context_data=None):
        """
        alert_data: output do AttackClassificationEngine e CorrelationEngine
        context_data: output do ContextEnrichmentEngine (Geo, ASN, Reputação)
        """
        base_score = 0

        # Fator 1: Severidade do Ataque Detectado
        severity = alert_data.get("severity", "Low")
        if severity == "Critical":
            base_score += 80
        elif severity == "High":
            base_score += 60
        elif severity == "Medium":
            base_score += 40
        else:
            base_score += 10

        # Fator 2: Pontuação dos Sensores (Correlation)
        scores = alert_data.get("scores", {})
        total_sensor_score = scores.get("l3_score", 0) + scores.get("l4_score", 0) + scores.get("l7_score", 0)
        # Normaliza score dos sensores (ex: max 20 pontos extra)
        base_score += min(20, total_sensor_score / 5)

        # Fator 3: Contexto (se disponível)
        if context_data:
            reputation = context_data.get("local_reputation", 0)
            # Reputação negativa aumenta risco
            if reputation < 0:
                base_score += abs(reputation) # Se rep for -50, soma +50 no risco
            # Reputação positiva diminui risco (Whitelist)
            elif reputation > 0:
                base_score -= reputation

            geo = context_data.get("geo", {})
            # Exemplo de regra Geo: Risco maior se país desconhecido ou específico (simulação)
            if geo.get("country") == "XX":
                base_score += 20

        return min(100, max(0, base_score))
