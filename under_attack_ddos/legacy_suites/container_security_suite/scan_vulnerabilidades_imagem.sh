#!/bin/bash
# Script: scan_vulnerabilidades_imagem.sh
# Descrição: Scan de más práticas e configurações inseguras em imagens Docker.
# Autor: Jules

IMAGE_NAME=$1

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Runtime não encontrado."
    exit 1
fi

if [ -z "$IMAGE_NAME" ]; then
    echo "Uso: $0 <nome_imagem> ou 'all'"
    echo "Exemplo: $0 nginx:latest"
    exit 1
fi

scan_image() {
    local img=$1
    echo ">>> Analisando imagem: $img"
    local score=0

    # Obter JSON de configuração
    local config=$($RUNTIME inspect "$img" 2>/dev/null)

    if [ -z "$config" ]; then
        echo "Erro: Imagem não encontrada."
        return
    fi

    # 1. Verificar Usuario Root
    # Melhorado para usar format string em vez de grep no JSON
    local user=$($RUNTIME inspect --format '{{.Config.User}}' "$img")
    if [ -z "$user" ] || [ "$user" == "root" ] || [ "$user" == "0" ]; then
        echo "  [ALTA] Executa como ROOT (User não definido ou 0)."
        score=$((score + 3))
    else
        echo "  [OK] Usuário definido: $user"
    fi

    # 2. Verificar Tag Latest
    if [[ "$img" == *":latest" ]]; then
        echo "  [MÉDIA] Uso da tag 'latest' (não versionado)."
        score=$((score + 2))
    fi

    # 3. Verificar Healthcheck
    if ! echo "$config" | grep -q '"Healthcheck":'; then
        echo "  [BAIXA] Healthcheck não configurado."
        score=$((score + 1))
    fi

    # 4. Verificar Segredos em ENV (Melhorado)
    local envs=$($RUNTIME inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$img")
    if echo "$envs" | grep -iE "pass=|key=|secret=|token="; then
        echo "  [CRÍTICO] Possíveis credenciais em variáveis de ambiente (ENV)."
        score=$((score + 5))
    fi

    # 5. Portas de risco (ex: 22)
    local ports=$($RUNTIME inspect --format '{{json .Config.ExposedPorts}}' "$img")
    if echo "$ports" | grep -q '"22/tcp":'; then
        echo "  [ALTA] Porta SSH (22) exposta. Containers não devem rodar SSHD."
        score=$((score + 3))
    fi

    echo "  >> Score de Risco: $score (0=Bom, >5=Ruim)"
    echo "---------------------------------------------------"
}

if [ "$IMAGE_NAME" == "all" ]; then
    for img in $($RUNTIME images --format "{{.Repository}}:{{.Tag}}"); do
        scan_image "$img"
    done
else
    scan_image "$IMAGE_NAME"
fi
