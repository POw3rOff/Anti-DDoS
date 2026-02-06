#!/bin/bash
#
# 1. Detetor de Exfiltração de Dados
# Autor: Jules (AI Agent)
# Descrição: Monitora picos de tráfego de saída e conexões persistentes de alto volume.

THRESHOLD_MB=100 # Limite de dados em MB para alerta
INTERVAL=60      # Intervalo de verificação em segundos
INTERFACE="eth0" # Interface padrão

# Verifica se ifstat está instalado (opcional, fallback para /proc)
use_proc=1
if command -v ifstat >/dev/null; then
    use_proc=0
fi

get_tx_bytes() {
    grep "$INTERFACE" /proc/net/dev | awk '{print $10}'
}

echo "[*] Iniciando Monitor de Exfiltração na interface $INTERFACE..."
echo "    Limite de alerta: ${THRESHOLD_MB}MB em ${INTERVAL}s"

while true; do
    RX1=$(get_tx_bytes)
    sleep "$INTERVAL"
    RX2=$(get_tx_bytes)

    # Calcular delta
    DELTA_BYTES=$((RX2 - RX1))
    DELTA_MB=$((DELTA_BYTES / 1024 / 1024))

    if [ "$DELTA_MB" -ge "$THRESHOLD_MB" ]; then
        echo "[!] ALERTA DE EXFILTRAÇÃO: $DELTA_MB MB enviados nos últimos $INTERVAL segundos!"
        echo "    Tentando identificar conexões com alto tráfego..."

        # Tenta identificar usando ss/netstat e send-q
        echo "    Top conexões por Send-Q (Fila de envio):"
        ss -ntu | sort -nk4 | tail -n 5

        # Opcional: Logar processos ativos
        # ps -eo pid,user,%cpu,%mem,cmd --sort=-%cpu | head -n 10
    fi
done
