#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Firewall Dinâmica Autônoma
==========================
Monitora conexões em tempo real e aplica regras de bloqueio (iptables)
baseado em comportamento abusivo (DoS, Scan, Flood).

Recursos:
- Detecção de SYN Flood (Muitos SYN_RECV).
- Detecção de Connection Flood (Muitas conexões de um único IP).
- Lista de permissão (Whitelist) para evitar auto-bloqueio.
- Modo Dry-Run (padrão) para segurança.

Uso:
    python3 firewall_dinamica_autonomo.py --max-conns 50 --apply
"""

import argparse
import subprocess
import time
import re
import sys
import os
from collections import defaultdict

# Configurações
WHITELIST = ["127.0.0.1", "::1", "0.0.0.0", "*", "::"] # Adicione IPs confiáveis aqui
CHECK_INTERVAL = 5 # Segundos

def get_active_connections_ss():
    """Usa o comando 'ss' para obter estatísticas de conexão mais detalhadas e rápidas."""
    conns = []
    try:
        # ss -ntu (TCP e UDP, numérico, todas as conexões)
        cmd = ["ss", "-ntu"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        lines = result.stdout.splitlines()[1:] # Pular cabeçalho
        for line in lines:
            parts = line.split()
            if len(parts) < 5: continue

            state = parts[1]
            # Ignorar sockets em Listen (não são conexões remotas ativas)
            if state == 'LISTEN':
                continue

            # ss output: Netid State Recv-Q Send-Q Local Peer
            # Dependendo da versão, pode variar. Geralmente índice 5 é Peer.
            # Mas se tiver coluna extra, pode deslocar.
            # Vamos assumir o padrão (idx 5).
            peer = parts[5]

            # Extrair IP (suporta IPv4 e IPv6 [..])
            if "]" in peer: # IPv6
                ip = peer.split("]:")[0].strip("[")
            else:
                ip = peer.split(":")[0]

            if ip in WHITELIST:
                continue

            conns.append({"ip": ip, "state": state})

    except Exception as e:
        print(f"[!] Erro ao executar ss: {e}")
    return conns

def block_ip(ip, reason, apply_rules=False):
    if ip in WHITELIST:
        print(f"[IGNORADO] Tentativa de bloquear IP na whitelist: {ip} ({reason})")
        return False

    print(f"[BLOQUEIO] Detectado {ip}: {reason}")

    cmd = ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP", "-m", "comment", "--comment", f"AutoBlock: {reason}"]

    if apply_rules:
        try:
            subprocess.run(cmd, check=True)
            print(f"   [SUCESSO] Regra aplicada: iptables -A INPUT -s {ip} -j DROP")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   [ERRO] Falha ao aplicar regra: {e}")
    else:
        print(f"   [DRY-RUN] Comando seria: {' '.join(cmd)}")

    return False

def monitor_and_protect(max_conns, max_syn, apply_rules):
    print(f"[*] Iniciando Firewall Autônoma...")
    print(f"[*] Limite Conexões/IP: {max_conns}")
    print(f"[*] Limite SYN_RECV/IP: {max_syn}")
    print(f"[*] Modo de Aplicação: {'ATIVADO' if apply_rules else 'DRY-RUN (Apenas simulação)'}")

    blocked_ips = set()

    while True:
        conns = get_active_connections_ss()

        ip_counts = defaultdict(int)
        syn_counts = defaultdict(int)

        for c in conns:
            ip = c["ip"]
            state = c["state"]

            ip_counts[ip] += 1
            if state == "SYN-RECV":
                syn_counts[ip] += 1

        # Analisar contagens
        for ip, count in ip_counts.items():
            if ip in blocked_ips: continue

            if count > max_conns:
                if block_ip(ip, f"Connection Flood ({count} conns)", apply_rules):
                    blocked_ips.add(ip)

        for ip, count in syn_counts.items():
            if ip in blocked_ips: continue

            if count > max_syn:
                if block_ip(ip, f"SYN Flood ({count} syn-recv)", apply_rules):
                    blocked_ips.add(ip)

        time.sleep(CHECK_INTERVAL)

def main():
    parser = argparse.ArgumentParser(description="Firewall Dinâmica Autônoma")
    parser.add_argument('--max-conns', type=int, default=100, help="Máximo de conexões simultâneas por IP (Padrão: 100)")
    parser.add_argument('--max-syn', type=int, default=10, help="Máximo de conexões SYN_RECV por IP (Padrão: 10)")
    parser.add_argument('--apply', action='store_true', help="Aplicar regras iptables reais (Requer root)")

    args = parser.parse_args()

    if args.apply and os.geteuid() != 0:
        print("[!] AVISO: Modo --apply requer privilégios de root para modificar iptables.")

    try:
        monitor_and_protect(args.max_conns, args.max_syn, args.apply)
    except KeyboardInterrupt:
        print("\n[*] Firewall encerrada.")

if __name__ == "__main__":
    main()
