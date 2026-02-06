#!/bin/bash
# Script: fallback_destino.sh
# Descrição: Implementa lógica de failover (fallback) para backups.
# Tenta realizar backup no destino primário; se falhar, tenta destinos secundários sequencialmente.

LOG_FILE="/var/log/fallback_destino.log"
SOURCE_DIR=""
DESTINATIONS=()

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
    echo "Uso: $0 -s <origem> -d <destino_primario> -d <destino_secundario> ..."
    echo "O primeiro destino fornecido é considerado o PRIMÁRIO."
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

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

log "Iniciando processo de Backup com Fallback."
log "Origem: $SOURCE_DIR"

SUCCESS=0

for i in "${!DESTINATIONS[@]}"; do
    DEST="${DESTINATIONS[$i]}"
    TYPE="PRIMÁRIO"
    if [ $i -gt 0 ]; then
        TYPE="SECUNDÁRIO (FALLBACK #$i)"
    fi

    log "Tentando destino $TYPE: $DEST"

    # Check remote vs local
    if [[ "$DEST" == *:* ]]; then
        rsync -avz --timeout=300 "$SOURCE_DIR" "$DEST" >> "${LOG_FILE}.rsync" 2>&1
        RESULT=$?
    else
        if [ ! -d "$DEST" ]; then
             mkdir -p "$DEST" 2>/dev/null
        fi
        rsync -av --timeout=300 "$SOURCE_DIR" "$DEST" >> "${LOG_FILE}.rsync" 2>&1
        RESULT=$?
    fi

    if [ $RESULT -eq 0 ]; then
        log "SUCESSO: Backup realizado no destino $TYPE."
        echo -e "${GREEN}Backup concluído com sucesso em $DEST.${NC}"
        SUCCESS=1
        break # Exit loop on success
    else
        log "ALERTA: Falha no destino $TYPE ($DEST). Tentando próximo..."
        echo -e "${YELLOW}Falha em $DEST. Ativando fallback...${NC}"
    fi
done

if [ $SUCCESS -eq 1 ]; then
    exit 0
else
    log "ERRO CRÍTICO: Todos os destinos falharam."
    echo -e "${RED}Falha total. Nenhum destino disponível.${NC}"
    exit 1
fi
