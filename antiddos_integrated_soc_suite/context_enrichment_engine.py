#!/usr/bin/env python3
import random

class ContextEnrichmentEngine:
    """
    Adiciona contexto (GeoIP, ASN, Reputação) aos eventos normalizados.
    Em produção, usaria MaxMind GeoIP ou chamadas API externas.
    Aqui usamos dados simulados para demonstração dependency-free.
    """
    def __init__(self):
        # Cache local simples para consistência simulada
        self.ip_cache = {}

    def get_asn_info(self, ip):
        if not ip: return {}
        if ip in self.ip_cache: return self.ip_cache[ip]['asn']

        # Simulação
        asn_data = {
            "asn": f"AS{random.randint(1000, 65000)}",
            "org": random.choice(["ISP-A", "CloudProvider-B", "University-C", "Hosting-D"])
        }
        self._ensure_cache(ip)
        self.ip_cache[ip]['asn'] = asn_data
        return asn_data

    def get_geo_info(self, ip):
        if not ip: return {}
        if ip in self.ip_cache and 'geo' in self.ip_cache[ip]: return self.ip_cache[ip]['geo']

        # Simulação
        geo_data = {
            "country": random.choice(["US", "BR", "CN", "RU", "DE", "FR"]),
            "city": random.choice(["New York", "Sao Paulo", "Beijing", "Moscow", "Berlin", "Paris"])
        }
        self._ensure_cache(ip)
        self.ip_cache[ip]['geo'] = geo_data
        return geo_data

    def get_local_reputation(self, ip):
        """Consulta base interna de reputação (simulada)."""
        if not ip: return 0
        # 0 = neutro, -100 = bloqueado, +100 = whitelist
        return random.choice([0, 0, 0, -10, -50, 10])

    def _ensure_cache(self, ip):
        if ip not in self.ip_cache:
            self.ip_cache[ip] = {}

    def enrich_event(self, event):
        """Enriquece um único evento in-place."""
        ip = event.get("src_ip")
        if ip:
            event["enrichment"] = {
                "asn": self.get_asn_info(ip),
                "geo": self.get_geo_info(ip),
                "local_reputation": self.get_local_reputation(ip)
            }
        return event

if __name__ == "__main__":
    engine = ContextEnrichmentEngine()
    dummy_event = {"src_ip": "192.168.1.50", "layer": 7}
    print(engine.enrich_event(dummy_event))
