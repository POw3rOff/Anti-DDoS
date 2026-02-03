#!/bin/bash
# Script: auditoria_containers.sh
# Descrição: Audita configurações gerais de segurança de containers em execução.
# Autor: Jules

# Detetar Runtime
if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Docker ou Podman não encontrados."
    exit 1
fi

echo "=== Auditoria Geral de Containers ($RUNTIME) ==="
echo "Data: $(date)"

# Formatar saída
printf "%-20s %-15s %-15s %-15s %-15s %-10s\n" "CONTAINER" "USER" "MEM_LIMIT" "NET_MODE" "RESTART" "READONLY"
echo "-----------------------------------------------------------------------------------------------"

# Listar IDs de containers em execução
for id in $($RUNTIME ps -q); do
    # Obter dados
    name=$($RUNTIME inspect --format "{{.Name}}" "$id" | sed "s/\///")
    user=$($RUNTIME inspect --format "{{.Config.User}}" "$id")
    [ -z "$user" ] && user="root(padrao)"

    mem_limit=$($RUNTIME inspect --format "{{.HostConfig.Memory}}" "$id")
    if [ "$mem_limit" -eq 0 ]; then mem_limit="Sem Limite"; else mem_limit="${mem_limit}B"; fi

    net_mode=$($RUNTIME inspect --format "{{.HostConfig.NetworkMode}}" "$id")
    restart_policy=$($RUNTIME inspect --format "{{.HostConfig.RestartPolicy.Name}}" "$id")
    readonly_fs=$($RUNTIME inspect --format "{{.HostConfig.ReadonlyRootfs}}" "$id")

    printf "%-20s %-15s %-15s %-15s %-15s %-10s\n"         "${name:0:20}" "$user" "$mem_limit" "$net_mode" "$restart_policy" "$readonly_fs"
done

echo ""
echo "=== Recomendações ==="
echo "1. Defina limites de memória e CPU para evitar DoS."
echo "2. Evite rodar como root (Use USER no Dockerfile)."
echo "3. Use read-only filesystem sempre que possível."
echo "4. Evite network_mode: host em produção."
