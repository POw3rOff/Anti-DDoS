#!/bin/bash
# restore_parcial.sh
#
# Descrição: Restaura apenas arquivos ou diretórios específicos de um backup completo.
# Útil quando apenas uma parte dos dados foi corrompida ou perdida.
#
# Uso: ./restore_parcial.sh <arquivo_backup> <caminho_arquivo_no_backup>

BACKUP_FILE="$1"
TARGET_FILE="$2"
RESTORE_DEST="./restore_parcial_output"

if [[ -z "$BACKUP_FILE" || -z "$TARGET_FILE" ]]; then
    echo "[ERRO] Uso: $0 <arquivo_backup> <arquivo_a_restaurar>"
    exit 1
fi

echo "[INFO] Tentando restaurar $TARGET_FILE de $BACKUP_FILE..."
mkdir -p "$RESTORE_DEST"

# Extrai apenas o arquivo solicitado
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DEST" "$TARGET_FILE"

if [[ $? -eq 0 ]]; then
    echo "[SUCESSO] Arquivo $TARGET_FILE restaurado em $RESTORE_DEST."
else
    echo "[ERRO] Falha ao extrair arquivo específico. Verifique se o caminho está correto no arquivo tar."
    exit 1
fi
