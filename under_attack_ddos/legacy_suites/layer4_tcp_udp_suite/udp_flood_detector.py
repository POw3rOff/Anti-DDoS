#!/usr/bin/env python3

"""
udp_flood_detector.py
Layer 4 TCP/UDP Suite: Detetor de UDP Flood.

Funcionalidades:
- Monitoriza taxas de pacotes UDP (InDatagrams) via /proc/net/snmp.
- Deteta erros de recepção (InErrors, RcvbufErrors) indicando buffer overflow.
- Monitoriza filas de recepção (rx_queue) em sockets UDP abertos via /proc/net/udp.
- Deteta ataques de porta aleatória/fechada (NoPorts).
"""

import time
import argparse
import sys
import os
import struct
import socket

def read_snmp_udp():
    """Lê estatísticas UDP do /proc/net/snmp."""
    stats = {}
    path = "/proc/net/snmp"
    if not os.path.exists(path):
        return stats

    try:
        with open(path, "r") as f:
            lines = f.readlines()
            # Procurar linhas Udp:
            # Header: Udp: InDatagrams NoPorts InErrors OutDatagrams RcvbufErrors SndbufErrors InCsumErrors IgnoredMulti
            header = []
            values = []
            for line in lines:
                if line.startswith("Udp:"):
                    parts = line.strip().split()
                    if not header:
                        header = parts[1:]
                    else:
                        values = parts[1:]
                        break

            if header and values:
                for k, v in zip(header, values):
                    stats[k] = int(v)
    except Exception:
        pass
    return stats

def read_udp_sockets():
    """
    Lê /proc/net/udp e retorna lista de sockets com filas altas.
    Formato: sl  local_address rem_address   st tx_queue:rx_queue tr tm->when retrnsmt   uid  timeout inode ref pointer drops
    """
    high_queue_sockets = []
    path = "/proc/net/udp"
    if not os.path.exists(path):
        return high_queue_sockets

    try:
        with open(path, "r") as f:
            lines = f.readlines()[1:] # Skip header
            for line in lines:
                parts = line.strip().split()
                if len(parts) < 4:
                    continue

                # parts[1]: local_address (IP:Port hex)
                # parts[4]: tx_queue:rx_queue (hex:hex)

                local_addr = parts[1]
                queues = parts[4]

                if ":" in queues:
                    tx_hex, rx_hex = queues.split(":")
                    rx_q = int(rx_hex, 16)

                    if rx_q > 1000: # Threshold arbitrário para fila cheia
                        # Decode IP:Port
                        try:
                            ip_hex, port_hex = local_addr.split(":")
                            port = int(port_hex, 16)
                            # Simple IP decode
                            if len(ip_hex) == 8:
                                ip = socket.inet_ntoa(struct.pack("<L", int(ip_hex, 16)))
                            else:
                                ip = ip_hex

                            high_queue_sockets.append({"ip": ip, "port": port, "rx_queue": rx_q})
                        except:
                            pass
    except Exception:
        pass

    return high_queue_sockets

def main():
    parser = argparse.ArgumentParser(description="Detetor de UDP Flood")
    parser.add_argument("--pps-threshold", type=int, default=2000, help="Limite de pacotes UDP/s para alerta (default: 2000)")
    parser.add_argument("--interval", type=int, default=2, help="Intervalo de monitorização em segundos (default: 2)")
    args = parser.parse_args()

    print(f"[*] Iniciando UDP Flood Detector (PPS Limit: {args.pps_threshold}, Interval: {args.interval}s)")

    last_stats = {}

    try:
        while True:
            current_stats = read_snmp_udp()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            alerts = []

            if last_stats:
                delta_time = args.interval # Aproximado

                in_datagrams = current_stats.get("InDatagrams", 0) - last_stats.get("InDatagrams", 0)
                in_errors = current_stats.get("InErrors", 0) - last_stats.get("InErrors", 0)
                rcvbuf_errors = current_stats.get("RcvbufErrors", 0) - last_stats.get("RcvbufErrors", 0)
                no_ports = current_stats.get("NoPorts", 0) - last_stats.get("NoPorts", 0)

                pps = in_datagrams / delta_time

                if pps > args.pps_threshold:
                    alerts.append(f"Alta taxa de pacotes UDP: {pps:.0f} PPS")

                if rcvbuf_errors > 0:
                    alerts.append(f"Buffer Overflow (RcvbufErrors): {rcvbuf_errors} drops")

                if no_ports > 100:
                    alerts.append(f"Possível Scan/Flood em portas fechadas (NoPorts): {no_ports}")

            # Verificar filas
            stuck_sockets = read_udp_sockets()
            for sock in stuck_sockets:
                alerts.append(f"Socket saturado: {sock['ip']}:{sock['port']} RX_QUEUE: {sock['rx_queue']}")

            if alerts:
                print(f"[ALERTA] {timestamp} -> {'; '.join(alerts)}")
            elif last_stats:
                 # print(f"[INFO] UDP PPS: {pps:.0f}")
                 pass

            last_stats = current_stats
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[*] Monitorização interrompida.")

if __name__ == "__main__":
    main()
