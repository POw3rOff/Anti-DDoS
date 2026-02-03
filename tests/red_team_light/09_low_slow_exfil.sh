#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Exfiltração Lenta (Low & Slow)"
DUMMY="/tmp/cardholder_data.csv"
dd if=/dev/urandom of="$DUMMY" bs=1024 count=500 2>/dev/null
echo "Enviando dados em pequenos chunks..."
# Simula leitura/envio lento
for i in {1..10}; do
    head -n 10 "$DUMMY" > /dev/null
    sleep 2
    echo -n "."
done
rm "$DUMMY"
echo ""
log_event "CONCLUÍDO: Exfiltração terminada."
