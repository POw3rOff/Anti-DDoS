#!/bin/bash
# restore_sem_root.sh
#
# Descrição: Valida e executa restore em espaço de usuário (user-space),
# útil quando não se tem privilégios de root ou para restaurar arquivos pessoais.
#
# Uso: ./restore_sem_root.sh <arquivo_backup>

BACKUP_FILE="$1"
USER_RESTORE_DIR="$HOME/restore_user_space"

CURRENT_UID=$(id -u)

if [[ "$CURRENT_UID" -eq 0 ]]; then
    echo "[AVISO] Você está rodando como ROOT. Este script é destinado a testes como usuário comum."
    echo "Continuando mesmo assim..."
else
    echo "[INFO] Rodando como usuário (UID: $CURRENT_UID). Modo seguro ativado."
fi

if [[ -z "$BACKUP_FILE" ]]; then
    echo "[ERRO] Arquivo de backup necessário."
    exit 1
fi

echo "[INFO] Restaurando para diretório do usuário: $USER_RESTORE_DIR"
mkdir -p "$USER_RESTORE_DIR"

# Tenta restaurar. Se houver arquivos de sistema ou permissões especiais, o tar vai avisar/falhar parcialmente.
tar -xzf "$BACKUP_FILE" -C "$USER_RESTORE_DIR" --warning=no-timestamp

if [[ $? -eq 0 ]]; then
    echo "[SUCESSO] Restore de usuário concluído."
else
    echo "[AVISO] Restore concluído com erros (possivelmente permissões). Verifique os arquivos."
    # Não falhamos completamente pois é esperado ter erros de permissão se o backup veio de root
fi
