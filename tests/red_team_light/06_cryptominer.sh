#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Simulação de Cryptominer"
# Copia sleep para um nome suspeito para aparecer no 'ps'
cp /bin/sleep /tmp/xmrig-miner
/tmp/xmrig-miner 10 &
PID=$!
log_event "Minerador falso rodando (PID: $PID - /tmp/xmrig-miner)"
echo "Aguardando 10 segundos..."
wait $PID
rm /tmp/xmrig-miner
log_event "CONCLUÍDO: Minerador removido."
