#!/bin/bash
# Script: filtragem_trafego_saida.sh
# Descrição: Configura regras estritas de Egress (Saída) no IPTables.
# Uso: ./filtragem_trafego_saida.sh [--apply]
# Autor: Jules (AI Agent)

if [ "$(id -u)" -ne 0 ]; then
    echo "[ERRO] Execute como root."
    exit 1
fi

APPLY=0
if [ "$1" == "--apply" ]; then
    APPLY=1
fi

echo "=== Filtragem de Tráfego de Saída (Egress Filtering) ==="

if [ $APPLY -eq 0 ]; then
    echo "[MODO AUDITORIA] Nenhuma alteração será feita sem o argumento --apply."
    echo ""
    echo "Atualmente, a política de OUTPUT é:"
    iptables -L OUTPUT -n | grep "policy"
    echo ""
    echo "Regras propostas:"
    echo "1. Permitir tráfego local (lo)."
    echo "2. Permitir conexões JÁ ESTABELECIDAS (Stateful)."
    echo "3. Permitir DNS (53 UDP/TCP)."
    echo "4. Permitir HTTP/HTTPS (80/443 TCP) para atualizações/web."
    echo "5. Permitir NTP (123 UDP) para relógio."
    echo "6. LOGAR e BLOQUEAR o resto."
    echo ""
    echo "Para aplicar, execute: $0 --apply"
else
    echo "[MODO APLICAÇÃO] Aplicando regras em 5 segundos... (Ctrl+C para cancelar)"
    sleep 5

    echo "[*] Configurando regras..."

    # Aceita conexões estabelecidas
    iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

    # Aceita Loopback
    iptables -A OUTPUT -o lo -j ACCEPT

    # Aceita DNS
    iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

    # Aceita HTTP/HTTPS
    iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

    # Aceita NTP
    iptables -A OUTPUT -p udp --dport 123 -j ACCEPT

    # Logar pacotes bloqueados
    iptables -A OUTPUT -m limit --limit 5/min -j LOG --log-prefix "[IPTABLES DROP OUT]: " --log-level 7

    # Mudar política para DROP
    iptables -P OUTPUT DROP

    echo "[OK] Regras aplicadas com sucesso."

    # Opcional: Liberar ICMP
    iptables -A OUTPUT -p icmp -j ACCEPT
    echo "[*] ICMP liberado para testes de conectividade."

    echo ""
    echo "Regras Atuais de OUTPUT:"
    iptables -L OUTPUT -n -v
fi
