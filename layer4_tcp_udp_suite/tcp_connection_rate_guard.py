#!/usr/bin/env python3

"""
tcp_connection_rate_guard.py
Layer 4 TCP/UDP Suite: Monitor de Taxa de Conexões TCP.

Funcionalidades:
- Monitoriza a taxa de novas conexões TCP por IP de origem.
- Deteta IPs agressivos que abrem muitas conexões num curto período.
- Suporta diferenciação por IP único.
"""

import time
import argparse
import sys
import os
import socket
import struct
from collections import defaultdict, deque

def hex_to_ip(hex_str):
    try:
        # IPv4
        if len(hex_str) == 8:
            ip_int = int(hex_str, 16)
            return socket.inet_ntoa(struct.pack("<L", ip_int))
        # IPv6 logic could be added here, returning raw hex for now to avoid complexity
        return hex_str
    except:
        return hex_str

def get_active_connections():
    """
    Retorna um set de strings únicas identificando conexões: "RemoteIP:RemotePort->LocalPort"
    """
    conns = set()
    files = ["/proc/net/tcp", "/proc/net/tcp6"]

    for fpath in files:
        if not os.path.exists(fpath):
            continue

        try:
            with open(fpath, "r") as f:
                lines = f.readlines()[1:]
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) < 4:
                        continue

                    # parts[1] = local_addr:port
                    # parts[2] = rem_addr:port
                    # parts[3] = state

                    state = parts[3]
                    # 0A is LISTEN. Ignore.
                    if state == "0A":
                        continue

                    l_addr, l_port = parts[1].split(":")
                    r_addr, r_port = parts[2].split(":")

                    remote_ip = hex_to_ip(r_addr)
                    remote_port = int(r_port, 16)
                    local_port = int(l_port, 16)

                    # Identificador único da conexão
                    conn_id = f"{remote_ip}:{remote_port}->{local_port}"

                    # Armazenamos também o IP separado para contagem
                    conns.add((conn_id, remote_ip))

        except Exception:
            pass

    return conns

def main():
    parser = argparse.ArgumentParser(description="Monitor de Taxa de Conexões TCP")
    parser.add_argument("--limit", type=int, default=10, help="Limite de novas conexões por segundo por IP (default: 10)")
    parser.add_argument("--interval", type=float, default=1.0, help="Intervalo de amostragem em segundos (default: 1.0)")
    args = parser.parse_args()

    print(f"[*] Iniciando TCP Connection Rate Guard (Limit: {args.limit} conn/s, Interval: {args.interval}s)")

    # Estado anterior: set de conn_ids
    seen_conn_ids = set()

    # Histórico de hits por IP: {ip: deque([timestamp1, timestamp2...])}
    ip_hits = defaultdict(deque)

    # Inicialização
    initial_conns = get_active_connections()
    seen_conn_ids = {c[0] for c in initial_conns}

    try:
        while True:
            time.sleep(args.interval)

            current_conns_full = get_active_connections()
            current_conn_ids = {c[0] for c in current_conns_full}

            # Novas conexões são as que estão em current mas não em seen
            new_conn_ids = current_conn_ids - seen_conn_ids

            now = time.time()

            # Processar novas conexões
            # Precisamos mapear conn_id -> ip para contar
            # Podemos reconstruir o map ou iterar current_conns_full

            # Criar map auxiliar para lookup rápido de IP das novas conexões
            conn_id_to_ip = {c[0]: c[1] for c in current_conns_full if c[0] in new_conn_ids}

            for cid in new_conn_ids:
                ip = conn_id_to_ip.get(cid)
                if ip:
                    ip_hits[ip].append(now)

            # Limpar histórico antigo (janela de 1 segundo ou interval?)
            # O limite é "conexões por segundo". Então mantemos histórico de 1s (ou args.interval se for maior?).
            # Vamos manter janela de 1 segundo deslizante.
            window = 1.0

            alerts = []

            for ip, timestamps in list(ip_hits.items()):
                # Remover timestamps antigos (> window)
                while timestamps and timestamps[0] < now - window:
                    timestamps.popleft()

                if not timestamps:
                    del ip_hits[ip]
                    continue

                count = len(timestamps)
                if count > args.limit:
                    alerts.append(f"IP {ip} excedeu limite: {count} novas conexões/s")

            if alerts:
                timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
                for alert in alerts:
                    print(f"[ALERTA] {timestamp_str} - {alert}")

            # Atualizar seen
            seen_conn_ids = current_conn_ids

    except KeyboardInterrupt:
        print("\n[*] Monitorização interrompida.")

if __name__ == "__main__":
    main()
