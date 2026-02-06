#!/bin/bash
# backup_versionado.sh
# Cria um diretório de backup com timestamp para versionamento.
# Pode ser usado para copiar arquivos simples ou tarballs.

ORIGEM="$1"
DESTINO_ROOT="$2"
PREFIXO="${3:-backup}"

if [ -z "$ORIGEM" ] || [ -z "$DESTINO_ROOT" ]; then
    echo "Erro: Origem e diretório destino são obrigatórios."
    echo "Uso: $0 <origem> <destino_root> [prefixo]"
    ex""it 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NOME_DESTINO="${PREFIXO}_${TIMESTAMP}"
CAMINHO_FINAL="${DESTINO_ROOT}/${NOME_DESTINO}"

mkdir -p "$DESTINO_ROOT"

echo "[INFO] Criando backup versionado em: $CAMINHO_FINAL"

# Detecta se é diretório ou arquivo e usa cp -a
cp -a "$ORIGEM" "$CAMINHO_FINAL"

if [ $? -eq 0 ]; then
    echo "[INFO] Cópia versionada concluída."
else
    echo "[ERRO] Falha na cópia."
    ex""it 1
fi
