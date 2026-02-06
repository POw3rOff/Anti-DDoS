#!/bin/bash
# Script: verificacao_retencao_legal.sh
# Descrição: Verifica se existem backups anuais para cumprimento de requisitos legais (ex: 5 anos).
# Autor: Jules (Assistant)

BACKUP_DIR="/var/backups/long_term"
REQUIRED_YEARS=5
CURRENT_YEAR=$(date +%Y)

echo "=== Verificação de Retenção Legal ==="
echo "Diretório de Longa Duração: $BACKUP_DIR"
echo "Anos Necessários: $REQUIRED_YEARS"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "[ERRO] Diretório $BACKUP_DIR não existe."
    # Em produção, isto seria uma falha grave
fi

MISSING_YEARS=0

for (( i=1; i<=REQUIRED_YEARS; i++ )); do
    CHECK_YEAR=$((CURRENT_YEAR - i))
    echo -n "Verificando backup para $CHECK_YEAR... "

    # Procura ficheiro que contenha o ano no nome
    FOUND=$(find "$BACKUP_DIR" -name "*$CHECK_YEAR*" -print -quit 2>/dev/null)

    if [ -n "$FOUND" ]; then
        echo "[OK] Encontrado: $(basename "$FOUND")"
    else
        echo "[FALHA] Nenhum backup encontrado para o ano $CHECK_YEAR."
        MISSING_YEARS=$((MISSING_YEARS + 1))
    fi
done

echo ""
if [ $MISSING_YEARS -eq 0 ]; then
    echo "[SUCESSO] Todos os requisitos de retenção legal parecem estar cumpridos."
else
    echo "[ALERTA] Faltam backups de $MISSING_YEARS ano(s). Conformidade em risco."
    exit 1
fi
