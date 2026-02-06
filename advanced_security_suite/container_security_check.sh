#!/bin/bash
#
# 8. Detetor de Containers Suspeitos (Docker/Podman)
# Autor: Jules (AI Agent)
# Descrição: Verifica containers privilegiados ou com mounts inseguros.

RUNTIME=""
if command -v docker >/dev/null; then
    RUNTIME="docker"
elif command -v podman >/dev/null; then
    RUNTIME="podman"
fi

if [ -z "$RUNTIME" ]; then
    echo "Info: Nenhum container runtime (docker/podman) encontrado."
else
    echo "[*] Usando runtime: $RUNTIME"

    # Lista containers rodando
    CONTAINERS=$($RUNTIME ps -q)

    if [ -z "$CONTAINERS" ]; then
        echo "[OK] Nenhum container em execução."
    else
        for cid in $CONTAINERS; do
            name=$($RUNTIME inspect --format '{{.Name}}' "$cid")

            # 1. Verifica modo privilegiado (--privileged)
            privileged=$($RUNTIME inspect --format '{{.HostConfig.Privileged}}' "$cid")

            # 2. Verifica mounts sensíveis (ex: / var/run/docker.sock)
            mounts=$($RUNTIME inspect --format '{{json .Mounts}}' "$cid")

            suspicious=0

            if [ "$privileged" == "true" ]; then
                echo "[!] ALERTA: Container Privilegiado: $name ($cid)"
                suspicious=1
            fi

            if echo "$mounts" | grep -q "docker.sock"; then
                echo "[!] ALERTA: Container com acesso ao Docker Socket: $name ($cid)"
                suspicious=1
            fi

            # Escape de aspas para grep pode variar, usando string simples se possivel ou regex
            if echo "$mounts" | grep -q '"Source":"/"'; then
                echo "[!] ALERTA: Container com mount da raiz do host (/): $name ($cid)"
                suspicious=1
            fi

            if [ "$suspicious" -eq 0 ]; then
                echo "[OK] Container $name parece limpo (verificação básica)."
            fi
        done
    fi
fi
