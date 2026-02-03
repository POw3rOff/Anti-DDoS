#!/bin/bash
#
# alertas_backup.sh
#
# Descrição: Script centralizado para envio de alertas de segurança de backup.
# Suporta envio por e-mail e registro em log (syslog/arquivo).
#
# Uso: ./alertas_backup.sh "Assunto" "Mensagem de Detalhes" [nivel: INFO|WARNING|CRITICAL]
#
# Exemplo: ./alertas_backup.sh "Falha de Integridade" "A assinatura do backup XPTO falhou." CRITICAL
#

SUBJECT="$1"
MESSAGE="$2"
LEVEL="${3:-INFO}"

# Configurações (Ajuste conforme ambiente)
ADMIN_EMAIL="admin@localhost"
LOG_FILE="/var/log/backup_security.log"
USE_SYSLOG=true

if [[ -z "$SUBJECT" || -z "$MESSAGE" ]]; then
    echo "Uso: $0 \"Assunto\" \"Mensagem\" [nivel]"
    exit 1
fi

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
FORMATTED_MSG="[$TIMESTAMP] [$LEVEL] $SUBJECT - $MESSAGE"

# 1. Registrar em arquivo de log
echo "$FORMATTED_MSG" >> "$LOG_FILE"

# 2. Registrar no Syslog
if [[ "$USE_SYSLOG" == "true" ]]; then
    # Mapeia níveis para prioridades logger
    PRIORITY="user.info"
    case "$LEVEL" in
        "WARNING") PRIORITY="user.warning" ;;
        "CRITICAL") PRIORITY="user.err" ;;
    esac
    logger -p "$PRIORITY" -t "BACKUP_SEC" "$SUBJECT - $MESSAGE"
fi

# 3. Enviar E-mail (Apenas para Warning e Critical)
if [[ "$LEVEL" == "WARNING" || "$LEVEL" == "CRITICAL" ]]; then
    if command -v mail &> /dev/null; then
        echo "$MESSAGE" | mail -s "BACKUP SEC: $SUBJECT" "$ADMIN_EMAIL"
    else
        echo "[-] Comando mail não encontrado. E-mail não enviado." >> "$LOG_FILE"
    fi
fi

echo "[+] Alerta processado: $LEVEL"
