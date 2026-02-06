#!/bin/bash
# Script: monitorizacao_runtime_container.sh
# Descrição: Monitora recursos e processos suspeitos em containers ativos.
# Autor: Jules

THRESH_CPU=80
THRESH_MEM=80

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Runtime não encontrado."
    exit 1
fi

echo "=== Monitorização Runtime de Containers ==="
echo "Data: $(date)"

# 1. Verificar Recursos (CPU/MEM)
echo "--- Verificação de Recursos ---"
# docker stats output: CONTAINER ID, NAME, CPU %, MEM USAGE / LIMIT, MEM %, ...
$RUNTIME stats --no-stream --format "{{.Name}} {{.CPUPerc}} {{.MemPerc}}" | tr -d '%' | while read name cpu mem; do
    # Remover sufixos de unidade se houver (mas tr -d % já limpou percentual)
    # CPU pode ser 0.00 ou 105.00
    cpu_int=${cpu%.*}
    mem_int=${mem%.*}

    if [ "$cpu_int" -ge "$THRESH_CPU" ]; then
        echo "[ALERTA] $name: Alta Carga de CPU (${cpu}%)"
    fi

    if [ "$mem_int" -ge "$THRESH_MEM" ]; then
        echo "[ALERTA] $name: Alto Uso de Memória (${mem}%)"
    fi
done

# 2. Verificar Processos Suspeitos
echo "--- Verificação de Processos Suspeitos ---"
SUSPICIOUS_PROCS="nc|netcat|ncat|ssh|sshd|xmrig|minerd"

for id in $($RUNTIME ps -q); do
    name=$($RUNTIME inspect --format "{{.Name}}" "$id" | sed "s/\///")

    # Listar processos dentro do container
    procs=$($RUNTIME top "$id")

    if echo "$procs" | grep -E "$SUSPICIOUS_PROCS" > /dev/null; then
        echo "[PERIGO] Processo suspeito detectado em $name!"
        echo "$procs" | grep -E "$SUSPICIOUS_PROCS"
    fi
done

echo "Monitorização concluída."
