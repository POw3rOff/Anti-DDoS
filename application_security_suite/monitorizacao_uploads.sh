#!/bin/bash
# Nome: monitorizacao_uploads.sh
# Descricao: Monitora diretorios de upload
# Autor: Jules

UPLOAD_DIRS="/var/www/html/uploads /var/www/html/wp-content/uploads"
SUSPICIOUS_EXT="php|phtml|py|pl|cgi|exe|dll|jsp|asp|aspx|sh"
OUTPUT_LOG="/var/log/uploads_monitor.log"

echo "[*] Iniciando monitorizacao de uploads em $(date)" | tee -a "$OUTPUT_LOG"

for dir in $UPLOAD_DIRS; do
    if [ -d "$dir" ]; then
        echo "[*] Verificando $dir..." | tee -a "$OUTPUT_LOG"
        # Regex busca ponto seguido de extensao
        find "$dir" -type f -regextype posix-extended -regex ".*\.($SUSPICIOUS_EXT)$" 2>/dev/null | while read -r file; do
            echo "[!] PERIGO: Arquivo suspeito: $file" | tee -a "$OUTPUT_LOG"
        done
    fi
done

echo "[*] Monitorizacao concluida." | tee -a "$OUTPUT_LOG"
