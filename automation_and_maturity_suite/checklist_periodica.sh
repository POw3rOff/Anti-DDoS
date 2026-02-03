#!/bin/bash

# ==============================================================================
# Script: Checklist Periódica
# Descrição: Executa verificações de rotina (diárias/semanais).
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

LOG_FILE="checklist_$(date +%Y%m%d).log"
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

log() {
    echo "[$(date +%H:%M:%S)] $1" | tee -a "$LOG_FILE"
}

log "Iniciando Checklist Periódica..."

# 1. Verificar Espaço em Disco
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d "%")
if [ "$DISK_USAGE" -gt 90 ]; then
    log "ALERTA: Disco quase cheio ($DISK_USAGE%)"
else
    log "Disco OK ($DISK_USAGE%)"
fi

# 2. Verificar Atualizações (Simulado/Genérico)
if command -v apt &>/dev/null; then
    UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
    if [ "$UPDATES" -gt 1 ]; then
        log "AVISO: Existem pacotes para atualizar."
    else
        log "Sistema parece atualizado."
    fi
else
    log "Gerenciador de pacotes não suportado para check automático."
fi

# 3. Executar Auditoria de Automação
if [ -f "$SCRIPT_DIR/auditoria_automacao.sh" ]; then
    log "Executando auditoria de scripts..."
    bash "$SCRIPT_DIR/auditoria_automacao.sh" >> "$LOG_FILE" 2>&1
    log "Auditoria de scripts concluída."
fi

# 4. Executar Score Global
if [ -f "$SCRIPT_DIR/score_global_seguranca.sh" ]; then
    log "Calculando score de segurança..."
    bash "$SCRIPT_DIR/score_global_seguranca.sh" >> "$LOG_FILE" 2>&1
    log "Cálculo de score concluído."
fi

log "Checklist finalizada. Verifique $LOG_FILE para detalhes."
