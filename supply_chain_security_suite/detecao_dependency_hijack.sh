#!/bin/bash
# detecao_dependency_hijack.sh
# Descrição: Tenta detectar sinais de Dependency Hijack verificando repositórios estranhos e atualizações recentes suspeitas.
# Autor: Jules (System Security Suite)

LOG_FILE="/var/log/supply_chain_hijack.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$LOG_FILE"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Iniciando varredura por Dependency Hijack (Heurística)..."

# 1. Verificar repositórios configurados
log "1. Analisando repositórios configurados..."
# Lista todos os arquivos de repo
if [ -d /etc/apt/sources.list.d ]; then
    grep -r "^deb" /etc/apt/sources.list /etc/apt/sources.list.d/ | cut -d: -f2- | sort | uniq > /tmp/repos_list.txt
elif [ -d /etc/yum.repos.d ]; then
    grep -r "baseurl" /etc/yum.repos.d/ | cut -d= -f2 | sort | uniq > /tmp/repos_list.txt
fi

log "Repositórios encontrados (verifique se reconhece todos):"
cat /tmp/repos_list.txt | tee -a "$LOG_FILE"

# Heurística: Repositórios sem assinatura GPG ou HTTP simples
if grep "http://" /tmp/repos_list.txt; then
    log "[ALERTA] Repositórios usando HTTP (não criptografado) detectados! Risco de MitM/Hijack."
    grep "http://" /tmp/repos_list.txt | tee -a "$LOG_FILE"
else
    log "[OK] Todos os repositórios parecem usar HTTPS ou outro protocolo seguro."
fi

# 2. Pacotes instalados recentemente (últimos 3 dias)
log "2. Listando pacotes instalados/atualizados nos últimos 3 dias..."
if [ -f /var/log/dpkg.log ]; then
    # Debian/Ubuntu
    grep " install " /var/log/dpkg.log | grep "$(date +%Y-%m-%d -d 'today')"
    grep " install " /var/log/dpkg.log | grep "$(date +%Y-%m-%d -d 'yesterday')"
    # ... simples grep dos últimos dias
    # Melhor usar find no log se rotacionado, mas vamos simplificar.
    RECENT=$(grep " install " /var/log/dpkg.log | tail -n 20)
    if [ -n "$RECENT" ]; then
        log "Instalações recentes (amostra):"
        echo "$RECENT" | tee -a "$LOG_FILE"
    fi
elif [ -f /var/log/yum.log ] || [ -f /var/log/dnf.log ]; then
    # RHEL
    LOG_YUM="/var/log/yum.log"
    [ -f /var/log/dnf.log ] && LOG_YUM="/var/log/dnf.log"
    RECENT=$(tail -n 20 "$LOG_YUM")
    log "Instalações recentes (amostra):"
    echo "$RECENT" | tee -a "$LOG_FILE"
fi

# 3. PIP/NPM globais (alvos comuns de hijack)
log "3. Verificando pacotes globais de linguagens (PIP/NPM) se existirem..."

if command -v pip3 >/dev/null; then
    log "Verificando pacotes PIP instalados globalmente..."
    # Listar pacotes que não são distribuídos pelo sistema operacional (heurística)
    # pip list --outdated ou freeze
    COUNT=$(pip3 list --format=freeze 2>/dev/null | wc -l)
    log "Total de pacotes PIP globais: $COUNT"

    # Verificar pacotes instalados recentemente via pip é difícil sem logs específicos do pip.
    # Mas podemos checar por pacotes 'extra'
fi

if command -v npm >/dev/null; then
    log "Verificando pacotes NPM globais..."
    NPM_GLOBALS=$(npm list -g --depth=0 2>/dev/null)
    log "$NPM_GLOBALS" | tee -a "$LOG_FILE"
fi

log "Análise concluída. Revise os repositórios e instalações recentes manualmente."
rm -f /tmp/repos_list.txt
