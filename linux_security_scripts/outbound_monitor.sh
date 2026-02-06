#!/bin/bash

# Monitor de Tráfego de Saída Suspeito
# Detecta conexões estabelecidas para portas não padrão

LOG_FILE="/var/log/outbound_monitor.log"

# Portas remotas permitidas (Destinos comuns de saída)
# 80/443 (Web), 22 (SSH/Git), 53 (DNS), 123 (NTP)
WHITELIST_REMOTE_PORTS="80|443|22|53|123|8080"

# Portas locais permitidas (Meus serviços ouvindo)
# Se a conexão sai DAQUI, a porta local deve ser aleatória (alta).
# Se a porta local é BAIXA (ex: 22), então é uma conexão ENTRANDO (Cliente -> Eu:22).
# Devemos ignorar conexões onde Local Port < 1024 (Services) ou conhecidas.
IGNORED_LOCAL_PORTS="22|80|443|2222|21"

# Cores
RED="\033[0;31m"
NC="\033[0m"

log_msg() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" >> "$LOG_FILE"
}

alert() {
    echo -e "${RED}[ALERTA] $1${NC}"
    log_msg "[ALERTA] $1"
}

check_connections() {
    echo "Verificando conexões..."

    conns=""
    if command -v ss &> /dev/null; then
        # -H: No header
        # -t: TCP, -u: UDP, -n: Numeric, -p: Process
        conns=$(ss -tunpH state established)
    elif command -v netstat &> /dev/null; then
        conns=$(netstat -tunp | grep ESTABLISHED)
    else
        echo "Erro: ss ou netstat não encontrados."
        return 1
    fi

    # Lendo linha a linha
    # IFS= evita que espaços no inicio/fim sejam removidos, mas read -r é o importante
    echo "$conns" | while read -r line; do
        if [ -z "$line" ]; then continue; fi

        # ss output format (approx):
        # ESTAB 0 0 192.168.1.5:44810 1.2.3.4:80 users:(...)
        # Col 4: Local, Col 5: Remote

        # Netstat output format:
        # tcp 0 0 192.168.1.5:44810 1.2.3.4:80 ESTABLISHED ...
        # Col 4: Local, Col 5: Remote

        # Usando awk para pegar campos 4 e 5
        local_socket=$(echo "$line" | awk "{print \$4}")
        remote_socket=$(echo "$line" | awk "{print \$5}")

        # Extrair portas
        # Formato pode ser IP:Porta ou [IP]:Porta
        local_port=${local_socket##*:}
        remote_port=${remote_socket##*:}

        remote_ip=${remote_socket%:*}

        # Ignorar Localhost
        if [[ "$remote_ip" == "127.0.0.1" ]] || [[ "$remote_ip" == "::1" ]]; then
            continue
        fi

        # 1. Verificar se é uma conexão ENTRANDO (Servidor)
        # Se a porta local for baixa (<1024) ou estiver na lista de serviços, ignorar.
        if [[ "$local_port" -lt 1024 ]] || [[ "$local_port" =~ ^($IGNORED_LOCAL_PORTS)$ ]]; then
            continue
        fi

        # 2. Se a porta local é alta, provavel ser SAÍDA.
        # Verificar se a porta remota é confiável.
        if ! [[ "$remote_port" =~ ^($WHITELIST_REMOTE_PORTS)$ ]]; then
            # Porta remota estranha!
            proc_info=$(echo "$line" | grep -o "users:.*")
            if [ -z "$proc_info" ]; then
                # Fallback para netstat process info (ultima coluna normalmente)
                proc_info=$(echo "$line" | awk "{print \$NF}")
            fi

            msg="Saída Suspeita Detectada! Local: $local_socket -> Destino: $remote_socket ($remote_port). Processo: $proc_info"
            alert "$msg"
        fi
    done
}

if [ "$(id -u)" != "0" ]; then
   echo "Execute como root."
else
   check_connections
fi
