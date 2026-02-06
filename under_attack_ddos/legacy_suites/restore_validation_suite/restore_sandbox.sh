#!/bin/bash
# restore_sandbox.sh
#
# Descrição: Realiza um restore em um ambiente isolado (Sandbox) para análise forense ou validação,
# garantindo que não afete o sistema de produção.
#
# Uso: ./restore_sandbox.sh <arquivo_backup>

BACKUP_FILE="$1"
SANDBOX_DIR="/var/tmp/sandbox_restore_$(date +%Y%m%d_%H%M%S)"

echo "[INFO] Preparando ambiente Sandbox em: ${SANDBOX_DIR}"

if [[ -z "$BACKUP_FILE" ]]; then
    echo "[ERRO] Arquivo de backup não especificado."
    exit 1
fi

mkdir -p "$SANDBOX_DIR"
chmod 700 "$SANDBOX_DIR"

echo "[INFO] Restaurando backup..."
tar -xzf "$BACKUP_FILE" -C "$SANDBOX_DIR"

if [[ $? -eq 0 ]]; then
    echo "[SUCESSO] Restore realizado na Sandbox."
    echo "[INFO] Você pode inspecionar os arquivos em: ${SANDBOX_DIR}"
    echo "[INFO] Lembre-se de remover o diretório quando finalizar."
else
    echo "[ERRO] Falha ao restaurar na Sandbox."
    rm -rf "$SANDBOX_DIR"
    exit 1
fi
