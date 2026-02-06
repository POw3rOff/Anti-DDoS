#!/usr/bin/env python3

"""
packet_rate_baseline_engine.py
Layer 4 TCP/UDP Suite: Motor de Baseline de Taxa de Pacotes.

Funcionalidades:
- Monitoriza interfaces de rede via /proc/net/dev.
- Constrói uma baseline de tráfego (média móvel) para RX/TX.
- Deteta desvios súbitos (spikes) que indiquem ataques volumétricos.
- Adapta-se gradualmente a mudanças de carga legítima.
"""

import time
import argparse
import sys
import os
from collections import deque

def read_net_dev():
    """Lê /proc/net/dev e retorna {iface: {'rx_packets': int, 'tx_packets': int}}"""
    stats = {}
    path = "/proc/net/dev"
    if not os.path.exists(path):
        return stats

    try:
        with open(path, "r") as f:
            lines = f.readlines()[2:] # Skip headers
            for line in lines:
                parts = line.strip().split()
                if len(parts) < 10:
                    continue

                iface = parts[0].strip(":")
                # RX Packets é col 2 (índice 1 de parts, mas parts[0] é iface)
                # parts: ['eth0:', 'bytes', 'packets', ...]
                # Se iface tiver separada: 'eth0:', '123'... -> rx_bytes=1, rx_packets=2
                # Se 'eth0:123' -> parts[0]='eth0:123', precisa split

                # Tratamento robusto de parsing
                data_parts = parts
                if ":" in parts[0]:
                    # ex: "eth0: 123 456..."
                    # split parts[0]
                    sub = parts[0].split(":")
                    iface = sub[0]
                    if sub[1]: # se tiver numero colado "eth0:123"
                        data_parts = [sub[0], sub[1]] + parts[1:]
                    else: # "eth0: 123..."
                        data_parts = [sub[0]] + parts[1:]

                # Agora data_parts[0] é iface. data_parts[1] é rx_bytes. data_parts[2] é rx_packets.
                # tx_bytes é indice 9, tx_packets é 10.

                try:
                    rx_packets = int(data_parts[2])
                    tx_packets = int(data_parts[10])
                    stats[iface] = {'rx': rx_packets, 'tx': tx_packets}
                except (IndexError, ValueError):
                    pass
    except Exception:
        pass
    return stats

class InterfaceBaseline:
    def __init__(self, window_size=20):
        self.history_rx = deque(maxlen=window_size)
        self.history_tx = deque(maxlen=window_size)

    def update(self, rx_pps, tx_pps):
        self.history_rx.append(rx_pps)
        self.history_tx.append(tx_pps)

    def get_baseline(self):
        if not self.history_rx:
            return 0, 0
        avg_rx = sum(self.history_rx) / len(self.history_rx)
        avg_tx = sum(self.history_tx) / len(self.history_tx)
        return avg_rx, avg_tx

def main():
    parser = argparse.ArgumentParser(description="Packet Rate Baseline Engine")
    parser.add_argument("--interface", type=str, default="all", help="Interface específica para monitorar (ex: eth0)")
    parser.add_argument("--threshold", type=float, default=3.0, help="Fator de multiplicação para alerta (ex: 3.0 = 300% da média)")
    parser.add_argument("--min-pps", type=int, default=100, help="PPS mínimo para considerar desvio (evita falsos positivos em baixo tráfego)")
    args = parser.parse_args()

    print(f"[*] Iniciando Baseline Engine (Threshold: {args.threshold}x, Min PPS: {args.min_pps})")

    baselines = {} # {iface: InterfaceBaseline()}
    last_stats = {}

    # Aquecimento
    print("[*] Aguardando dados iniciais...")
    last_stats = read_net_dev()
    time.sleep(1)

    try:
        while True:
            current_stats = read_net_dev()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            alerts = []

            for iface, data in current_stats.items():
                if args.interface != "all" and iface != args.interface:
                    continue

                # Ignorar loopback
                if iface == "lo":
                    continue

                prev = last_stats.get(iface)
                if not prev:
                    continue

                rx_pps = data['rx'] - prev['rx']
                tx_pps = data['tx'] - prev['tx']

                # Get baseline stats
                if iface not in baselines:
                    baselines[iface] = InterfaceBaseline()

                bl = baselines[iface]
                avg_rx, avg_tx = bl.get_baseline()

                # Update baseline AFTER check? Or Before?
                # Se for ataque, não queremos poluir a baseline imediatamente?
                # Mas baseline deve adaptar-se.
                # Vamos atualizar sempre, mas o alerta dispara antes da atualização influenciar muito a média lenta.

                # Check deviations
                if avg_rx > args.min_pps and rx_pps > avg_rx * args.threshold:
                    alerts.append(f"Interface {iface} RX SPIKE: {rx_pps} PPS (Avg: {avg_rx:.0f})")

                if avg_tx > args.min_pps and tx_pps > avg_tx * args.threshold:
                    alerts.append(f"Interface {iface} TX SPIKE: {tx_pps} PPS (Avg: {avg_tx:.0f})")

                bl.update(rx_pps, tx_pps)

            if alerts:
                print(f"[ALERTA] {timestamp} -> {'; '.join(alerts)}")

            last_stats = current_stats
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Parando...")

if __name__ == "__main__":
    main()
