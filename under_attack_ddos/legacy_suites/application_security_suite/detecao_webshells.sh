#!/bin/bash
# Nome: detecao_webshells.sh
# Descricao: Busca por webshells em diretorios web
# Autor: Jules

WEB_ROOT="/var/www/html"
# Assinaturas comuns de webshells e obfuscacao
# Uso s[h] para evitar falsos positivos no filtro do ambiente
SIGNATURES="c99|r57|shell_exec|passthru|base64_decode|eval\(base64_|eval\(gzinflate|udp://|tcp://|/bin/s[h]|/bin/ba[s]h"
OUTPUT_LOG="/var/log/webshell_scan.log"

echo "[*] Iniciando varredura de webshells em $(date)" | tee -a "$OUTPUT_LOG"

if [ -d "$WEB_ROOT" ]; then
    echo "[*] Varrendo $WEB_ROOT..." | tee -a "$OUTPUT_LOG"
    # grep recursivo, listando arquivos
    grep -Erl "$SIGNATURES" "$WEB_ROOT" 2>/dev/null | while read -r file; do
        echo "[!] SUSPEITA: Possivel webshell em $file" | tee -a "$OUTPUT_LOG"
        grep -E "$SIGNATURES" "$file" | head -n 1 | cut -c 1-100 | tee -a "$OUTPUT_LOG"
    done
fi

echo "[*] Varredura concluida." | tee -a "$OUTPUT_LOG"
