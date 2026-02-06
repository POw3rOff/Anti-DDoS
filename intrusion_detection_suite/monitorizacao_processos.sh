#!/bin/bash
# Monitorização de Processos
# Coleta informações sobre processos ativos e uso de recursos

LOG_FILE="/tmp/process_monitor.log"
echo "--- Monitorização de Processos: $(date) ---" | tee -a "$LOG_FILE"

# Top 10 processos por memória
echo "Top 10 Consumo Memória:" | tee -a "$LOG_FILE"
ps -eo pid,ppid,user,cmd,%mem --sort=-%mem | head -n 11 | tee -a "$LOG_FILE"

# Top 10 processos por CPU
echo -e "\nTop 10 Consumo CPU:" | tee -a "$LOG_FILE"
ps -eo pid,ppid,user,cmd,%cpu --sort=-%cpu | head -n 11 | tee -a "$LOG_FILE"

# Processos Zumbis
echo -e "\nProcessos Zumbis:" | tee -a "$LOG_FILE"
ZOMBIES=$(ps -eo pid,stat,cmd | grep '^[[:space:]]*[0-9]\+[[:space:]]*Z')
if [ -z "$ZOMBIES" ]; then
    echo "Nenhum processo zumbi detetado." | tee -a "$LOG_FILE"
else
    echo "$ZOMBIES" | tee -a "$LOG_FILE"
fi

echo "Relatório salvo em $LOG_FILE"
