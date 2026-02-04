#!/usr/bin/env python3


"""
syn_flood_detector.py
Layer 4 TCP/UDP Suite: Detetor de SYN Flood e Half-Open Connections.
"""

import time
import argparse
import sys
import os

# Definições de Estados TCP (Linux kernel)
# 01: ESTABLISHED
# 02: SYN_SENT
# 03: SYN_RECV
# 04: FIN_WAIT1
# ...
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

def count_tcp_states():
    # Lê /proc/net/tcp e /proc/net/tcp6 para contar estados das conexões.
    counts = {state: 0 for state in TCP_STATES.values()}
    files = ['/proc/net/tcp', '/proc/net/tcp6']

    for fpath in files:
        if not os.path.exists(fpath):
            continue

        try:
            with open(fpath, 'r') as f:
                # Ignorar cabeçalho
                lines = f.readlines()[1:]
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        st_hex = parts[3]
                        state_name = TCP_STATES.get(st_hex, 'UNKNOWN')
                        if state_name in counts:
                            counts[state_name] += 1
        except Exception as e:
            print(f'[ERRO] Falha ao ler {fpath}: {e}', file=sys.stderr)

    return counts

def main():
    parser = argparse.ArgumentParser(description='Monitor de SYN Flood')
    parser.add_argument('--threshold', type=int, default=100, help='Limite de conexões SYN_RECV para alerta (default: 100)')
    parser.add_argument('--interval', type=int, default=2, help='Intervalo de verificação em segundos (default: 2)')
    args = parser.parse_args()

    print(f'[*] Iniciando Monitor de SYN Flood (Threshold: {args.threshold}, Interval: {args.interval}s)')

    try:
        while True:
            counts = count_tcp_states()
            syn_recv_count = counts.get('SYN_RECV', 0)

            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

            if syn_recv_count > args.threshold:
                print(f'[ALERTA] {timestamp} - Possível SYN Flood detetado! SYN_RECV: {syn_recv_count} (Threshold: {args.threshold})')
            else:
                if syn_recv_count > 0:
                     print(f'[INFO] {timestamp} - SYN_RECV: {syn_recv_count}')

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print('\n[*] Monitorização interrompida.')

if __name__ == '__main__':
    main()
