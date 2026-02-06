#!/bin/bash
# Script: monitorizacao_dns_suspeito.sh
# Descrição: Monitora tráfego DNS em busca de tunelamento e DGA.
# Autor: Jules (AI Agent)

DATA=$(date +%Y%m%d_%H%M%S)
LOG_FILE="dns_suspeito_$DATA.log"

echo "=== Monitorização de DNS Suspeito ===" | tee -a "$LOG_FILE"

if ! command -v tcpdump >/dev/null; then
    echo "[ERRO] tcpdump não encontrado. Instale com 'apt install tcpdump' ou 'yum install tcpdump'."
    exit 1
fi

INTERFACE=$(ip route | grep default | head -n1 | awk '{print $5}')
if [ -z "$INTERFACE" ]; then INTERFACE="eth0"; fi

echo "[*] Monitorando interface: $INTERFACE por 30 segundos..."
echo "[*] Procurando queries longas (>50 chars) ou tipos suspeitos (TXT, NULL)."

# Captura em background
TEMP_DUMP=$(mktemp)
tcpdump -i "$INTERFACE" -n -l udp port 53 -c 1000 2>/dev/null > "$TEMP_DUMP" &
PID=$!

sleep 30
kill $PID 2>/dev/null

echo "[*] Analisando captura..." | tee -a "$LOG_FILE"

# 1. Detectar Domínios Muito Longos
TEMP_DOMAINS=$(mktemp)
grep " A? " "$TEMP_DUMP" | awk '{for(i=1;i<=NF;i++) if($i=="A?") print $(i+1)}' | sort | uniq > "$TEMP_DOMAINS"

echo "--- Domínios Longos (Possível DGA/Tunneling) ---" >> "$LOG_FILE"
while read domain; do
    LEN=${#domain}
    if [ "$LEN" -gt 50 ]; then
        echo "[ALERTA] Domínio Longo ($LEN chars): $domain" | tee -a "$LOG_FILE"
    fi
done < "$TEMP_DOMAINS"

# 2. Detectar Tipos de Query Suspeitos
TXT_COUNT=$(grep " TXT? " "$TEMP_DUMP" | wc -l)
if [ "$TXT_COUNT" -gt 10 ]; then
    echo "[AVISO] Volume alto de queries TXT detectado: $TXT_COUNT" | tee -a "$LOG_FILE"
fi

# 3. Detectar Queries para TLDs incomuns
TEMP_TLD=$(mktemp)
grep -E "\.(xyz|top|pw|cc|tk)\." "$TEMP_DOMAINS" > "$TEMP_TLD"
if [ -s "$TEMP_TLD" ]; then
    echo "--- TLDs Suspeitos Detectados ---" | tee -a "$LOG_FILE"
    cat "$TEMP_TLD" | tee -a "$LOG_FILE"
fi

rm -f "$TEMP_DUMP" "$TEMP_DOMAINS" "$TEMP_TLD"
echo "=== Fim da Monitorização ===" | tee -a "$LOG_FILE"
