#!/bin/bash
# alerta_supply_chain.sh
# Descrição: Verifica logs dos scripts de supply chain e gera alertas unificados.
# Autor: Jules (System Security Suite)

LOG_DIR="/var/log"
ALERT_LOG="$LOG_DIR/supply_chain_alerts.log"

# Palavras-chave para alerta
KEYWORDS="CRÍTICO|PERIGO|ALERTA|FAILED|BAD|MISSING KEY"

log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$ALERT_LOG"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Iniciando verificação de alertas de Supply Chain..."

# Arquivos de log para verificar
FILES=(
    "$LOG_DIR/supply_chain_auditoria.log"
    "$LOG_DIR/supply_chain_assinaturas.log"
    "$LOG_DIR/supply_chain_alteracoes.log"
    "$LOG_DIR/supply_chain_dependencias.log"
    "$LOG_DIR/supply_chain_hijack.log"
    "$LOG_DIR/supply_chain_updates.log"
)

FOUND_ALERTS=0

for F in "${FILES[@]}"; do
    if [ -f "$F" ]; then
        # Verifica se o arquivo foi modificado recentemente (ex: últimas 24h)
        if find "$F" -mtime -1 | grep -q .; then
            # Procura por keywords
            ALERTS=$(grep -E "$KEYWORDS" "$F")
            if [ -n "$ALERTS" ]; then
                log "=== ALERTAS ENCONTRADOS EM $F ==="
                echo "$ALERTS" | tee -a "$ALERT_LOG"
                FOUND_ALERTS=1
            fi
        fi
    fi
done

if [ "$FOUND_ALERTS" -eq 1 ]; then
    log "[STATUS] Problemas detectados. Verifique $ALERT_LOG"
    # Enviar para syslog
    logger -p authpriv.crit -t SUPPLY_CHAIN_ALERT "Problemas detectados na auditoria de Supply Chain. Verifique $ALERT_LOG"

    # Exemplo de e-mail (comentado)
    # echo "Alertas detectados. Veja anexo." | mail -s "Supply Chain Alert" admin@localhost < "$ALERT_LOG"
else
    log "[STATUS] Nenhum alerta recente encontrado nos logs analisados."
fi
