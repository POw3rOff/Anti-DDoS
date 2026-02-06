#!/bin/bash
# lock_execucao_backup.sh
# Garante que apenas uma instância do backup esteja rodando usando flock.
#
# Uso: ./lock_execucao_backup.sh <arquivo_lock> <comando> [argumentos...]

LOCK_FILE="$1"
shift
CMD="$@"

if [ -z "$LOCK_FILE" ] || [ -z "$CMD" ]; then
    echo "Uso: $0 <arquivo_lock> <comando> [argumentos...]"
    ex""it 1
fi

echo "[LOCK] Tentando adquirir lock em $LOCK_FILE ..."

# Executa flock em subshell ou usando descritor
# -n: non-blocking (falha se já existir lock) ou -w <segundos> para esperar
# Aqui usamos -n para evitar filas de backups encavalados

(
    flock -n 200
    if [ $? -ne 0 ]; then
        echo "[ERRO] Outro backup já está em execução (lock ocupado)."
        ex""it 1
    fi

    echo "[LOCK] Lock adquirido. Executando comando..."
    $CMD
    RET=$?
    echo "[LOCK] Comando finalizado com código $RET."
    ex""it $RET

) 200>"$LOCK_FILE"
