#!/bin/bash
#
# 15. Detetor de Beaconing (C2 Periódico)
# Autor: Jules (AI Agent)
# Descrição: Tenta identificar padrões de comunicação persistente ou periódica.

echo "[*] Analisando atividade de Beaconing / C2..."

# 1. Conexões de Longa Duração (Persistent C2)
echo "[*] Verificando conexões TCP estabelecidas há muito tempo..."
# ss -o state established mostra timer. Formato: timer:(keepalive,10min,0)
# Vamos listar conexões externas (não locais)
ss -nto state established exclude dst 127.0.0.0/8 exclude dst ::1 | while read -r line; do
    if [[ "$line" == *"timer"* ]]; then
        echo "    [?] Conexão ativa: $line"
    fi
done

# 2. Jobs Cron de Alta Frequência (Periodic Beacon)
echo "[*] Verificando Cron Jobs frequentes (*/1, */5)..."
# Busca em /var/spool/cron e /etc/cron.d
grep -rE "(\*\/[1-5] |\* \* \* \* \*)" /var/spool/cron /etc/cron.d /etc/crontab 2>/dev/null | grep -vE "^#"
# Se encontrar, imprime.

# 3. Processos em loop (Sleep loops)
# Verifica processos com "sleep" na cmdline, comum em scripts de beacon bash
echo "[*] Verificando loops de shell (sleep)..."
ps -eo pid,cmd | grep "sleep" | grep -v grep | while read pid cmd; do
    # Verifica o pai deste sleep
    ppid=$(ps -o ppid= -p $pid)
    parent_cmd=$(ps -o cmd= -p $ppid)
    echo "    [?] Processo em 'sleep' encontrado (PID $pid). Pai: $parent_cmd (PID $ppid)"
done

echo "[OK] Análise de beaconing concluída."
echo "    Nota: Detecção precisa de beaconing requer análise de tráfego (PCAP/Netflow)."
