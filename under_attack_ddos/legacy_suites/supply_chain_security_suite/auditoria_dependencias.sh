#!/bin/bash
# auditoria_dependencias.sh
# Descrição: Identifica dependências órfãs e não utilizadas no sistema.
# Autor: Jules (System Security Suite)

LOG_FILE="/var/log/supply_chain_dependencias.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$LOG_FILE"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Iniciando auditoria de dependências..."

audit_apt() {
    log "Sistema APT detectado."

    # Verificar pacotes autoremove
    log "Verificando pacotes sugeridos para autoremove (órfãos)..."
    AUTOREMOVE=$(apt-get --dry-run autoremove | grep "^Remv")

    if [ -n "$AUTOREMOVE" ]; then
        log "[AVISO] Encontrados pacotes órfãos que podem ser removidos:"
        echo "$AUTOREMOVE" | tee -a "$LOG_FILE"
        COUNT=$(echo "$AUTOREMOVE" | wc -l)
        log "Total de pacotes órfãos: $COUNT"
    else
        log "[OK] Nenhum pacote órfão detectado pelo apt-get autoremove."
    fi

    # Verificar com deborphan se disponível
    if command -v deborphan >/dev/null; then
        log "Executando deborphan..."
        ORPHANS=$(deborphan)
        if [ -n "$ORPHANS" ]; then
            log "[AVISO] deborphan detectou bibliotecas órfãs:"
            echo "$ORPHANS" | tee -a "$LOG_FILE"
        fi
    fi
}

audit_rpm() {
    log "Sistema RPM detectado."

    if command -v package-cleanup >/dev/null; then
        log "Verificando 'leaves' (pacotes folha/órfãos) com package-cleanup..."
        LEAVES=$(package-cleanup --leaves --all 2>/dev/null)
        if [ -n "$LEAVES" ]; then
            log "[INFO] Pacotes 'leaves' encontrados (potenciais órfãos se não foram instalados explicitamente):"
            echo "$LEAVES" | head -n 20 | tee -a "$LOG_FILE"
            log "(Lista truncada)"
        fi

        log "Verificando problemas de dependência com package-cleanup --problems..."
        PROBLEMS=$(package-cleanup --problems 2>/dev/null)
        if [ -n "$PROBLEMS" ]; then
            log "[ALERTA] Problemas de dependência encontrados:"
            echo "$PROBLEMS" | tee -a "$LOG_FILE"
        else
            log "[OK] Nenhum problema de dependência detectado."
        fi
    elif command -v dnf >/dev/null; then
        log "Verificando autoremove com dnf..."
        # dnf autoremove list
        AUTOREMOVE=$(dnf autoremove --assumeno 2>/dev/null | grep "^ ")
        # A saída do dnf é formatada, difícil de parsear perfeitamente sem rodar.
        log "Executando 'dnf repoquery --unneeded' (se disponível)..."
        if dnf repoquery --unneeded >/dev/null 2>&1; then
             UNNEEDED=$(dnf repoquery --unneeded)
             log "[INFO] Pacotes desnecessários detectados pelo DNF:"
             echo "$UNNEEDED" | head -n 20 | tee -a "$LOG_FILE"
        fi
    else
        log "Ferramentas yum-utils ou dnf não encontradas para análise profunda."
    fi
}

if [ -f /etc/debian_version ]; then
    audit_apt
elif [ -f /etc/redhat-release ]; then
    audit_rpm
else
    if command -v apt-get >/dev/null; then
        audit_apt
    elif command -v rpm >/dev/null; then
        audit_rpm
    else
        log "Gerenciador não suportado."
        exit 1
    fi
fi

log "Auditoria de dependências concluída."
