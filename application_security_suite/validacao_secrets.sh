#!/bin/bash
# Nome: validacao_secrets.sh
# Descricao: Busca por segredos (chaves, senhas) hardcoded no codigo ou configs
# Autor: Jules

SEARCH_DIR="/var/www/html"
# Padroes comuns de chaves e senhas
PATTERNS="API_KEY|SECRET_KEY|AWS_ACCESS_KEY|BEGIN RSA PRIVATE KEY|password\s*=|passwd\s*=|db_password|DB_PASS"
# Excluir diretorios de bibliotecas e git
EXCLUDE_DIRS="--exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=.git"
OUTPUT_LOG="/var/log/secrets_scan.log"

echo "[*] Iniciando varredura de secrets em $(date)" | tee -a "$OUTPUT_LOG"

if [ -d "$SEARCH_DIR" ]; then
    echo "[*] Varrendo $SEARCH_DIR..." | tee -a "$OUTPUT_LOG"
    grep -Ern $EXCLUDE_DIRS "$PATTERNS" "$SEARCH_DIR" 2>/dev/null | cut -c 1-200 | tee -a "$OUTPUT_LOG"
fi

echo "[*] Varredura concluida." | tee -a "$OUTPUT_LOG"
