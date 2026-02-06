#!/bin/bash
# Script: sanitizacao_backups.sh
# Descrição: Limpa ficheiros temporários, corrompidos ou inválidos e corrige permissões.
# Autor: Jules (Assistant)

BACKUP_DIR="/var/backups"
FIX_PERMISSIONS=true
PERM_MODE="600" # Apenas dono lê/escreve
OWNER="root"

echo "=== Sanitização de Backups ==="

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Diretório $BACKUP_DIR não encontrado."
    exit 1
fi

echo "[1/3] Removendo ficheiros temporários e incompletos..."
# Remove .tmp, .part, .swp
find "$BACKUP_DIR" -type f \( -name "*.tmp" -o -name "*.part" -o -name "*.swp" \) -print -delete

echo "[2/3] Removendo ficheiros vazios (0 bytes)..."
find "$BACKUP_DIR" -type f -empty -print -delete

if [ "$FIX_PERMISSIONS" = true ]; then
    echo "[3/3] Corrigindo permissões e propriedade..."
    # Apenas corrigir se formos root
    if [ "$(id -u)" -eq 0 ]; then
        chown -R "$OWNER:$OWNER" "$BACKUP_DIR"
        find "$BACKUP_DIR" -type f -exec chmod "$PERM_MODE" {} \;
        find "$BACKUP_DIR" -type d -exec chmod 700 {} \;
        echo "[OK] Permissões definidas para $PERM_MODE (files) e 700 (dirs)."
    else
        echo "[AVISO] Não é root. Pulando correção de permissões."
    fi
fi

echo "=== Sanitização Concluída ==="
