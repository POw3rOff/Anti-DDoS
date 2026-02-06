#!/bin/bash
# Script: detecao_tunels.sh
# Descrição: Detecta interfaces e processos associados a túneis (VPN, SSH, etc).
# Autor: Jules (AI Agent)

DATA=$(date +%Y%m%d_%H%M%S)
LOG_FILE="detecao_tunels_$DATA.log"

echo "=== Detecção de Túneis e VPNs ===" | tee -a "$LOG_FILE"

# 1. Verificar Interfaces
echo "[*] Verificando interfaces de rede suspeitas..."
INTERFACES=$(ip link show | grep -E ": (tun|tap|wg|ppp)[0-9]+")

if [ -n "$INTERFACES" ]; then
    echo "[ALERTA] Interfaces de túnel detectadas:" | tee -a "$LOG_FILE"
    echo "$INTERFACES" | tee -a "$LOG_FILE"
else
    echo "[OK] Nenhuma interface tun/tap/wg/ppp óbvia encontrada." | tee -a "$LOG_FILE"
fi

# 2. Verificar Processos
echo "[*] Verificando processos de tunelamento..."
PROCS=$(ps aux | grep -E "(openvpn|wireguard|stunnel|tinc|pppd|vpnc|tailscale|zerotier)" | grep -v grep)

if [ -n "$PROCS" ]; then
    echo "[ALERTA] Processos de VPN/Túnel detectados:" | tee -a "$LOG_FILE"
    echo "$PROCS" | awk '{print $1, $2, $11}' | tee -a "$LOG_FILE"
else
    echo "[OK] Nenhum processo de VPN comum encontrado." | tee -a "$LOG_FILE"
fi

# 3. Verificar SSH Tunnels
echo "[*] Verificando túneis SSH (Forwarding)..."
SSH_TUNNELS=$(ps aux | grep ssh | grep -E "(\-L|\-R|\-D)" | grep -v grep)
if [ -n "$SSH_TUNNELS" ]; then
     echo "[ALERTA] Sessões SSH com Port Forwarding detectadas:" | tee -a "$LOG_FILE"
     echo "$SSH_TUNNELS" | tee -a "$LOG_FILE"
else
     echo "[OK] Nenhuma sessão SSH com flags explícitas de túnel (-L/-R/-D) encontrada." | tee -a "$LOG_FILE"
fi

# 4. Portas de VPN
echo "[*] Verificando portas comuns de VPN..."
if command -v ss >/dev/null; then
    VPN_PORTS=$(ss -ulnp | grep -E ":(1194|51820|500|4500)")
    if [ -n "$VPN_PORTS" ]; then
        echo "[ALERTA] Portas de VPN ouvindo:" | tee -a "$LOG_FILE"
        echo "$VPN_PORTS" | tee -a "$LOG_FILE"
    fi
fi
echo "=== Fim da Análise ===" | tee -a "$LOG_FILE"
