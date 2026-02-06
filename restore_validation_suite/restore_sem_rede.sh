#!/bin/bash
# restore_sem_rede.sh
#
# Descrição: Simula e executa restore a partir de mídias locais ou caches
# quando a rede não está disponível.
#
# Uso: ./restore_sem_rede.sh <ponto_montagem_local>

LOCAL_MOUNT="$1"
DESTINATION="/tmp/restore_offline"

# Simula verificação de rede
echo "[INFO] Verificando conectividade..."
ping -c 1 8.8.8.8 &> /dev/null

if [[ $? -eq 0 ]]; then
    echo "[INFO] Rede detectada, mas forçando modo OFFLINE para este teste."
else
    echo "[ALERTA] Rede indisponível. Iniciando protocolo offline."
fi

if [[ -z "$LOCAL_MOUNT" ]]; then
    echo "[ERRO] Especifique o ponto de montagem do backup local (USB/Disco)."
    exit 1
fi

if [[ ! -d "$LOCAL_MOUNT" ]]; then
    echo "[ERRO] Ponto de montagem não encontrado: $LOCAL_MOUNT"
    exit 1
fi

echo "[INFO] Buscando backups em $LOCAL_MOUNT..."
LATEST_BACKUP=$(ls -t "$LOCAL_MOUNT"/*.tar.gz 2>/dev/null | head -n 1)

if [[ -n "$LATEST_BACKUP" ]]; then
    echo "[INFO] Restore local iniciado com: $LATEST_BACKUP"
    mkdir -p "$DESTINATION"
    tar -xzf "$LATEST_BACKUP" -C "$DESTINATION"
    echo "[SUCESSO] Restore offline concluído em $DESTINATION"
else
    echo "[ERRO] Nenhum backup encontrado na mídia local."
    exit 1
fi
