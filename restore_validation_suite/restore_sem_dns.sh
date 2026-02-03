#!/bin/bash
# restore_sem_dns.sh
#
# Descrição: Executa restore utilizando endereços IP diretos, contornando falhas de DNS.
#
# Uso: ./restore_sem_dns.sh <ip_servidor_backup> <caminho_remoto>

BACKUP_SERVER_IP="$1"
REMOTE_PATH="$2"
DESTINATION="./restore_nodns"

if [[ -z "$BACKUP_SERVER_IP" || -z "$REMOTE_PATH" ]]; then
    echo "[ERRO] Uso: $0 <ip_servidor> <caminho_remoto>"
    echo "Exemplo: $0 192.168.1.50 /backups/data.tar.gz"
    exit 1
fi

# Validação simples de IP (regex simplificado)
if [[ ! "$BACKUP_SERVER_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "[ERRO] Formato de IP inválido: $BACKUP_SERVER_IP"
    echo "Este script requer um IP direto para evitar dependência de DNS."
    exit 1
fi

echo "[INFO] Tentando conexão direta com $BACKUP_SERVER_IP (Sem DNS)..."
mkdir -p "$DESTINATION"

# Tenta transferência real via SCP (assume chaves SSH configuradas ou interatividade)
# Nota: Em ambiente sem DNS, SSH pode demorar no reverse lookup se não configurado "UseDNS no" no servidor,
# mas funcionará.

scp -o ConnectTimeout=10 "user@$BACKUP_SERVER_IP:$REMOTE_PATH" "$DESTINATION/"

if [[ $? -eq 0 ]]; then
    echo "[SUCESSO] Transferência concluída."
    echo "[INFO] Arquivo salvo em: $DESTINATION"
else
    echo "[ERRO] Falha na transferência via IP. Verifique conectividade, credenciais e se o serviço SSH está acessível no IP informado."
    exit 1
fi
