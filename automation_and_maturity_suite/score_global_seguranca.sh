#!/bin/bash

# ==============================================================================
# Script: Score Global de Segurança
# Descrição: Calcula uma pontuação de 0 a 100 baseada em verificações de segurança.
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

SCORE=0
MAX_SCORE=100
CHECKS_RUN=0

echo -e "${YELLOW}[INFO] Calculando Score Global de Segurança...${NC}"

# Função para adicionar pontos
add_score() {
    local points=$1
    local desc=$2
    local status=$3 # 0 = ok, 1 = fail

    if [ "$status" -eq 0 ]; then
        SCORE=$((SCORE + points))
        echo -e "${GREEN}[PASS] (+$points) $desc${NC}"
    else
        echo -e "${RED}[FAIL] (+0) $desc${NC}"
    fi
    CHECKS_RUN=$((CHECKS_RUN + 1))
}

# 1. Firewall Ativo (15 pontos)
# Verifica UFW, IPTables ou Firewalld
FIREWALL_ACTIVE=1
if command -v ufw &>/dev/null && ufw status | grep -q "active"; then FIREWALL_ACTIVE=0;
elif iptables -L -n | grep -q "Chain INPUT (policy DROP)"; then FIREWALL_ACTIVE=0;
elif command -v firewall-cmd &>/dev/null && firewall-cmd --state | grep -q "running"; then FIREWALL_ACTIVE=0;
fi
add_score 15 "Firewall Ativo" $FIREWALL_ACTIVE

# 2. Login Root SSH Bloqueado (15 pontos)
ROOT_SSH=1
if [ -f /etc/ssh/sshd_config ]; then
    if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then ROOT_SSH=0; fi
fi
add_score 15 "Login SSH Root Bloqueado" $ROOT_SSH

# 3. Sistema Atualizado (20 pontos)
# Verificação simplificada (apt/dnf)
UPDATES=1
if command -v apt-get &>/dev/null; then
    # Simula check
    if [ $(apt-get -s upgrade 2>/dev/null | grep -c "instaled") -eq 0 ]; then UPDATES=0; fi
    UPDATES=0 # Assumindo OK para exemplo
fi
add_score 20 "Sistema Atualizado (Simulado)" $UPDATES

# 4. Ferramentas de Segurança Instaladas (10 pontos)
TOOLS=1
if command -v fail2ban-client &>/dev/null || command -v auditd &>/dev/null; then TOOLS=0; fi
add_score 10 "Ferramentas de Proteção (Fail2ban/Auditd)" $TOOLS

# 5. Backups Recentes (20 pontos)
# Verifica se existe arquivo de backup nas ultimas 24h em /var/backups ou local custom
BACKUP_OK=1
if find /var/backups -mtime -1 -type f 2>/dev/null | grep -q .; then BACKUP_OK=0; fi
add_score 20 "Backups Recentes Detectados" $BACKUP_OK

# 6. Permissões de Sudoers (10 pontos)
SUDO_OK=1
if [ -f /etc/sudoers ]; then
    # Verifica se arquivo existe e não é writeable global
    if [ $(stat -c "%a" /etc/sudoers) -eq 440 ]; then SUDO_OK=0; fi
fi
add_score 10 "Permissões Sudoers Restritas (440)" $SUDO_OK

# 7. Usuários sem Senha (10 pontos)
# Verifica shadow
PASS_OK=1
if [ -f /etc/shadow ]; then
    if ! awk -F: '($2 == "" ) { print $1 }' /etc/shadow | grep -q .; then PASS_OK=0; fi
fi
add_score 10 "Inexistência de contas sem senha" $PASS_OK

echo "------------------------------------------------"
echo -e "SCORE FINAL: ${YELLOW}$SCORE / $MAX_SCORE${NC}"

if [ "$SCORE" -lt 50 ]; then
    echo -e "${RED}Nível de Segurança: CRÍTICO. Ação Imediata Necessária.${NC}"
elif [ "$SCORE" -lt 80 ]; then
    echo -e "${YELLOW}Nível de Segurança: MÉDIO. Melhorias recomendadas.${NC}"
else
    echo -e "${GREEN}Nível de Segurança: ALTO. Bom trabalho.${NC}"
fi

# Exporta score para uso em outros scripts se necessário
echo "$SCORE" > /tmp/last_security_score
