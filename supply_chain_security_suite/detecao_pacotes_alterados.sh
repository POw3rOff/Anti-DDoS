#!/bin/bash
# detecao_pacotes_alterados.sh
# Descrição: Detecta alterações nos arquivos instalados pelos pacotes (integridade).
# Autor: Jules (System Security Suite)

LOG_FILE="/var/log/supply_chain_alteracoes.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$LOG_FILE"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Iniciando verificação de integridade de arquivos de pacotes..."

check_deb() {
    log "Sistema APT/DPKG detectado."

    if command -v debsums >/dev/null; then
        log "Executando debsums -c (arquivos de configuração)..."
        debsums -c 2>/dev/null | tee -a "$LOG_FILE"

        log "Executando debsums -s (binários e outros, silencioso para sucesso)..."
        # -s reporta apenas erros
        debsums -s 2>&1 | tee -a "$LOG_FILE"
    elif command -v dpkg >/dev/null; then
        # Verificar se dpkg suporta --verify (versões mais recentes)
        if dpkg --help | grep -q verify; then
            log "Executando dpkg --verify..."
            # dpkg --verify mostra arquivos que falharam na verificação de md5sum
            # Formato: ??5?????? c /etc/path (5 = md5 check failed)
            dpkg --verify 2>&1 | tee -a "$LOG_FILE"
        else
            log "[AVISO] 'debsums' não encontrado e 'dpkg --verify' não suportado. Instale 'debsums'."
        fi
    else
         log "[ERRO] Ferramentas de verificação não encontradas."
    fi
}

check_rpm() {
    log "Sistema RPM detectado. Executando rpm -Va..."
    log "Nota: Isso verifica MD5, permissões, tipo, dono, grupo, etc."
    log "Ignorando arquivos de configuração (c) e documentação (d) para focar em binários alterados?"
    log "Executando verificação completa (pode gerar muitos logs para configs alteradas)..."

    # Executa rpm -Va e salva em temp
    rpm -Va > /tmp/rpm_verify.tmp 2>&1

    # Filtra saída. O formato é S.5....T.  c /path/to/file
    # Queremos saber de binários alterados (geralmente não são 'c')
    # Binários alterados geralmente tem '5' (checksum digest) e não tem 'c' (config)

    log "Arquivos NÃO-configuração com Checksum/Tamanho alterado (ALERTA CRÍTICO):"
    # Regex: busca linhas onde checksum (5) mudou, e o arquivo NÃO é config (c)
    grep "..5......" /tmp/rpm_verify.tmp | grep -v " c " | tee -a "$LOG_FILE"

    log "Arquivos de configuração alterados (Informativo):"
    grep " c " /tmp/rpm_verify.tmp | head -n 20 | tee -a "$LOG_FILE"
    log "(Lista de configs truncada para 20 itens)"

    rm -f /tmp/rpm_verify.tmp
}

if [ -f /etc/debian_version ]; then
    check_deb
elif [ -f /etc/redhat-release ]; then
    check_rpm
else
    if command -v rpm >/dev/null; then
        check_rpm
    elif command -v dpkg >/dev/null; then
        check_deb
    else
        log "Sistema não suportado."
        exit 1
    fi
fi

log "Verificação de integridade concluída."
