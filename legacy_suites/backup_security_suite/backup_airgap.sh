#!/bin/bash
#
# backup_airgap.sh
#
# Descrição: Implementa um mecanismo de "Air Gap" lógico.
# Conecta a interface de rede ou monta o disco APENAS durante a execução do comando de backup,
# desconectando imediatamente após o término, independente de sucesso ou falha.
#
# Uso: ./backup_airgap.sh <tipo: network|disk> <identificador> <comando_backup>
#
# Exemplo Disk: ./backup_airgap.sh disk /dev/sdb1 "/usr/local/bin/meu_script_backup.sh"
# Exemplo Network: ./backup_airgap.sh network eth1 "/usr/local/bin/rsync_backup.sh"
#

TYPE="$1"
ID="$2"
CMD="$3"

if [[ -z "$TYPE" || -z "$ID" || -z "$CMD" ]]; then
    echo "Uso: $0 <tipo: network|disk> <identificador> <comando_backup>"
    exit 1
fi

MOUNT_POINT="/mnt/secure_backup"

cleanup() {
    echo "[*] Executando limpeza (Isolamento Air Gap)..."
    if [[ "$TYPE" == "disk" ]]; then
        if mountpoint -q "$MOUNT_POINT"; then
            echo "    -> Desmontando disco..."
            umount "$MOUNT_POINT"
        fi
    elif [[ "$TYPE" == "network" ]]; then
        echo "    -> Derrubando interface de rede $ID..."
        ip link set "$ID" down
    fi
    echo "[+] Ambiente isolado novamente."
}

# Garante que cleanup rode ao sair, erro ou interrupção
trap cleanup EXIT

echo "[*] Iniciando procedimento de Backup com Air Gap"
echo "    -> Tipo: $TYPE"
echo "    -> ID: $ID"

# 1. Conectar/Montar
if [[ "$TYPE" == "disk" ]]; then
    mkdir -p "$MOUNT_POINT"
    echo "    -> Montando disco $ID em $MOUNT_POINT..."
    mount "$ID" "$MOUNT_POINT"
    if [[ $? -ne 0 ]]; then
        echo "[-] Falha ao montar disco."
        exit 1
    fi
elif [[ "$TYPE" == "network" ]]; then
    echo "    -> Levantando interface de rede $ID..."
    ip link set "$ID" up
    # Aguarda obter IP (dhcp) ou link up
    sleep 5
    if [[ $? -ne 0 ]]; then
        echo "[-] Falha ao levantar interface."
        exit 1
    fi
else
    echo "[-] Tipo desconhecido: $TYPE"
    exit 1
fi

# 2. Executar Backup
echo "[*] Executando comando de backup..."
eval "$CMD"
BACKUP_STATUS=$?

if [[ $BACKUP_STATUS -eq 0 ]]; then
    echo "[+] Comando de backup finalizado com sucesso."
else
    echo "[-] Comando de backup falhou com código $BACKUP_STATUS."
fi

# Cleanup é chamado automaticamente pelo trap
