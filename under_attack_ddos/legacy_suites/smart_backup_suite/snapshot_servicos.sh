#!/bin/bash
# snapshot_servicos.sh
# Realiza dumps de bancos de dados e comandos pré/pós backup para garantir consistência.

BACKUP_DIR="${1:-/tmp/backups_db}"
MYSQL_USER="${2:-root}"
# MYSQL_PASS deve ser passado via env ou .my.cnf para segurança

mkdir -p "$BACKUP_DIR"

echo "[INFO] Iniciando snapshot de serviços..."

# Detecta MySQL/MariaDB
if command -v mysqldump &> /dev/null; then
    echo "[INFO] Detectado MySQL/MariaDB. Iniciando dump..."
    # --single-transaction para InnoDB evita lock total
    # --quick recupera linhas uma a uma
    DUMP_FILE="$BACKUP_DIR/mysql_full_$(date +%F_%H%M).sql"

    # Tenta usar credenciais do ambiente ou arquivo de config padrão
    mysqldump --all-databases --single-transaction --quick --events --routines --triggers > "$DUMP_FILE" 2>> "$BACKUP_DIR/mysql_error.log"

    if [ $? -eq 0 ]; then
        echo "[INFO] MySQL dump concluído: $DUMP_FILE"
        gzip "$DUMP_FILE"
    else
        echo "[AVISO] Falha no dump do MySQL. Verifique logs."
    fi
fi

# Detecta PostgreSQL
if command -v pg_dumpall &> /dev/null; then
    echo "[INFO] Detectado PostgreSQL. Iniciando dump..."
    # Assume que o usuário executando tem permissão (ex: via sudo -u postgres)
    DUMP_FILE_PG="$BACKUP_DIR/postgres_full_$(date +%F_%H%M).sql"

    # Se não for root ou postgres, talvez falhe se não configurado .pgpass ou trust
    pg_dumpall > "$DUMP_FILE_PG" 2>> "$BACKUP_DIR/pg_error.log"

    if [ $? -eq 0 ]; then
        echo "[INFO] PostgreSQL dump concluído: $DUMP_FILE_PG"
        gzip "$DUMP_FILE_PG"
    else
        echo "[AVISO] Falha no dump do PostgreSQL. Verifique logs."
    fi
fi

echo "[INFO] Snapshots de serviços finalizados."
