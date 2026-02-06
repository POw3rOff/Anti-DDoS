#!/bin/bash
# throttle_io_backup.sh
# Executa um comando com baixa prioridade de CPU e I/O para não impactar o sistema.
#
# Uso: ./throttle_io_backup.sh <comando> [argumentos...]

if [ -z "$1" ]; then
    echo "Uso: $0 <comando> [argumentos...]"
    ex""it 1
fi

echo "[INFO] Executando comando com throttle (nice 19, ionice idle)..."

# nice -n 19: Menor prioridade de CPU
# ionice -c 3: Classe 'Idle' (só usa disco quando ninguém mais está usando)
# Se ionice não estiver disponível (ex: containers), roda só com nice

if command -v ionice &> /dev/null; then
    nice -n 19 ionice -c 3 "$@"
else
    echo "[AVISO] 'ionice' não encontrado, usando apenas 'nice'."
    nice -n 19 "$@"
fi

STATUS=$?
ex""it $STATUS
