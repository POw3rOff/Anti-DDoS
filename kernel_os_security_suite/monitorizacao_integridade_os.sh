#!/bin/bash

# Script: monitorizacao_integridade_os.sh
# Descrição: Monitora alterações em arquivos críticos de configuração do SO.
# Autor: Jules (Agente de IA)

DATA_DIR="/var/log/os_integrity"
HASH_FILE="/hashes.sha256"
FILES_TO_MONITOR="/etc/passwd /etc/shadow /etc/group /etc/sudoers /etc/ssh/sshd_config /etc/fstab /etc/crontab /etc/hosts"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p ""

echo -e "=== Monitoramento de Integridade de Arquivos Críticos ==="

if [ ! -f "" ]; then
    echo -e "[INFO] Base de dados de integridade não encontrada. Criando inicial..."
    for file in ; do
        if [ -f "" ]; then
            sha256sum "" >> ""
        fi
    done
    echo -e "[OK] Base criada em ."
    exit 0
fi

echo -e "[*] Verificando integridade..."

CHANGES_DETECTED=0

# Verifica arquivo por arquivo
TEMP_CHECK=/tmp/tmp.Pwn6rvr8HO
sha256sum -c "" > "" 2>/dev/null
CHECK_STATUS=0

if [  -ne 0 ]; then
    echo -e "[!] ALTERAÇÕES DETECTADAS EM ARQUIVOS CRÍTICOS:"
    grep "FAILED" "" | sed 's/: FAILED//' | while read -r file; do
         echo -e "    -  (Conteúdo modificado)"
    done
    CHANGES_DETECTED=1
else
    echo -e "[OK] Todos os arquivos monitorados estão íntegros."
fi

if [  -eq 1 ]; then
    echo -e "[?] Deseja atualizar a base de hashes com as novas versões? (s/N)"
    read -r -t 10 response
    if [[ "" =~ ^[sS]$ ]]; then
        echo -e "[*] Atualizando base de hashes..."
        > ""
        for file in ; do
            if [ -f "" ]; then
                sha256sum "" >> ""
            fi
        done
        echo -e "[OK] Base atualizada."
    else
        echo -e "[!] Base não atualizada. O alerta persistirá."
    fi
fi

rm -f ""
echo -e "=== Concluído ==="
