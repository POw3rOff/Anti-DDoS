#!/bin/bash
#
# snapshot_em_incidente.sh
#
# Tenta identificar o sistema de arquivos (LVM, ZFS, Btrfs) e criar um snapshot
# imediato para preservar o estado do disco durante um incidente.
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -u

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
SNAPSHOT_NAME="INCIDENT_${TIMESTAMP}"
LOG_FILE="/var/log/incident_snapshot.log"

# Cores
GREEN="\033[0;32m"
RED="\033[0;31m"
NC="\033[0m"

log() {
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

log "Iniciando snapshot de emergência: ${SNAPSHOT_NAME}"

# Detectar Root FS type
ROOT_FS_TYPE=$(findmnt -n -o FSTYPE /)
ROOT_SOURCE=$(findmnt -n -o SOURCE /)

log "Filesystem raiz detectado: ${ROOT_FS_TYPE} em ${ROOT_SOURCE}"

case "$ROOT_FS_TYPE" in
    ext4|xfs)
        # Verifica se está sobre LVM
        if lvs "$ROOT_SOURCE" >/dev/null 2>&1; then
            log "LVM detectado. Tentando criar snapshot LVM..."
            VG_NAME=$(lvs --noheadings -o vg_name "$ROOT_SOURCE" | tr -d " ")
            LV_NAME=$(lvs --noheadings -o lv_name "$ROOT_SOURCE" | tr -d " ")

            # Tamanho do snapshot: Tenta usar 10% do espaço livre do VG ou 1GB fixo se falhar detecção
            # Simplificação: Usando 1G para garantir criação (ajuste conforme necessidade)
            if lvcreate -L 1G -s -n "${SNAPSHOT_NAME}" "/dev/${VG_NAME}/${LV_NAME}"; then
                log "${GREEN}[SUCESSO] Snapshot LVM criado: /dev/${VG_NAME}/${SNAPSHOT_NAME}${NC}"
            else
                log "${RED}[ERRO] Falha ao criar snapshot LVM (verifique espaço livre no VG).${NC}"
                exit 1
            fi
        else
            log "${RED}[AVISO] Filesystem é ext4/xfs mas NÃO parece ser LVM. Snapshot nativo não suportado.${NC}"
            exit 1
        fi
        ;;

    btrfs)
        log "Btrfs detectado. Criando snapshot..."
        # Assume que / é o subvolume, snapshot será criado em /.snapshots se existir, ou na raiz
        DEST_SNAP="/.snapshots/${SNAPSHOT_NAME}"
        if [ ! -d "/.snapshots" ]; then
            DEST_SNAP="/${SNAPSHOT_NAME}"
        fi

        if btrfs subvolume snapshot / "$DEST_SNAP"; then
            log "${GREEN}[SUCESSO] Snapshot Btrfs criado em $DEST_SNAP${NC}"
        else
            log "${RED}[ERRO] Falha ao criar snapshot Btrfs.${NC}"
            exit 1
        fi
        ;;

    zfs)
        log "ZFS detectado. Criando snapshot..."
        # Obtém o nome do dataset raiz (remove prefixo montagem se necessario, mas source geralmente é o dataset)
        DATASET="$ROOT_SOURCE"
        if zfs snapshot "${DATASET}@${SNAPSHOT_NAME}"; then
            log "${GREEN}[SUCESSO] Snapshot ZFS criado: ${DATASET}@${SNAPSHOT_NAME}${NC}"
        else
            log "${RED}[ERRO] Falha ao criar snapshot ZFS.${NC}"
            exit 1
        fi
        ;;

    *)
        log "${RED}[ERRO] Sistema de arquivos ${ROOT_FS_TYPE} não suportado para snapshot automático neste script.${NC}"
        exit 1
        ;;
esac

log "Operação finalizada."
