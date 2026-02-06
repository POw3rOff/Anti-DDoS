#!/bin/bash
# Script: backup_containers.sh
# Descrição: Realiza backup de containers Docker (Imagem 'commitada' + Volumes).
# Preserva o estado atual do container e seus dados persistentes.

LOG_FILE="/var/log/backup_containers.log"
BACKUP_DIR="/var/backups/docker"
CONTAINER_NAME=""

# Cores
GREEN='\033[0;32m'
NC='\033[0m'

usage() {
    echo "Uso: $0 -c <nome_container_ou_id> [-d diretorio_backup]"
    echo "Exemplo: $0 -c web_server -d /mnt/backup/docker"
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while getopts "c:d:" opt; do
    case $opt in
        c) CONTAINER_NAME="$OPTARG" ;;
        d) BACKUP_DIR="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$CONTAINER_NAME" ]; then
    usage
fi

if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
fi

# Verifica se docker está instalado
if ! command -v docker &> /dev/null; then
    log "ERRO: Docker não encontrado."
    exit 1
fi

# Verifica se container existe
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "ERRO: Container '$CONTAINER_NAME' não encontrado."
    exit 1
fi

log "Iniciando backup do container: $CONTAINER_NAME"

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
IMAGE_BACKUP_NAME="${CONTAINER_NAME}_backup_${TIMESTAMP}"
TAR_FILE="${BACKUP_DIR}/${CONTAINER_NAME}_image_${TIMESTAMP}.tar"
VOL_FILE="${BACKUP_DIR}/${CONTAINER_NAME}_volumes_${TIMESTAMP}.tar.gz"

# 1. Backup da Imagem (Commit)
log "Criando imagem snapshot..."
docker commit "$CONTAINER_NAME" "$IMAGE_BACKUP_NAME" 2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "Exportando imagem para arquivo tar..."
    docker save -o "$TAR_FILE" "$IMAGE_BACKUP_NAME" 2>> "$LOG_FILE"

    if [ $? -eq 0 ]; then
        log "Imagem salva com sucesso em: $TAR_FILE"
    else
        log "ERRO ao salvar imagem."
    fi

    # Limpeza da imagem temporária
    docker rmi "$IMAGE_BACKUP_NAME" > /dev/null 2>&1
else
    log "ERRO ao criar commit do container."
fi

# 2. Backup dos Volumes
# Utiliza um container temporário (busybox) para acessar os volumes do container alvo
log "Realizando backup dos volumes..."

docker run --rm --volumes-from "$CONTAINER_NAME" \
    -v "$BACKUP_DIR":/backup \
    busybox tar czf "/backup/$(basename "$VOL_FILE")" -C / . 2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "Volumes salvos com sucesso em: $VOL_FILE"
    echo -e "${GREEN}Backup de container $CONTAINER_NAME concluído.${NC}"
else
    log "ERRO ou AVISO ao salvar volumes (pode não haver volumes montados ou erro de permissão)."
fi

exit 0
