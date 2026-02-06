#!/bin/bash
# Monitorização de Portas
# Verifica portas abertas (TCP/UDP) e conexões ativas

echo "--- Portas em Escuta (Listening) ---"
# -t (tcp), -u (udp), -l (listening), -n (numeric)
ss -tuln | awk 'NR==1 || /LISTEN/ || /UNCONN/'

echo -e "\n--- Conexões Estabelecidas ---"
ss -tun state established

echo -e "\n--- Resumo por Protocolo ---"
ss -s
