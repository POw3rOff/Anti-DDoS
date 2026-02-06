#!/bin/bash

# ==============================================================================
# Script: Gestão de Dependências de Scripts
# Descrição: Verifica se os binários essenciais para a suite de segurança estão instalados.
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

# Cores para saída
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}[INFO] Iniciando verificação de dependências...${NC}"

# Lista de ferramentas essenciais
FERRAMENTAS=("awk" "sed" "grep" "ip" "ss" "curl" "openssl" "iptables" "jq" "chattr" "lsattr" "mktemp" "sha256sum" "tar" "gzip")

DEPENDENCIAS_FALTANDO=0

for cmd in "${FERRAMENTAS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}[FALHA] Ferramenta não encontrada: $cmd${NC}"
        DEPENDENCIAS_FALTANDO=$((DEPENDENCIAS_FALTANDO + 1))
    else
        VERSION=$( "$cmd" --version 2>/dev/null | head -n 1 )
        if [ -z "$VERSION" ]; then
             VERSION="Instalado (versão desconhecida)"
        fi
        echo -e "${GREEN}[OK] $cmd encontrado.${NC}"
    fi
done

# Verificações adicionais de pacotes opcionais mas recomendados
echo -e "${YELLOW}[INFO] Verificando ferramentas recomendadas...${NC}"
FERRAMENTAS_OPCIONAIS=("auditd" "ufw" "nmap" "tcpdump")

for cmd in "${FERRAMENTAS_OPCIONAIS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${YELLOW}[AVISO] Ferramenta recomendada ausente: $cmd${NC}"
    else
        echo -e "${GREEN}[OK] $cmd encontrado.${NC}"
    fi
done

if [ "$DEPENDENCIAS_FALTANDO" -eq 0 ]; then
    echo -e "${GREEN}[SUCESSO] Todas as dependências essenciais estão satisfeitas.${NC}"
    exit 0
else
    echo -e "${RED}[ERRO] Faltam $DEPENDENCIAS_FALTANDO ferramentas essenciais. Instale-as para garantir o funcionamento da suite.${NC}"
    exit 1
fi
