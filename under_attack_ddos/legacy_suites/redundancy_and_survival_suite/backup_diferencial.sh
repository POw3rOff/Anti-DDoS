#!/bin/bash
# Script: backup_diferencial.sh
# Descrição: Realiza backup Diferencial ou Completo usando GNU Tar.
# Diferencial: Salva alterações desde o último backup Completo.

LOG_FILE="/var/log/backup_diferencial.log"
TYPE="" # full ou diff
SOURCE_DIR=""
DEST_DIR=""
BASE_NAME="backup"

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "Uso: $0 -t <full|diff> -s <origem> -d <destino> [-n nome_base]"
    echo "Exemplo: $0 -t full -s /etc -d /backup/etc -n config"
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while getopts "t:s:d:n:" opt; do
    case $opt in
        t) TYPE="$OPTARG" ;;
        s) SOURCE_DIR="$OPTARG" ;;
        d) DEST_DIR="$OPTARG" ;;
        n) BASE_NAME="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$TYPE" ] || [ -z "$SOURCE_DIR" ] || [ -z "$DEST_DIR" ]; then
    usage
fi

if [ ! -d "$DEST_DIR" ]; then
    mkdir -p "$DEST_DIR"
fi

DATE=$(date '+%Y%m%d_%H%M%S')
SNAPSHOT_FILE="$DEST_DIR/$BASE_NAME.snar"

log "Iniciando backup tipo $TYPE para $SOURCE_DIR"

if [ "$TYPE" == "full" ]; then
    # Backup Completo
    ARCHIVE="$DEST_DIR/${BASE_NAME}_full_${DATE}.tar.gz"

    # Remove snapshot anterior para forçar nível 0
    if [ -f "$SNAPSHOT_FILE" ]; then
        rm "$SNAPSHOT_FILE"
        log "Snapshot anterior removido para forçar backup completo."
    fi

    tar -czg "$SNAPSHOT_FILE" -f "$ARCHIVE" "$SOURCE_DIR" 2>> "$LOG_FILE"
    RET=$?

elif [ "$TYPE" == "diff" ]; then
    # Backup Diferencial
    ARCHIVE="$DEST_DIR/${BASE_NAME}_diff_${DATE}.tar.gz"

    if [ ! -f "$SNAPSHOT_FILE" ]; then
        log "ERRO: Snapshot de referência ($SNAPSHOT_FILE) não encontrado. Execute um backup FULL primeiro."
        exit 1
    fi

    # Copia snapshot para temporário para não atualizar o original (Comportamento Diferencial)
    # Se usássemos o original, seria Incremental.
    TEMP_SNAR=$(mktemp)
    cp "$SNAPSHOT_FILE" "$TEMP_SNAR"

    tar -czg "$TEMP_SNAR" -f "$ARCHIVE" "$SOURCE_DIR" 2>> "$LOG_FILE"
    RET=$?

    rm "$TEMP_SNAR"
else
    usage
fi

if [ $RET -eq 0 ]; then
    log "SUCESSO: Backup $TYPE criado em $ARCHIVE"
    echo -e "${GREEN}Backup concluído: $ARCHIVE${NC}"
else
    log "FALHA no backup $TYPE. Código: $RET"
    exit 1
fi

exit 0
