#!/bin/bash
#
# 2. Monitor de DNS Suspeito (DGA / Domínios Estranhos)
# Autor: Jules (AI Agent)
# Descrição: Analisa queries DNS em busca de padrões anômalos.

# Requer tcpdump para monitoramento em tempo real
if ! command -v tcpdump >/dev/null; then
    echo "Erro: tcpdump não encontrado. Instale-o para usar este script."
    # exit 1 (Simulado)
fi

INTERFACE="eth0"
DURATION=60 # Monitorar por 60 segundos (mode batch) ou 'forever'
LOG_FILE="/var/log/dns_monitor.log"

echo "[*] Capturando tráfego DNS (Porta 53) na $INTERFACE..."

# Captura pacotes DNS e processa (Simulado por DURATION)
# Filtra query names e comprimentos
# Aviso: Execução contínua requer rodar em background ou serviço
if command -v tcpdump >/dev/null; then
    tcpdump -i "$INTERFACE" -n -l udp port 53 2>/dev/null | grep --line-buffered " A? " | while read -r line; do
        # Extrai o domínio (campo varia, ajuste conforme output do tcpdump)
        # Exemplo: IP 1.2.3.4.5353 > 8.8.8.8.53: 1234+ A? example.com. (29)
        domain=$(echo "$line" | grep -oE 'A\? [a-zA-Z0-9.-]+' | awk '{print $2}')

        if [ -n "$domain" ]; then
            # 1. Checa comprimento (DGA costuma ser longo e randômico)
            len=${#domain}
            if [ "$len" -gt 30 ]; then
                 echo "[!] ALERTA DGA POTENCIAL: Domínio muito longo ($len chars): $domain" >> "$LOG_FILE"
                 echo "[!] ALERTA DGA POTENCIAL: Domínio muito longo ($len chars): $domain"
            fi

            # 2. Checa TLDs suspeitos (Exemplo básico)
            if [[ "$domain" =~ \.(xyz|top|pw|cc|tk)$ ]]; then
                 echo "[?] AVISO: Domínio com TLD suspeito: $domain" >> "$LOG_FILE"
            fi
        fi
    done &

    PID=$!
    echo "Monitor rodando em background (PID $PID). Pare manualmente quando necessário."
fi
