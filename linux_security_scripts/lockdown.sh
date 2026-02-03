#!/bin/bash

# Script de Lockdown de Emergência
# Bloqueia todo o tráfego exceto SSH e Loopback em caso de ataque

BACKUP_FILE="/tmp/iptables.lockdown.backup"
LOG_FILE="/var/log/lockdown.log"

log_msg() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" >> "$LOG_FILE"
    echo "$1"
}

lockdown() {
    log_msg "INICIANDO LOCKDOWN DE EMERGÊNCIA..."

    # 1. Backup das regras atuais
    if command -v iptables-save &> /dev/null; then
        iptables-save > "$BACKUP_FILE"
        log_msg "Backup das regras iptables salvo em $BACKUP_FILE"
    else
        log_msg "Erro: iptables-save não encontrado. Abortando para segurança."
        return 1
    fi

    # 2. Limpar regras atuais (Flush)
    iptables -F
    iptables -X
    iptables -Z

    # 3. Adicionar Regras de Permissão PRIMEIRO (Para evitar desconexão)

    # Permitir Loopback
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT

    # Permitir conexões estabelecidas
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

    # Permitir SSH (Porta 22) - ESSENCIAL
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    log_msg "SSH (porta 22) permitido."

    # Permitir Saída Essencial (DNS, HTTP/S para updates/alertas) - Opcional, mas recomendado
    iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

    # 4. Definir Políticas Padrão para DROP (No final)
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT DROP

    log_msg "LOCKDOWN APLICADO! Todo o tráfego não essencial foi bloqueado."
}

unlock() {
    log_msg "Desativando Lockdown..."

    if [ -f "$BACKUP_FILE" ]; then
        iptables-restore < "$BACKUP_FILE"
        log_msg "Regras anteriores restauradas de $BACKUP_FILE"
    else
        log_msg "Arquivo de backup não encontrado. Limpando regras e definindo ACCEPT (Cuidado!)."
        iptables -F
        iptables -X
        iptables -P INPUT ACCEPT
        iptables -P FORWARD ACCEPT
        iptables -P OUTPUT ACCEPT
    fi
}

main() {
    if [ "$(id -u)" != "0" ]; then
        echo "Execute como root."
        return 1
    fi

    if [ "$1" == "on" ]; then
        lockdown
    elif [ "$1" == "off" ]; then
        unlock
    else
        echo "Uso: $0 [on|off]"
        echo "  on  - Ativa o modo de lockdown (Bloqueia tudo exceto SSH e serviços essenciais de saída)"
        echo "  off - Restaura as regras anteriores"
    fi
}

main "$@"
