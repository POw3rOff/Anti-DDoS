#!/bin/bash
# Monitorização de Tráfego de Rede
# Exibe estatísticas de tráfego das interfaces de rede

echo "--- Estatísticas de Interface (ip -s link) ---"
ip -s link

echo -e "\n--- Resumo Simples (/proc/net/dev) ---"
cat /proc/net/dev

echo -e "\n--- Monitorização em tempo real (amostra de 5s) ---"
if command -v sar >/dev/null 2>&1; then
    sar -n DEV 1 5
else
    echo "'sar' não encontrado. Recomenda-se instalar sysstat."
    echo "Usando leitura básica de bytes..."
    grep eth0 /proc/net/dev 2>/dev/null || grep wlan0 /proc/net/dev 2>/dev/null || cat /proc/net/dev
fi
