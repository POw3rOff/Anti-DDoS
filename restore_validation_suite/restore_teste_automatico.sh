#!/bin/bash
# restore_teste_automatico.sh
#
# Descrição: Automatiza o teste de integridade de backups restaurando para um local temporário
# e verificando se os arquivos foram extraídos corretamente.
#
# Uso: ./restore_teste_automatico.sh <arquivo_backup>

BACKUP_FILE="$1"
TEMP_RESTORE_DIR=$(mktemp -d /tmp/restore_test_XXXXXX)

echo "[INFO] Iniciando teste automático de restore..."
echo "[INFO] Arquivo de backup: ${BACKUP_FILE}"
echo "[INFO] Diretório temporário: ${TEMP_RESTORE_DIR}"

if [[ -z "$BACKUP_FILE" ]]; then
    echo "[ERRO] Por favor, forneça o caminho do arquivo de backup."
    echo "Uso: $0 <arquivo_backup>"
    rm -rf "${TEMP_RESTORE_DIR}"
    exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "[ERRO] Arquivo de backup não encontrado."
    rm -rf "${TEMP_RESTORE_DIR}"
    exit 1
fi

# Tenta extrair (assume tar.gz para este exemplo)
tar -xzf "$BACKUP_FILE" -C "$TEMP_RESTORE_DIR" 2>/dev/null

if [[ $? -eq 0 ]]; then
    echo "[SUCESSO] Extração concluída com sucesso."

    # Verificação simples: contar arquivos
    FILE_COUNT=$(find "$TEMP_RESTORE_DIR" -type f | wc -l)
    if [[ "$FILE_COUNT" -gt 0 ]]; then
        echo "[SUCESSO] $FILE_COUNT arquivos restaurados verificados."
    else
        echo "[AVISO] O backup parece estar vazio (nenhum arquivo encontrado)."
    fi
else
    echo "[ERRO] Falha na extração do backup."
    rm -rf "${TEMP_RESTORE_DIR}"
    exit 1
fi

# Limpeza
echo "[INFO] Limpando diretório temporário..."
rm -rf "${TEMP_RESTORE_DIR}"
echo "[INFO] Teste finalizado."
