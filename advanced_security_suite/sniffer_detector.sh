#!/bin/bash
#
# 11. Detetor de Sniffers / Interfaces em Modo Promíscuo
# Autor: Jules (AI Agent)
# Descrição: Verifica se alguma interface de rede está em modo promíscuo (sniffer ativo).

echo "[*] Verificando interfaces de rede..."

FOUND=0

# Método 1: ip link
if command -v ip >/dev/null; then
    # Procura pela flag PROMISC na saída do ip link
    # Ignora loopback e interfaces virtuais de container se possível, mas PROMISC é sempre suspeito no host
    PROMISC_IFS=$(ip link show | grep "PROMISC")

    if [ -n "$PROMISC_IFS" ]; then
        echo "[!] ALERTA: Interfaces em modo PROMÍSCUO detectadas (ip link):"
        echo "$PROMISC_IFS"
        FOUND=1
    fi
else
    # Método 2: ifconfig (Legacy)
    if command -v ifconfig >/dev/null; then
        PROMISC_IFS=$(ifconfig | grep "PROMISC")
        if [ -n "$PROMISC_IFS" ]; then
            echo "[!] ALERTA: Interfaces em modo PROMÍSCUO detectadas (ifconfig):"
            echo "$PROMISC_IFS"
            FOUND=1
        fi
    fi
fi

# Método 3: Verificação via /sys/class/net (Linux nativo)
# Flag IFF_PROMISC é 0x100
echo "[*] Verificando flags em /sys/class/net..."
for iface in /sys/class/net/*; do
    if [ -e "$iface/flags" ]; then
        flags=$(cat "$iface/flags")
        # Decodificar hex. 0x100 bit set?
        # Bash arithmetic handles hex automatically
        if (( (flags & 0x100) != 0 )); then
            ifname=$(basename "$iface")
            echo "[!] ALERTA: Interface $ifname tem flag PROMISC ativa (Flags: $flags)"
            FOUND=1
        fi
    fi
done

if [ "$FOUND" -eq 0 ]; then
    echo "[OK] Nenhuma interface em modo promíscuo detectada."
else
    echo ""
    echo "[!] AVISO: Modo promíscuo é normal em Bridges, VMs e Docker."
    echo "    Verifique se estas interfaces pertencem a virtualização."
fi
