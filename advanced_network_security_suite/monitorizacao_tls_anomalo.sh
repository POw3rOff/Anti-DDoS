#!/bin/bash
# Script: monitorizacao_tls_anomalo.sh
# Descrição: Analisa conexões TLS ativas em busca de anomalias.
# Autor: Jules (AI Agent)

DATA=$(date +%Y%m%d_%H%M%S)
LOG_FILE="tls_anomalo_$DATA.log"

echo "=== Monitorização de TLS Anômalo ===" | tee -a "$LOG_FILE"

echo "[*] Listando conexões de saída na porta 443..."
# Usa ss para listar
CONNS=$(ss -nt state established '( dport = :443 )' | grep -v "Local" | awk '{print $5}')

if [ -z "$CONNS" ]; then
    echo "[OK] Nenhuma conexão HTTPS ativa no momento." | tee -a "$LOG_FILE"
else
    echo "[*] Verificando certificados de destinos (Amostragem - Max 5)..." | tee -a "$LOG_FILE"

    echo "$CONNS" | cut -d: -f1 | sort | uniq | head -n 5 | while read IP; do
        CLEAN_IP=$(echo $IP | sed 's/[][]//g')
        echo "    -> Verificando $CLEAN_IP..." | tee -a "$LOG_FILE"

        OUTPUT=$(timeout 5 openssl s_client -connect ${CLEAN_IP}:443 -servername ${CLEAN_IP} < /dev/null 2>&1)

        if echo "$OUTPUT" | grep -q "verify error"; then
            echo "       [ALERTA] Erro de verificação de certificado em $CLEAN_IP!" | tee -a "$LOG_FILE"
        elif echo "$OUTPUT" | grep -q "self signed"; then
             echo "       [ALERTA] Certificado Auto-Assinado em $CLEAN_IP!" | tee -a "$LOG_FILE"
        else
             EXPIRE=$(echo "$OUTPUT" | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
             echo "       [OK] Certificado válido. Expira em: $EXPIRE" | tee -a "$LOG_FILE"
        fi
    done
fi

echo "[*] Verificando serviços locais ouvindo em portas não-padrão..."
if command -v ss >/dev/null; then
    ss -tulnp | grep LISTEN | grep -vE ":(22|80|443|53|123|68|631)" | while read line; do
        echo "[INFO] Porta não-padrão ouvindo: $line" | tee -a "$LOG_FILE"
    done
fi
echo "=== Fim da Análise ===" | tee -a "$LOG_FILE"
