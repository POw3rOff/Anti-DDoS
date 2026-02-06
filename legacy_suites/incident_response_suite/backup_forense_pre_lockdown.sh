#!/bin/bash
#
# backup_forense_pre_lockdown.sh
#
# Este script realiza uma coleta forense rápida de dados voláteis e logs
# antes de iniciar um procedimento de lockdown/isolamento do servidor.
#
# Funcionalidades:
# - Coleta lista de processos, conexões de rede, arquivos abertos.
# - Copia logs do sistema (/var/log).
# - Gera hashes dos dados coletados.
# - Armazena em diretório seguro (ex: /root/forensics_YYYYMMDD).
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -e
set -o pipefail

DEST_DIR="/root/forensics_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${DEST_DIR}/forensic_log.txt"

# Cores para output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo -e "${YELLOW}[!] Iniciando Coleta Forense Pré-Lockdown...${NC}"

mkdir -p "$DEST_DIR"
touch "$LOG_FILE"

log() {
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# 1. Coleta de Dados Voláteis
log "Coletando dados voláteis..."

# Conexões de rede
log "Salvando conexões de rede (ss, netstat)..."
ss -tupna > "${DEST_DIR}/ss_output.txt" 2>/dev/null || log "Erro ao executar ss"
netstat -tupna > "${DEST_DIR}/netstat_output.txt" 2>/dev/null || log "Erro ao executar netstat"

# Processos
log "Salvando lista de processos (ps)..."
ps auxwf > "${DEST_DIR}/ps_output.txt" 2>/dev/null

# Arquivos abertos
log "Salvando arquivos abertos (lsof)..."
lsof > "${DEST_DIR}/lsof_output.txt" 2>/dev/null || log "Erro ao executar lsof (pode não estar instalado)"

# Memória (Resumo)
log "Salvando estado da memória (free, vmstat)..."
free -h > "${DEST_DIR}/free_output.txt"
vmstat 1 5 > "${DEST_DIR}/vmstat_output.txt"

# Uptime e usuários
log "Salvando uptime e usuários logados (w, who)..."
w > "${DEST_DIR}/w_output.txt"
who -a > "${DEST_DIR}/who_output.txt"

# 2. Coleta de Logs
log "Copiando logs do sistema (/var/log)..."
mkdir -p "${DEST_DIR}/logs"
# Copia preservando atributos, mas ignora erros de leitura (ex: arquivos socket)
cp -a /var/log/* "${DEST_DIR}/logs/" 2>/dev/null || true

# 3. Coleta de Arquivos de Configuração Críticos (Snapshot rápido)
log "Copiando configurações de rede e sistema..."
mkdir -p "${DEST_DIR}/etc_copy"
cp -a /etc/passwd /etc/shadow /etc/group /etc/sudoers /etc/hosts /etc/resolv.conf "${DEST_DIR}/etc_copy/"
cp -a /etc/ssh "${DEST_DIR}/etc_copy/" 2>/dev/null || true
cp -a /etc/network "${DEST_DIR}/etc_copy/" 2>/dev/null || true
cp -a /etc/netplan "${DEST_DIR}/etc_copy/" 2>/dev/null || true

# 4. Hashing dos dados coletados
log "Gerando hashes SHA256 dos dados coletados..."
find "$DEST_DIR" -type f -exec sha256sum {} + > "${DEST_DIR}/hashes.sha256"

# 5. Compactação (Opcional, para facilitar exfiltração segura)
log "Compactando evidências..."
tar -czf "${DEST_DIR}.tar.gz" -C "$(dirname "$DEST_DIR")" "$(basename "$DEST_DIR")"

echo -e "${GREEN}[OK] Coleta forense concluída em: ${DEST_DIR}${NC}"
echo -e "${YELLOW}NOTA: Mova o arquivo ${DEST_DIR}.tar.gz para um local externo seguro imediatamente.${NC}"
