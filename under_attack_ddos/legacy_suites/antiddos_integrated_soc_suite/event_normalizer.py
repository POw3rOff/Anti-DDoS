#!/usr/bin/env python3
import time
import json

class EventNormalizer:
    """
    Normaliza eventos brutos de diferentes layers para um formato padrão JSON.
    """
    def __init__(self):
        pass

    def normalize(self, raw_data):
        """
        Recebe dados brutos (dict) e retorna lista de eventos normalizados.
        Formato padrão:
        {
            "event_id": str,
            "timestamp": float,
            "layer": int,
            "src_ip": strOrNone,
            "type": str,
            "metrics": dict,
            "raw": dict
        }
        """
        normalized_events = []
        layer = raw_data.get("layer", 0)
        ts = raw_data.get("timestamp", time.time())

        if layer == 3:
            # L3 é agregado, geralmente não tem IP por pacote neste sensor simples
            # Gera um evento de estatística
            normalized_events.append({
                "event_id": f"L3-{ts}",
                "timestamp": ts,
                "layer": 3,
                "src_ip": None,
                "type": "traffic_stats",
                "metrics": raw_data.get("icmp", {}),
                "traffic_raw": raw_data.get("traffic", {})
            })

        elif layer == 4:
            # L4 também é agregado neste modelo (ss/netstat)
            normalized_events.append({
                "event_id": f"L4-{ts}",
                "timestamp": ts,
                "layer": 4,
                "src_ip": None,
                "type": "connection_stats",
                "metrics": raw_data.get("tcp_states", {}),
                "udp_count": raw_data.get("udp_connections", 0)
            })

        elif layer == 7:
            # L7 tem lista de eventos individuais
            for evt in raw_data.get("events", []):
                normalized_events.append({
                    "event_id": f"L7-{ts}-{evt.get('src_ip')}",
                    "timestamp": evt.get("timestamp", ts),
                    "layer": 7,
                    "src_ip": evt.get("src_ip"),
                    "type": "http_request",
                    "method": evt.get("method"),
                    "url": evt.get("url"),
                    "status": evt.get("status"),
                    "user_agent": evt.get("user_agent")
                })

        return normalized_events
