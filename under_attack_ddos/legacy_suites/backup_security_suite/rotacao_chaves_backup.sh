#!/bin/bash
#
# rotacao_chaves_backup.sh
#
# Descrição: Realiza a rotação de chaves simétricas utilizadas para encriptação de backups.
# Gera uma nova senha aleatória forte e arquiva a anterior.
#
# Uso: ./rotacao_chaves_backup.sh <caminho_arquivo_senha>
#
# Exemplo: ./rotacao_chaves_backup.sh /etc/backup/keys/backup_pass.txt
#

KEY_FILE="$1"

if [[ -z "$KEY_FILE" ]]; then
    echo "Uso: $0 <caminho_arquivo_senha>"
    exit 1
fi

KEY_DIR=$(dirname "$KEY_FILE")
mkdir -p "$KEY_DIR"

# Data para o arquivo de backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [[ -f "$KEY_FILE" ]]; then
    BACKUP_KEY="${KEY_FILE}.${TIMESTAMP}.old"
    echo "[*] Arquivando chave atual para: $BACKUP_KEY"
    mv "$KEY_FILE" "$BACKUP_KEY"
    chmod 600 "$BACKUP_KEY"
fi

echo "[*] Gerando nova chave de encriptação (64 caracteres hex)..."
# Gera 32 bytes aleatórios e converte para hex (64 chars)
openssl rand -hex 32 > "$KEY_FILE"

if [[ -f "$KEY_FILE" ]]; then
    chmod 600 "$KEY_FILE"
    echo "[+] Nova chave gerada e salva em: $KEY_FILE"
    echo "[!] ATENÇÃO: Certifique-se de atualizar seus scripts de backup para usar esta nova chave."
else
    echo "[-] Erro ao gerar nova chave."
    exit 1
fi
