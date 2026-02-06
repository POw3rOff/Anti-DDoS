#!/bin/bash
# Script: detecao_scans_internos.sh
# Descrição: Detecta tentativas de varredura (scan) de portas originadas de IPs internos.
# Autor: Jules (AI Agent)

DATA=$(date +%Y%m%d_%H%M%S)
REPORT="relatorio_scans_$DATA.txt"

echo "=== Detecção de Scans Internos ===" | tee -a "$REPORT"

# 1. Análise de Logs de Firewall (Kernel Logs)
# Procura por bloqueios onde a origem (SRC) é um IP privado
PRIVATE_IPS="SRC=(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)"
LOG_FILES="/var/log/kern.log /var/log/syslog /var/log/messages /var/log/ufw.log"

echo "[*] Analisando logs de firewall em busca de bloqueios internos..." | tee -a "$REPORT"
FOUND_LOGS=0

for LOG in $LOG_FILES; do
    if [ -f "$LOG" ]; then
        # Conta ocorrências por IP
        HITS=$(grep -E "(BLOCK|DROP|REJECT)" "$LOG" 2>/dev/null | grep -E "$PRIVATE_IPS" | grep -oE "SRC=[0-9.]+" | sort | uniq -c | sort -nr | head -n 10)

        if [ -n "$HITS" ]; then
            echo "[ALERTA] Scans/Bloqueios detectados em $LOG:" | tee -a "$REPORT"
            echo "$HITS" | tee -a "$REPORT"
            FOUND_LOGS=1
        fi
    fi
done

if [ $FOUND_LOGS -eq 0 ]; then
    echo "[INFO] Nenhum padrão claro de scan interno encontrado nos logs (ou logs vazios/sem bloqueios)." | tee -a "$REPORT"
fi

# 2. Análise de Conexões Ativas (Estado SYN_RECV)
echo "[*] Verificando conexões em estado SYN_RECV (possível SYN Flood/Scan)..." | tee -a "$REPORT"
if command -v ss >/dev/null; then
    SYN_COUNT=$(ss -nt state syn-recv | wc -l)
    if [ "$SYN_COUNT" -gt 10 ]; then
        echo "[ALERTA] Alta quantidade de conexões SYN_RECV: $SYN_COUNT" | tee -a "$REPORT"
        ss -nt state syn-recv | tee -a "$REPORT"
    else
        echo "[OK] Conexões SYN_RECV normais (Total: $SYN_COUNT)." | tee -a "$REPORT"
    fi
fi

echo "=== Fim da Análise ===" | tee -a "$REPORT"
