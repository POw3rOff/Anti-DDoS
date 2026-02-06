#!/bin/bash
#
# 1. Hardening Automático do Sistema
# Autor: Jules (AI Agent)
# Descrição: Desativa serviços desnecessários, aplica sysctl seguros e corrige permissões.

if [ "$EUID" -ne 0 ]; then
    echo "Por favor, execute como root."
    # Requer root para funcionar corretamente
fi

echo "[*] Iniciando Hardening do Sistema..."

# --- 1. Desativar Serviços Desnecessários ---
echo "[*] Verificando serviços desnecessários..."
SERVICES_TO_DISABLE=(
    "cups"              # Impressão
    "avahi-daemon"      # Discovery mDNS
    "rpcbind"           # RPC
    "nfs-server"        # NFS
    "bluetooth"         # Bluetooth
)

for service in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "    - Desativando $service..."
        systemctl stop "$service"
        systemctl disable "$service"
    else
        echo "    - $service já está inativo ou não instalado."
    fi
done

# --- 2. Aplicar Sysctl Seguros ---
echo "[*] Aplicando configurações de kernel (Sysctl)..."
SYSCTL_CONF="/etc/sysctl.d/99-security-hardening.conf"

cat <<EOT > "$SYSCTL_CONF"
# IP Spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP broadcast requests
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Block SYN attacks
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# Log Martians
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
EOT

sysctl -p "$SYSCTL_CONF" > /dev/null
echo "    - Sysctl aplicado."

# --- 3. Permissões de Arquivos e Diretórios ---
echo "[*] Ajustando permissões de diretórios críticos..."

# /tmp e /var/tmp devem ter sticky bit
chmod +t /tmp /var/tmp
echo "    - Sticky bit aplicado em /tmp e /var/tmp"

# Permissões de home (impede leitura por outros usuários)
# Cuidado: Isso pode afetar serviços que leem arquivos de usuários (ex: web server userdir)
echo "    - Ajustando permissões em /home/* (750)"
for user_home in /home/*; do
    if [ -d "$user_home" ]; then
        chmod 750 "$user_home"
    fi
done

echo "[*] Hardening concluído."
