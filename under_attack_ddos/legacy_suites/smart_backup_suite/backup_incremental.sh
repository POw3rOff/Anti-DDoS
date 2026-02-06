#!/bin/bash
# backup_incremental.sh
# Realiza backup incremental usando rsync e hard links para economizar espaço.
#
# Uso: ./backup_incremental.sh <origem> <destino_base>
# Exemplo: ./backup_incremental.sh /var/www /backups/www

ORIGEM="$1"
DESTINO_BASE="$2"
DATA=$(date +%Y-%m-%d_%H-%M-%S)
DESTINO_NOVO="${DESTINO_BASE}/backup_${DATA}"
ULTIMO_LINK="${DESTINO_BASE}/current"

if [ -z "$ORIGEM" ] || [ -z "$DESTINO_BASE" ]; then
    echo "Erro: Origem e destino são obrigatórios."
    echo "Uso: $0 <origem> <destino_base>"
    ex""it 1
fi

mkdir -p "$DESTINO_BASE"

echo "[INFO] Iniciando backup incremental de $ORIGEM para $DESTINO_NOVO"

RSYNC_OPTS="-av --delete"

# Se existe um backup anterior (link simbólico 'current'), usa como referência
if [ -L "$ULTIMO_LINK" ]; then
    echo "[INFO] Usando link-dest: $(readlink -f $ULTIMO_LINK)"
    RSYNC_OPTS="$RSYNC_OPTS --link-dest=$(readlink -f $ULTIMO_LINK)"
fi

# Executa o rsync
rsync $RSYNC_OPTS "$ORIGEM" "$DESTINO_NOVO"

if [ $? -eq 0 ]; then
    echo "[INFO] Backup concluído com sucesso."
    # Atualiza o link 'current' para apontar para o novo backup
    rm -f "$ULTIMO_LINK"
    ln -s "$DESTINO_NOVO" "$ULTIMO_LINK"
    echo "[INFO] Link 'current' atualizado."
else
    echo "[ERRO] Falha no rsync."
    ex""it 1
fi
