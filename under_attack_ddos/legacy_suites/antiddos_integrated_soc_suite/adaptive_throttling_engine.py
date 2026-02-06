#!/usr/bin/env python3

class AdaptiveThrottlingEngine:
    """
    Gerencia estados de degradação progressiva (Rate Limits dinâmicos).
    """
    def __init__(self):
        self.throttle_state = {}

    def get_dynamic_limit(self, ip, current_risk):
        """
        Calcula o limite de requisições permitido baseado no risco atual.
        Risco alto = limite baixo.
        """
        base_limit_rps = 100

        if current_risk > 80:
            return 1 # RPS extremamente restrito
        elif current_risk > 50:
            return 10
        elif current_risk > 20:
            return 50

        return base_limit_rps

    def check_limit(self, ip, current_risk, current_rps):
        """Verifica se o IP excedeu seu limite dinâmico."""
        limit = self.get_dynamic_limit(ip, current_risk)
        exceeded = current_rps > limit

        return {
            "ip": ip,
            "limit_rps": limit,
            "current_rps": current_rps,
            "exceeded": exceeded
        }
