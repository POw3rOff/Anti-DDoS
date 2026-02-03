#!/bin/bash
# Script: retry_inteligente.sh
# Descrição: Realiza backup com mecanismo de retentativa inteligente (Exponential Backoff).
# Útil para conexões instáveis ou servidores sobrecarregados.

LOG_FILE="/var/log/retry_inteligente.log"
SOURCE_DIR=""
DESTINATION=""
MAX_RETRIES=5
BASE_WAIT=5 # Segundos

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
    echo "Uso: $0 -s <origem> -d <destino> [-r max_retries]"
    echo "Exemplo: $0 -s /dados -d /backup -r 5"
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while getopts "s:d:r:" opt; do
    case $opt in
        s) SOURCE_DIR="$OPTARG" ;;
        d) DESTINATION="$OPTARG" ;;
        r) MAX_RETRIES="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$SOURCE_DIR" ] || [ -z "$DESTINATION" ]; then
    usage
fi

ATTEMPT=1
SUCCESS=0

log "Iniciando backup com retry inteligente para $DESTINATION"

while [ $ATTEMPT -le $MAX_RETRIES ]; do
    log "Tentativa $ATTEMPT de $MAX_RETRIES..."

    # Executa rsync
    rsync -avz --timeout=300 "$SOURCE_DIR" "$DESTINATION" >> "${LOG_FILE}.rsync" 2>&1
    RESULT=$?

    if [ $RESULT -eq 0 ]; then
        log "SUCESSO: Backup concluído na tentativa $ATTEMPT."
        echo -e "${GREEN}Backup realizado com sucesso.${NC}"
        SUCCESS=1
        break
    else
        log "FALHA na tentativa $ATTEMPT. Código de erro: $RESULT"

        if [ $ATTEMPT -lt $MAX_RETRIES ]; then
            # Exponential Backoff
            WAIT_TIME=$((BASE_WAIT * (2 ** (ATTEMPT - 1))))
            log "Aguardando $WAIT_TIME segundos antes da próxima tentativa..."
            echo -e "${YELLOW}Falha. Retentando em ${WAIT_TIME}s...${NC}"
            sleep $WAIT_TIME
        fi
        ((ATTEMPT++))
    fi
done

if [ $SUCCESS -eq 0 ]; then
    log "ERRO CRÍTICO: Todas as $MAX_RETRIES tentativas falharam."
    echo -e "${RED}Falha permanente após múltiplas tentativas.${NC}"
    exit 1
fi

exit 0
