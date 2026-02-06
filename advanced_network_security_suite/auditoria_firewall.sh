#!/bin/bash
# Script: auditoria_firewall.sh
# Descrição: Audita as regras de firewall (iptables/nftables/ufw) em busca de vulnerabilidades comuns.
# Autor: Jules (AI Agent)

DATA=$(date +%Y%m%d_%H%M%S)
LOG_FILE="auditoria_firewall_$DATA.log"

log() {
    echo "$1"
    echo "$1" >> "$LOG_FILE"
}

log "=== Iniciando Auditoria de Firewall: $DATA ==="

# Verificação de Privilégios
if [ "$(id -u)" -ne 0 ]; then
   log "[ERRO] Este script precisa ser executado como root."
   exit 1
fi

# 1. Identificação do Firewall
FIREWALL_DETECTED=0

# UFW
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
    log "[INFO] UFW está ATIVO."
    FIREWALL_DETECTED=1

    # Check Default Policy
    DEFAULT_INCOMING=$(ufw status verbose | grep "Default:" | grep -o "incoming [a-z]*" | awk '{print $2}')
    if [ "$DEFAULT_INCOMING" == "allow" ]; then
        log "[ALERTA CRÍTICO] UFW: Política padrão de entrada é ALLOW (Permitir)."
    else
        log "[OK] UFW: Política padrão de entrada é $DEFAULT_INCOMING."
    fi
fi

# IPTABLES (Legacy)
if command -v iptables >/dev/null; then
    # Verifica se há regras carregadas
    COUNT=$(iptables -L INPUT -n | wc -l)
    if [ "$COUNT" -gt 2 ]; then
        log "[INFO] IPTables: Regras detectadas."
        FIREWALL_DETECTED=1

        # Check Policies
        log "[*] Checando Políticas Padrão do IPTables..."
        if iptables -L INPUT -n | grep -q "policy ACCEPT"; then
            log "[ALERTA] IPTables: Chain INPUT tem política padrão ACCEPT."
        else
            log "[OK] IPTables: Chain INPUT tem política restritiva (DROP/REJECT)."
        fi

        if iptables -L FORWARD -n | grep -q "policy ACCEPT"; then
             log "[ALERTA] IPTables: Chain FORWARD tem política padrão ACCEPT. (Risco se não for roteador)"
        fi

        # Check for Empty Password Rules
        log "[*] Checando portas comuns abertas para o mundo (0.0.0.0/0)..."
        DANGEROUS_PORTS="21 23 25 3389 445 139"
        for PORT in $DANGEROUS_PORTS; do
            if iptables -L INPUT -n -v | grep -E "dpt:$PORT" | grep -q "0.0.0.0/0"; then
                log "[AVISO] Porta $PORT aberta para TODAS as origens (0.0.0.0/0) no IPTables."
            fi
        done

        # Check invalid packets drop
        if ! iptables -L INPUT -n -v | grep -q "state INVALID"; then
             log "[SUGESTÃO] Considere bloquear pacotes INVALID no topo da chain INPUT."
        fi

    elif [ "$FIREWALL_DETECTED" -eq 0 ]; then
        log "[INFO] IPTables instalado mas sem regras ativas (ou apenas policies padrão)."
    fi
fi

# NFTABLES
if command -v nft >/dev/null; then
    if nft list ruleset | grep -q "table"; then
        log "[INFO] NFTables: Regras detectadas."
        FIREWALL_DETECTED=1
        log "[*] Listando tabelas ativas do NFTables..."
        nft list tables >> "$LOG_FILE"
    fi
fi

if [ "$FIREWALL_DETECTED" -eq 0 ]; then
    log "[ALERTA CRÍTICO] Nenhum firewall ativo detectado (UFW, IPTables com regras, NFTables)."
    log "[RECOMENDAÇÃO] Configure um firewall imediatamente."
else
    log "[INFO] Auditoria concluída. Revise o log $LOG_FILE para detalhes."
fi

log "=== Fim da Auditoria ==="
