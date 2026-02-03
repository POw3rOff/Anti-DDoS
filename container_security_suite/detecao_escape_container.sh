#!/bin/bash
# Script: detecao_escape_container.sh
# Descrição: Detecta configurações que facilitam escape de container para o host.
# Autor: Jules

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Runtime não encontrado."
    exit 1
fi

echo "=== Scan de Vetores de Escape de Container ==="

for id in $($RUNTIME ps -q); do
    name=$($RUNTIME inspect --format "{{.Name}}" "$id" | sed "s/\///")

    # 1. Namespaces de Host
    pid_mode=$($RUNTIME inspect --format "{{.HostConfig.PidMode}}" "$id")
    ipc_mode=$($RUNTIME inspect --format "{{.HostConfig.IpcMode}}" "$id")
    net_mode=$($RUNTIME inspect --format "{{.HostConfig.NetworkMode}}" "$id")

    # 2. Mounts perigosos
    mounts=$($RUNTIME inspect --format "{{json .Mounts}}" "$id")

    RISK=0

    if [ "$pid_mode" == "host" ]; then
        echo "[CRÍTICO] $name usa PID namespace do host (pode matar processos do host)."
        RISK=1
    fi
    if [ "$ipc_mode" == "host" ]; then
        echo "[ALTA] $name usa IPC namespace do host (memória compartilhada)."
        RISK=1
    fi
    if [ "$net_mode" == "host" ]; then
        echo "[ALTA] $name usa Network do host (bypass firewall container)."
        RISK=1
    fi

    # Verificar mounts sensíveis
    # Docker socket
    if echo "$mounts" | grep -q "docker.sock"; then
        echo "[CRÍTICO] $name monta o socket do Docker (controle total do host)."
        RISK=1
    fi
    # Raiz do host
    if echo "$mounts" | grep -q '"Source":"/"'; then
        echo "[CRÍTICO] $name monta a raiz do sistema (/)."
        RISK=1
    fi
    # /proc ou /sys
    if echo "$mounts" | grep -q '"Source":"/proc"'; then
        echo "[ALTA] $name monta /proc do host."
        RISK=1
    fi

done

echo "Scan concluído."
