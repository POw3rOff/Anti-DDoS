#!/bin/bash
# Script: alerta_container_comprometido.sh
# Descrição: Busca sinais de comprometimento em logs e estados de containers.
# Autor: Jules

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Runtime não encontrado."
    exit 1
fi

echo "=== Análise de Comprometimento de Containers ==="

KEYWORDS="Permission denied|segfault|core dump|exploit|attack|unauthorized|root check|uid=0"

for id in $($RUNTIME ps -aq); do
    name=$($RUNTIME inspect --format "{{.Name}}" "$id" | sed "s/\///")
    state=$($RUNTIME inspect --format "{{.State.Status}}" "$id")
    oom=$($RUNTIME inspect --format "{{.State.OOMKilled}}" "$id")
    exit_code=$($RUNTIME inspect --format "{{.State.ExitCode}}" "$id")

    # 1. Verificar OOM Killed (Pode ser DoS ou memory leak)
    if [ "$oom" == "true" ]; then
        echo "[ALERTA] $name foi morto por falta de memória (OOMKilled)."
    fi

    # 2. Verificar Exit Code suspeito (ex: 139 = segfault, 137 = kill -9)
    if [ "$state" == "exited" ] && [ "$exit_code" -gt 0 ]; then
        if [ "$exit_code" -eq 139 ]; then
            echo "[ALERTA] $name terminou com Segmentation Fault (código 139) - Possível exploit?"
        elif [ "$exit_code" -eq 137 ]; then
             echo "[AVISO] $name foi forçado a parar (SIGKILL - código 137)."
        fi
    fi

    # 3. Analisar Logs Recentes
    # Apenas se estiver rodando ou terminou recentemente
    logs=$($RUNTIME logs --tail 200 "$id" 2>&1)

    if echo "$logs" | grep -iE "$KEYWORDS" > /dev/null; then
        echo "[PERIGO] Logs suspeitos encontrados em $name:"
        echo "$logs" | grep -iE "$KEYWORDS" | head -n 5
        echo "..."
    fi
done

echo "Análise concluída."
