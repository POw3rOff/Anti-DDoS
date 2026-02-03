#!/bin/bash
# Deteção de Comportamento Anómalo
# Identifica picos de atividade e tentativas repetidas de acesso

THRESHOLD_FAILED_LOGINS=5
LOG_AUTH="/var/log/auth.log"

echo "--- Verificação de Comportamento Anómalo ---"

# 1. Tentativas repetidas de login falhado
if [ -f "$LOG_AUTH" ]; then
    echo "[*] Verificando força bruta (logins falhados)..."
    # Conta ocorrências de 'Failed password' por IP (se disponível no formato)
    grep "Failed password" "$LOG_AUTH" | awk '{print $(NF-3)}' | sort | uniq -c | sort -nr | while read count ip; do
        if [ "$count" -gt "$THRESHOLD_FAILED_LOGINS" ]; then
            echo "ALERTA: $count tentativas de login falhadas do IP $ip"
        fi
    done
fi

# 2. Uso excessivo de CPU por um longo período (snapshot simples aqui)
echo "[*] Verificando processos com uso de CPU > 90%..."
ps -eo pid,user,cmd,%cpu --sort=-%cpu | awk '$4 > 90.0 {print "ALERTA: Processo " $1 " (" $2 ") consumindo " $4 "% CPU"}'

# 3. Utilizadores com shell interativo logados
echo "[*] Utilizadores logados atualmente:"
who
