#!/bin/bash
# politica_retencao_gfs.sh
# Implementa política de retenção Grandfather-Father-Son.
# Mantém: 7 dias, 4 semanas, 12 meses.
#
# Uso: ./politica_retencao_gfs.sh <diretorio_backups>

DIR_BACKUP="$1"

if [ -z "$DIR_BACKUP" ]; then
    echo "Uso: $0 <diretorio_backups>"
    ex""it 1
fi

echo "[INFO] Aplicando política GFS em $DIR_BACKUP"

# Encontra arquivos de backup (assume formato *YYYY-MM-DD*)
# Atenção: Este script é uma implementação simplificada que limpa backups antigos.

# 1. Manter últimos 7 dias (Daily)
# Nada a fazer, apenas não apagar.

# 2. Identificar arquivos com mais de 7 dias
find "$DIR_BACKUP" -maxdepth 1 -type f -mtime +7 | while read arquivo; do
    NOME=$(basename "$arquivo")
    # Tenta extrair data do nome do arquivo (ex: backup_2023-10-27...)
    DATA_ARQUIVO=$(echo "$NOME" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')

    if [ -z "$DATA_ARQUIVO" ]; then
        echo "[SKIP] Formato de data não encontrado em $NOME"
        continue
    fi

    DIA_SEMANA=$(date -d "$DATA_ARQUIVO" +%u) # 1=Segunda, 7=Domingo
    DIA_MES=$(date -d "$DATA_ARQUIVO" +%d)

    # Regra Weekly: Manter se for Segunda-feira (1) e tiver menos de 30 dias (4 semanas aprox)
    # Regra Monthly: Manter se for dia 01 e tiver menos de 365 dias

    IDADE_DIAS=$(( ( $(date +%s) - $(date -d "$DATA_ARQUIVO" +%s) ) / 86400 ))

    KEEPER=0

    # É um backup semanal? (Segunda-feira e < 30 dias)
    if [ "$DIA_SEMANA" -eq 1 ] && [ "$IDADE_DIAS" -lt 35 ]; then
        KEEPER=1
        echo "[KEEP-WEEKLY] Mantendo $NOME (Semanal)"
    fi

    # É um backup mensal? (Dia 01 e < 365 dias)
    if [ "$DIA_MES" -eq 01 ] && [ "$IDADE_DIAS" -lt 370 ]; then
        KEEPER=1
        echo "[KEEP-MONTHLY] Mantendo $NOME (Mensal)"
    fi

    if [ $KEEPER -eq 0 ]; then
        echo "[DELETE] Removendo backup antigo/redundante: $NOME"
        rm -f "$arquivo"
    fi
done

echo "[INFO] Limpeza GFS concluída."
