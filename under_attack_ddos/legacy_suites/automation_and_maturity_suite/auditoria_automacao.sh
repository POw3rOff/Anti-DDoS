#!/bin/bash

# ==============================================================================
# Script: Auditoria de Automação
# Descrição: Verifica a segurança dos próprios scripts de automação (permissões, ownership).
# Autor: Automacão de Segurança
# Data: $(date +%Y-%m-%d)
# ==============================================================================

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo -e "${YELLOW}[INFO] Iniciando auditoria dos scripts de automação...${NC}"

# Diretório base (assume que este script está dentro do diretório da suite ou um nível abaixo)
BASE_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
if [ "$BASE_DIR" == "/" ]; then
    BASE_DIR=$(dirname "$(readlink -f "$0")")
fi

echo -e "${YELLOW}[INFO] Verificando scripts em: $BASE_DIR${NC}"

ISSUES=0

# Encontrar scripts .sh
find "$BASE_DIR" -type f -name "*.sh" | while read -r script; do
    # 1. Verificar permissões (não deve ser 777 ou writable por outros)
    PERM=$(stat -c "%a" "$script")

    # Check "others" write bit
    if [ $((PERM & 1)) -ne 0 ] || [ $((PERM & 2)) -ne 0 ]; then
        echo -e "${RED}[RISCO] Permissão insegura ($PERM) em: $script${NC}"
        ISSUES=1
    fi

    # 2. Verificar Owner (idealmente root ou user admin específico)
    OWNER=$(stat -c "%U" "$script")
    if [ "$OWNER" != "root" ] && [ "$OWNER" != "$(whoami)" ]; then
        echo -e "${YELLOW}[AVISO] Script não pertence ao root/user atual ($OWNER): $script${NC}"
    fi

    # 3. Verificar shebang
    if ! head -n 1 "$script" | grep -q "^#!"; then
        echo -e "${YELLOW}[AVISO] Script sem shebang definido: $script${NC}"
    fi
done

if [ "$ISSUES" -eq 0 ]; then
    echo -e "${GREEN}[SUCESSO] Permissões dos scripts de automação parecem seguras.${NC}"
else
    echo -e "${RED}[FALHA] Foram encontrados riscos de permissão nos scripts. Corrija imediatamente (chmod 700 ou 750).${NC}"
fi
