#!/bin/bash
# Deteção de Assinaturas Básicas
# Analisa logs em busca de padrões de ataque conhecidos

LOG_AUTH="/var/log/auth.log"
LOG_SYSLOG="/var/log/syslog"

echo "Iniciando varredura de assinaturas..."

if [ -f "$LOG_AUTH" ]; then
    echo "[*] Analisando $LOG_AUTH..."
    grep -i "Failed password" "$LOG_AUTH" | tail -n 10
    grep -i "Invalid user" "$LOG_AUTH" | tail -n 10
    grep -i "sudo: .* : command not found" "$LOG_AUTH" | tail -n 5
else
    echo "Log de autenticação ($LOG_AUTH) não encontrado."
fi

if [ -f "$LOG_SYSLOG" ]; then
    echo "[*] Analisando $LOG_SYSLOG..."
    grep -i "segfault" "$LOG_SYSLOG" | tail -n 5
    grep -i "promiscuous mode" "$LOG_SYSLOG" | tail -n 5
else
    echo "Syslog ($LOG_SYSLOG) não encontrado."
fi

# Deteção de shellshock (antigo mas exemplo de assinatura) no access log se existir
APACHE_LOG="/var/log/apache2/access.log"
if [ -f "$APACHE_LOG" ]; then
    echo "[*] Analisando Apache Log..."
    grep "() { :;};" "$APACHE_LOG" | tail -n 5
fi

echo "Varredura concluída."
