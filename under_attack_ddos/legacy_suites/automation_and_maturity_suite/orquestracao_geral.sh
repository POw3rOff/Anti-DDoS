#!/bin/bash

# ==============================================================================
# Script: Orquestração Geral
# Descrição: Menu central para gerenciar e executar scripts de todas as suites de segurança.
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

# Cores
BLUE="\033[0;34m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

# Diretório base
BASE_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
if [ "$BASE_DIR" == "/" ]; then
    BASE_DIR=$(dirname "$(readlink -f "$0")")
fi

while true; do
    clear
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}       ORQUESTRADOR GERAL DE SEGURANÇA (MASTER)       ${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo ""
    echo -e "${YELLOW}1.${NC} Painel de Estado (Dashboard)"
    echo -e "${YELLOW}2.${NC} Executar Auditoria Completa"
    echo -e "${YELLOW}3.${NC} Gerar Relatório de Maturidade"
    echo -e "${YELLOW}4.${NC} Verificar Dependências"
    echo -e "${YELLOW}5.${NC} Listar Suites de Segurança Detectadas"
    echo -e "${YELLOW}0.${NC} Sair"
    echo ""
    read -p "Escolha uma opção: " OPTION

    case $OPTION in
        1)
            bash "${BASE_DIR}/automation_and_maturity_suite/dashboard_estado.sh"
            read -p "Pressione Enter para voltar..."
            ;;
        2)
            bash "${BASE_DIR}/automation_and_maturity_suite/auditoria_completa.sh"
            read -p "Pressione Enter para voltar..."
            ;;
        3)
            bash "${BASE_DIR}/automation_and_maturity_suite/relatorio_maturidade.sh"
            read -p "Pressione Enter para voltar..."
            ;;
        4)
            bash "${BASE_DIR}/automation_and_maturity_suite/gestao_dependencias_scripts.sh"
            read -p "Pressione Enter para voltar..."
            ;;
        5)
            echo ""
            echo -e "${GREEN}Suites encontradas em $BASE_DIR:${NC}"
            ls -F "$BASE_DIR" | grep "/" | grep "suite"
            echo -e "${GREEN}Outros diretórios de segurança:${NC}"
            ls -F "$BASE_DIR" | grep "/" | grep -E "security|protection"
            echo ""
            read -p "Pressione Enter para voltar..."
            ;;
        0)
            echo "Saindo..."
            exit 0
            ;;
        *)
            echo "Opção inválida."
            sleep 1
            ;;
    esac
done
