#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Simulação de C2 Beaconing"
# Gera tráfego HTTP repetitivo (Heartbeat)
for i in {1..5}; do
    curl -s -o /dev/null "http://$FAKE_C2_DOMAIN/api/heartbeat?id=$(date +%s)"
    echo "Beacon enviado para $FAKE_C2_DOMAIN..."
    sleep 3 # Intervalo fixo é a assinatura
done
log_event "CONCLUÍDO: Beaconing finalizado."
