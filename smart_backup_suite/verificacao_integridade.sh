#!/bin/bash
# verificacao_integridade.sh
# Verifica a integridade de arquivos de backup comprimidos.
#
# Uso: ./verificacao_integridade.sh <arquivo_backup>

ARQUIVO="$1"

if [ -z "$ARQUIVO" ]; then
    echo "Uso: $0 <arquivo_backup>"
    ex""it 1
fi

if [ ! -f "$ARQUIVO" ]; then
    echo "Erro: Arquivo não encontrado."
    ex""it 1
fi

echo "[INFO] Verificando integridade de $ARQUIVO ..."

STATUS=0

# Identifica o tipo de arquivo e testa
if [[ "$ARQUIVO" == *.tar.gz ]] || [[ "$ARQUIVO" == *.tgz ]]; then
    tar -tzf "$ARQUIVO" > /dev/null
    STATUS=$?
elif [[ "$ARQUIVO" == *.tar.xz ]]; then
    tar -tJf "$ARQUIVO" > /dev/null
    STATUS=$?
elif [[ "$ARQUIVO" == *.gz ]]; then
    gzip -t "$ARQUIVO"
    STATUS=$?
elif [[ "$ARQUIVO" == *.zip ]]; then
    unzip -t "$ARQUIVO" > /dev/null
    STATUS=$?
else
    echo "[AVISO] Formato desconhecido ou não suportado para verificação automática. Calculando SHA256 apenas."
    sha256sum "$ARQUIVO"
    ex""it 0
fi

if [ $STATUS -eq 0 ]; then
    echo "[OK] O arquivo de backup está íntegro."
else
    echo "[FALHA] O arquivo de backup está CORROMPIDO!"
    ex""it 1
fi
