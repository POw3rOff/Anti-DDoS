#!/bin/bash
# verificacao_assinaturas.sh
# Descrição: Verificação de assinaturas GPG de pacotes e repositórios para garantir autenticidade.
# Autor: Jules (System Security Suite)

LOG_FILE="/var/log/supply_chain_assinaturas.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$LOG_FILE"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Iniciando verificação de assinaturas..."

verify_apt() {
    log "Verificando chaves e assinaturas APT..."

    # Listar chaves confiáveis
    KEY_COUNT=$(apt-key list 2>/dev/null | grep "pub" | wc -l)
    log "Chaves GPG confiáveis encontradas: $KEY_COUNT"

    # Verificar se existem repositórios sem assinatura ou inseguros
    # grep em sources.list
    if grep -r "trusted=yes" /etc/apt/sources.list /etc/apt/sources.list.d/ >/dev/null; then
        log "[AVISO] Encontrados repositórios marcados explicitamente como confiáveis (trusted=yes). Verifique se é intencional."
        grep -r "trusted=yes" /etc/apt/sources.list /etc/apt/sources.list.d/ | tee -a "$LOG_FILE"
    fi

    # Tentar verificar pacotes instalados sem assinatura (difícil com dpkg diretamente, mas debsigs pode ajudar se instalado)
    # Alternativa: verificar integridade do cache
    # apt-get update checa assinaturas.
    # Vamos verificar políticas
    if command -v apt-config >/dev/null; then
        SECURE=$(apt-config dump | grep "Acquire::AllowInsecureRepositories")
        if [[ "$SECURE" == *"true"* ]]; then
            log "[PERIGO] Configuração Acquire::AllowInsecureRepositories está ativa!"
        else
            log "[OK] Repositórios inseguros não são permitidos por padrão."
        fi
    fi
}

verify_rpm() {
    log "Verificando assinaturas RPM..."

    # Listar chaves importadas
    KEYS=$(rpm -qa gpg-pubkey*)
    if [ -n "$KEYS" ]; then
        log "Chaves GPG importadas no RPM DB:"
        echo "$KEYS" | tee -a "$LOG_FILE"
    else
        log "[ALERTA] Nenhuma chave GPG encontrada no banco de dados RPM!"
    fi

    # Verificar todos os pacotes (pode demorar)
    log "Verificando assinaturas de todos os pacotes instalados (rpm -Ka)... Isso pode demorar."
    # checksig agora é -K
    # Filtramos apenas os que falham ou não estão assinados
    rpm -Ka > /tmp/rpm_verify_sig.tmp 2>&1

    UNSIGNED=$(grep -i "NOT SIGNED" /tmp/rpm_verify_sig.tmp)
    BADSIG=$(grep -i "BAD" /tmp/rpm_verify_sig.tmp)
    MISSINGKEY=$(grep -i "MISSING KEY" /tmp/rpm_verify_sig.tmp)

    if [ -n "$UNSIGNED" ]; then
        COUNT=$(echo "$UNSIGNED" | wc -l)
        log "[AVISO] $COUNT pacotes não assinados encontrados."
        # log detalhado opcional
    fi

    if [ -n "$BADSIG" ]; then
        log "[CRÍTICO] Pacotes com assinatura INVÁLIDA encontrados!"
        echo "$BADSIG" | tee -a "$LOG_FILE"
    fi

    if [ -n "$MISSINGKEY" ]; then
        log "[AVISO] Pacotes assinados com chave desconhecida (chave pública faltando):"
        echo "$MISSINGKEY" | head -n 10 | tee -a "$LOG_FILE"
        log "(Lista truncada para 10 itens)"
    fi

    rm -f /tmp/rpm_verify_sig.tmp
    log "Verificação RPM concluída."
}

if [ -f /etc/debian_version ]; then
    verify_apt
elif [ -f /etc/redhat-release ]; then
    verify_rpm
else
    # Fallback
    if command -v rpm >/dev/null; then
        verify_rpm
    elif command -v apt-key >/dev/null; then
        verify_apt
    else
        log "Sistema não suportado para verificação de assinaturas padrão."
        exit 1
    fi
fi

log "Verificação de assinaturas finalizada."
