#!/bin/bash
# verificacao_timestamps_logs.sh
# Verifica inconsistências cronológicas nos logs
# Autor: Jules (Assistant)

RED="\033[0;31m"
NC="\033[0m"

LOG_FILE="${1:-/var/log/syslog}"

if [ ! -f "$LOG_FILE" ]; then
    echo "Arquivo $LOG_FILE não encontrado."
    exit 1
fi

echo "[*] Verificando $LOG_FILE..."

# Script Python interno para processamento
python3 -c "
import sys
import re

try:
    from dateutil import parser
except ImportError:
    print('ERRO: python-dateutil não instalado.')
    sys.exit(0)

if len(sys.argv) < 2:
    sys.exit(1)

filename = sys.argv[1]
last_dt = None
issues = 0

try:
    with open(filename, 'r', errors='ignore') as f:
        ln = 0
        for line in f:
            ln += 1
            header = line[:30]
            try:
                dt = parser.parse(header, fuzzy=True)
                if last_dt and dt < last_dt:
                    if (last_dt - dt).total_seconds() > 1:
                        print('LINHA {}: Salto no tempo. Atual: {} | Anterior: {}'.format(ln, dt, last_dt))
                        issues += 1
                last_dt = dt
            except:
                pass

    if issues > 0:
        print('Total de inconsistências: {}'.format(issues))
        sys.exit(1)
    else:
        print('Nenhuma inconsistência encontrada.')
        sys.exit(0)

except Exception as e:
    print('Erro: {}'.format(e))
    sys.exit(1)
" "$LOG_FILE"
