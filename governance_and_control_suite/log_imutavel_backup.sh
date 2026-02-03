#!/bin/bash
# Script: log_imutavel_backup.sh
# Descrição: Configura logs de backup como imutáveis (append-only) para evitar manipulação.
# Autor: Jules (Assistant)

LOG_DIR="/var/log/backups"
FILE_PATTERN="*.log"

echo "=== Configuração de Logs Imutáveis ==="

if [ ! -d "$LOG_DIR" ]; then
    echo "Criando diretório de log: $LOG_DIR"
    mkdir -p "$LOG_DIR"
fi

# Verificar comando chattr
if ! command -v chattr >/dev/null; then
    echo "[ERRO] Comando chattr não encontrado. Instale o pacote e2fsprogs."
    exit 1
fi

echo "Aplicando atributo append-only (+a) aos logs em $LOG_DIR..."

# Encontrar arquivos de log e aplicar atributo
find "$LOG_DIR" -name "$FILE_PATTERN" -type f | while read -r logfile; do
    if chattr +a "$logfile"; then
        echo "[SUCESSO] Atributo +a aplicado: $logfile"
    else
        echo "[ERRO] Falha ao aplicar atributo em: $logfile"
    fi
done

echo ""
echo "Verificação de atributos:"
lsattr "$LOG_DIR"/*.log 2>/dev/null || echo "Nenhum log encontrado."

echo "=== Concluído ==="
