#!/bin/bash
# Script: detecao_portas_expostas.sh
# Descrição: Identifica serviços ouvindo em interfaces públicas (0.0.0.0, [::] ou IPs públicos).
# Autor: Jules (AI Agent)

DATA=$(date +%Y%m%d_%H%M%S)
LOG_FILE="portas_expostas_$DATA.log"

echo "=== Detecção de Portas Expostas: $DATA ===" | tee -a "$LOG_FILE"

# Verifica ferramenta
if command -v ss >/dev/null; then
    CMD="ss -tuln"
    # Adiciona -p se for root para ver processos
    if [ "$(id -u)" -eq 0 ]; then CMD="ss -tulnp"; fi
elif command -v netstat >/dev/null; then
    CMD="netstat -tuln"
    if [ "$(id -u)" -eq 0 ]; then CMD="netstat -tulnp"; fi
else
    echo "[ERRO] 'ss' ou 'netstat' não encontrados." | tee -a "$LOG_FILE"
    exit 1
fi

echo "[INFO] Executando: $CMD" | tee -a "$LOG_FILE"
OUTPUT=$($CMD)

# Lista de IPs locais para ignorar (loopback e ranges privados se quiser ser estrito, mas foco é exposição externa)
# Vamos focar em 0.0.0.0 e [::] que indicam escuta global.

EXPOSED=$(echo "$OUTPUT" | grep -E "(0\.0\.0\.0|\[::\]|0:0:0:0:0:0:0:0)")

if [ -z "$EXPOSED" ]; then
    echo "[OK] Nenhum serviço detectado ouvindo em 0.0.0.0 ou [::]." | tee -a "$LOG_FILE"
else
    echo "[ALERTA] Serviços ouvindo em TODAS as interfaces (Global):" | tee -a "$LOG_FILE"
    echo "$EXPOSED" | tee -a "$LOG_FILE"

    echo "" | tee -a "$LOG_FILE"
    echo "[*] Análise Rápida de Risco:" | tee -a "$LOG_FILE"

    # Processa linha por linha para dar avisos específicos
    echo "$EXPOSED" | while read line; do
        # Tenta extrair a porta. ss output: State Recv-Q Send-Q Local Address:Port ...
        # Ex: LISTEN 0 128 0.0.0.0:22 ...
        PORT=$(echo "$line" | awk '{print $5}' | awk -F: '{print $NF}')

        # Correção para IPv6 [::]:80 -> pega 80
        if [[ "$PORT" =~ \].* ]]; then
             PORT=$(echo "$PORT" | awk -F] '{print $2}' | sed 's/://')
        fi

        # Mensagens de Risco
        case "$PORT" in
            21) MSG="FTP (Inseguro - Texto Claro)" ;;
            22) MSG="SSH (Verifique se é necessário estar público)" ;;
            23) MSG="TELNET (CRÍTICO - Inseguro)" ;;
            25) MSG="SMTP (Relay Aberto?)" ;;
            53) MSG="DNS (Risco de Amplificação DDoS)" ;;
            80) MSG="HTTP (Web)" ;;
            443) MSG="HTTPS (Web)" ;;
            445) MSG="SMB (CRÍTICO - Risco Ransomware/WannaCry)" ;;
            3306) MSG="MySQL (Deveria ser local?)" ;;
            3389) MSG="RDP (CRÍTICO - Alvo frequente de força bruta)" ;;
            5432) MSG="PostgreSQL (Deveria ser local?)" ;;
            6379) MSG="Redis (Inseguro se sem senha/TLS)" ;;
            8080) MSG="HTTP Alternativo (Proxy?)" ;;
            27017) MSG="MongoDB (Verifique autenticação)" ;;
            *) MSG="Serviço Desconhecido/Genérico" ;;
        esac

        echo "    -> Porta $PORT: $MSG" | tee -a "$LOG_FILE"
    done
fi

echo "=== Fim da Análise ===" | tee -a "$LOG_FILE"
