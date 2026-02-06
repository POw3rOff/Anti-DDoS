#!/bin/bash
# Script: alerta_alteracao_politica.sh
# Descrição: Monitora alterações em ficheiros de configuração de política de backup.
# Autor: Jules (Assistant)

# Lista de ficheiros de configuração a monitorar
CONFIG_FILES=(
    "/etc/crontab"
    "/etc/fstab"
    "/etc/rsyncd.conf"
    "/usr/local/bin/backup_script.sh"
)
CHECKSUM_DB="/var/lib/backup_policy_checksums.db"

echo "=== Monitoramento de Alterações de Política ==="

# Verifica integridade dos ficheiros
CHANGES_DETECTED=0

if [ ! -f "$CHECKSUM_DB" ]; then
    echo "[INFO] Base de dados de checksum não encontrada. Inicializando..."
    mkdir -p "$(dirname "$CHECKSUM_DB")"
    > "$CHECKSUM_DB"
    for file in "${CONFIG_FILES[@]}"; do
        if [ -f "$file" ]; then
            sha256sum "$file" >> "$CHECKSUM_DB"
            echo "Adicionado: $file"
        fi
    done
    echo "[SUCESSO] Base de referência criada."
else
    echo "[INFO] Verificando integridade contra base de referência..."

    # Cria ficheiro temporário com checksums atuais
    CURRENT_CHECKSUMS=$(mktemp)

    for file in "${CONFIG_FILES[@]}"; do
        if [ -f "$file" ]; then
            sha256sum "$file" >> "$CURRENT_CHECKSUMS"
        fi
    done

    # Compara
    if diff -u "$CHECKSUM_DB" "$CURRENT_CHECKSUMS" > /dev/null; then
        echo "[OK] Nenhuma alteração detetada."
    else
        echo "[ALERTA] Alterações detetadas nas políticas de backup!"
        echo "Diferenças:"
        diff -u "$CHECKSUM_DB" "$CURRENT_CHECKSUMS"
        CHANGES_DETECTED=1
    fi
    rm "$CURRENT_CHECKSUMS"
fi

if [ $CHANGES_DETECTED -eq 1 ]; then
    echo ""
    echo "[ACAO NECESSARIA] Verifique se as alterações foram autorizadas."
    echo "Para atualizar a base de referência, apague o ficheiro $CHECKSUM_DB e execute novamente."
    exit 1
fi

echo "=== Verificação Concluída ==="
