#!/bin/bash
# janela_backup_segura.sh
# Verifica se o horário atual está dentro da janela permitida para backups.
#
# Uso: ./janela_backup_segura.sh <hora_inicio> <hora_fim>
# Exemplo: ./janela_backup_segura.sh 0200 0600

INICIO="${1:-0200}" # Padrão 2 da manhã
FIM="${2:-0600}"    # Padrão 6 da manhã

AGORA=$(date +%H%M)

echo "[CHECK] Hora atual: $AGORA. Janela permitida: $INICIO - $FIM."

# Lógica simples para janela no mesmo dia (ex: 0200 a 0600)
if [ "$INICIO" -le "$FIM" ]; then
    if [ "$AGORA" -ge "$INICIO" ] && [ "$AGORA" -le "$FIM" ]; then
        echo "[OK] Dentro da janela de backup."
        ex""it 0
    else
        echo "[BLOQUEIO] Fora da janela de backup."
        ex""it 1
    fi
else
    # Lógica para janela que cruza meia-noite (ex: 2200 a 0400)
    if [ "$AGORA" -ge "$INICIO" ] || [ "$AGORA" -le "$FIM" ]; then
        echo "[OK] Dentro da janela de backup (cruzou meia-noite)."
        ex""it 0
    else
        echo "[BLOQUEIO] Fora da janela de backup."
        ex""it 1
    fi
fi
