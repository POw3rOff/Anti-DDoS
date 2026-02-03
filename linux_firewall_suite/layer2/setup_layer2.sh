#!/bin/bash
#
# Script de Configuração Layer 2 (Arptables & Ebtables)
# Autor: Jules (AI Agent)
# Uso: Proteção contra ARP Spoofing e filtragem de Bridge.

echo "Aplicando regras Layer 2..."

# --- Arptables (ARP Firewall) ---
# Útil para evitar ARP Spoofing/Poisoning localmente.

# Limpar regras
arptables -F

# Política Padrão: Aceitar (cuidado ao mudar para DROP sem permitir gateway)
arptables -P INPUT ACCEPT
arptables -P OUTPUT ACCEPT

# Regra: Permitir ARP apenas do Gateway conhecido (Exemplo: 192.168.1.1 é o GW, MAC aa:bb:cc:dd:ee:ff)
# GATEWAY_IP="192.168.1.1"
# GATEWAY_MAC="aa:bb:cc:dd:ee:ff"
# arptables -A INPUT --source-ip $GATEWAY_IP --source-mac ! $GATEWAY_MAC -j DROP
# echo "Proteção ARP Spoofing para Gateway ativada (comentada no script)."

# --- Ebtables (Ethernet Bridge Tables) ---
# Útil se esta máquina for uma bridge (ex: host de VMs, switch linux).

# Limpar regras
ebtables -F

# Anti-Spoofing em Bridge:
# Bloquear pacotes onde o IP de origem não bate com o MAC esperado (requer configuração específica por porta)
# ebtables -t nat -A PREROUTING -i eth0 -s ! 00:11:22:33:44:55 -j DROP

# Bloquear frames de broadcast excessivos (Storm Control simples)
# ebtables -A INPUT --limit 100/sec -j ACCEPT
# ebtables -A FORWARD --limit 100/sec -j ACCEPT

echo "Regras Layer 2 aplicadas (verifique o script para descomentar regras específicas)."
