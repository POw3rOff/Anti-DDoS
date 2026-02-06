#!/bin/bash
#
# 14. Detetor de Tunnels (SSH, DNS, ICMP)
# Autor: Jules (AI Agent)
# Descrição: Procura por indícios de tunelamento de tráfego.

echo "[*] Procurando Tunnels..."
FOUND=0

# 1. SSH Tunnels (Local, Remote, Dynamic)
# Flags: -L (Local), -R (Remote), -D (Dynamic/SOCKS)
echo "[*] Verificando SSH Tunnels..."
# ps aux | grep ssh | grep -E "\-L|\-R|\-D"
# Usando /proc para maior precisão
for pid in $(pgrep ssh); do
    if [ -f "/proc/$pid/cmdline" ]; then
        cmd=$(tr '\0' ' ' < /proc/$pid/cmdline)
        if [[ "$cmd" == *"-L "* ]] || [[ "$cmd" == *"-R "* ]] || [[ "$cmd" == *"-D "* ]]; then
            echo "[!] ALERTA: Tunnel SSH detectado (PID $pid)"
            echo "    CMD: $cmd"
            FOUND=1
        fi
    fi
done

# 2. Processos de Tunneling Conhecidos (DNS/ICMP)
echo "[*] Verificando ferramentas de tunneling conhecidas..."
TUNNEL_TOOLS="iodine dnscat ptunnel hans icmptx udptunnel socat"
for tool in $TUNNEL_TOOLS; do
    pids=$(pgrep -f "$tool")
    if [ -n "$pids" ]; then
        echo "[!] ALERTA: Ferramenta suspeita detectada: $tool (PIDs: $pids)"
        FOUND=1
    fi
done

# 3. Interfaces TUN/TAP suspeitas
# Tunnels DNS/ICMP frequentemente criam interfaces tunX ou tapX
echo "[*] Verificando interfaces TUN/TAP..."
TUN_INTERFACES=$(ip link show | grep -E "tun[0-9]|tap[0-9]" | awk -F: '{print $2}')
if [ -n "$TUN_INTERFACES" ]; then
    echo "[?] AVISO: Interfaces virtuais encontradas (podem ser VPN legítima):"
    echo "$TUN_INTERFACES"
    # Diferenciar VPN legítima (OpenVPN) de tools estranhas é difícil só pelo nome
fi

if [ "$FOUND" -eq 0 ]; then
    echo "[OK] Nenhum tunnel óbvio detectado via processos."
fi
