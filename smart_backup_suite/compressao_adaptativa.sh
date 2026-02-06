#!/bin/bash
# compressao_adaptativa.sh
# Escolhe o algoritmo de compressão baseado na carga do sistema.
#
# Uso: ./compressao_adaptativa.sh <arquivo_ou_diretorio>

ALVO="$1"

if [ -z "$ALVO" ]; then
    echo "Uso: $0 <arquivo_ou_diretorio>"
    ex""it 1
fi

# Obtém Load Average de 1 minuto
LOAD=$(awk '{print $1}' /proc/loadavg)
CPUS=$(nproc)

# Limite simples: se load > num_cpus, o sistema está carregado
LIMITE=$(echo "$CPUS * 0.8" | bc) # 80% da capacidade
EH_ALTO=$(echo "$LOAD > $LIMITE" | bc -l)

NOME_BASE=$(basename "$ALVO")
DATA=$(date +%Y%m%d_%H%M%S)

if [ "$EH_ALTO" -eq 1 ]; then
    echo "[INFO] Carga alta ($LOAD / $CPUS CPUs). Usando compressão rápida (gzip fast)."
    # gzip -1 é rápido
    tar -cvf - "$ALVO" | gzip -1 > "${NOME_BASE}_${DATA}.tar.gz"
else
    echo "[INFO] Carga baixa ($LOAD / $CPUS CPUs). Usando alta compressão (xz)."
    # xz é lento mas comprime muito bem. -T0 usa todos os cores disponíveis para acelerar.
    tar -cvf - "$ALVO" | xz -T0 > "${NOME_BASE}_${DATA}.tar.xz"
fi

if [ $? -eq 0 ]; then
    echo "[INFO] Compressão concluída."
else
    echo "[ERRO] Falha na compressão."
    ex""it 1
fi
