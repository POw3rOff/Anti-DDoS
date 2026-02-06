#!/bin/bash
# Script: backup_vms.sh
# Descrição: Realiza backup de Máquinas Virtuais KVM/Libvirt.
# Método: Suspend (Save State) -> Copy Disk -> Resume. Garante consistência.

LOG_FILE="/var/log/backup_vms.log"
BACKUP_DIR="/var/backups/vms"
VM_NAME=""

# Cores
GREEN='\033[0;32m'
NC='\033[0m'

usage() {
    echo "Uso: $0 -n <nome_vm> [-d diretorio_backup]"
    echo "Exemplo: $0 -n vm_database -d /mnt/backup/vms"
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while getopts "n:d:" opt; do
    case $opt in
        n) VM_NAME="$OPTARG" ;;
        d) BACKUP_DIR="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$VM_NAME" ]; then
    usage
fi

if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
fi

if ! command -v virsh &> /dev/null; then
    log "ERRO: virsh (libvirt) não encontrado."
    exit 1
fi

# Verifica estado da VM
STATE=$(virsh domstate "$VM_NAME" 2>/dev/null)
if [ -z "$STATE" ]; then
    log "ERRO: VM '$VM_NAME' não encontrada."
    exit 1
fi

log "Iniciando backup da VM: $VM_NAME (Estado atual: $STATE)"
DATE=$(date '+%Y%m%d_%H%M%S')
BACKUP_PATH="$BACKUP_DIR/$VM_NAME-$DATE"
mkdir -p "$BACKUP_PATH"

# 1. Dump da configuração XML
log "Salvando configuração XML..."
virsh dumpxml "$VM_NAME" > "$BACKUP_PATH/$VM_NAME.xml"

# 2. Identificar discos
# (Assume disco principal no bloco XML, extração simples via grep/awk)
# Para script robusto, use xmlstarlet ou xpath, mas aqui faremos heurística
DISKS=$(virsh domblklist "$VM_NAME" --details | grep 'disk' | awk '{print $4}')

# 3. Processo de Backup
if [ "$STATE" == "running" ]; then
    log "VM está rodando. Iniciando suspensão para backup consistente..."

    # Opção A: Suspend (Pause)
    virsh suspend "$VM_NAME"
    if [ $? -ne 0 ]; then
        log "ERRO ao suspender VM. Abortando."
        exit 1
    fi
    log "VM Suspensa. Copiando discos..."

    for disk in $DISKS; do
        if [ -f "$disk" ]; then
            disk_name=$(basename "$disk")
            log "Copiando $disk..."
            cp "$disk" "$BACKUP_PATH/$disk_name"
        else
             log "AVISO: Disco não é um arquivo regular ou não encontrado: $disk"
        fi
    done

    log "Cópia finalizada. Retomando VM..."
    virsh resume "$VM_NAME"
else
    log "VM não está rodando ($STATE). Copiando discos diretamente..."
    for disk in $DISKS; do
        if [ -f "$disk" ]; then
            disk_name=$(basename "$disk")
            cp "$disk" "$BACKUP_PATH/$disk_name"
        fi
    done
fi

log "Compactando backup..."
tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "$VM_NAME-$DATE"
rm -rf "$BACKUP_PATH"

log "SUCESSO: Backup de $VM_NAME concluído em $BACKUP_PATH.tar.gz"
echo -e "${GREEN}Backup VM Finalizado.${NC}"
exit 0
