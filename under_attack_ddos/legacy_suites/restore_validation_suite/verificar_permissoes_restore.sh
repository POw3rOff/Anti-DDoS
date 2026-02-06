#!/bin/bash
# verificar_permissoes_restore.sh
#
# Descrição: Verifica se os arquivos restaurados possuem permissões inseguras (ex: 777)
# ou diferentes do esperado (baseado em um padrão seguro).
#
# Uso: ./verificar_permissoes_restore.sh <diretorio_restaurado>

TARGET_DIR="$1"

if [[ -z "$TARGET_DIR" ]]; then
    echo "[ERRO] Diretório não especificado."
    echo "Uso: $0 <diretorio_restaurado>"
    exit 1
fi

echo "[INFO] Verificando permissões em: $TARGET_DIR"

# Busca arquivos com permissão 777 (world writable/executable)
INSECURE_FILES=$(find "$TARGET_DIR" -type f -perm 777)

if [[ -n "$INSECURE_FILES" ]]; then
    echo "[ALERTA] Arquivos com permissão 777 encontrados:"
    echo "$INSECURE_FILES"
    echo "[RECOMENDACAO] Corrija as permissões imediatamente com chmod."
else
    echo "[OK] Nenhum arquivo com permissão 777 detectado."
fi

# Busca arquivos SUID (pode ser perigoso se restaurado de fonte não confiável)
SUID_FILES=$(find "$TARGET_DIR" -perm /4000)
if [[ -n "$SUID_FILES" ]]; then
    echo "[ALERTA] Arquivos com bit SUID encontrados:"
    echo "$SUID_FILES"
else
    echo "[OK] Nenhum arquivo SUID detectado."
fi
