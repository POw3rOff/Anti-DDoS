#!/bin/bash
#
# 8. Scanner de Ficheiros Suspeitos (Webshells/Malware)
# Autor: Jules (AI Agent)
# Descrição: Procura por padrões comuns de webshells e código ofuscado.

SEARCH_DIRS="/var/www /tmp /home" # Diretórios para escanear
OUTPUT_FILE="/var/log/security_malware_scan.log"

# Padrões suspeitos (PHP/Perl/Bash)
# Cuidado: Pode gerar falsos positivos em arquivos legítimos (minified js, frameworks).
PATTERNS="eval(|base64_decode(|shell_exec(|passthru(|system(|proc_open(|gzinflate("

echo "[*] Iniciando scan em: $SEARCH_DIRS"
echo "[*] Log será salvo em: $OUTPUT_FILE"

# Cria/Limpa log
> "$OUTPUT_FILE"

for dir in $SEARCH_DIRS; do
    if [ -d "$dir" ]; then
        echo "    - Analisando $dir ..."
        # Grep recursivo, mostra linha e arquivo
        # -I (ignora binários), -n (número da linha), -r (recursivo), -E (regex estendido)
        grep -I -n -r -E "$PATTERNS" "$dir" >> "$OUTPUT_FILE" 2>/dev/null
    fi
done

HITS=$(wc -l < "$OUTPUT_FILE")
echo "[*] Scan finalizado. Encontradas $HITS ocorrências potenciais."

if [ "$HITS" -gt 0 ]; then
    echo "[!] Verifique o arquivo de log para detalhes."
    echo "    Exemplo das primeiras 5 ocorrências:"
    head -n 5 "$OUTPUT_FILE"
else
    echo "[OK] Nenhum padrão óbvio encontrado."
fi
