#!/bin/bash

# ==============================================================================
# Script: Agendamento Seguro
# Descrição: Audita tarefas agendadas (Cron) em busca de permissões inseguras e comandos suspeitos.
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

LOG_FILE=$(mktemp)

echo -e "${YELLOW}[INFO] Iniciando auditoria de agendamento (Cron)...${NC}"

# 1. Verificar permissões dos diretórios do Cron
DIRS_CRON=("/etc/crontab" "/etc/cron.d" "/etc/cron.daily" "/etc/cron.hourly" "/etc/cron.monthly" "/etc/cron.weekly" "/var/spool/cron")

ERROR_COUNT=0

for dir in "${DIRS_CRON[@]}"; do
    if [ -e "$dir" ]; then
        # Verifica se é owned por root
        OWNER=$(stat -c "%U" "$dir")
        if [ "$OWNER" != "root" ]; then
            echo -e "${RED}[ALERTA] $dir não pertence ao root (Dono atual: $OWNER)${NC}"
            ((ERROR_COUNT++))
        else
            echo -e "${GREEN}[OK] Permissões de dono em $dir${NC}"
        fi

        # Verifica permissões de escrita (não deve ser writable por outros)
        PERM=$(stat -c "%a" "$dir")
        if [ "$PERM" -gt 755 ] && [ -d "$dir" ]; then
             echo -e "${RED}[ALERTA] Permissões inseguras em diretório $dir: $PERM${NC}"
             ((ERROR_COUNT++))
        elif [ "$PERM" -gt 644 ] && [ -f "$dir" ]; then
             echo -e "${RED}[ALERTA] Permissões inseguras em arquivo $dir: $PERM${NC}"
             ((ERROR_COUNT++))
        fi
    fi
done

# 2. Buscar por padrões suspeitos em crontabs
echo -e "${YELLOW}[INFO] Buscando padrões suspeitos em tarefas agendadas...${NC}"
PATTERNS_SUSPEITOS=("curl " "wget " "nc " "/dev/tcp" "base64" "python -c" "perl -e")

# Varre crontabs de sistema e usuários
grep -rE "curl|wget|nc|/dev/tcp|base64" /etc/cron* /var/spool/cron 2>/dev/null > "$LOG_FILE"

if [ -s "$LOG_FILE" ]; then
    echo -e "${RED}[ATENÇÃO] Encontrados comandos potencialmente perigosos em tarefas agendadas:${NC}"
    cat "$LOG_FILE"
    ((ERROR_COUNT++))
else
    echo -e "${GREEN}[OK] Nenhum comando obviamente malicioso detectado nos crons padrão.${NC}"
fi

rm -f "$LOG_FILE"

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}[SUCESSO] Auditoria de agendamento concluída sem erros críticos.${NC}"
    exit 0
else
    echo -e "${RED}[FALHA] Foram encontrados $ERROR_COUNT problemas no agendamento.${NC}"
    exit 1
fi
