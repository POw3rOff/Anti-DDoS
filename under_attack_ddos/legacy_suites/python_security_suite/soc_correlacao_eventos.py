#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SOC - Correlação de Eventos
===========================
Correlaciona logs de firewall, SSH, sistema e aplicações para detectar:
- Padrões de ataque distribuído (DDoS / Botnets).
- Brute-force lento (Low and Slow).
- Movimentação lateral (Login -> Sudo/Execução suspeita).

Uso:
    python3 soc_correlacao_eventos.py --logs /var/log/auth.log /var/log/syslog
"""

import argparse
import re
import sys
import time
from collections import defaultdict, deque
from datetime import datetime

# Configurações de Detecção (Heurísticas)
BRUTE_FORCE_THRESHOLD = 5       # Falhas por IP
TIME_WINDOW = 300               # Segundos (5 minutos)
DISTRIBUTED_THRESHOLD = 10      # IPs diferentes falhando auth
LATERAL_WINDOW = 60             # Segundos após login para detectar sudo/su

class Evento:
    def __init__(self, timestamp, src_ip, user, event_type, raw):
        self.timestamp = timestamp
        self.src_ip = src_ip
        self.user = user
        self.event_type = event_type  # 'auth_fail', 'auth_success', 'sudo', 'connect'
        self.raw = raw

def parse_line(line):
    # Exemplo: Jan 10 12:34:56 host sshd[123]: Failed password for invalid user root from 192.168.1.5 port 22 ssh2
    ts_regex = r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2})'
    ip_regex = r'from\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    user_regex = r'(?:for|user)\s+([a-zA-Z0-9_-]+)'

    match_ts = re.search(ts_regex, line)
    if not match_ts:
        return None

    try:
        current_year = datetime.now().year
        dt_str = f"{current_year} {match_ts.group(1)}"
        dt_obj = datetime.strptime(dt_str, "%Y %b %d %H:%M:%S")
        timestamp = dt_obj.timestamp()
    except Exception:
        return None

    src_ip = "0.0.0.0"
    match_ip = re.search(ip_regex, line)
    if match_ip:
        src_ip = match_ip.group(1)

    user = "unknown"
    match_user = re.search(user_regex, line)
    if match_user:
        user = match_user.group(1)

    event_type = "unknown"
    if "Failed password" in line or "authentication failure" in line:
        event_type = "auth_fail"
    elif "Accepted" in line and "ssh" in line.lower():
        event_type = "auth_success"
    elif "sudo:" in line or "COMMAND=" in line:
        event_type = "sudo"
    elif "Disconnect" in line:
        event_type = "disconnect"

    if event_type == "unknown":
        return None

    return Evento(timestamp, src_ip, user, event_type, line.strip())

def analyze_logs(log_files):
    events = []
    print(f"[*] Lendo {len(log_files)} arquivos de log...")

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    evt = parse_line(line)
                    if evt:
                        events.append(evt)
        except Exception as e:
            print(f"[!] Erro ao ler {log_file}: {e}")

    events.sort(key=lambda x: x.timestamp)
    print(f"[*] Total de eventos relevantes identificados: {len(events)}")
    return events

def detect_brute_force(events):
    print("\n[+] Analisando Brute-Force (Single Source)...")
    failures = defaultdict(list)
    detected = set()

    for evt in events:
        if evt.event_type == 'auth_fail':
            failures[evt.src_ip].append(evt.timestamp)
            valid_window = [t for t in failures[evt.src_ip] if evt.timestamp - t <= TIME_WINDOW]
            failures[evt.src_ip] = valid_window

            if len(valid_window) >= BRUTE_FORCE_THRESHOLD and evt.src_ip not in detected:
                print(f"   [ALERTA] Brute-force detectado de {evt.src_ip} ({len(valid_window)} falhas em {TIME_WINDOW}s)")
                detected.add(evt.src_ip)

def detect_distributed_attack(events):
    print("\n[+] Analisando Ataque Distribuído (Multiple Sources)...")
    # Lista de tuplas (timestamp, ip) para falhas
    fail_events = []

    for evt in events:
        if evt.event_type == 'auth_fail':
            fail_events.append((evt.timestamp, evt.src_ip))

    # Janela deslizante
    window_start = 0
    unique_ips = defaultdict(int) # ip -> count in window

    # Simulação de janela deslizante
    # Para simplificar, iterar e olhar para tras window

    # Mas é mais fácil iterar e limpar:
    # Vamos agrupar por minuto? Não, sliding window precisa ser preciso.

    # Melhor: Iterar eventos. Para cada evento, contar quantos IPs unicos falharam nos ultimos TIME_WINDOW

    # Otimização: manter uma deque de (timestamp, ip) dentro da janela
    window = deque()
    reported_windows = set() # evitar spam

    for ts, ip in fail_events:
        window.append((ts, ip))

        # Remove old
        while window and window[0][0] < ts - TIME_WINDOW:
            window.popleft()

        # Count unique IPs in window
        unique_ips_in_window = set(x[1] for x in window)

        if len(unique_ips_in_window) >= DISTRIBUTED_THRESHOLD:
            # Check if we recently reported logic to avoid spam per event
            # Use timestamp rounded to minute as key
            key = int(ts / 60)
            if key not in reported_windows:
                print(f"   [ALERTA] Ataque Distribuído Detectado! {len(unique_ips_in_window)} IPs diferentes falharam autenticação nos últimos {TIME_WINDOW}s.")
                reported_windows.add(key)

def detect_lateral_movement(events):
    print("\n[+] Analisando Movimentação Lateral...")
    logins = {}

    for evt in events:
        if evt.event_type == 'auth_success':
            logins[evt.user] = (evt.timestamp, evt.src_ip)

        elif evt.event_type == 'sudo':
            if evt.user in logins:
                login_ts, login_ip = logins[evt.user]
                if evt.timestamp - login_ts <= LATERAL_WINDOW:
                    print(f"   [ALERTA] Movimentação Lateral/Escalação: '{evt.user}' sudo após login de {login_ip}.")
                    del logins[evt.user]

def main():
    parser = argparse.ArgumentParser(description="SOC - Correlação de Eventos")
    parser.add_argument('--logs', nargs='+', required=True, help="Lista de arquivos de log")
    args = parser.parse_args()

    events = analyze_logs(args.logs)
    if not events:
        print("[-] Nenhum evento relevante encontrado.")
        return

    detect_brute_force(events)
    detect_distributed_attack(events)
    detect_lateral_movement(events)
    print("\n[*] Análise concluída.")

if __name__ == "__main__":
    main()
