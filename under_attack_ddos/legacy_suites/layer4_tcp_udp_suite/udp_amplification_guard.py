#!/usr/bin/env python3

"""
udp_amplification_guard.py
Layer 4 TCP/UDP Suite: Detetor de Amplificação UDP (DNS, NTP, SSDP, CLDAP, etc).

Funcionalidades:
- Monitoriza tráfego UDP de entrada usando Raw Sockets.
- Identifica tráfego excessivo vindo de portas de origem conhecidas por amplificação.
- Calcula o volume (bytes e pacotes) por porta de origem.
- Requer privilégios de root/sudo para criar RAW Sockets.

Portas Monitoradas por Padrão:
- 53 (DNS)
- 123 (NTP)
- 1900 (SSDP)
- 389 (CLDAP)
- 11211 (Memcached)
- 161 (SNMP)
- 19 (CharGEN)
"""

import socket
import struct
import argparse
import time
import sys
import os
from collections import defaultdict

# Portas comuns de amplificação
AMPLIFICATION_PORTS = {
    53: "DNS",
    123: "NTP",
    1900: "SSDP",
    389: "CLDAP",
    11211: "Memcached",
    161: "SNMP",
    19: "CharGEN",
    17: "QOTD"
}

def sniff_udp_traffic(duration, interface_ip="0.0.0.0"):
    """
    Captura pacotes UDP por 'duration' segundos.
    Retorna estatísticas: {port: {'packets': x, 'bytes': y, 'src_ips': set()}}
    """
    stats = defaultdict(lambda: {'packets': 0, 'bytes': 0, 'src_ips': set()})

    try:
        # Cria raw socket para UDP (protocolo 17)
        # AF_INET, SOCK_RAW, IPPROTO_UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
        s.bind((interface_ip, 0))
    except PermissionError:
        print("[ERRO] Permissão negada. Execute como root/sudo para usar Raw Sockets.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERRO] Falha ao criar socket: {e}", file=sys.stderr)
        return None

    # Set timeout para não bloquear indefinidamente se não houver tráfego
    s.settimeout(1.0)

    start_time = time.time()

    while time.time() - start_time < duration:
        try:
            # Buffer de 65535 bytes
            data, addr = s.recvfrom(65535)
            # addr é (src_ip, 0) no raw socket geralmente, ou (src_ip, port) dependendo do OS/Socket
            # No Linux SOCK_RAW IPPROTO_UDP, recebemos o pacote IP completo incluindo header.

            # Header IP tem 20 bytes (normalmente)
            # Primeiros byte: version + IHL
            if len(data) < 28: # 20 bytes IP + 8 bytes UDP
                continue

            ip_header_len = (data[0] & 0x0F) * 4
            udp_header_start = ip_header_len

            # UDP Header:
            # Source Port (2 bytes)
            # Dest Port (2 bytes)
            # Length (2 bytes)
            # Checksum (2 bytes)

            src_port = struct.unpack("!H", data[udp_header_start:udp_header_start+2])[0]
            dst_port = struct.unpack("!H", data[udp_header_start+2:udp_header_start+4])[0]
            length = struct.unpack("!H", data[udp_header_start+4:udp_header_start+6])[0]

            src_ip = addr[0]

            # Se a porta de origem for uma das portas de amplificação
            if src_port in AMPLIFICATION_PORTS:
                stats[src_port]['packets'] += 1
                stats[src_port]['bytes'] += length
                stats[src_port]['src_ips'].add(src_ip)

        except socket.timeout:
            continue
        except Exception:
            continue

    s.close()
    return stats

def main():
    parser = argparse.ArgumentParser(description="Detector de Amplificação UDP")
    parser.add_argument("--threshold-bytes", type=int, default=1024 * 1024, help="Limite de bytes/s para alerta (default: 1MB/s)")
    parser.add_argument("--threshold-pps", type=int, default=1000, help="Limite de pacotes/s para alerta (default: 1000 PPS)")
    parser.add_argument("--interval", type=int, default=2, help="Duração de cada amostragem em segundos")
    args = parser.parse_args()

    print(f"[*] Iniciando UDP Amplification Guard (Threshold: {args.threshold_bytes} bytes/s, {args.threshold_pps} PPS)")

    try:
        while True:
            # Captura amostra
            stats = sniff_udp_traffic(args.interval)

            if stats is None:
                sys.exit(1)

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            alerts = []

            for port, data in stats.items():
                pps = data['packets'] / args.interval
                bps = data['bytes'] / args.interval
                unique_ips = len(data['src_ips'])

                service = AMPLIFICATION_PORTS.get(port, "Unknown")

                if bps > args.threshold_bytes or pps > args.threshold_pps:
                    alerts.append(f"Amplificação {service} (Port {port}): {pps:.0f} PPS, {bps/1024:.2f} KB/s, IPs únicos: {unique_ips}")

            if alerts:
                print(f"[ALERTA] {timestamp} -> {'; '.join(alerts)}")
            else:
                # print(f"[INFO] {timestamp} - Tráfego analisado, sem anomalias.")
                pass

            # Pequena pausa se necessário, ou loop contínuo
            # Como a função sniff dura args.interval, o loop já tem tempo.

    except KeyboardInterrupt:
        print("\n[*] Monitorização interrompida.")

if __name__ == "__main__":
    main()
