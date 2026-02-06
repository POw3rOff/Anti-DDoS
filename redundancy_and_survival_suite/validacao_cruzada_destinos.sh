#!/bin/bash
# Script: validacao_cruzada_destinos.sh
# Descrição: Compara dois destinos de backup para garantir consistência entre eles.
# Utiliza rsync em modo de simulação (dry-run) com checksum para detectar diferenças.

LOG_FILE="/var/log/validacao_cruzada.log"
DEST1=""
DEST2=""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
    echo "Uso: $0 -a <destino_A> -b <destino_B>"
    echo "Exemplo: $0 -a /mnt/backup1 -b /mnt/backup2"
    echo "Suporta destinos remotos (user@host:/path)"
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while getopts "a:b:" opt; do
    case $opt in
        a) DEST1="$OPTARG" ;;
        b) DEST2="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$DEST1" ] || [ -z "$DEST2" ]; then
    usage
fi

log "Iniciando validação cruzada entre:"
log "Destino A: $DEST1"
log "Destino B: $DEST2"

log "Comparando dados (isso pode levar tempo dependendo do tamanho)..."

# Usamos rsync -n (dry-run) -a (archive) -c (checksum) --delete (check for extras)
# Se não houver output, são idênticos.
# Note: rsync compara source com dest. Se Dest A tem arquivos que Dest B não tem, aparecerão.
# Se Dest B tem arquivos que Dest A não tem, precisamos do --delete para vê-los (como 'deletions').

DIFF_OUTPUT=$(rsync -n -ac --delete --out-format="%n" "$DEST1/" "$DEST2/" 2>/dev/null)
RESULT=$?

if [ $RESULT -ne 0 ]; then
    log "ERRO: Falha na execução do rsync para comparação. Verifique conexões/permissões."
    exit 1
fi

if [ -z "$DIFF_OUTPUT" ]; then
    log "SUCESSO: Os destinos são IDÊNTICOS."
    echo -e "${GREEN}Validação Cruzada: OK. Destinos sincronizados.${NC}"
    exit 0
else
    log "DIFERENÇAS DETECTADAS:"
    echo "$DIFF_OUTPUT" | head -20 | tee -a "$LOG_FILE"
    echo "... (ver log para lista completa)" >> "$LOG_FILE"
    echo -e "${RED}Validação Cruzada: FALHA. Diferenças encontradas.${NC}"
    exit 1
fi
