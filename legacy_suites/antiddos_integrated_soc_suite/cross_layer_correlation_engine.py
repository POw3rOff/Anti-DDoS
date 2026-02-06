#!/usr/bin/env python3

class CrossLayerCorrelationEngine:
    """
    Correlaciona eventos de L3, L4 e L7 para identificar ataques complexos.
    Ex: IP fazendo port scan (L4) e depois login brute-force (L7).
    """
    def __init__(self):
        # Armazena 'suspeitas' indexadas por IP
        self.suspects = {}

    def ingest_events(self, events):
        """Processa lista de eventos normalizados e atualiza estado dos suspeitos."""
        for event in events:
            src_ip = event.get("src_ip")
            if not src_ip: continue

            if src_ip not in self.suspects:
                self.suspects[src_ip] = {"l3_score": 0, "l4_score": 0, "l7_score": 0, "last_seen": 0}

            self.suspects[src_ip]["last_seen"] = event.get("timestamp")

            # Lógica simples de correlação
            layer = event.get("layer")
            if layer == 4:
                # Ex: muitas conexões SYN_SENT ou erro
                metrics = event.get("metrics", {})
                if metrics.get("SYN_SENT", 0) > 5:
                    self.suspects[src_ip]["l4_score"] += 10
            elif layer == 7:
                # Ex: erro 404 ou 500 repetido
                status = event.get("status", 200)
                if status >= 400:
                    self.suspects[src_ip]["l7_score"] += 5
                if event.get("method") == "POST" and "login" in event.get("url", ""):
                    self.suspects[src_ip]["l7_score"] += 2 # Peso extra para login

    def get_correlated_alerts(self):
        """Retorna IPs que mostram comportamento suspeito em múltiplas camadas."""
        alerts = []
        for ip, scores in self.suspects.items():
            total_score = scores["l3_score"] + scores["l4_score"] + scores["l7_score"]
            cross_layer = (scores["l4_score"] > 0 and scores["l7_score"] > 0)

            if total_score > 50 or cross_layer:
                alerts.append({
                    "ip": ip,
                    "scores": scores,
                    "cross_layer": cross_layer,
                    "total_score": total_score
                })
        return alerts
