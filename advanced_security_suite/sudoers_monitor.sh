#!/bin/bash
#
# 13. Monitor de Alterações em Sudoers
# Autor: Jules (AI Agent)
# Descrição: Verifica integridade de arquivos sudoers.

BASELINE_DB="/var/lib/sudoers_monitor.db"
TARGETS="/etc/sudoers /etc/sudoers.d"

generate_hash() {
    # Hash do conteúdo concatenado de todos os arquivos encontrados
    find $TARGETS -type f 2>/dev/null | sort | xargs cat 2>/dev/null | sha256sum | awk '{print $1}'
}

echo "[*] Verificando integridade do Sudoers..."

if [ ! -f "$BASELINE_DB" ]; then
    echo "[*] Baseline não encontrada. Criando..."
    generate_hash > "$BASELINE_DB"
    echo "    Baseline criada: $(cat $BASELINE_DB)"
else
    OLD_HASH=$(cat "$BASELINE_DB")
    NEW_HASH=$(generate_hash)

    if [ "$OLD_HASH" != "$NEW_HASH" ]; then
        echo "[!] ALERTA CRÍTICO: Alterações detectadas em $TARGETS!"
        echo "    Hash Antigo: $OLD_HASH"
        echo "    Hash Novo:   $NEW_HASH"
        echo ""
        echo "    Arquivos modificados recentemente:"
        find $TARGETS -type f -mmin -60 -ls 2>/dev/null

        # Opcional: Mostrar diff se tiver backup
    else
        echo "[OK] Arquivos sudoers íntegros."
    fi
fi
