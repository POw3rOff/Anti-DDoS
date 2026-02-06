#!/bin/bash

# ==============================================================================
# Script: Dashboard de Estado
# Descrição: Exibe um painel de controle simples com o status atual da segurança.
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

clear
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}       PAINEL DE CONTROLE DE SEGURANÇA (DASHBOARD)    ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "Host: $(hostname) | IP: $(hostname -I | cut -d" " -f1) | Kernel: $(uname -r)"
echo -e "${BLUE}------------------------------------------------------${NC}"

# 1. Status do Último Score
SCORE_FILE="/tmp/last_security_score"
if [ -f "$SCORE_FILE" ]; then
    SCORE=$(cat "$SCORE_FILE")
    if [ "$SCORE" -lt 50 ]; then COLOR=$RED;
    elif [ "$SCORE" -lt 80 ]; then COLOR=$YELLOW;
    else COLOR=$GREEN; fi
    echo -e "Último Score de Segurança: ${COLOR}${SCORE}/100${NC}"
else
    echo -e "Último Score de Segurança: ${YELLOW}N/A (Execute o score_global_seguranca.sh)${NC}"
fi

# 2. Status do Firewall
if command -v ufw &>/dev/null && ufw status | grep -q "active"; then
    echo -e "Firewall (UFW):            ${GREEN}ATIVO${NC}"
elif iptables -L -n | grep -q "Chain INPUT (policy DROP)"; then
    echo -e "Firewall (IPTables):       ${GREEN}ATIVO (Política DROP)${NC}"
else
    echo -e "Firewall:                  ${RED}INATIVO ou NÃO DETECTADO${NC}"
fi

# 3. Status de Conexões Ativas (Top 3 portas)
echo -e "${BLUE}------------------------------------------------------${NC}"
echo -e "Portas Ouvindo (Top 5):"
ss -tuln | head -n 6 | tail -n 5

# 4. Uso de Disco /
DISK=$(df -h / | awk 'NR==2 {print $5}')
echo -e "${BLUE}------------------------------------------------------${NC}"
echo -e "Uso de Disco (/):          ${YELLOW}$DISK${NC}"

# 5. Dependências Críticas
MISSING=0
for cmd in awk grep sed ip curl; do
    if ! command -v $cmd &>/dev/null; then MISSING=1; fi
done
if [ "$MISSING" -eq 0 ]; then
    echo -e "Ferramentas Básicas:       ${GREEN}OK${NC}"
else
    echo -e "Ferramentas Básicas:       ${RED}FALHA${NC}"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "Para atualizar, execute este script novamente."
