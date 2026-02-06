#!/bin/bash
# Script: detetor_destino_comprometido.sh
# Descrição: Verifica o diretório de backup em busca de sinais de comprometimento (Ransomware).
# Analisa extensões suspeitas, notas de resgate e alterações em massa recentes.

LOG_FILE="/var/log/detetor_destino_comprometido.log"
BACKUP_DIR=""
SUSPICIOUS_EXTENSIONS=("encrypted" "locked" "crypto" "shit" "fuck" "crypted" "wannacry" "lockbit")
RANSOM_NOTES=("READ_ME" "DECRYPT_FILES" "RESTORE_INSTRUCTIONS" "HOW_TO_DECRYPT")

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
    echo "Uso: $0 -d <diretorio_backup>"
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while getopts "d:" opt; do
    case $opt in
        d) BACKUP_DIR="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$BACKUP_DIR" ]; then
    usage
fi

if [ ! -d "$BACKUP_DIR" ]; then
    log "Diretório não encontrado: $BACKUP_DIR"
    exit 1
fi

log "Iniciando varredura de integridade em: $BACKUP_DIR"
COMPROMISED=0

# 1. Verificação de Extensões Suspeitas
log "Verificando extensões de arquivos suspeitas..."
for ext in "${SUSPICIOUS_EXTENSIONS[@]}"; do
    FOUND=$(find "$BACKUP_DIR" -type f -name "*.$ext" | head -5)
    if [ ! -z "$FOUND" ]; then
        log "ALERTA: Arquivos com extensão suspeita (.$ext) encontrados!"
        echo "$FOUND" | tee -a "$LOG_FILE"
        COMPROMISED=1
    fi
done

# 2. Verificação de Notas de Resgate
log "Verificando notas de resgate comuns..."
for note in "${RANSOM_NOTES[@]}"; do
    FOUND=$(find "$BACKUP_DIR" -type f -name "*$note*" | head -5)
    if [ ! -z "$FOUND" ]; then
        log "ALERTA: Possível nota de resgate encontrada ($note)!"
        echo "$FOUND" | tee -a "$LOG_FILE"
        COMPROMISED=1
    fi
done

# 3. Verificação de integridade básica (opcional, ex: verificar arquivos vazios em massa)
EMPTY_FILES=$(find "$BACKUP_DIR" -type f -empty | wc -l)
if [ "$EMPTY_FILES" -gt 100 ]; then
    log "AVISO: Grande quantidade de arquivos vazios detectada ($EMPTY_FILES)."
    # Não marca necessariamente como comprometido, mas é suspeito
fi

if [ $COMPROMISED -eq 1 ]; then
    echo -e "${RED}PERIGO: O destino de backup parece estar COMPROMETIDO!${NC}"
    log "Status final: COMPROMETIDO. Recomenda-se isolamento imediato."
    exit 2
else
    echo -e "${GREEN}Nenhum sinal óbvio de comprometimento detectado.${NC}"
    log "Status final: LIMPO."
    exit 0
fi
