#!/bin/bash
# Alerta de Intrusão
# Script centralizador de alertas

LOG_FILE="/var/log/intrusion_alerts.log"
ADMIN_EMAIL="root@localhost"

# $1 = Mensagem, $2 = Nível (INFO, WARNING, CRITICAL)
MESSAGE="$1"
LEVEL="${2:-INFO}"

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# 1. Log local
echo "[$TIMESTAMP] [$LEVEL] $MESSAGE" >> "$LOG_FILE"
# Fallback to /tmp if /var/log fails (non-root)
if [ $? -ne 0 ]; then
    echo "[$TIMESTAMP] [$LEVEL] $MESSAGE" >> "/tmp/intrusion_alerts.log"
fi

# 2. Enviar Email (se mail existir)
if command -v mail >/dev/null 2>&1; then
    echo "$MESSAGE" | mail -s "Alerta de Intrusão [$LEVEL]" "$ADMIN_EMAIL"
fi

# 3. Wall (para users logados, se crítico)
if [ "$LEVEL" == "CRITICAL" ]; then
    echo "ALERTA DE SEGURANÇA: $MESSAGE" | wall 2>/dev/null
fi
