#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Timeline Forense Automática
===========================
Gera uma linha do tempo unificada combinando logs do sistema e metadados de arquivos.
Essencial para investigações pós-incidente.

Fontes de dados:
- Logs: /var/log/auth.log, /var/log/syslog, /var/log/kern.log
- Arquivos: Modificações (mtime) e Criações/Metadados (ctime) em /home, /etc, /tmp, /root

Uso:
    python3 timeline_forense_automatica.py --days 1 --output timeline.csv
"""

import os
import sys
import re
import csv
import argparse
from datetime import datetime, timedelta
import glob

# Configurações
LOG_FILES = [
    '/var/log/auth.log',
    '/var/log/syslog',
    '/var/log/kern.log',
    '/var/log/messages',
    '/var/log/secure' # RHEL/CentOS
]

SCAN_DIRS = [
    '/etc',
    '/home',
    '/root',
    '/tmp',
    '/var/www'
]

class Event:
    def __init__(self, timestamp, source, event_type, description):
        self.timestamp = timestamp
        self.source = source
        self.event_type = event_type
        self.description = description

    def to_row(self):
        return [
            datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            self.source,
            self.event_type,
            self.description
        ]

def parse_syslog_line(line, year):
    # Format: Jan 10 12:34:56 hostname app[pid]: message
    # Format 2 (Rsyslog ISO): 2023-01-10T12:34:56...

    try:
        # Tentar formato padrão (RFC 3164)
        # Regex: ^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2})\s+([^\s]+)\s+(.*)$
        match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2})\s+([^\s]+)\s+(.*)$', line)
        if match:
            ts_str = match.group(1)
            host = match.group(2)
            msg = match.group(3)

            # Converter data
            # Assumindo ano fornecido, lidando com virada de ano é complexo sem contexto
            full_ts_str = f"{year} {ts_str}"
            dt = datetime.strptime(full_ts_str, "%Y %b %d %H:%M:%S")
            return dt.timestamp(), host, msg

        # Tentar formato ISO8601 (RFC 5424)
        # 2023-01-10T...
        match_iso = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^ ]*)\s+([^ ]+)\s+(.*)$', line)
        if match_iso:
            # Parse ISO simplificado
            ts_str = match_iso.group(1).split('.')[0] # Remove msec/timezone for simplicity
            host = match_iso.group(2)
            msg = match_iso.group(3)
            # Tentar remover timezone offset se existir na string simples
            # Ex: 2023-01-01T10:00:00+00:00 -> ignorar offset no strptime simples ou usar lib
            if '+' in ts_str: ts_str = ts_str.split('+')[0]
            if '-' in ts_str[-6:]: ts_str = ts_str.rsplit('-', 1)[0] # Cuidado com data

            dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
            return dt.timestamp(), host, msg

    except Exception:
        pass
    return None, None, None

def collect_logs(days_back):
    events = []
    print("[*] Coletando logs do sistema...")
    cutoff_time = datetime.now() - timedelta(days=days_back)
    current_year = datetime.now().year

    for log_path in LOG_FILES:
        # Expandir globs (ex: auth.log.1)
        # Por enquanto apenas arquivos ativos e .1 (texto plano)
        candidates = glob.glob(log_path) + glob.glob(log_path + ".1")

        for lp in candidates:
            if not os.path.exists(lp): continue

            try:
                with open(lp, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        ts, host, msg = parse_syslog_line(line, current_year)
                        if ts:
                            if ts < cutoff_time.timestamp():
                                continue

                            evt_type = "LOG"
                            if "sshd" in msg: evt_type = "SSH"
                            elif "sudo" in msg: evt_type = "SUDO"
                            elif "kernel" in msg: evt_type = "KERNEL"

                            events.append(Event(ts, f"LOG:{os.path.basename(lp)}", evt_type, msg.strip()))
            except Exception as e:
                print(f"[!] Erro lendo {lp}: {e}")

    return events

def collect_filesystem(days_back):
    events = []
    print("[*] Coletando metadados de arquivos...")
    cutoff_time = datetime.now() - timedelta(days=days_back)
    cutoff_ts = cutoff_time.timestamp()

    for directory in SCAN_DIRS:
        if not os.path.exists(directory): continue

        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    stat = os.stat(filepath)

                    # Modified Time
                    if stat.st_mtime >= cutoff_ts:
                        events.append(Event(stat.st_mtime, "FILE", "MODIFIED", f"{filepath} (Size: {stat.st_size})"))

                    # Change Time (Metadata)
                    if stat.st_ctime >= cutoff_ts:
                        # Evitar duplicata se mtime == ctime (comum na criação)
                        if abs(stat.st_ctime - stat.st_mtime) > 1:
                            events.append(Event(stat.st_ctime, "FILE", "METADATA_CHANGE", f"{filepath} (Perms/Owner changed)"))

                except OSError:
                    pass
    return events

def main():
    parser = argparse.ArgumentParser(description="Timeline Forense Automática")
    parser.add_argument('--days', type=int, default=7, help="Analisar últimos N dias (Padrão: 7)")
    parser.add_argument('--output', default='timeline_forense.csv', help="Arquivo de saída CSV")

    args = parser.parse_args()

    print(f"[*] Gerando timeline dos últimos {args.days} dias...")

    log_events = collect_logs(args.days)
    print(f"   -> {len(log_events)} eventos de log.")

    file_events = collect_filesystem(args.days)
    print(f"   -> {len(file_events)} eventos de arquivo.")

    all_events = log_events + file_events
    all_events.sort(key=lambda x: x.timestamp)

    print(f"[*] Salvando {len(all_events)} eventos em {args.output}...")

    try:
        with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Source', 'Type', 'Description'])
            for evt in all_events:
                writer.writerow(evt.to_row())
        print("[*] Timeline concluída com sucesso.")
    except Exception as e:
        print(f"[!] Erro ao salvar arquivo: {e}")

if __name__ == "__main__":
    main()
