#!/bin/bash
# Deteção de Execuções Suspeitas
# Procura processos rodando de diretórios temporários ou incomuns

echo "--- Deteção de Execuções Suspeitas ---"

# 1. Processos em /tmp ou /dev/shm
echo "[*] Processos executados a partir de /tmp ou /dev/shm:"
# lsof -n | grep -E "/tmp/|/dev/shm/" | awk '{print $1, $2, $9}' | sort -u
# Usando ls -l /proc/*/exe para maior precisão sem lsof se necessário
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
    if [ -d "/proc/$pid" ]; then
        exe_link=$(readlink -f /proc/$pid/exe 2>/dev/null)
        if [[ "$exe_link" == /tmp/* ]] || [[ "$exe_link" == /dev/shm/* ]] || [[ "$exe_link" == /var/tmp/* ]]; then
            echo "SUSPEITO: PID $pid executando de $exe_link"
            cat /proc/$pid/cmdline 2>/dev/null
            echo ""
        fi
    fi
done

# 2. Verifica se existem binários ocultos (começando com .)
echo "[*] Procurando binários ocultos em execução:"
ps -eo pid,cmd | grep "/\." | grep -v "grep" | head -n 5

echo "Verificação concluída."
