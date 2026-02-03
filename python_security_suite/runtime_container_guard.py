#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Runtime Container Guard
=======================
Monitora containers Docker em tempo real para detectar atividades suspeitas.
- Deteta criação de containers privilegiados.
- Deteta montagens de diretórios sensíveis do host (/proc, /sys, /etc).
- Alerta sobre execuções de shell (docker exec /bin/sh).

Requisitos:
    - Docker CLI instalado e acessível.
    - Usuário com permissão no grupo 'docker'.

Uso:
    python3 runtime_container_guard.py
"""

import subprocess
import json
import time
import argparse
import sys
import re
from datetime import datetime

# Diretórios sensíveis que não devem ser montados
SENSITIVE_MOUNTS = [
    "/proc",
    "/sys",
    "/etc",
    "/root",
    "/var/run/docker.sock"
]

def log_alert(level, message, container_id=None, image=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx = f" [Container: {container_id[:12]}]" if container_id else ""
    ctx += f" [Img: {image}]" if image else ""
    print(f"[{ts}] [{level}]{ctx} {message}")

def inspect_container(container_id):
    """Executa docker inspect e analisa configurações de segurança."""
    try:
        cmd = ["docker", "inspect", container_id]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return

        data = json.loads(result.stdout)[0]
        image = data['Config']['Image']
        host_config = data.get('HostConfig', {})

        # 1. Privileged Mode
        if host_config.get('Privileged'):
            log_alert("CRITICO", "Container iniciado em modo PRIVILEGED!", container_id, image)

        # 2. Sensitive Mounts
        mounts = data.get('Mounts', [])
        for m in mounts:
            source = m.get('Source', '')
            for sensitive in SENSITIVE_MOUNTS:
                if source.startswith(sensitive):
                    log_alert("ALTA", f"Montagem sensível detectada: {source} -> {m['Destination']}", container_id, image)

        # 3. Capabilities
        caps = host_config.get('CapAdd')
        if caps:
            if 'SYS_ADMIN' in caps or 'NET_ADMIN' in caps:
                log_alert("ALTA", f"Capabilities perigosas adicionadas: {caps}", container_id, image)

        # 4. PID Host
        if host_config.get('PidMode') == 'host':
            log_alert("ALTA", "Container compartilha PID Namespace com o host!", container_id, image)

        # 5. Network Host
        if host_config.get('NetworkMode') == 'host':
            log_alert("MEDIA", "Container compartilha Network Namespace com o host.", container_id, image)

    except Exception as e:
        log_alert("ERRO", f"Falha ao inspecionar container: {e}", container_id)

def monitor_events():
    """Lê stream de eventos do Docker."""
    print("[*] Iniciando monitoramento de containers Docker...")

    # Filtra eventos de container
    cmd = ["docker", "events", "--format", "{{json .}}", "--filter", "type=container"]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in process.stdout:
            try:
                event = json.loads(line)
                action = event.get('Action')
                actor = event.get('Actor', {})
                container_id = actor.get('ID')
                attributes = actor.get('Attributes', {})
                image = attributes.get('image', 'unknown')

                # Evento: Start/Create
                if action == 'start':
                    log_alert("INFO", "Container iniciado. Analisando conformidade...", container_id, image)
                    inspect_container(container_id)

                # Evento: Exec (Execução de comando em container rodando)
                elif action == 'exec_create':
                    exec_cmd = attributes.get('execID', 'unknown')
                    # docker events não mostra o comando exato no exec_create diretamente no json padrão as vezes
                    # Mas podemos tentar inferir ou apenas alertar.
                    # Para saber o comando, precisaríamos inspecionar o execID, mas é efêmero.
                    log_alert("AVISO", f"Execução de comando detectada (possível shell interativo).", container_id, image)

                elif action == 'die':
                    # Container parou
                    pass

            except json.JSONDecodeError:
                pass

    except FileNotFoundError:
        print("[!] Erro: Docker CLI não encontrado. O Docker está instalado?")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[*] Monitoramento encerrado.")

def main():
    parser = argparse.ArgumentParser(description="Runtime Container Guard")
    args = parser.parse_args()

    monitor_events()

if __name__ == "__main__":
    main()
