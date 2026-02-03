#!/bin/bash
# Script: compliance_check.sh
# Descrição: Verifica a conformidade do ambiente de backup com políticas de segurança e governança.
# Autor: Jules (Assistant)

BACKUP_DIR="/var/backups"
LOG_DIR="/var/log/backups"
CONFIG_FILE="/etc/backup.conf"

FAILURES=0
WARNINGS=0

pass() { echo -e "[\e[32mPASS\e[0m] $1"; }
fail() { echo -e "[\e[31mFAIL\e[0m] $1"; FAILURES=$((FAILURES+1)); }
warn() { echo -e "[\e[33mWARN\e[0m] $1"; WARNINGS=$((WARNINGS+1)); }

echo "=== Verificação de Compliance de Backup ==="

# 1. Verificar existência do diretório de backup
if [ -d "$BACKUP_DIR" ]; then
    pass "Diretório de backup existe ($BACKUP_DIR)."
else
    fail "Diretório de backup não encontrado."
fi

# 2. Verificar encriptação (procura por arquivos encriptados)
if find "$BACKUP_DIR" -name "*.gpg" -o -name "*.enc" -o -name "*.age" | grep -q .; then
    pass "Arquivos encriptados detetados."
else
    warn "Nenhum arquivo com extensão de encriptação (.gpg, .enc, .age) encontrado."
fi

# 3. Verificar logs de auditoria/imutabilidade
if lsattr "$LOG_DIR"/*.log 2>/dev/null | grep -q "\-a\-"; then
    pass "Logs configurados como append-only (imutáveis)."
else
    warn "Logs não parecem ter atributo append-only (+a)."
fi

# 4. Verificar existência de plano de Disaster Recovery (documentação)
if [ -f "documentation/DR_PLAN.md" ] || [ -f "/root/DR_PLAN.pdf" ]; then
    pass "Plano de Recuperação de Desastres encontrado."
else
    warn "Plano de Recuperação de Desastres não localizado nos caminhos padrão."
fi

# 5. Verificar testes de restore recentes (logs de sucesso)
if [ -d "$LOG_DIR" ] && grep -r "RESTORE_SUCCESS" "$LOG_DIR" | grep -q "$(date +%Y-%m)"; then
    pass "Teste de restore realizado este mês."
else
    fail "Nenhum registo de 'RESTORE_SUCCESS' encontrado para este mês."
fi

echo "=== Resumo de Compliance ==="
echo "Falhas Críticas: $FAILURES"
echo "Avisos: $WARNINGS"

if [ $FAILURES -eq 0 ]; then
    echo "Estado: CONFORME (Com ressalvas)"
    [ $WARNINGS -eq 0 ] && echo "Estado: TOTALMENTE CONFORME"
    exit 0
else
    echo "Estado: NÃO CONFORME"
    exit 1
fi
