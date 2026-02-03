#!/bin/bash
# Script: backup_multidestino.sh
# Descrição: Realiza backup de um diretório origem para múltiplos destinos configurados.

LOG_FILE="/var/log/backup_multidestino.log"
SOURCE_DIR=""
DESTINATIONS=()

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

usage() {
    echo "Uso: $0 -s <origem> -d <destino1> -d <destino2> ..."
    echo "Exemplo: $0 -s /var/www -d /mnt/backup_local -d user@192.168.1.50:/backup/remote"
    exit 1
}

log() {
    local msg="$1"
    local level="$2" # INFO, ERROR, WARN
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${msg}" | tee -a "$LOG_FILE"
}

# Parse arguments
while getopts "s:d:" opt; do
    case $opt in
        s) SOURCE_DIR="$OPTARG" ;;
        d) DESTINATIONS+=("$OPTARG") ;;
        *) usage ;;
    esac
done

if [ -z "$SOURCE_DIR" ] || [ ${#DESTINATIONS[@]} -eq 0 ]; then
    usage
fi

if [ ! -d "$SOURCE_DIR" ]; then
    log "Diretório de origem não encontrado: $SOURCE_DIR" "ERROR"
    exit 1
fi

log "Iniciando backup multidestino de: $SOURCE_DIR" "INFO"

SUCCESS_COUNT=0
FAIL_COUNT=0

for dest in "${DESTINATIONS[@]}"; do
    log "Iniciando transferência para: $dest" "INFO"

    # Check if destination is local or remote
    if [[ "$dest" == *:* ]]; then
        # Remote destination (assumes SSH keys setup)
        rsync -avz --timeout=300 "$SOURCE_DIR" "$dest" >> "${LOG_FILE}.rsync" 2>&1
        RESULT=$?
    else
        # Local destination
        if [ ! -d "$dest" ]; then
            mkdir -p "$dest" 2>/dev/null
        fi
        rsync -av --timeout=300 "$SOURCE_DIR" "$dest" >> "${LOG_FILE}.rsync" 2>&1
        RESULT=$?
    fi

    if [ $RESULT -eq 0 ]; then
        log "Backup para $dest concluído com SUCESSO." "INFO"
        ((SUCCESS_COUNT++))
    else
        log "FALHA no backup para $dest. Verifique logs detalhados." "ERROR"
        ((FAIL_COUNT++))
    fi
done

log "Resumo: $SUCCESS_COUNT sucessos, $FAIL_COUNT falhas." "INFO"

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}Todos os backups concluídos com sucesso.${NC}"
    exit 0
else
    echo -e "${RED}Houve falhas em alguns backups. Verifique $LOG_FILE${NC}"
    exit 1
fi
