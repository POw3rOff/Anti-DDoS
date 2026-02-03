#!/bin/bash
#
# Script de Configuração IPTables (Básico + Avançado)
# Autor: Jules (AI Agent)
# Descrição: Firewall stateful com proteção contra DDoS, scans e pacotes inválidos.

# --- Configurações ---
INT_NET="eth0" # Interface de rede principal (ajuste conforme necessário)
SSH_PORT="22"

echo "Aplicando regras de Firewall IPTables..."

# 1. Limpar regras existentes
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# 2. Definir Políticas Padrão (DROP tudo por padrão)
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# --- Regras Básicas ---

# Aceitar tráfego na interface de loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Aceitar conexões já estabelecidas e relacionadas
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Permitir SSH (com limite básico de taxa para evitar brute-force simples)
# Aceita novas conexões na porta SSH
iptables -A INPUT -p tcp --dport $SSH_PORT -m conntrack --ctstate NEW -m limit --limit 3/min --limit-burst 3 -j ACCEPT
# Nota: Para proteção SSH mais robusta, use Fail2ban.

# Permitir HTTP e HTTPS (Servidor Web)
iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m conntrack --ctstate NEW -j ACCEPT

# Permitir Ping (ICMP) com limite (evita flood)
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# --- Regras Avançadas (Hardening & Anti-DDoS) ---

# Bloquear Pacotes Inválidos
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Bloquear Pacotes com Flags TCP Bogus (XMAS, Null, etc.)
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP

# Proteção contra SYN Flood (Limitar novas conexões TCP que não são SYN)
iptables -A INPUT -p tcp ! --syn -m conntrack --ctstate NEW -j DROP

# Bloquear fragmentos (evita ataques de fragmentação)
iptables -A INPUT -f -j DROP

# Proteção contra Port Scanning (Bloqueia quem scaneia agressivamente)
# Cria uma lista 'port_scan' e bloqueia IPs que atingirem o limite
iptables -A INPUT -m recent --name port_scan --rcheck --seconds 86400 -j DROP
iptables -A INPUT -m recent --name port_scan --remove
iptables -A INPUT -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -m recent --name port_scan --set
# Se tentar mais de 10 conexões novas muito rápido em portas não abertas (logica simplificada aqui)
# Nota: Implementação real de port-scan via iptables pode ser complexa e bloquear legítimos.
# Usamos aqui uma regra genérica para limitar conexões simultâneas excessivas por IP de origem:
iptables -A INPUT -p tcp --syn -m connlimit --connlimit-above 50 -m connlimit-mask 32 -j REJECT --reject-with tcp-reset

# --- Kernel Hardening (Sysctl) ---
echo "Aplicando ajustes de Kernel..."

# Proteção contra IP Spoofing
for i in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 1 > "$i"; done

# Ignorar ICMP Broadcasts (Smurf attack)
echo 1 > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts

# Desabilitar Source Routing
for i in /proc/sys/net/ipv4/conf/*/accept_source_route; do echo 0 > "$i"; done

# Habilitar TCP SYN Cookies (Proteção SYN Flood)
echo 1 > /proc/sys/net/ipv4/tcp_syncookies

# Logar pacotes marcianos (IPs impossíveis naquela interface)
for i in /proc/sys/net/ipv4/conf/*/log_martians; do echo 1 > "$i"; done

echo "Regras aplicadas com sucesso."
echo "IMPORTANTE: Instale o pacote 'iptables-persistent' ou use 'iptables-save' para persistir após reboot."
