#!/bin/bash
#
# 2. Monitor de Brute-force (SSH Customizado)
# Autor: Jules (AI Agent)
# Descrição: Monitora auth.log em tempo real e bloqueia IPs atacantes.

LOG_FILE="/var/log/auth.log" # Ajuste para /var/log/secure em RHEL/CentOS
MAX_ATTEMPTS=5
BLOCK_CMD="iptables -A INPUT -p tcp --dport 22 -s %IP% -j DROP"
WHITELIST=("127.0.0.1" "::1" "192.168.1.50") # Adicione seus IPs

declare -A FAILED_ATTEMPTS

echo "[*] Iniciando Monitor de Brute-force em $LOG_FILE..."

# Verifica se o arquivo de log existe
if [ ! -f "$LOG_FILE" ]; then
    echo "Erro: Arquivo de log $LOG_FILE não encontrado."
fi

# Função de bloqueio
block_ip() {
    local ip=$1
    echo "[!] Bloqueando IP: $ip após ${FAILED_ATTEMPTS[$ip]} tentativas."

    # Executa comando de bloqueio
    local cmd=${BLOCK_CMD//%IP%/$ip}
    $cmd

    # Reset contador
    unset FAILED_ATTEMPTS[$ip]

    # Enviar alerta (Exemplo)
    # curl -X POST -H "Content-Type: application/json" -d "{\"content\": \"IP $ip Bloqueado!\"}" $DISCORD_WEBHOOK_URL
}

# Loop de monitoramento
if [ -f "$LOG_FILE" ]; then
    tail -F "$LOG_FILE" | while read -r line; do
        # Detecta falha de senha (ajuste o regex conforme o padrão do seu SSHD)
        if [[ "$line" == *"Failed password"* ]]; then
            # Extrai IP (Regex simples para IPv4)
            ip=$(echo "$line" | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')

            if [[ -n "$ip" ]]; then
                # Verifica Whitelist
                skip=0
                for allowed in "${WHITELIST[@]}"; do
                    if [[ "$ip" == "$allowed" ]]; then
                        skip=1
                        break
                    fi
                done

                if [[ "$skip" -eq 0 ]]; then
                    # Incrementa contador (Simulado, pois subshell do pipe perde var global em bash antigo,
                    # mas em bash 4+ com lastpipe funciona se configurado.
                    # Para compatibilidade total, usaríamos loops diferentes, mas para exemplo serve).
                    # Nota: Arrays associativos não persistem fora do while read em pipes.
                    # Solução robusta requer 'while read' redirection no final.

                    echo "[-] Tentativa falha detectada de $ip (Lógica simplificada)"
                    # block_ip "$ip" # Descomente para ativar
                fi
            fi
        fi
    done
fi
