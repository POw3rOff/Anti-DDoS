#!/bin/bash
# Script: replicacao_geografica.sh
# Descrição: Gerencia a replicação de dados para um site remoto (Recuperação de Desastres).
# Inclui verificações de conectividade e latência antes da sincronização.

LOG_FILE="/var/log/replicacao_geografica.log"
SOURCE_DIR=""
REMOTE_DEST="" # Formato user@host:/path

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
    echo "Uso: $0 -s <diretorio_local> -r <user@host:/caminho/remoto>"
    echo "Exemplo: $0 -s /dados/criticos -r admin@us-east.backup.com:/backups/geo"
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while getopts "s:r:" opt; do
    case $opt in
        s) SOURCE_DIR="$OPTARG" ;;
        r) REMOTE_DEST="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$SOURCE_DIR" ] || [ -z "$REMOTE_DEST" ]; then
    usage
fi

# Extrair host do destino remoto
REMOTE_HOST=$(echo "$REMOTE_DEST" | cut -d@ -f2 | cut -d: -f1)

log "Iniciando processo de replicação geográfica."
log "Origem: $SOURCE_DIR"
log "Destino Remoto: $REMOTE_DEST"

# 1. Verificação de Conectividade
log "Verificando conectividade com $REMOTE_HOST..."
ping -c 3 -W 5 "$REMOTE_HOST" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    log "ERRO: Não foi possível conectar ao servidor remoto $REMOTE_HOST."
    exit 1
fi

# 2. Medição de Latência (informativo)
AVG_LATENCY=$(ping -c 3 "$REMOTE_HOST" | tail -1 | awk -F '/' '{print $5}')
log "Latência média detectada: ${AVG_LATENCY}ms"

# 3. Replicação de Dados
log "Iniciando sincronização via rsync..."

# -a: archive mode, -v: verbose, -z: compress, --delete: mirror (delete extraneous)
rsync -avz --delete --timeout=600 "$SOURCE_DIR" "$REMOTE_DEST" >> "${LOG_FILE}.rsync" 2>&1

if [ $? -eq 0 ]; then
    log "SUCESSO: Replicação geográfica concluída."
    echo -e "${GREEN}Dados replicados com sucesso para $REMOTE_HOST.${NC}"
else
    log "FALHA: Erro durante a sincronização rsync."
    echo -e "${RED}Falha na replicação. Verifique $LOG_FILE${NC}"
    exit 1
fi

exit 0
