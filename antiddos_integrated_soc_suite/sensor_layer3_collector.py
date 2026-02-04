#!/usr/bin/env python3
import time
import subprocess
import re

class SensorLayer3Collector:
    """
    Coleta métricas de Layer 3 (IP, ICMP) diretamente do sistema.
    """
    def __init__(self):
        self.interface = "eth0" # Pode ser parametrizado
        self.history = []

    def get_icmp_metrics(self):
        """Lê /proc/net/snmp para obter estatísticas ICMP globais."""
        metrics = {}
        try:
            with open("/proc/net/snmp", "r") as f:
                for line in f:
                    if line.startswith("Icmp:"):
                        parts = line.split()
                        # Simples parsing de campos básicos, ajustável conforme necessidade
                        if parts[1].isdigit(): # Linha de valores
                            metrics["InMsgs"] = int(parts[1])
                            metrics["InErrors"] = int(parts[2])
                            metrics["InDestUnreach"] = int(parts[3])
                            metrics["InEchoReps"] = int(parts[6])
                            metrics["InEchos"] = int(parts[8])
        except FileNotFoundError:
            # Fallback para ambiente de teste que não seja Linux
            metrics = {"InMsgs": 0, "InErrors": 0, "InEchos": 0}
        return metrics

    def get_traffic_stats(self):
        """Lê /proc/net/dev para tráfego bruto."""
        stats = {}
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    if self.interface in line:
                        data = line.split(":")[1].split()
                        stats["rx_bytes"] = int(data[0])
                        stats["rx_packets"] = int(data[1])
                        stats["tx_bytes"] = int(data[8])
                        stats["tx_packets"] = int(data[9])
                        break
        except (FileNotFoundError, IndexError):
            stats = {"rx_bytes": 0, "rx_packets": 0, "tx_bytes": 0, "tx_packets": 0}
        return stats

    def collect(self):
        """Retorna um snapshot dos eventos L3."""
        data = {
            "layer": 3,
            "timestamp": time.time(),
            "icmp": self.get_icmp_metrics(),
            "traffic": self.get_traffic_stats()
        }
        return data

if __name__ == "__main__":
    sensor = SensorLayer3Collector()
    print(sensor.collect())
