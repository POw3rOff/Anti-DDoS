#!/bin/bash
#
# restore_configs.sh
#
# Restaura arquivos de configuração (/etc) de um backup.
# Permite restauração segura (extrair para temp) ou sobrescrita direta.
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -u

BACKUP_FILE="${1:-}"
TARGET_DIR="${2:-/tmp/restore_etc}"

# Cores
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: $0 <arquivo_backup_tar_gz> [diretorio_destino]"
    echo "Exemplo: $0 /backups/backup_etc.tar.gz /tmp/restore_etc"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Arquivo de backup não encontrado: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Iniciando restauração de configurações...${NC}"
echo "Origem: $BACKUP_FILE"
echo "Destino Temporário: $TARGET_DIR"

mkdir -p "$TARGET_DIR"

# Extração
echo "Extraindo..."
# Tenta detectar compressão
if tar -xf "$BACKUP_FILE" -C "$TARGET_DIR"; then
    echo -e "${GREEN}Extração concluída com sucesso em $TARGET_DIR${NC}"
else
    echo -e "${RED}Erro na extração.${NC}"
    exit 1
fi

echo ""
echo "Agora você pode comparar os arquivos restaurados com os atuais em /etc."
echo "Exemplo de comando para diff:"
echo "diff -r /etc $TARGET_DIR/etc"
echo ""
echo "Deseja SOBRESCREVER arquivos em /etc com os do backup? (PERIGOSO)"
read -p "Digite SIM para sobrescrever: " RESP

if [ "$RESP" == "SIM" ]; then
    echo -e "${RED}Sobrescrevendo configurações em /etc...${NC}"
    # Rsync é mais seguro que cp para preservar permissões e links
    rsync -av --existing "$TARGET_DIR/etc/" /etc/
    echo -e "${GREEN}Restauração aplicada.${NC}"
else
    echo "Operação de sobrescrita cancelada. Arquivos permanecem em $TARGET_DIR"
fi
