#!/bin/bash
#
# freeze_backup.sh
#
# Este script suspende temporariamente operações de backup automatizadas
# para prevenir a sobrescrita de dados bons por dados corrompidos/criptografados
# durante um incidente.
#
# Funcionalidades:
# - Para serviços de backup conhecidos.
# - Comenta temporariamente linhas de backup no crontab do root.
# - Mata processos de backup em execução.
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

LOG_FILE="/var/log/incident_freeze_backup.log"

log() {
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

log "INICIANDO CONGELAMENTO DE BACKUPS (FREEZE)"

# 1. Parar Serviços de Backup Comuns
SERVICES="bacula-fd bareos-fd veeamservice rsync"
for service in $SERVICES; do
    if systemctl is-active --quiet "$service"; then
        log "Parando serviço: $service"
        systemctl stop "$service"
        systemctl disable "$service"
    fi
done

# 2. Matar Processos de Backup Ativos
PROCESSES="rsync borg restic tar rclone aws azcopy"
log "Matando processos ativos: $PROCESSES"
# pkill -f retorna 0 se matou, 1 se nada encontrado
pkill -f "$PROCESSES" && log "Processos encerrados." || log "Nenhum processo ativo encontrado."

# 3. Desabilitar Cron Jobs de Backup (Heurística simples)
# Atenção: Isso modifica o crontab do root. Requer cuidado.
log "Verificando Crontab do root por tarefas de backup..."
if crontab -l | grep -qE "(backup|rsync|borg|restic|tar)"; then
    log "Encontradas tarefas de backup no crontab. Comentando..."
    # Faz backup do crontab atual
    crontab -l > "/root/crontab.bak.$(date +%Y%m%d_%H%M%S)"
    # Comenta linhas com palavras chave
    crontab -l | sed -E "/(backup|rsync|borg|restic|tar)/s/^/#FREEZE# /" | crontab -
    log "Crontab atualizado. Backup salvo em /root/crontab.bak.*"
else
    log "Nenhuma tarefa de backup óbvia encontrada no crontab do root."
fi

# 4. Bloquear Usuários de Backup (Opcional)
# Se houver um usuário dedicado "backup", bloquear senha/login
if id "backup" &>/dev/null; then
    log "Bloqueando usuário backup..."
    usermod -L backup
    chage -E 0 backup
fi

log "CONGELAMENTO CONCLUÍDO. Verifique manualmente outros agendadores (systemd timers)."
