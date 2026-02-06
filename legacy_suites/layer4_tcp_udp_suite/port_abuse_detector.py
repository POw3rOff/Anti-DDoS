#!/usr/bin/env python3

"""
port_abuse_detector.py
Layer 4 TCP/UDP Suite: Detetor de Abuso de Portas.

Funcionalidades:
- Monitoriza tráfego de entrada para todas as portas (TCP/UDP).
- Identifica portas sob ataque ou scan intenso.
- Permite definir portas críticas com limiares específicos.
- Requer privilégios de root (Raw Sockets).
"""

import socket
import struct
import argparse
import time
import sys
import os
from collections import defaultdict
import threading

# Configuração de portas críticas (Exemplo)
CRITICAL_PORTS = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    53: "DNS",
    3306: "MySQL",
    5432: "PostgreSQL"
}

stop_sniffing = False

def sniff_traffic(proto, stats_dict):
    """
    Captura tráfego de um protocolo específico (IPPROTO_TCP ou IPPROTO_UDP)
    e atualiza o dicionário stats_dict {dst_port: count}.
    """
    global stop_sniffing
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, proto)
        s.settimeout(1.0)
    except PermissionError:
        print(f"[ERRO] Permissão negada para proto {proto}. Use root.", file=sys.stderr)
        return
    except Exception:
        return

    while not stop_sniffing:
        try:
            data, _ = s.recvfrom(65535)
            if len(data) < 20:
                continue

            ip_header_len = (data[0] & 0x0F) * 4

            # TCP e UDP têm portas de origem e destino nos primeiros 4 bytes do payload
            # (Src Port 2b, Dst Port 2b)
            if len(data) < ip_header_len + 4:
                continue

            payload_start = ip_header_len
            dst_port = struct.unpack("!H", data[payload_start+2:payload_start+4])[0]

            stats_dict[dst_port] += 1

        except socket.timeout:
            continue
        except Exception:
            pass

    s.close()

def main():
    global stop_sniffing
    parser = argparse.ArgumentParser(description="Detector de Abuso de Portas")
    parser.add_argument("--limit", type=int, default=1000, help="Limite genérico de pacotes/s por porta")
    parser.add_argument("--interval", type=int, default=5, help="Intervalo de relatório (s)")
    args = parser.parse_args()

    print(f"[*] Iniciando Port Abuse Detector (Limit: {args.limit} pps, Interval: {args.interval}s)")

    # Stats acumulados
    tcp_stats = defaultdict(int)
    udp_stats = defaultdict(int)

    # Iniciar threads de captura
    t_tcp = threading.Thread(target=sniff_traffic, args=(socket.IPPROTO_TCP, tcp_stats))
    t_udp = threading.Thread(target=sniff_traffic, args=(socket.IPPROTO_UDP, udp_stats))

    t_tcp.daemon = True
    t_udp.daemon = True

    t_tcp.start()
    t_udp.start()

    try:
        while True:
            time.sleep(args.interval)

            # Copiar e resetar contadores de forma atómica (aproximadamente)
            # Para precisão perfeita precisaria de lock, mas para deteção de flood, isto serve.
            curr_tcp = tcp_stats.copy()
            curr_udp = udp_stats.copy()
            tcp_stats.clear()
            udp_stats.clear()

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            alerts = []

            # Analisar TCP
            for port, count in curr_tcp.items():
                pps = count / args.interval
                limit = args.limit
                # Se for porta crítica, poderia ter limite diferente (ex: SSH mais baixo)
                if port == 22:
                    limit = 100 # Exemplo: SSH threshold mais baixo

                if pps > limit:
                    service = CRITICAL_PORTS.get(port, str(port))
                    alerts.append(f"TCP Port {service}: {pps:.0f} PPS")

            # Analisar UDP
            for port, count in curr_udp.items():
                pps = count / args.interval
                limit = args.limit

                if pps > limit:
                    service = CRITICAL_PORTS.get(port, str(port))
                    alerts.append(f"UDP Port {service}: {pps:.0f} PPS")

            if alerts:
                print(f"[ALERTA] {timestamp} -> {'; '.join(alerts)}")

    except KeyboardInterrupt:
        stop_sniffing = True
        print("\n[*] Parando...")
        # Esperar threads terminarem se necessário (timeout do socket é 1s)
        time.sleep(1.5)

if __name__ == "__main__":
    main()
