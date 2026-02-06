#!/bin/bash
# validacao_updates.sh
# Descrição: Verifica atualizações disponíveis, priorizando correções de segurança.
# Autor: Jules (System Security Suite)

LOG_FILE="/var/log/supply_chain_updates.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$LOG_FILE"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Iniciando validação de atualizações..."

check_apt() {
    log "Atualizando lista de pacotes (apt-get update)..."
    apt-get update >/dev/null 2>&1

    log "Verificando atualizações de segurança disponíveis..."
    # Simulação de upgrade para ver o que seria instalado
    UPDATES=$(apt-get --just-print upgrade 2>&1 | grep "^Inst")

    SECURITY_UPDATES=$(grep -i "security" <<< "$UPDATES")

    if [ -n "$SECURITY_UPDATES" ]; then
        log "[ALERTA] Atualizações de SEGURANÇA disponíveis:"
        echo "$SECURITY_UPDATES" | tee -a "$LOG_FILE"
    elif [ -n "$UPDATES" ]; then
        log "[INFO] Atualizações regulares disponíveis (nenhuma marcada explicitamente como security na saída simples):"
        COUNT=$(echo "$UPDATES" | wc -l)
        log "Total de atualizações: $COUNT"
    else
        log "[OK] Sistema atualizado. Nenhuma atualização pendente."
    fi
}

check_rpm() {
    log "Verificando atualizações com yum/dnf..."

    if command -v dnf >/dev/null; then
        log "Verificando 'dnf updateinfo security'..."
        SEC_INFO=$(dnf updateinfo security 2>/dev/null)
        log "$SEC_INFO"

        log "Lista de atualizações de segurança (se houver):"
        dnf updateinfo list security 2>/dev/null | tee -a "$LOG_FILE"
    elif command -v yum >/dev/null; then
        # yum-security plugin
        log "Verificando atualizações de segurança (yum)..."
        yum list-security 2>/dev/null | tee -a "$LOG_FILE"
    fi
}

if [ -f /etc/debian_version ]; then
    check_apt
elif [ -f /etc/redhat-release ]; then
    check_rpm
else
    if command -v apt-get >/dev/null; then
        check_apt
    elif command -v rpm >/dev/null; then
        check_rpm
    else
        log "Gerenciador não suportado."
        exit 1
    fi
fi

log "Validação de updates finalizada."
