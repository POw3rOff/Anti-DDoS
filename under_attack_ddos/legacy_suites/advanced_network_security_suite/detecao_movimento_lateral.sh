#!/bin/bash
# Script: detecao_movimento_lateral.sh
# Descrição: Analisa logs em busca de sinais de movimento lateral (SSH entre IPs internos, su, SCP).
# Autor: Jules (AI Agent)

DATA=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="movimento_lateral_$DATA.log"

# Identificar arquivo de log de autenticação
if [ -f /var/log/auth.log ]; then
    AUTH_LOG="/var/log/auth.log"
elif [ -f /var/log/secure ]; then
    AUTH_LOG="/var/log/secure"
else
    echo "[ERRO] Arquivo de log de autenticação (auth.log/secure) não encontrado."
    exit 1
fi

echo "=== Detecção de Movimento Lateral: $DATA ===" | tee -a "$RESULT_FILE"
echo "[*] Analisando $AUTH_LOG..." | tee -a "$RESULT_FILE"

# Regex para IPs Privados (RFC 1918)
PRIVATE_IPS="(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)"

echo "[*] Procurando conexões SSH de origem interna (IPs privados)..." | tee -a "$RESULT_FILE"
# Usar mktemp para segurança
TEMP_SSH=$(mktemp)
grep "Accepted" "$AUTH_LOG" | grep -E "$PRIVATE_IPS" > "$TEMP_SSH"

if [ -s "$TEMP_SSH" ]; then
    echo "[ALERTA] Conexões SSH internas detectadas (Possível Movimento Lateral):" | tee -a "$RESULT_FILE"
    cat "$TEMP_SSH" | tee -a "$RESULT_FILE"
else
    echo "[OK] Nenhuma conexão SSH interna suspeita encontrada nos logs recentes." | tee -a "$RESULT_FILE"
fi

# Verifica trocas de usuário suspeitas (su)
echo "[*] Verificando uso do comando 'su' para troca de usuários..." | tee -a "$RESULT_FILE"
TEMP_SU=$(mktemp)
grep "su:" "$AUTH_LOG" | grep "session opened" | grep -v "by root" > "$TEMP_SU"

if [ -s "$TEMP_SU" ]; then
    echo "[AVISO] Uso de 'su' detectado (usuários não-root escalando ou trocando):" | tee -a "$RESULT_FILE"
    cat "$TEMP_SU" | tee -a "$RESULT_FILE"
fi

# Limpeza
rm -f "$TEMP_SSH" "$TEMP_SU"

echo "=== Fim da Análise ===" | tee -a "$RESULT_FILE"
