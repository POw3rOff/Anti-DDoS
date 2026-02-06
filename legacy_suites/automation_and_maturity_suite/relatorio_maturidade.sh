#!/bin/bash

# ==============================================================================
# Script: Relatório de Maturidade
# Descrição: Gera um relatório textual consolidado sobre a postura de segurança.
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

OUTPUT_FILE="relatorio_maturidade_$(date +%Y%m%d_%H%M).txt"
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

{
    echo "========================================================"
    echo "RELATÓRIO DE MATURIDADE E SEGURANÇA DO SISTEMA"
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "Kernel: $(uname -r)"
    echo "========================================================"
    echo ""

    echo "1. RESULTADO DA PONTUAÇÃO AUTOMÁTICA"
    echo "--------------------------------------------------------"
    if [ -f "$SCRIPT_DIR/score_global_seguranca.sh" ]; then
        # Remove códigos de cor ANSI da saída
        bash "$SCRIPT_DIR/score_global_seguranca.sh" | sed "s/\x1b\[[0-9;]*m//g"
    else
        echo "Script de score não encontrado."
    fi
    echo ""

    echo "2. DEPENDÊNCIAS DO SISTEMA"
    echo "--------------------------------------------------------"
    if [ -f "$SCRIPT_DIR/gestao_dependencias_scripts.sh" ]; then
        bash "$SCRIPT_DIR/gestao_dependencias_scripts.sh" | sed "s/\x1b\[[0-9;]*m//g"
    else
        echo "Script de dependências não encontrado."
    fi
    echo ""

    echo "3. VERIFICAÇÃO DE AGENDAMENTOS (CRON)"
    echo "--------------------------------------------------------"
    if [ -f "$SCRIPT_DIR/agendamento_seguro.sh" ]; then
        bash "$SCRIPT_DIR/agendamento_seguro.sh" | sed "s/\x1b\[[0-9;]*m//g"
    else
        echo "Script de agendamento não encontrado."
    fi
    echo ""

    echo "========================================================"
    echo "FIM DO RELATÓRIO"
    echo "========================================================"

} > "$OUTPUT_FILE"

echo -e "\033[0;32mRelatório gerado com sucesso em: $OUTPUT_FILE\033[0m"
cat "$OUTPUT_FILE"
