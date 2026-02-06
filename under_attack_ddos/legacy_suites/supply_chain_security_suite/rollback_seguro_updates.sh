#!/bin/bash
# rollback_seguro_updates.sh
# Descrição: Ferramenta para auxiliar no rollback de atualizações (via gerenciador de pacotes ou snapshot).
# Autor: Jules (System Security Suite)

LOG_FILE="/var/log/supply_chain_rollback.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$LOG_FILE"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Iniciando assistente de rollback..."

# 1. Verificar Snapshots (LVM/ZFS/BTRFS)
check_snapshots() {
    log "Verificando suporte a snapshots de sistema de arquivos..."
    if command -v lvs >/dev/null; then
        log "LVM detectado. Snapshots LVM disponíveis:"
        lvs 2>/dev/null | grep "swi" | tee -a "$LOG_FILE"
    fi
    if command -v zfs >/dev/null; then
        log "ZFS detectado. Snapshots ZFS:"
        zfs list -t snapshot 2>/dev/null | tail -n 5 | tee -a "$LOG_FILE"
    fi
    if command -v btrfs >/dev/null; then
        log "Btrfs detectado. Subvolumes:"
        btrfs subvolume list / 2>/dev/null | tail -n 5 | tee -a "$LOG_FILE"
    fi
}

rollback_rpm() {
    log "Sistema RPM detectado."

    if command -v dnf >/dev/null; then
        log "Exibindo histórico DNF recente:"
        dnf history list | head -n 10

        log "Para desfazer a última transação, execute: dnf history undo last"
        log "Deseja desfazer a última atualização AGORA? (s/N)"
        read -r RESP
        if [[ "$RESP" =~ ^[sS]$ ]]; then
            log "Executando rollback (dnf history undo last)..."
            dnf history undo last 2>&1 | tee -a "$LOG_FILE"
        else
            log "Rollback cancelado pelo usuário."
        fi
    elif command -v yum >/dev/null; then
        log "Exibindo histórico YUM recente:"
        yum history list | head -n 10

        log "Para desfazer a última transação: yum history undo last"
        log "Deseja desfazer a última atualização AGORA? (s/N)"
        read -r RESP
        if [[ "$RESP" =~ ^[sS]$ ]]; then
            log "Executando rollback (yum history undo last)..."
            yum history undo last 2>&1 | tee -a "$LOG_FILE"
        else
             log "Rollback cancelado."
        fi
    fi
}

rollback_apt() {
    log "Sistema APT detectado."
    log "AVISO: O APT não suporta rollback automático nativo como o DNF/YUM."
    log "Exibindo histórico recente (/var/log/apt/history.log) para auxiliar:"

    if [ -f /var/log/apt/history.log ]; then
        tail -n 20 /var/log/apt/history.log | tee -a "$LOG_FILE"

        log "Instrução: Para fazer rollback, identifique a versão anterior e instale manualmente:"
        log "apt-get install pacote=versao_antiga"
    else
        log "Log de histórico do APT não encontrado."
    fi
}

check_snapshots

if [ -f /etc/redhat-release ]; then
    rollback_rpm
elif [ -f /etc/debian_version ]; then
    rollback_apt
else
    if command -v rpm >/dev/null; then
        rollback_rpm
    elif command -v apt-get >/dev/null; then
        rollback_apt
    else
        log "Sistema não suportado."
    fi
fi

log "Assistente de rollback finalizado."
