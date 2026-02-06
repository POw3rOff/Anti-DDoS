#!/usr/bin/env python3
import time
import subprocess
import os

class SensorLayer4Collector:
    """
    Coleta métricas de Layer 4 (TCP/UDP) analisando conexões ativas.
    """
    def __init__(self):
        pass

    def get_tcp_states(self):
        """Conta estados TCP (SYN_RECV, ESTABLISHED, etc.) usando ss ou /proc."""
        states = {
            "ESTABLISHED": 0,
            "SYN_SENT": 0,
            "SYN_RECV": 0,
            "FIN_WAIT1": 0,
            "FIN_WAIT2": 0,
            "TIME_WAIT": 0,
            "CLOSE": 0,
            "CLOSE_WAIT": 0,
            "LAST_ACK": 0,
            "LISTEN": 0,
            "CLOSING": 0,
            "UNKNOWN": 0
        }

        # Tentativa via /proc/net/tcp para ser dependency-free e rápido
        try:
            with open("/proc/net/tcp", "r") as f:
                next(f) # Skip header
                for line in f:
                    parts = line.strip().split()
                    st = parts[3]
                    # Mapping hex states to standard names
                    # 01: ESTABLISHED, 02: SYN_SENT, 03: SYN_RECV, etc.
                    state_map = {
                        '01': 'ESTABLISHED', '02': 'SYN_SENT', '03': 'SYN_RECV',
                        '04': 'FIN_WAIT1', '05': 'FIN_WAIT2', '06': 'TIME_WAIT',
                        '07': 'CLOSE', '08': 'CLOSE_WAIT', '09': 'LAST_ACK',
                        '0A': 'LISTEN', '0B': 'CLOSING'
                    }
                    state_name = state_map.get(st, "UNKNOWN")
                    states[state_name] += 1
        except FileNotFoundError:
            # Fallback simulado para desenvolvimento
            pass

        return states

    def get_udp_count(self):
        """Conta conexões UDP."""
        count = 0
        try:
            with open("/proc/net/udp", "r") as f:
                next(f) # Skip header
                count = sum(1 for _ in f)
        except FileNotFoundError:
            pass
        return count

    def collect(self):
        """Retorna snapshot de eventos L4."""
        data = {
            "layer": 4,
            "timestamp": time.time(),
            "tcp_states": self.get_tcp_states(),
            "udp_connections": self.get_udp_count()
        }
        return data

if __name__ == "__main__":
    sensor = SensorLayer4Collector()
    print(sensor.collect())
