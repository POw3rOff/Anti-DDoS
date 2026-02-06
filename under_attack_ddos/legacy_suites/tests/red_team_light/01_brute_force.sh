#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Simulação de SSH Brute-Force"
echo "Gerando ruído nos logs de autenticação (auth.log)..."
for i in {1..15}; do
    # Simula falha de autenticação via logger (mais seguro que sshpass real)
    logger -t sshd -p auth.info "Failed password for invalid user $TARGET_USER from 192.168.1.66 port $RANDOM ssh2"
    echo -n "."
    sleep 0.2
done
echo ""
log_event "CONCLUÍDO: Brute-force simulado."
