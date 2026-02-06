#!/usr/bin/env python3

"""
tcp_state_exhaustion_detector.py
Layer 4 TCP/UDP Suite: Detetor de Exaustão de Estados TCP.

Funcionalidades:
- Monitoriza a tabela de conntrack (nf_conntrack).
- Monitoriza uso global de sockets e memória TCP (/proc/net/sockstat).
- Alerta quando o sistema se aproxima dos limites do kernel.
"""

import time
import argparse
import sys
import os

def read_file_int(path):
    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except:
        return None

def read_sockstat():
    """
    Lê /proc/net/sockstat e retorna dicionário.
    Exemplo output:
    sockets: used 154
    TCP: inuse 7 orphan 0 tw 0 alloc 9 mem 1
    ...
    """
    stats = {}
    path = "/proc/net/sockstat"
    if not os.path.exists(path):
        return stats

    try:
        with open(path, "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                key = parts[0] # sockets, TCP, UDP, RAW, FRAG
                values = parts[1].strip().split()
                # values é uma lista tipo ['used', '154'] ou ['inuse', '7', 'orphan', '0'...]

                # Transformar em dict interno
                sub_stats = {}
                for i in range(0, len(values), 2):
                    if i+1 < len(values):
                        k_sub = values[i]
                        v_sub = values[i+1]
                        sub_stats[k_sub] = int(v_sub)

                stats[key] = sub_stats
    except Exception as e:
        print(f"[ERRO] Falha ao ler sockstat: {e}", file=sys.stderr)

    return stats

def main():
    parser = argparse.ArgumentParser(description="Detetor de Exaustão de Estados TCP")
    parser.add_argument("--threshold", type=int, default=80, help="Percentagem de uso do conntrack para alerta (default: 80)")
    parser.add_argument("--interval", type=int, default=5, help="Intervalo de verificação em segundos (default: 5)")
    args = parser.parse_args()

    print(f"[*] Iniciando Monitor de Exaustão de Estados (Threshold: {args.threshold}%, Interval: {args.interval}s)")

    conntrack_count_path = "/proc/sys/net/netfilter/nf_conntrack_count"
    conntrack_max_path = "/proc/sys/net/netfilter/nf_conntrack_max"

    # Alguns sistemas antigos usam ip_conntrack
    if not os.path.exists(conntrack_count_path):
         conntrack_count_path = "/proc/sys/net/ipv4/netfilter/ip_conntrack_count"
         conntrack_max_path = "/proc/sys/net/ipv4/netfilter/ip_conntrack_max"

    try:
        while True:
            alerts = []
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # 1. Verificar Conntrack
            count = read_file_int(conntrack_count_path)
            maximum = read_file_int(conntrack_max_path)

            if count is not None and maximum is not None and maximum > 0:
                usage_pct = (count / maximum) * 100
                if usage_pct > args.threshold:
                    alerts.append(f"Conntrack Crítico: {usage_pct:.2f}% ({count}/{maximum})")
                elif usage_pct > 50:
                     # Info warning
                     pass

            # 2. Verificar Sockstat
            sock_stats = read_sockstat()
            tcp_stats = sock_stats.get("TCP", {})
            sockets_stats = sock_stats.get("sockets", {})

            tcp_inuse = tcp_stats.get("inuse", 0)
            tcp_orphan = tcp_stats.get("orphan", 0)
            tcp_tw = tcp_stats.get("tw", 0)

            # Orphan sockets alto pode indicar DoS (Out of memory para sockets TCP)
            # Não há um "max" fixo fácil de ler para sockets, depende da RAM (tcp_mem), mas orphan alto é mau sinal.
            if tcp_orphan > 2000: # Valor arbitrário conservador, servidores grandes aguentam mais
                alerts.append(f"Muitos sockets órfãos: {tcp_orphan}")

            if alerts:
                print(f"[ALERTA] {timestamp} -> {'; '.join(alerts)}")
            else:
                # Opcional: print stats
                # print(f"[INFO] {timestamp} Conntrack: {count}/{maximum} | TCP InUse: {tcp_inuse} Orphan: {tcp_orphan} TW: {tcp_tw}")
                pass

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[*] Monitorização interrompida.")

if __name__ == "__main__":
    main()
