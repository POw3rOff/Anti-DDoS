#!/usr/bin/env python3

"""
syn_ack_anomaly_monitor.py
Layer 4 TCP/UDP Suite: Monitor de Anomalias SYN/SYN-ACK.

Funcionalidades:
- Monitoriza estatísticas TCP do /proc/net/snmp e /proc/net/netstat.
- Deteta ativação de SYN Cookies.
- Analisa a proporção de conexões falhadas vs. tentativas.
- Identifica ataques silenciosos baseados em desequilíbrio de handshake.
"""

import time
import argparse
import sys
import os

def read_proc_file(filepath, header_prefix):
    """
    Lê ficheiro /proc e retorna dicionário com chaves e valores para a linha que começa com header_prefix.
    Exemplo: cat /proc/net/snmp
    Tcp: RtoAlgorithm RtoMin RtoMax MaxConn ActiveOpens PassiveOpens ...
    Tcp: 1 200 120000 -1 230 140 ...
    """
    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        header = []
        values = []

        for i, line in enumerate(lines):
            if line.startswith(header_prefix):
                # A próxima linha geralmente contém os valores ou está na mesma linha?
                # No /proc/net/snmp, headers e values são linhas separadas.
                parts = line.strip().split()
                if not header:
                    # Primeira ocorrência é o header
                    header = parts[1:]
                    # A próxima linha deve ser os valores
                    if i + 1 < len(lines):
                        val_parts = lines[i+1].strip().split()
                        if val_parts[0] == header_prefix:
                            values = val_parts[1:]
                            break

        if header and values and len(header) == len(values):
            return {k: int(v) for k, v in zip(header, values)}

    except Exception as e:
        print(f"[ERRO] Falha ao ler {filepath}: {e}", file=sys.stderr)

    return {}

def read_netstat_ext():
    """
    Lê estatísticas estendidas do /proc/net/netstat (e.g., Syncookies).
    Formato similar ao snmp: Header line, Value line.
    """
    return read_proc_file("/proc/net/netstat", "TcpExt:")

def main():
    parser = argparse.ArgumentParser(description="Monitor de Anomalias SYN/SYN-ACK")
    parser.add_argument("--interval", type=int, default=5, help="Intervalo de verificação em segundos (default: 5)")
    args = parser.parse_args()

    print(f"[*] Iniciando Monitor SYN/SYN-ACK (Interval: {args.interval}s)")

    last_stats = {}

    try:
        while True:
            snmp_stats = read_proc_file("/proc/net/snmp", "Tcp:")
            ext_stats = read_netstat_ext()

            # Combinar estatísticas
            current_stats = {**snmp_stats, **ext_stats}

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            if last_stats:
                # Calcular deltas
                delta = {}
                for k, v in current_stats.items():
                    prev = last_stats.get(k, 0)
                    delta[k] = v - prev

                # Análise
                syncookies_sent = delta.get("SyncookiesSent", 0)
                syncookies_failed = delta.get("SyncookiesFailed", 0)
                passive_opens = delta.get("PassiveOpens", 0) # Server receives SYN
                active_opens = delta.get("ActiveOpens", 0)   # Client sends SYN
                attempt_fails = delta.get("AttemptFails", 0)

                # Lógica de Detecção
                alerts = []

                if syncookies_sent > 0:
                    alerts.append(f"SYN Cookies ativados! Sent: {syncookies_sent}, Failed: {syncookies_failed}")

                if passive_opens > 0:
                    fail_ratio = attempt_fails / (passive_opens + active_opens + 1)
                    if fail_ratio > 0.5 and attempt_fails > 10:
                        alerts.append(f"Alta taxa de falha em conexões ({fail_ratio:.2f}). Possible SYN flood or port scan.")

                if alerts:
                    print(f"[ALERTA] {timestamp} -> {'; '.join(alerts)}")
                elif syncookies_sent == 0 and passive_opens > 0:
                     pass

            last_stats = current_stats
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[*] Monitorização interrompida.")

if __name__ == "__main__":
    main()
