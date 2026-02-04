#!/usr/bin/env python3

"""
tcp_flag_anomaly_detector.py
Layer 4 TCP/UDP Suite: Detetor de Anomalias em Flags TCP.

Funcionalidades:
- Monitoriza pacotes TCP em tempo real (Raw Sockets).
- Identifica combinações de flags inválidas ou suspeitas.
- Deteta scans do tipo NULL, XMAS, FIN e combinações ilegais (SYN+FIN).
- Requer privilégios de root.
"""

import socket
import struct
import argparse
import time
import sys
import threading

# Flags TCP
TCP_FIN = 0x01
TCP_SYN = 0x02
TCP_RST = 0x04
TCP_PSH = 0x08
TCP_ACK = 0x10
TCP_URG = 0x20

stop_sniffing = False

# Estatísticas
stats = {
    "NULL": 0,
    "XMAS": 0,
    "SYN_FIN": 0,
    "RST_FLOOD": 0,
    "TOTAL": 0
}

def analyze_flags(flags):
    """Retorna lista de anomalias encontradas nas flags."""
    anomalies = []

    # NULL Scan (Nenhuma flag)
    if flags == 0:
        anomalies.append("NULL")

    # XMAS Scan (FIN + URG + PSH)
    # Às vezes XMAS inclui todas as 6 flags, ou variações. O clássico é FIN, URG, PSH.
    if (flags & TCP_FIN) and (flags & TCP_URG) and (flags & TCP_PSH):
        anomalies.append("XMAS")

    # SYN + FIN (Illegal)
    if (flags & TCP_SYN) and (flags & TCP_FIN):
        anomalies.append("SYN_FIN")

    # RST check (se for flood, contagem será alta)
    if (flags & TCP_RST):
        anomalies.append("RST")

    return anomalies

def sniff_tcp():
    global stop_sniffing
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        s.settimeout(1.0)
    except PermissionError:
        print("[ERRO] Falha ao criar RAW Socket TCP. Use root.", file=sys.stderr)
        stop_sniffing = True
        return
    except Exception:
        stop_sniffing = True
        return

    while not stop_sniffing:
        try:
            data, _ = s.recvfrom(65535)
            # IP Header length
            if len(data) < 20: continue
            ip_header_len = (data[0] & 0x0F) * 4

            # TCP Header start
            tcp_header_start = ip_header_len
            if len(data) < tcp_header_start + 14: continue

            # Flags estão no offset 13 (byte 13 do TCP header)
            # TCP Header: Source(2), Dest(2), Seq(4), Ack(4), Offset+Res(1/2), Flags(1/2) ...
            # Offset (Data Offset) são os primeiros 4 bits do byte 12. Flags são os ultimos 6 bits do byte 13 + 2 bits do 12 (NS/CWR/ECE?)
            # Na verdade struct do TCP Header:
            # 2 bytes src, 2 dst, 4 seq, 4 ack. (Total 12 bytes)
            # Byte 12: Data Offset (4 bits) + Reserved (3 bits) + NS (1 bit)
            # Byte 13: CWR, ECE, URG, ACK, PSH, RST, SYN, FIN

            # Vamos ler byte 13 diretamente para as flags clássicas
            flags = data[tcp_header_start + 13]

            anoms = analyze_flags(flags)

            stats["TOTAL"] += 1
            for a in anoms:
                if a == "RST":
                    stats["RST_FLOOD"] += 1
                elif a in stats:
                    stats[a] += 1

        except socket.timeout:
            continue
        except Exception:
            pass
    s.close()

def main():
    global stop_sniffing
    parser = argparse.ArgumentParser(description="Detector de Anomalias Flags TCP")
    parser.add_argument("--interval", type=int, default=5, help="Intervalo de reporte (s)")
    args = parser.parse_args()

    print(f"[*] Iniciando TCP Flag Anomaly Detector (Interval: {args.interval}s)")

    t = threading.Thread(target=sniff_tcp)
    t.daemon = True
    t.start()

    # Dá tempo para thread iniciar e verificar erro de permissão
    time.sleep(1)
    if stop_sniffing:
        sys.exit(1)

    try:
        while True:
            time.sleep(args.interval)

            # Ler e resetar stats
            # (Não é atómico perfeito, mas serve)
            current_stats = stats.copy()
            for k in stats:
                stats[k] = 0

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            alerts = []

            if current_stats["NULL"] > 0:
                alerts.append(f"NULL Scans: {current_stats['NULL']}")
            if current_stats["XMAS"] > 0:
                alerts.append(f"XMAS Scans: {current_stats['XMAS']}")
            if current_stats["SYN_FIN"] > 0:
                alerts.append(f"SYN+FIN Packets: {current_stats['SYN_FIN']}")
            if current_stats["RST_FLOOD"] > 100: # Threshold arbitrário para RST
                alerts.append(f"RST Flood potential: {current_stats['RST_FLOOD']}")

            if alerts:
                print(f"[ALERTA] {timestamp} -> {'; '.join(alerts)}")

    except KeyboardInterrupt:
        stop_sniffing = True
        print("\n[*] Parando...")
        time.sleep(1)

if __name__ == "__main__":
    main()
