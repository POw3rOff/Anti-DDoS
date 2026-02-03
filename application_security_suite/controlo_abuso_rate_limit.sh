#!/bin/bash
# Nome: controlo_abuso_rate_limit.sh
# Descricao: Analisa logs recentes para detectar IPs com volume excessivo de requisicoes
# Autor: Jules

LOG_FILES="/var/log/apache2/access.log /var/log/nginx/access.log /var/log/httpd/access_log"
LIMIT=200 # Limite de requests na janela de analise
OUTPUT_LOG="/var/log/rate_limit_alerts.log"

echo "[*] Analisando trafego recente para deteccao de abuso..." | tee -a "$OUTPUT_LOG"

for log in $LOG_FILES; do
    if [ -f "$log" ]; then
        echo "[*] Analisando $log..."
        # Analisa as ultimas 5000 linhas do log (janela deslizante aproximada)
        # Extrai o IP (assumindo formato padrao common/combined onde IP e o primeiro campo)
        tail -n 5000 "$log" | awk '{print $1}' | sort | uniq -c | sort -nr | head -n 10 | while read count ip; do
            # Ignora linhas malformadas ou vazias
            if [[ ! "$count" =~ ^[0-9]+$ ]]; then continue; fi

            if [ "$count" -gt "$LIMIT" ]; then
                echo "[!] ALERTA: IP $ip realizou $count requisicoes recentes (Limite: $LIMIT) em $log" | tee -a "$OUTPUT_LOG"
                # Sugestao de bloqueio:
                # echo "iptables -A INPUT -s $ip -j DROP"
            fi
        done
    fi
done
