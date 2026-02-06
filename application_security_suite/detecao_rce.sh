#!/bin/bash
# Nome: detecao_rce.sh
# Descricao: Detecta tentativas de RCE (Remote Code Execution) nos logs
# Autor: Jules

LOG_DIRS="/var/log/apache2 /var/log/nginx /var/log/httpd"
# Padroes comuns de RCE em URL encoding ou plain text
# cmd=, eval(, system(, exec(, passthru(, shell_exec(, bash -i, python -c, etc.
PATTERNS="eval\(|system\(|exec\(|passthru\(|shell_exec\(|cmd=|bash%20-i|python%20-c|perl%20-e|wget%20|curl%20|whoami|cat%20/etc/passwd"
OUTPUT_LOG="/var/log/rce_alerts.log"

echo "[*] Iniciando varredura por RCE em $(date)" | tee -a "$OUTPUT_LOG"

for dir in $LOG_DIRS; do
    if [ -d "$dir" ]; then
        echo "[*] Verificando $dir..." | tee -a "$OUTPUT_LOG"
        # Busca recursiva nos logs
        grep -Eri "$PATTERNS" "$dir"/*.log 2>/dev/null | while read -r line; do
            echo "[!] ALERTA RCE DETECTADO: $line" | tee -a "$OUTPUT_LOG"
        done
    fi
done

echo "[*] Varredura concluida." | tee -a "$OUTPUT_LOG"
