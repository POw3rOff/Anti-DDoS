#!/bin/bash

# Script: alerta_kernel_anomalo.sh
# Descrição: Verifica logs do kernel em busca de anomalias críticas (Oops, Panic, Segfaults).
# Autor: Jules (Agente de IA)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

KEYWORDS="Call Trace|Oops|Kernel panic|segfault|Out of memory|Hardware Error|MCE|tainted"
LOG_FILES="/var/log/kern.log /var/log/syslog /var/log/messages /var/log/dmesg"

echo -e "${YELLOW}=== Análise de Anomalias do Kernel ===${NC}"

# 1. Verificar dmesg atual
echo -e "${YELLOW}[*] Analisando buffer atual do kernel (dmesg)...${NC}"
DMESG_ALERTS=$(dmesg | grep -E -i "$KEYWORDS" | tail -n 20)

if [ -n "$DMESG_ALERTS" ]; then
    echo -e "${RED}[!] Anomalias encontradas no dmesg (últimas 20 linhas relevantes):${NC}"
    echo "$DMESG_ALERTS"
else
    echo -e "${GREEN}[OK] Nenhuma anomalia crítica recente encontrada no dmesg.${NC}"
fi

# 2. Verificar arquivos de log históricos
echo -e "${YELLOW}[*] Analisando arquivos de log do sistema...${NC}"
FOUND_LOGS=0

for log in $LOG_FILES; do
    if [ -f "$log" ] && [ -r "$log" ]; then
        echo -e "${YELLOW}    -> Verificando $log...${NC}"
        # Grep nas últimas 1000 linhas para não ser lento demais
        LOG_ALERTS=$(tail -n 1000 "$log" | grep -E -i "$KEYWORDS" | tail -n 10)

        if [ -n "$LOG_ALERTS" ]; then
            echo -e "${RED}[!] Alertas encontrados em $log:${NC}"
            echo "$LOG_ALERTS"
            FOUND_LOGS=1
        fi
    fi
done

if [ $FOUND_LOGS -eq 0 ]; then
    echo -e "${GREEN}[OK] Nenhuma anomalia crítica encontrada nos logs recentes analisados.${NC}"
fi

echo -e "${YELLOW}=== Análise Concluída ===${NC}"
