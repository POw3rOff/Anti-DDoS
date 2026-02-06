#!/bin/bash
# Script: inventario_backups.sh
# Descrição: Gera um inventário detalhado dos backups existentes.
# Autor: Jules (Assistant)

BACKUP_DIR="/var/backups"
OUTPUT_FILE="inventario_backups_$(date +%Y%m%d).csv"

echo "=== Gerando Inventário de Backups ==="

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Diretório não encontrado: $BACKUP_DIR"
    exit 1
fi

echo "Diretório: $BACKUP_DIR"
echo "Relatório: $OUTPUT_FILE"

# Cabeçalho CSV
echo "Arquivo,Tamanho(Bytes),Data_Modificacao,Tipo" > "$OUTPUT_FILE"

# Encontra arquivos e processa
find "$BACKUP_DIR" -type f -not -name "*.csv" | while read -r file; do
    SIZE=$(stat -c%s "$file")
    DATE=$(stat -c%y "$file")
    NAME=$(basename "$file")

    # Tentativa básica de classificação
    if [[ "$NAME" == *"full"* ]]; then
        TYPE="FULL"
    elif [[ "$NAME" == *"inc"* ]]; then
        TYPE="INCREMENTAL"
    elif [[ "$NAME" == *"diff"* ]]; then
        TYPE="DIFFERENTIAL"
    else
        TYPE="UNKNOWN"
    fi

    echo "$NAME,$SIZE,$DATE,$TYPE" >> "$OUTPUT_FILE"
done

echo "Inventário concluído."
echo "Total de backups listados: $(tail -n +2 "$OUTPUT_FILE" | wc -l)"
echo "Tamanho total: $(du -sh "$BACKUP_DIR" | cut -f1)"

echo "=== Fim ==="
