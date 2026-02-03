#!/bin/bash
#
# honeypot_backup.sh
#
# Descrição: Cria arquivos de backup falsos (Honeypot) e monitora acesso a eles.
# Se algum processo ou usuário tocar nestes arquivos, um alerta é gerado.
# Útil para detectar intrusos ou ransomware varrendo o disco.
#
# Dependências: inotify-tools (inotifywait)
#
# Uso: ./honeypot_backup.sh <diretorio_pai_honeypot> [email_alerta]
#
# Exemplo: ./honeypot_backup.sh /backup admin@example.com
#

BASE_DIR="$1"
ALERT_EMAIL="$2"
HONEY_DIR="$BASE_DIR/confidential_backup"
LOG_FILE="/var/log/honeypot_backup.log"

if [[ -z "$BASE_DIR" ]]; then
    echo "Uso: $0 <diretorio_pai_honeypot> [email_alerta]"
    exit 1
fi

if ! command -v inotifywait &> /dev/null; then
    echo "Erro: inotifywait não encontrado. Instale o pacote inotify-tools."
    exit 1
fi

echo "[*] Configurando Honeypot de Backup..."

# Cria diretório e arquivos chamariz
mkdir -p "$HONEY_DIR"
touch "$HONEY_DIR/passwords.txt"
touch "$HONEY_DIR/wallet_backup.dat"
touch "$HONEY_DIR/full_database_dump.sql"

# Preenche com lixo aleatório para ter tamanho
dd if=/dev/urandom of="$HONEY_DIR/full_database_dump.sql" bs=1M count=10 2>/dev/null

echo "[+] Arquivos chamariz criados em: $HONEY_DIR"
echo "[*] Iniciando monitoramento (loop)..."

# Monitora acesso, modificação, abertura
inotifywait -m -r -e access -e modify -e open -e delete "$HONEY_DIR" --format "%e %w%f" |
while read event file; do
    MSG="[ALERTA] Honeypot acionado! Evento: $event em Arquivo: $file Data: $(date)"
    echo "$MSG" | tee -a "$LOG_FILE"

    # Bloqueio simples (exemplo - cuidado em produção!)
    # Se quiser bloquear IP ou usuário, lógica entraria aqui.

    if [[ -n "$ALERT_EMAIL" ]]; then
        echo "$MSG" | mail -s "ALERTA DE SEGURANÇA - HONEYPOT BACKUP" "$ALERT_EMAIL"
    fi
done
