#!/bin/bash
#
# rollback_assistido.sh
#
# Assistente interativo para reverter o sistema para um estado anterior.
# Suporta LVM, ZFS e Btrfs (detecção básica).
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -u

# Cores
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

echo -e "${BLUE}=== ASSISTENTE DE ROLLBACK DE EMERGÊNCIA ===${NC}"
echo "AVISO: Esta operação pode destruir dados atuais. Use com cautela."
echo ""

# 1. Detecção de Mecanismos de Snapshot
OPTIONS=()
count=0

# Check LVM
if command -v lvs &>/dev/null; then
    echo -e "${YELLOW}Buscando snapshots LVM...${NC}"
    # Listagem simplificada
    LVM_SNAPS=$(lvs --select "lv_attr =~ ^s" -o vg_name,lv_name,lv_time --noheadings --separator " " 2>/dev/null)
    if [ -n "$LVM_SNAPS" ]; then
        for snap in $LVM_SNAPS; do
            OPTIONS+=("LVM: $snap")
        done
    fi
fi

# Check ZFS
if command -v zfs &>/dev/null; then
    echo -e "${YELLOW}Buscando snapshots ZFS...${NC}"
    ZFS_SNAPS=$(zfs list -t snapshot -o name,creation -H 2>/dev/null)
    if [ -n "$ZFS_SNAPS" ]; then
        for snap in $ZFS_SNAPS; do
            OPTIONS+=("ZFS: $snap")
        done
    fi
fi

# Check Btrfs
# Btrfs snapshots são subvolumes, difícil distinguir sem convenção.
# Assumindo /.snapshots ou convenção do snapper
if [ -d "/.snapshots" ]; then
    echo -e "${YELLOW}Buscando snapshots Btrfs (/.snapshots)...${NC}"
    for snap in /.snapshots/*; do
        if [ -d "$snap" ]; then
            OPTIONS+=("BTRFS: $snap")
        fi
    done
fi

# 2. Exibição e Seleção
if [ ${#OPTIONS[@]} -eq 0 ]; then
    echo -e "${RED}Nenhum snapshot de sistema de arquivos detectado automaticamente.${NC}"
    echo "Recomendação: Verifique backups em disco ou fita manualmente."
    exit 1
fi

echo "Snapshots disponíveis:"
i=0
for opt in "${OPTIONS[@]}"; do
    echo "[$i] $opt"
    ((i++))
done

echo ""
read -p "Selecione o número do snapshot para restaurar (ou CTRL+C para cancelar): " SELECTION

if ! [[ "$SELECTION" =~ ^[0-9]+$ ]] || [ "$SELECTION" -ge ${#OPTIONS[@]} ]; then
    echo -e "${RED}Seleção inválida.${NC}"
    exit 1
fi

SELECTED_OPT="${OPTIONS[$SELECTION]}"
echo -e "${YELLOW}Você selecionou: $SELECTED_OPT${NC}"
echo -e "${RED}ATENÇÃO: O ROLLBACK É DESTRUTIVO PARA DADOS APÓS O SNAPSHOT.${NC}"
read -p "Digite \"CONFIRMAR\" para prosseguir: " CONFIRM

if [ "$CONFIRM" != "CONFIRMAR" ]; then
    echo "Operação cancelada."
    exit 1
fi

# 3. Execução do Rollback
TYPE=$(echo "$SELECTED_OPT" | cut -d: -f1)
DETAILS=$(echo "$SELECTED_OPT" | cut -d: -f2- | sed "s/^ //")

case "$TYPE" in
    LVM)
        VG=$(echo "$DETAILS" | awk "{print \$1}")
        LV=$(echo "$DETAILS" | awk "{print \$2}")
        echo "Executando: lvconvert --merge /dev/$VG/$LV"
        lvconvert --merge "/dev/$VG/$LV" && echo -e "${GREEN}Rollback LVM agendado/concluído. Reboot pode ser necessário.${NC}"
        ;;
    ZFS)
        SNAP_NAME=$(echo "$DETAILS" | awk "{print \$1}")
        echo "Executando: zfs rollback -r $SNAP_NAME"
        zfs rollback -r "$SNAP_NAME" && echo -e "${GREEN}Rollback ZFS concluído.${NC}"
        ;;
    BTRFS)
        SNAP_PATH="$DETAILS"
        echo "Rollback Btrfs manual:"
        echo "1. Monte o subvolume raiz (ID 5)."
        echo "2. Mova o subvolume atual para backup."
        echo "3. Crie um snapshot do $SNAP_PATH para o local original."
        ;;
esac
