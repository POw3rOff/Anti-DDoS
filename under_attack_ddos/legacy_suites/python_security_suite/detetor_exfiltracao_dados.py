#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detector de Exfiltração de Dados
================================
Analisa tráfego de rede para identificar exfiltração silenciosa.
- Monitora volume de upload (TX Bytes).
- Identifica conexões longas ou volumosas (TCP).
- Heurística de DNS: Monitora taxa de pacotes UDP (OutDatagrams) via /proc/net/snmp.

Uso:
    python3 detetor_exfiltracao_dados.py --limit-mb 50 --interval 10
"""

import argparse
import time
import socket
import struct
import os
import sys

# Conversão de estados TCP do /proc/net/tcp
TCP_STATES = {
    '01': 'ESTABLISHED',
    '02': 'SYN_SENT',
    '03': 'SYN_RECV',
    '04': 'FIN_WAIT1',
    '05': 'FIN_WAIT2',
    '06': 'TIME_WAIT',
    '07': 'CLOSE',
    '08': 'CLOSE_WAIT',
    '09': 'LAST_ACK',
    '0A': 'LISTEN',
    '0B': 'CLOSING'
}

def hex_to_ip(hex_str):
    """Converte IP hexadecimal (little-endian) para string legível."""
    try:
        # Ex: 0100007F -> 127.0.0.1
        addr = int(hex_str, 16)
        return socket.inet_ntoa(struct.pack("<L", addr))
    except:
        return hex_str

def get_active_connections():
    """Lê /proc/net/tcp e retorna lista de conexões estabelecidas de saída."""
    connections = []
    try:
        with open('/proc/net/tcp', 'r') as f:
            lines = f.readlines()[1:]
            for line in lines:
                parts = line.split()
                if len(parts) < 4: continue

                local_addr = parts[1]
                rem_addr = parts[2]
                state = parts[3]

                # Apenas ESTABLISHED (01)
                if state != '01':
                    continue

                local_ip_hex, local_port_hex = local_addr.split(':')
                rem_ip_hex, rem_port_hex = rem_addr.split(':')

                rem_ip = hex_to_ip(rem_ip_hex)
                rem_port = int(rem_port_hex, 16)
                local_ip = hex_to_ip(local_ip_hex)

                # Ignorar localhost
                if rem_ip.startswith("127."):
                    continue

                connections.append({
                    "src": local_ip,
                    "dst": rem_ip,
                    "dport": rem_port,
                    "raw_line": line
                })
    except Exception as e:
        print(f"[!] Erro ao ler conexões: {e}")
    return connections

def get_interface_stats():
    """Retorna bytes e packets TX/RX totais."""
    stats = {}
    try:
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()[2:]
            for line in lines:
                parts = line.split()
                iface = parts[0].strip(':')
                if iface == 'lo': continue

                stats[iface] = {
                    "rx_bytes": int(parts[1]),
                    "tx_bytes": int(parts[9]),
                    "tx_packets": int(parts[10]) # Depende do kernel, geralmente 10 é tx_pkts ou 9 é bytes. Check headers.
                    # cat /proc/net/dev: face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
                    # 0:face 1:rx_bytes 2:rx_pkts ... 9:tx_bytes 10:tx_pkts
                }
    except:
        pass
    return stats

def get_udp_stats():
    """Lê /proc/net/snmp para pegar contadores UDP globais."""
    try:
        with open('/proc/net/snmp', 'r') as f:
            for line in f:
                if line.startswith("Udp:"):
                    # Linha 1: Cabeçalho, Linha 2: Valores
                    # Mas o arquivo tem pares Header/Values.
                    # Udp: InDatagrams NoPorts InErrors OutDatagrams RcvbufErrors SndbufErrors InCsumErrors IgnoredMulti
                    # Udp: 123 0 0 456 ...
                    # Vamos ler a próxima linha se a atual for header?
                    # Geralmente vem: Udp: ... \n Udp: ...
                    parts = line.split()
                    if parts[1] == 'InDatagrams': continue # Header line
                    return int(parts[4]) # OutDatagrams (index 4 se Udp: for 0)
    except:
        pass
    return 0

def analyze_exfiltration(limit_mb_per_min, udp_limit_per_min, interval):
    print(f"[*] Iniciando monitoramento de exfiltração...")
    print(f"[*] Limite de Upload: {limit_mb_per_min} MB/min")
    print(f"[*] Limite UDP (DNS Heurística): {udp_limit_per_min} pkts/min")
    print(f"[*] Intervalo de checagem: {interval} segundos")

    last_stats = get_interface_stats()
    last_udp = get_udp_stats()

    while True:
        time.sleep(interval)
        current_stats = get_interface_stats()
        current_udp = get_udp_stats()

        # 1. Análise de Volume (Upload)
        for iface, curr in current_stats.items():
            prev = last_stats.get(iface)
            if not prev: continue

            delta_tx = curr["tx_bytes"] - prev["tx_bytes"]
            mb_sent = delta_tx / (1024 * 1024)
            mb_per_min = (mb_sent / interval) * 60

            if mb_per_min > limit_mb_per_min:
                print(f"[ALERTA] Alto volume de upload em {iface}: {mb_per_min:.2f} MB/min (Limite: {limit_mb_per_min})")

        last_stats = current_stats

        # 2. Análise de UDP (DNS Tunneling Heurística)
        delta_udp = current_udp - last_udp
        udp_rate_min = (delta_udp / interval) * 60

        if udp_rate_min > udp_limit_per_min:
            print(f"[ALERTA] Alto tráfego UDP detectado: {udp_rate_min:.0f} pkts/min (Possível DNS Tunneling/Exfiltração)")

        last_udp = current_udp

        # 3. Análise de Conexões Suspeitas (TCP)
        conns = get_active_connections()
        suspicious_ports = [4444, 1337, 6667]

        dst_counts = {}

        for c in conns:
            dst = c["dst"]
            port = c["dport"]
            dst_counts[dst] = dst_counts.get(dst, 0) + 1

            if port in suspicious_ports:
                print(f"[ALERTA] Conexão para porta suspeita: {dst}:{port}")

        for dst, count in dst_counts.items():
            if count > 20:
                print(f"[ALERTA] Múltiplas conexões ({count}) para o mesmo destino: {dst}")

def main():
    parser = argparse.ArgumentParser(description="Detector de Exfiltração de Dados")
    parser.add_argument('--limit-mb', type=float, default=50.0, help="Limite de upload em MB por minuto (Padrão: 50)")
    parser.add_argument('--udp-limit', type=int, default=1000, help="Limite de pacotes UDP/min (Padrão: 1000)")
    parser.add_argument('--interval', type=int, default=10, help="Intervalo de verificação em segundos (Padrão: 10)")

    args = parser.parse_args()

    try:
        analyze_exfiltration(args.limit_mb, args.udp_limit, args.interval)
    except KeyboardInterrupt:
        print("\n[*] Monitoramento encerrado.")

if __name__ == "__main__":
    main()
