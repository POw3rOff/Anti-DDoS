#!/bin/bash
#
# isolamento_credenciais.sh
#
# Descrição: Audita e corrige permissões de arquivos de credenciais usados em backups.
# Busca por arquivos comuns (.env, .pgpass, .my.cnf, keys) e aplica chmod 600.
#
# Uso: ./isolamento_credenciais.sh <diretorio_configs> [usuario_dono]
#
# Exemplo: ./isolamento_credenciais.sh /etc/backup/configs backupuser
#

SEARCH_DIR="$1"
OWNER="$2"

if [[ -z "$SEARCH_DIR" ]]; then
    echo "Uso: $0 <diretorio_configs> [usuario_dono]"
    exit 1
fi

if [[ ! -d "$SEARCH_DIR" ]]; then
    echo "Erro: Diretório $SEARCH_DIR não encontrado."
    exit 1
fi

echo "[*] Iniciando auditoria de credenciais em: $SEARCH_DIR"

# Lista de padrões de arquivos sensíveis
PATTERNS=("*.env" "*.pgpass" "*.my.cnf" "*.key" "*.password" "id_rsa" "credentials")

for pattern in "${PATTERNS[@]}"; do
    find "$SEARCH_DIR" -maxdepth 2 -name "$pattern" | while read -r file; do
        echo "[*] Processando: $file"

        # Alterar dono se especificado
        if [[ -n "$OWNER" ]]; then
            echo "    -> Ajustando dono para $OWNER"
            chown "$OWNER" "$file"
        fi

        # Verificar e ajustar permissões
        CURRENT_PERM=$(stat -c "%a" "$file")
        if [[ "$CURRENT_PERM" != "600" && "$CURRENT_PERM" != "400" ]]; then
            echo "    -> Permissões inseguras ($CURRENT_PERM). Alterando para 600."
            chmod 600 "$file"
        else
            echo "    -> Permissões OK ($CURRENT_PERM)."
        fi
    done
done

echo "[+] Isolamento de credenciais concluído."
