#!/bin/bash
# Script: score_risco_rede.sh
# Descrição: Calcula um Score de Risco de Rede (0-100).
# Autor: Jules (AI Agent)

SCORE=100
DETAILS=""

check_fail() {
    SCORE=$((SCORE - $2))
    DETAILS="$DETAILS\n[Risco -$2] $1"
}

echo "=== Cálculo de Score de Risco de Rede ==="

# 1. Firewall Ativo?
FIREWALL_ACTIVE=0
if command -v ufw >/dev/null && ufw status | grep -q "active"; then FIREWALL_ACTIVE=1; fi
if command -v systemctl >/dev/null && systemctl is-active firewalld >/dev/null; then FIREWALL_ACTIVE=1; fi
if command -v iptables >/dev/null; then
    if iptables -L INPUT -n | grep -v "Chain" | grep -v "target" | grep -q "[A-Z]"; then FIREWALL_ACTIVE=1; fi
fi

if [ $FIREWALL_ACTIVE -eq 0 ]; then
    check_fail "Nenhum Firewall ativo detectado" 50
else
    echo "[OK] Firewall ativo."
fi

# 2. Portas Inseguras
if command -v ss >/dev/null; then
    PORTS=$(ss -tuln)
else
    PORTS=$(netstat -tuln 2>/dev/null)
fi

if echo "$PORTS" | grep -E ":(23|21) "; then
    check_fail "Serviços inseguros (Telnet/FTP) detectados" 20
fi

# 3. Porta SSH Exposta globalmente
if echo "$PORTS" | grep -E "0.0.0.0:22"; then
    if ! ps aux | grep -q fail2ban; then
        check_fail "SSH exposto globalmente sem Fail2Ban detectado" 10
    fi
fi

# 4. IP Forwarding
IPFW=$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null)
if [ "$IPFW" -eq 1 ]; then
    check_fail "IP Forwarding habilitado" 10
fi

# 5. ICMP Redirects
REDIRECTS=$(sysctl -n net.ipv4.conf.all.accept_redirects 2>/dev/null)
if [ "$REDIRECTS" -eq 1 ]; then
    check_fail "ICMP Redirects habilitados" 5
fi

# 6. Syn Cookies
SYNCOOKIES=$(sysctl -n net.ipv4.tcp_syncookies 2>/dev/null)
if [ "$SYNCOOKIES" -eq 0 ]; then
    check_fail "TCP SYN Cookies desabilitados" 5
fi

echo ""
echo "--- Detalhes dos Riscos ---"
if [ -z "$DETAILS" ]; then
    echo "Nenhum risco crítico detectado pelos testes básicos."
else
    echo -e "$DETAILS"
fi

echo ""
echo "=== SCORE FINAL: $SCORE / 100 ==="

if [ $SCORE -lt 50 ]; then
    echo "Estado: CRÍTICO 🔴"
elif [ $SCORE -lt 80 ]; then
    echo "Estado: ATENÇÃO 🟡"
else
    echo "Estado: BOM 🟢"
fi
