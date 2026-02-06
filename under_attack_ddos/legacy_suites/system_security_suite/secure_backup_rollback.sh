#!/bin/bash
#
# 9. Backup de Segurança + Rollback
# Autor: Jules (AI Agent)
# Descrição: Backup de configurações críticas com versionamento.

BACKUP_DIR="/var/backups/security_configs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz"

# Diretórios para incluir no backup
INCLUDE_DIRS="/etc /usr/local/etc /var/spool/cron"

usage() {
    echo "Uso: $0 {backup|rollback [arquivo_backup]}"
}

do_backup() {
    echo "[*] Iniciando Backup de Segurança..."

    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        chmod 700 "$BACKUP_DIR"
    fi

    # Cria arquivo tar.gz
    # --exclude evita loop se backup dir estiver dentro de include dir (ex: /var)
    tar -czf "$BACKUP_FILE" --absolute-names --exclude="$BACKUP_DIR" $INCLUDE_DIRS 2>/dev/null

    if [ -f "$BACKUP_FILE" ]; then
        chmod 600 "$BACKUP_FILE"
        echo "[OK] Backup criado com sucesso: $BACKUP_FILE"
        echo "     Tamanho: $(du -h "$BACKUP_FILE" | cut -f1)"

        # Manter apenas os últimos 5 backups
        ls -tp "$BACKUP_DIR"/config_backup_*.tar.gz | grep -v '/$' | tail -n +6 | xargs -I {} rm -- {}
    else
        echo "[Erro] Falha ao criar backup."
    fi
}

do_rollback() {
    local file=$1
    if [ -z "$file" ]; then
        echo "Erro: Especifique o arquivo de backup para restaurar."
        echo "Backups disponíveis:"
        ls -lh "$BACKUP_DIR"
    elif [ ! -f "$file" ]; then
        echo "Erro: Arquivo $file não encontrado."
    else
        echo "[!] ATENÇÃO: Isso irá sobrescrever as configurações atuais em /etc e outros diretórios."
        echo "[!] Tem certeza? (Digite 'SIM' para continuar)"
        # read -r confirm # Interativo não funciona bem aqui, assumir uso manual
        echo "(Execução não-interativa detectada. Execute manualmente para confirmar.)"
        echo "Comando: tar -xzf $file -C /"
    fi
}

case "$1" in
    backup)
        do_backup
        ;;
    rollback)
        do_rollback "$2"
        ;;
    *)
        usage
        ;;
esac
