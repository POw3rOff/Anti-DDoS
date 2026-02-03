#!/bin/bash
# correlacao_eventos.sh
# Script simples para correlacionar eventos de diferentes logs baseados em usuário ou IP
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

usage() {
    echo "Uso: $0 [IP|USUARIO]"
    echo "Exemplo: $0 192.168.1.50"
    echo "Exemplo: $0 root"
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

TARGET="$1"
TMP_FILE="/tmp/correlacao_$$.txt"

echo -e "${YELLOW}[*] Buscando eventos para: $TARGET${NC}"

# Coleta de auth.log / secure
if [ -f /var/log/auth.log ]; then
    grep "$TARGET" /var/log/auth.log >> "$TMP_FILE"
elif [ -f /var/log/secure ]; then
    grep "$TARGET" /var/log/secure >> "$TMP_FILE"
fi

# Coleta de syslog / messages
if [ -f /var/log/syslog ]; then
    grep "$TARGET" /var/log/syslog | grep -v "auth.log" >> "$TMP_FILE" 2>/dev/null
elif [ -f /var/log/messages ]; then
    grep "$TARGET" /var/log/messages | grep -v "secure" >> "$TMP_FILE" 2>/dev/null
fi

# Coleta de journalctl (últimas 24h para evitar excesso)
if command -v journalctl >/dev/null 2>&1; then
    journalctl -S "24 hours ago" | grep "$TARGET" >> "$TMP_FILE" 2>/dev/null
fi

if [ ! -s "$TMP_FILE" ]; then
    echo -e "${RED}Nenhum evento encontrado para $TARGET.${NC}"
    rm -f "$TMP_FILE"
    exit 0
fi

# Ordenar e remover duplicatas (simplificado, assumindo formatos de data similares ou apenas agrupando)
# Logs podem ter formatos diferentes, ordenação perfeita em bash é difícil sem normalização.
# Vamos apenas exibir e destacar keywords.

echo -e "${GREEN}=== Linha do Tempo de Eventos (Bruta) ===${NC}"
sort "$TMP_FILE" | uniq | while read -r line; do
    # Highlight keywords
    if [[ "$line" == *"Failed"* ]] || [[ "$line" == *"failure"* ]]; then
        echo -e "${RED}$line${NC}"
    elif [[ "$line" == *"Accepted"* ]] || [[ "$line" == *"session opened"* ]]; then
        echo -e "${GREEN}$line${NC}"
    elif [[ "$line" == *"sudo"* ]] || [[ "$line" == *"COMMAND"* ]]; then
        echo -e "${YELLOW}$line${NC}"
    else
        echo "$line"
    fi
done

rm -f "$TMP_FILE"
