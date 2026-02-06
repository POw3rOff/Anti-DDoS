#!/bin/bash
# score_risco_supply_chain.sh
# Descrição: Calcula um Score de Risco de Supply Chain baseado nos logs das auditorias.
# Autor: Jules (System Security Suite)

LOG_DIR="/var/log"
SCORE=100

log() {
    echo "$1"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Calculando Supply Chain Risk Score (Base: 100)..."

# 1. Verificar Repositórios Inseguros
if grep -q "HTTP" "$LOG_DIR/supply_chain_hijack.log" 2>/dev/null; then
    log "[RISCO] Repositórios HTTP detectados (-20 pontos)"
    SCORE=$((SCORE - 20))
fi

# 2. Verificar Pacotes Não Assinados
if grep -q "NOT SIGNED" "$LOG_DIR/supply_chain_assinaturas.log" 2>/dev/null; then
    COUNT=$(grep "NOT SIGNED" "$LOG_DIR/supply_chain_assinaturas.log" | wc -l)
    PENALTY=$((COUNT * 2))
    [ $PENALTY -gt 30 ] && PENALTY=30
    log "[RISCO] $COUNT Pacotes não assinados detectados (-$PENALTY pontos)"
    SCORE=$((SCORE - PENALTY))
fi

# 3. Verificar Assinaturas Inválidas
if grep -q "BAD" "$LOG_DIR/supply_chain_assinaturas.log" 2>/dev/null; then
    log "[RISCO CRÍTICO] Assinaturas inválidas detectadas (-50 pontos)"
    SCORE=$((SCORE - 50))
fi

# 4. Verificar Arquivos Alterados
if [ -f "$LOG_DIR/supply_chain_alteracoes.log" ]; then
    # Conta linhas que parecem checksum failed (..5..)
    ALTERED=$(grep "..5......" "$LOG_DIR/supply_chain_alteracoes.log" | grep -v " c " | wc -l)
    if [ "$ALTERED" -gt 0 ]; then
        PENALTY=$((ALTERED * 5))
        [ $PENALTY -gt 40 ] && PENALTY=40
        log "[RISCO] $ALTERED Binários/Arquivos críticos alterados (-$PENALTY pontos)"
        SCORE=$((SCORE - PENALTY))
    fi
fi

# 5. Dependências Quebradas
if grep -q "Problemas" "$LOG_DIR/supply_chain_auditoria.log" 2>/dev/null; then
    log "[RISCO] Dependências quebradas detectadas (-10 pontos)"
    SCORE=$((SCORE - 10))
fi

# Limites
if [ $SCORE -lt 0 ]; then SCORE=0; fi

log "--------------------------------------------------"
log "SCORE FINAL DE SUPPLY CHAIN: $SCORE / 100"
log "--------------------------------------------------"

if [ $SCORE -lt 50 ]; then
    log "Classificação: CRÍTICO - Ação imediata necessária."
elif [ $SCORE -lt 80 ]; then
    log "Classificação: ALERTA - Verifique os problemas encontrados."
else
    log "Classificação: BOM - Mantenha o monitoramento."
fi
