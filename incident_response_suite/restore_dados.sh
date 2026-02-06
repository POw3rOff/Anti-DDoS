#!/bin/bash
#
# restore_dados.sh
#
# Script para restauração de grandes volumes de dados (Web, Home, Mail).
# Verifica espaço em disco antes de iniciar.
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -u

BACKUP_SOURCE="${1:-}"
DESTINATION="${2:-}"

# Cores
GREEN="\033[0;32m"
RED="\033[0;31m"
NC="\033[0m"

if [ -z "$BACKUP_SOURCE" ] || [ -z "$DESTINATION" ]; then
    echo "Uso: $0 <fonte_backup> <destino_restauro>"
    echo "Fonte pode ser um arquivo .tar.gz ou um diretório (para rsync)."
    echo "Exemplo: $0 /mnt/backup/home.tar.gz /home"
    exit 1
fi

if [ ! -e "$BACKUP_SOURCE" ]; then
    echo -e "${RED}Fonte não encontrada: $BACKUP_SOURCE${NC}"
    exit 1
fi

echo "Calculando tamanho necessário..."
if [ -d "$BACKUP_SOURCE" ]; then
    REQUIRED_SIZE=$(du -s "$BACKUP_SOURCE" | cut -f1) # em KB
elif [ -f "$BACKUP_SOURCE" ]; then
    # Estimar tamanho descompactado (muito aproximado, x2)
    COMPRESSED_SIZE=$(du -s "$BACKUP_SOURCE" | cut -f1)
    REQUIRED_SIZE=$((COMPRESSED_SIZE * 2))
fi

# Verificar espaço livre no destino
# df output: Filesystem 1K-blocks Used Available Use% Mounted on
# Pegar Available (coluna 4) do mount point do destino
mkdir -p "$DESTINATION"
AVAILABLE_SPACE=$(df "$DESTINATION" | tail -1 | awk "{print \$4}")

echo "Espaço estimado necessário: ${REQUIRED_SIZE} KB"
echo "Espaço disponível: ${AVAILABLE_SPACE} KB"

if [ "$REQUIRED_SIZE" -gt "$AVAILABLE_SPACE" ]; then
    echo -e "${RED}[ERRO] Espaço insuficiente no destino!${NC}"
    exit 1
fi

echo -e "${GREEN}Espaço suficiente. Iniciando restauração...${NC}"

if [ -d "$BACKUP_SOURCE" ]; then
    # Fonte é diretório -> Rsync
    echo "Executando rsync..."
    rsync -avP "$BACKUP_SOURCE/" "$DESTINATION/"
elif [ -f "$BACKUP_SOURCE" ]; then
    # Fonte é arquivo -> Tar
    echo "Executando tar..."
    tar -xvf "$BACKUP_SOURCE" -C "$DESTINATION"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Restauração concluída com sucesso.${NC}"
else
    echo -e "${RED}Houve erros durante a restauração.${NC}"
    exit 1
fi
