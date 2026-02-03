#!/bin/bash

# ==============================================================================
# Script: Detecção de Execuções Falhadas
# Descrição: Monitora logs do sistema em busca de falhas na execução de scripts de segurança.
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

RED="\033[0;31m"
YELLOW="\033[1;33m"
GREEN="\033[0;32m"
NC="\033[0m"

# Arquivos de log comuns
LOGS=("/var/log/syslog" "/var/log/messages" "/var/log/auth.log")
KEYWORDS=("Falha no script" "Permission denied" "command not found" "Error executing" "segfault")

echo -e "${YELLOW}[INFO] Buscando indícios de falhas de execução nas últimas 24h...${NC}"

FOUND=0

# Define filtro de tempo (ex: grep do dia atual ou ultimas linhas)
# Para simplificar e ser compatível, vamos olhar as ultimas 1000 linhas se o log for grande
# ou usar find com mtime se logs forem rotacionados.

for log in "${LOGS[@]}"; do
    if [ -f "$log" ]; then
        echo -e "${YELLOW}[INFO] Analisando $log...${NC}"

        for key in "${KEYWORDS[@]}"; do
            # Busca case-insensitive
            MATCHES=$(grep -i "$key" "$log" | tail -n 5)
            if [ ! -z "$MATCHES" ]; then
                echo -e "${RED}[DETECTADO] Possíveis falhas encontradas em $log (palavra-chave: '$key'):${NC}"
                echo "$MATCHES"
                FOUND=1
            fi
        done
    fi
done

# Verificar status de serviços systemd se existirem scripts rodando como serviços
if command -v systemctl &> /dev/null; then
    echo -e "${YELLOW}[INFO] Verificando unidades systemd falhadas...${NC}"
    FAILED_UNITS=$(systemctl list-units --state=failed --no-legend)
    if [ ! -z "$FAILED_UNITS" ]; then
        echo -e "${RED}[DETECTADO] Serviços falhados:${NC}"
        echo "$FAILED_UNITS"
        FOUND=1
    else
        echo -e "${GREEN}[OK] Nenhuma unidade systemd em estado de falha.${NC}"
    fi
fi

if [ "$FOUND" -eq 0 ]; then
    echo -e "${GREEN}[SUCESSO] Nenhuma falha crítica recente detectada nos logs padrão.${NC}"
    exit 0
else
    echo -e "${RED}[ATENÇÃO] Verifique os logs acima para detalhes das falhas.${NC}"
    exit 1
fi
