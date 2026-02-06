#!/bin/bash
#
# killswitch_backup.sh
#
# AÇÃO DE EMERGÊNCIA: Isola imediatamente o armazenamento de backup.
# Use isto se houver suspeita de que o ataque está tentando destruir os backups.
#
# Funcionalidades:
# - Desmonta forçadamente pontos de montagem de backup.
# - Bloqueia tráfego de rede para servidores de backup (se IPs definidos).
# - Encerra conexões iSCSI/NFS.
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -u

LOG_FILE="/var/log/incident_killswitch.log"
# Defina IPs dos servidores de backup aqui se conhecido, ou deixe vazio
BACKUP_SERVERS="" # Ex: "192.168.1.100 10.0.0.50"

log() {
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

log "!!! ATIVANDO KILLSWITCH DE BACKUP !!!"

# 1. Matar Processos de I/O em discos de backup (Tentativa)
log "Tentando identificar processos em /mnt/backup, /media/backup..."
fuser -k -m /mnt/backup 2>/dev/null
fuser -k -m /media/* 2>/dev/null

# 2. Desmontar Filesystems de Rede/Backup
log "Desmontando compartilhamentos NFS/CIFS e montagens com backup no nome..."
# Lista montagens, filtra por nfs/cifs ou path contendo backup
MOUNTS=$(findmnt -n -o TARGET | grep -E "(/mnt/|/media/|backup)")

for mnt in $MOUNTS; do
    log "Desmontando forçado: $mnt"
    umount -f -l "$mnt" || log "Falha ao desmontar $mnt"
done

# 3. Cortar Conexões de Rede (Se IPs definidos)
if [ -n "$BACKUP_SERVERS" ]; then
    log "Bloqueando tráfego para servidores de backup: $BACKUP_SERVERS"
    for ip in $BACKUP_SERVERS; do
        iptables -I OUTPUT -d "$ip" -j DROP
        iptables -I INPUT -s "$ip" -j DROP
        log "Bloqueado IP $ip"
    done
else
    log "Nenhum IP de servidor de backup definido no script. Pulando bloqueio de firewall específico."
    log "Recomendação: Isole a interface de rede se crítico."
fi

# 4. Parar iSCSI
log "Verificando sessões iSCSI..."
if command -v iscsiadm &>/dev/null; then
    iscsiadm -m session -u 2>/dev/null && log "Sessões iSCSI desconectadas."
fi

log "KILLSWITCH EXECUTADO. Verifique se os volumes foram desmontados."
