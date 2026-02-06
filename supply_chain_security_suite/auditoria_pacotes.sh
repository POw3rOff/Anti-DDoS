#!/bin/bash
# auditoria_pacotes.sh
# Descrição: Auditoria de pacotes instalados, verificando integridade e dependências quebradas.
# Autor: Jules (System Security Suite)

LOG_FILE="/var/log/supply_chain_auditoria.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Função de log
log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$LOG_FILE"
}

# Verificar permissões de root
if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Iniciando auditoria de pacotes..."

# Função para sistemas DEBIAN/UBUNTU
audit_debian() {
    log "Sistema detectado: Debian/Ubuntu (APT/DPKG)"

    # Verificar dependências quebradas
    log "Verificando dependências quebradas (apt-get check)..."
    if apt-get check >/dev/null 2>&1; then
        log "[OK] Estrutura de dependências íntegra."
    else
        log "[ALERTA] Encontrados problemas nas dependências!"
        apt-get check 2>&1 | tee -a "$LOG_FILE"
    fi

    # Verificar pacotes parcialmente instalados
    log "Verificando pacotes configurados parcialmente..."
    PARTIAL=$(dpkg -l | grep -v "^ii" | grep -v "^rc" | tail -n +6)
    if [ -n "$PARTIAL" ]; then
        log "[ALERTA] Pacotes em estado inconsistente encontrados:"
        echo "$PARTIAL" | tee -a "$LOG_FILE"
    else
        log "[OK] Nenhum pacote em estado inconsistente."
    fi

    # Contagem total
    TOTAL=$(dpkg -l | grep "^ii" | wc -l)
    log "Total de pacotes instalados: $TOTAL"
}

# Função para sistemas RHEL/CENTOS/FEDORA
audit_rhel() {
    log "Sistema detectado: RHEL/CentOS/Fedora (RPM)"

    # Verificar problemas com yum/dnf
    local MANAGE_TOOL=""
    if command -v dnf >/dev/null; then
        MANAGE_TOOL="dnf"
    elif command -v yum >/dev/null; then
        MANAGE_TOOL="yum"
    fi

    if [ -n "$MANAGE_TOOL" ]; then
        log "Executando verificação com $MANAGE_TOOL check..."
        if $MANAGE_TOOL check >/dev/null 2>&1; then
            log "[OK] Nenhuma inconsistência detectada pelo $MANAGE_TOOL."
        else
            log "[ALERTA] $MANAGE_TOOL detectou problemas:"
            $MANAGE_TOOL check 2>&1 | tee -a "$LOG_FILE"
        fi
    else
        log "[AVISO] Nem dnf nem yum encontrados para verificação avançada."
    fi

    # Verificar pacotes duplicados
    log "Verificando pacotes duplicados (package-cleanup)..."
    if command -v package-cleanup >/dev/null; then
        DUPLICATES=$(package-cleanup --dupes)
        if [ -n "$DUPLICATES" ]; then
            log "[ALERTA] Pacotes duplicados encontrados:"
            echo "$DUPLICATES" | tee -a "$LOG_FILE"
        else
            log "[OK] Nenhum pacote duplicado encontrado."
        fi
    else
        # Tenta verificar duplicados via rpm
        DUPLICATES_RPM=$(rpm -qa --qf "%{NAME}\n" | sort | uniq -d)
        if [ -n "$DUPLICATES_RPM" ]; then
             log "[ALERTA] Possíveis pacotes duplicados (verificação simples):"
             echo "$DUPLICATES_RPM" | tee -a "$LOG_FILE"
        fi
    fi

    TOTAL=$(rpm -qa | wc -l)
    log "Total de pacotes instalados: $TOTAL"
}

# Detecção do gerenciador
if [ -f /etc/debian_version ]; then
    audit_debian
elif [ -f /etc/redhat-release ]; then
    audit_rhel
else
    # Fallback genérico
    if command -v dpkg >/dev/null; then
        audit_debian
    elif command -v rpm >/dev/null; then
        audit_rhel
    else
        log "[ERRO] Sistema não suportado (não foi possível detectar apt/dpkg ou yum/rpm)."
        exit 1
    fi
fi

log "Auditoria de pacotes finalizada."
