#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Orquestrador de Resposta a Incidentes
=====================================
Motor de automação para resposta a incidentes de segurança.
Executa ações de contenção, preservação de evidências e notificação.

Ações Suportadas:
- block_ip: Bloqueia tráfego de entrada/saída de um IP específico.
- isolate_host: Isola a máquina da rede (exceto IPs de gestão).
- snapshot: Coleta logs e evidências voláteis.
- notify: Envia alertas (Simulado/Stdout).

Uso:
    python3 orquestrador_resposta_incidente.py --action block_ip --target 192.168.1.100
    python3 orquestrador_resposta_incidente.py --action isolate_host --mgmt-ip 10.0.0.5
    python3 orquestrador_resposta_incidente.py --action snapshot
"""

import argparse
import subprocess
import os
import sys
import shutil
from datetime import datetime
import json

EVIDENCE_DIR = "/var/log/security_evidence"
MGMT_PORTS = ["22"] # SSH

def run_cmd(cmd):
    try:
        print(f"[*] Executando: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] Erro ao executar comando: {e}")
        return False

def action_block_ip(ip):
    print(f"[ACTION] Bloqueando IP: {ip}")
    # Iptables Drop Input and Output
    cmds = [
        ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP", "-m", "comment", "--comment", "IncidentResponse_Block"],
        ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP", "-m", "comment", "--comment", "IncidentResponse_Block"]
    ]
    success = True
    for cmd in cmds:
        if not run_cmd(cmd): success = False

    if success:
        print(f"[OK] IP {ip} bloqueado com sucesso.")

def action_isolate_host(mgmt_ip):
    print(f"[ACTION] Isolando Host (Permitindo apenas gestão de {mgmt_ip})")

    # 1. Permitir Loopback
    run_cmd(["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
    run_cmd(["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])

    # 2. Permitir conexões estabelecidas
    run_cmd(["iptables", "-A", "INPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"])

    # 3. Permitir Gestão (SSH) do IP confiável
    if mgmt_ip:
        for port in MGMT_PORTS:
            run_cmd(["iptables", "-A", "INPUT", "-s", mgmt_ip, "-p", "tcp", "--dport", port, "-j", "ACCEPT"])

    # 4. Bloquear todo o resto (INPUT e OUTPUT)
    # Cuidado: Isso corta acesso se não configurado direito.
    # Vamos setar policy para DROP é arriscado em script cego.
    # Vamos adicionar regras de DROP no final da chain.

    run_cmd(["iptables", "-A", "INPUT", "-j", "DROP", "-m", "comment", "--comment", "IncidentResponse_Isolation"])
    run_cmd(["iptables", "-A", "OUTPUT", "-j", "DROP", "-m", "comment", "--comment", "IncidentResponse_Isolation"])

    print("[OK] Host isolado.")

def action_snapshot():
    print(f"[ACTION] Coletando Evidências (Snapshot)...")

    if not os.path.exists(EVIDENCE_DIR):
        os.makedirs(EVIDENCE_DIR)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(EVIDENCE_DIR, f"evidence_{ts}")
    os.makedirs(dest_dir)

    # Lista de arquivos/comandos para coletar
    tasks = [
        ("cp /var/log/auth.log", f"{dest_dir}/auth.log"),
        ("cp /var/log/syslog", f"{dest_dir}/syslog"),
        ("netstat -tuln >", f"{dest_dir}/netstat.txt"),
        ("ps aux >", f"{dest_dir}/ps_aux.txt"),
        ("lsof -n >", f"{dest_dir}/lsof.txt"),
        ("iptables-save >", f"{dest_dir}/iptables_rules.txt")
    ]

    for cmd, dest in tasks:
        # Simplificação: se for cp, usa shutil. Se for comando, subprocess shell.
        try:
            if cmd.startswith("cp "):
                src = cmd.split()[1]
                shutil.copy2(src, dest)
            elif ">" in cmd:
                real_cmd = cmd.replace(">", "").strip()
                with open(dest, "w") as f:
                    subprocess.run(real_cmd.split(), stdout=f)
        except Exception as e:
            print(f"[!] Falha na tarefa '{cmd}': {e}")

    # Compress
    shutil.make_archive(dest_dir, 'gztar', dest_dir)
    print(f"[OK] Evidências salvas em {dest_dir}.tar.gz")

def action_notify(message):
    print(f"[NOTIFICATION] >>> {message}")
    # Aqui entraria integração com Slack/Email
    # Ex: requests.post(webhook_url, json={"text": message})

def main():
    parser = argparse.ArgumentParser(description="Orquestrador de Resposta a Incidentes")
    parser.add_argument('--action', choices=['block_ip', 'isolate_host', 'snapshot', 'notify'], required=True, help="Ação a executar")
    parser.add_argument('--target', help="Alvo (IP) para block_ip")
    parser.add_argument('--mgmt-ip', help="IP de gestão permitido para isolate_host")
    parser.add_argument('--message', help="Mensagem para notificação")

    args = parser.parse_args()

    # Check root for blocking/isolation
    if args.action in ['block_ip', 'isolate_host'] and os.geteuid() != 0:
        print("[!] Erro: Privilégios de root necessários para alterar firewall.")
        sys.exit(1)

    if args.action == 'block_ip':
        if not args.target:
            print("[!] Erro: --target IP necessário.")
            sys.exit(1)
        action_block_ip(args.target)
        action_notify(f"IP {args.target} foi bloqueado automaticamente.")

    elif args.action == 'isolate_host':
        if not args.mgmt_ip:
            print("[!] Aviso: --mgmt-ip não fornecido. Você pode perder acesso se estiver via SSH.")
            confirm = input("Deseja continuar sem IP de gestão? (s/n): ")
            if confirm.lower() != 's':
                sys.exit(0)
        action_isolate_host(args.mgmt_ip)
        action_notify(f"Host isolado da rede (exceto gestão {args.mgmt_ip}).")

    elif args.action == 'snapshot':
        action_snapshot()
        action_notify("Snapshot de evidências coletado.")

    elif args.action == 'notify':
        action_notify(args.message if args.message else "Teste de notificação.")

if __name__ == "__main__":
    main()
