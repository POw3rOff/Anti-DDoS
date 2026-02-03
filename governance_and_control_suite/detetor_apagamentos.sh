#!/bin/bash
# Script: detetor_apagamentos.sh
# Descrição: Deteta eventos de apagamento (delete, unlink, rmdir) em diretórios de backup.
# Autor: Jules (Assistant)

BACKUP_DIR="/var/backups"

echo "=== Detetor de Apagamentos de Backup ==="
echo "Monitorando: $BACKUP_DIR"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Diretório não encontrado: $BACKUP_DIR"
    exit 1
fi

# Método 1: Auditd (Recomendado para Governança)
if command -v ausearch >/dev/null; then
    echo "[INFO] Verificando logs de auditoria (ausearch)..."
    # Procura syscalls de remoção.

    # Verifica se existem regras para o diretório
    if auditctl -l | grep -q "$BACKUP_DIR"; then
        echo "[INFO] Regras de auditoria ativas encontradas."
        ausearch -f "$BACKUP_DIR" -i | grep -E "type=PATH|type=SYSCALL" | grep -E "unlink|rmdir|rename" | tail -n 20
    else
        echo "[AVISO] Nenhuma regra de auditoria ativa para $BACKUP_DIR."
        echo "Sugestão: Execute 'auditctl -w $BACKUP_DIR -p wa -k backup_changes' para monitorar."
    fi
else
    echo "[INFO] auditd não encontrado. Usando verificação por inotify (tempo real) se disponível."
fi

# Método 2: Inotify (Monitoramento em tempo real)
if command -v inotifywait >/dev/null; then
    echo ""
    echo "[INFO] Iniciando monitoramento em tempo real com inotifywait por 10 segundos..."
    echo "(Pressione Ctrl+C para parar se executado manualmente)"
    timeout 10s inotifywait -m -r -e delete -e move -e attrib "$BACKUP_DIR"
else
    echo "[INFO] inotifywait não instalado. Instale 'inotify-tools' para monitoramento em tempo real."
fi

echo ""
echo "=== Verificação Concluída ==="
