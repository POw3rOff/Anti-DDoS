#!/bin/bash
# Script: detecao_containers_privilegiados.sh
# Descrição: Detecta containers rodando em modo privilegiado ou com capabilities perigosas.
# Autor: Jules

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Docker ou Podman não encontrados."
    exit 1
fi

echo "=== Detecção de Containers Privilegiados ==="
FOUND_ISSUES=0

for id in $($RUNTIME ps -q); do
    name=$($RUNTIME inspect --format "{{.Name}}" "$id" | sed "s/\///")
    privileged=$($RUNTIME inspect --format "{{.HostConfig.Privileged}}" "$id")
    caps=$($RUNTIME inspect --format "{{.HostConfig.CapAdd}}" "$id")

    IS_DANGEROUS=0
    MSG=""

    if [ "$privileged" == "true" ]; then
        MSG="$MSG [PRIVILEGED]"
        IS_DANGEROUS=1
    fi

    if echo "$caps" | grep -E "SYS_ADMIN|NET_ADMIN|ALL" > /dev/null; then
        MSG="$MSG [DANGEROUS CAPS: $caps]"
        IS_DANGEROUS=1
    fi

    if [ $IS_DANGEROUS -eq 1 ]; then
        echo "[ALERTA] Container: $name - $MSG"
        FOUND_ISSUES=1
    fi
done

if [ $FOUND_ISSUES -eq 0 ]; then
    echo "Nenhum container privilegiado detectado."
else
    echo ""
    echo "ATENÇÃO: Containers privilegiados têm acesso quase total ao host!"
fi
