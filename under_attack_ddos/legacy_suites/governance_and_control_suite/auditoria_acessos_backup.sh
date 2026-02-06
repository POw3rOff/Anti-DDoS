#!/bin/bash
# Script: auditoria_acessos_backup.sh
# Descrição: Audita acessos a ficheiros e diretórios de backup através de logs do sistema e auditd.
# Autor: Jules (Assistant)

BACKUP_DIR="/var/backups"
LOG_FILE="/var/log/audit_backup.log"
SEARCH_DAYS=7

echo "=== Auditoria de Acessos a Backups ==="
echo "Data: $(date)"
echo "Diretório Alvo: $BACKUP_DIR"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Erro: Diretório de backup $BACKUP_DIR não encontrado."
    exit 1
fi

# Verificar se auditd está instalado e a funcionar
if command -v ausearch >/dev/null 2>&1; then
    echo "[INFO] Usando ausearch para auditoria..."
    # Procura acessos ao diretório de backup
    ausearch -f "$BACKUP_DIR" -ts recent 2>/dev/null | aureport -f -i
else
    echo "[AVISO] ausearch não encontrado. Recorrendo a logs de sistema padrão."

    # Tenta detetar o log de autenticação correto
    if [ -f /var/log/auth.log ]; then
        SYS_LOG="/var/log/auth.log"
    elif [ -f /var/log/secure ]; then
        SYS_LOG="/var/log/secure"
    else
        echo "[ERRO] Não foi possível encontrar log de autenticação (auth.log ou secure)."
        exit 1
    fi

    echo "[INFO] Analisando $SYS_LOG..."
    grep -i "backup" "$SYS_LOG" | tail -n 50
fi

# Verificar acessos recentes de modificação (ctime/mtime)
echo ""
echo "[INFO] Ficheiros modificados nos últimos $SEARCH_DAYS dias em $BACKUP_DIR:"
find "$BACKUP_DIR" -type f -mtime -$SEARCH_DAYS -ls 2>/dev/null

echo "=== Fim da Auditoria ==="
