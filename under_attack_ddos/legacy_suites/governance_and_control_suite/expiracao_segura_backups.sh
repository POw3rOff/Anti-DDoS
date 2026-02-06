#!/bin/bash
# Script: expiracao_segura_backups.sh
# Descrição: Identifica e remove de forma segura backups expirados.
# Autor: Jules (Assistant)

BACKUP_DIR="/var/backups"
RETENTION_DAYS=365
# Use "shred" para sobrescrever antes de apagar (mais seguro, mais lento)
SECURE_DELETE=true

echo "=== Expiração Segura de Backups ==="
echo "Diretório: $BACKUP_DIR"
echo "Retenção: $RETENTION_DAYS dias"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Diretório não encontrado."
    exit 1
fi

# Listar ficheiros expirados
echo "Procurando ficheiros com mais de $RETENTION_DAYS dias..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -print0 | while IFS= read -r -d '' file; do
    echo "Expirado: $file"

    if [ "$SECURE_DELETE" = true ]; then
        if command -v shred >/dev/null; then
            echo "  [SEGURANÇA] Sobrescrevendo com shred..."
            shred -u -z -n 1 "$file"
            if [ $? -eq 0 ]; then
                echo "  [REMOVIDO] Ficheiro apagado com segurança."
            else
                echo "  [ERRO] Falha ao executar shred."
            fi
        else
            echo "  [AVISO] 'shred' não encontrado. Usando 'rm' padrão."
            rm "$file"
        fi
    else
        echo "  [INFO] Apagamento padrão (rm)..."
        rm "$file"
    fi
done

echo "=== Processo Concluído ==="
