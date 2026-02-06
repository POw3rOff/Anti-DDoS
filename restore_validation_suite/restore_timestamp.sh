#!/bin/bash
# restore_timestamp.sh
#
# Descrição: Localiza e restaura o arquivo de backup mais próximo de um timestamp fornecido.
#
# Uso: ./restore_timestamp.sh <diretorio_backups> <data_YYYY-MM-DD>

BACKUP_DIR="$1"
TARGET_DATE="$2"

if [[ -z "$BACKUP_DIR" || -z "$TARGET_DATE" ]]; then
    echo "[ERRO] Uso: $0 <diretorio_backups> <data_YYYY-MM-DD>"
    exit 1
fi

echo "[INFO] Buscando backups modificados em ou antes de $TARGET_DATE em $BACKUP_DIR..."

# Encontra arquivo modificado mais recentemente antes da data
# Converte data alvo para segundos
TARGET_SEC=$(date -d "$TARGET_DATE" +%s 2>/dev/null)

if [[ -z "$TARGET_SEC" ]]; then
    echo "[ERRO] Formato de data inválido."
    exit 1
fi

BEST_CANDIDATE=""
MIN_DIFF=9999999999

for f in "$BACKUP_DIR"/*.tar.gz; do
    [ -e "$f" ] || continue
    FILE_SEC=$(stat -c %Y "$f")

    # Se arquivo é mais antigo ou igual a data alvo
    if [[ $FILE_SEC -le $TARGET_SEC ]]; then
        DIFF=$((TARGET_SEC - FILE_SEC))
        if [[ $DIFF -lt $MIN_DIFF ]]; then
            MIN_DIFF=$DIFF
            BEST_CANDIDATE="$f"
        fi
    fi
done

if [[ -n "$BEST_CANDIDATE" ]]; then
    echo "[INFO] Melhor candidato encontrado: $BEST_CANDIDATE"
    echo "[INFO] Data do arquivo: $(date -d @$(stat -c %Y "$BEST_CANDIDATE"))"
    echo "[PERGUNTA] Deseja restaurar este arquivo? (s/n)"
    read -r RESP
    if [[ "$RESP" == "s" ]]; then
        mkdir -p ./restored_timestamp
        tar -xzf "$BEST_CANDIDATE" -C ./restored_timestamp
        echo "[SUCESSO] Restaurado em ./restored_timestamp"
    else
        echo "[INFO] Operação cancelada."
    fi
else
    echo "[AVISO] Nenhum backup encontrado anterior a $TARGET_DATE."
fi
