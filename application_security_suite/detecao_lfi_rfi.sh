#!/bin/bash
# Nome: detecao_lfi_rfi.sh
# Descricao: Detecta tentativas de LFI (Local File Inclusion) e RFI (Remote File Inclusion) nos logs
# Autor: Jules

LOG_DIRS="/var/log/apache2 /var/log/nginx /var/log/httpd"
# Padroes: Traversal (../), caminhos sensiveis, e URLs remotas em parametros
PATTERNS="\.\./|\.\.%2f|/etc/passwd|/proc/self|%00|c:\\\\windows|=http://|=https://|=ftp://|=php://"
OUTPUT_LOG="/var/log/lfi_rfi_alerts.log"

echo "[*] Iniciando varredura LFI/RFI em $(date)" | tee -a "$OUTPUT_LOG"

for dir in $LOG_DIRS; do
    if [ -d "$dir" ]; then
        echo "[*] Verificando $dir..." | tee -a "$OUTPUT_LOG"
        grep -Eri "$PATTERNS" "$dir"/*.log 2>/dev/null | while read -r line; do
             echo "[!] ALERTA LFI/RFI DETECTADO: $line" | tee -a "$OUTPUT_LOG"
        done
    fi
done

echo "[*] Varredura concluida." | tee -a "$OUTPUT_LOG"
