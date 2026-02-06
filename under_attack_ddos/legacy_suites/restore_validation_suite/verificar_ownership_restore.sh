#!/bin/bash
# verificar_ownership_restore.sh
#
# Descrição: Verifica a propriedade (ownership) dos arquivos restaurados.
# Identifica arquivos com UIDs/GIDs desconhecidos ou pertencentes a root indevidamente.
#
# Uso: ./verificar_ownership_restore.sh <diretorio_restaurado>

TARGET_DIR="$1"

if [[ -z "$TARGET_DIR" ]]; then
    echo "[ERRO] Diretório não especificado."
    exit 1
fi

echo "[INFO] Verificando ownership em: $TARGET_DIR"

# Verifica arquivos sem usuário/grupo correspondente no sistema (ID numérico solto)
NOUSER_FILES=$(find "$TARGET_DIR" -nouser -o -nogroup)

if [[ -n "$NOUSER_FILES" ]]; then
    echo "[ALERTA] Arquivos com UID/GID sem correspondência encontrados:"
    echo "$NOUSER_FILES"
else
    echo "[OK] Todos os arquivos possuem proprietários válidos no sistema."
fi

# Verifica arquivos pertencentes ao root (pode ser intencional ou risco de segurança se restaurado por user comum)
ROOT_FILES=$(find "$TARGET_DIR" -user 0)
if [[ -n "$ROOT_FILES" ]]; then
    echo "[INFO] Arquivos pertencentes ao root detectados (verificar se é esperado)."
    # echo "$ROOT_FILES" | head -n 5 # Opcional: listar apenas alguns
else
    echo "[INFO] Nenhum arquivo pertencente ao root encontrado."
fi
