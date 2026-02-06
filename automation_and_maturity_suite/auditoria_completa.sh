#!/bin/bash

# ==============================================================================
# Script: Auditoria Completa
# Descrição: Executa uma bateria completa de testes de segurança e auditoria.
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

LOG_FILE="auditoria_completa_$(date +%Y%m%d_%H%M).log"
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
BASE_DIR=$(dirname "$SCRIPT_DIR")

# Cores
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo -e "${GREEN}Iniciando Auditoria Completa...${NC}"
echo "Log: $LOG_FILE"
echo ""

run_check() {
    local script_path="$1"
    local desc="$2"

    echo -e "${YELLOW}>>> Executando: $desc ($script_path)${NC}"
    echo ">>> INICIO: $desc" >> "$LOG_FILE"

    if [ -f "$script_path" ]; then
        bash "$script_path" >> "$LOG_FILE" 2>&1
        if [ $? -eq 0 ]; then
             echo -e "${GREEN}[OK] Execução concluída.${NC}"
        else
             echo -e "${RED}[ERRO] Falha na execução.${NC}"
        fi
    else
        echo -e "${RED}[SKIP] Script não encontrado: $script_path${NC}"
        echo "Script nao encontrado" >> "$LOG_FILE"
    fi
    echo ">>> FIM: $desc" >> "$LOG_FILE"
    echo ""
}

# 1. Dependências
run_check "$SCRIPT_DIR/gestao_dependencias_scripts.sh" "Verificação de Dependências"

# 2. Segurança da Própria Automação
run_check "$SCRIPT_DIR/auditoria_automacao.sh" "Auditoria da Automação"

# 3. Cron e Agendamento
run_check "$SCRIPT_DIR/agendamento_seguro.sh" "Auditoria de Agendamento (Cron)"

# 4. Falhas Recentes
run_check "$SCRIPT_DIR/deteccao_execucoes_falhadas.sh" "Detecção de Falhas de Execução"

# 5. Score Global
run_check "$SCRIPT_DIR/score_global_seguranca.sh" "Cálculo de Score de Segurança"

# 6. Testes Zero Trust (se disponível)
ZERO_TRUST_SCRIPT="$BASE_DIR/zero_trust_suite/zero_trust_tests.sh"
if [ -f "$ZERO_TRUST_SCRIPT" ]; then
    run_check "$ZERO_TRUST_SCRIPT" "Testes Zero Trust"
fi

# 7. Monitoramento de Saída (se disponível)
OUTBOUND_SCRIPT="$BASE_DIR/linux_security_scripts/outbound_monitor.sh"
if [ -f "$OUTBOUND_SCRIPT" ]; then
    # Atenção: scripts de monitoramento podem ser loop infinito.
    # Assumindo que este script é de checagem ou configuração.
    # Se for monitoramento contínuo, não devemos rodar aqui.
    # Consultando memória: outbound_monitor.sh é um monitor. Talvez não deva rodar na auditoria.
    echo -e "${YELLOW}[INFO] Script de monitoramento detectado ($OUTBOUND_SCRIPT). Não executado automaticamente para evitar bloqueio.${NC}"
fi

# 8. Testes de Resistência (se disponível)
RESISTANCE_SCRIPT="$BASE_DIR/system_resistance_suite/resistance_tests.sh"
if [ -f "$RESISTANCE_SCRIPT" ]; then
    run_check "$RESISTANCE_SCRIPT" "Testes de Resistência do Sistema"
fi


echo -e "${GREEN}Auditoria Completa finalizada.${NC}"
echo "Relatório salvo em $LOG_FILE"
