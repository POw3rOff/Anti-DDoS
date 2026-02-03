#!/bin/bash
# Nome: detecao_ssrf.sh
# Descricao: Detecta tentativas de SSRF (Server-Side Request Forgery) nos logs
# Autor: Jules

LOG_DIRS="/var/log/apache2 /var/log/nginx /var/log/httpd"
# Padroes: tenta aceder a loopback, metadados de cloud (AWS/GCP/Azure), ou redes privadas via parametro URL
PATTERNS="=http://127\.|127\.0\.0\.1|=http://localhost|=http://0\.0\.0\.0|169\.254\.169\.254|metadata\.google\.internal|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}"
OUTPUT_LOG="/var/log/ssrf_alerts.log"

echo "[*] Iniciando varredura SSRF em $(date)" | tee -a "$OUTPUT_LOG"

for dir in $LOG_DIRS; do
    if [ -d "$dir" ]; then
        echo "[*] Verificando $dir..." | tee -a "$OUTPUT_LOG"
        grep -Eri "$PATTERNS" "$dir"/*.log 2>/dev/null | while read -r line; do
             echo "[!] ALERTA SSRF DETECTADO: $line" | tee -a "$OUTPUT_LOG"
        done
    fi
done

echo "[*] Varredura concluida." | tee -a "$OUTPUT_LOG"
