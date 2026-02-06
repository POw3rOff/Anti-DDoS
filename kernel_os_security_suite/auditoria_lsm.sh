#!/bin/bash

# Script: auditoria_lsm.sh
# Descrição: Audita o status dos Módulos de Segurança Linux (LSM) como SELinux e AppArmor.
# Autor: Jules (Agente de IA)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Auditoria de LSM (Linux Security Modules) ===${NC}"

LSM_FOUND=0

# 1. Verificar SELinux
if command -v sestatus >/dev/null 2>&1; then
    LSM_FOUND=1
    echo -e "${YELLOW}[*] SELinux detectado.${NC}"
    SE_OUTPUT=$(sestatus)
    echo "$SE_OUTPUT"

    STATUS=$(echo "$SE_OUTPUT" | grep "SELinux status" | awk '{print $3}')
    MODE=$(echo "$SE_OUTPUT" | grep "Current mode" | awk '{print $3}')

    if [ "$STATUS" == "enabled" ]; then
        if [ "$MODE" == "enforcing" ]; then
             echo -e "${GREEN}[OK] SELinux está ativo e bloqueando (Enforcing).${NC}"
        else
             echo -e "${RED}[!] AVISO: SELinux está ativo mas em modo permissivo ($MODE).${NC}"
        fi
    else
        echo -e "${RED}[!] PERIGO: SELinux está desativado!${NC}"
    fi
fi

# 2. Verificar AppArmor
if command -v aa-status >/dev/null 2>&1; then
    LSM_FOUND=1
    echo -e "${YELLOW}[*] AppArmor detectado.${NC}"
    # aa-status requer root normalmente
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}[i] Execute como root para detalhes completos do AppArmor.${NC}"
    fi

    AA_STATUS=$(aa-status --json 2>/dev/null)
    # Fallback se json não suportado ou erro
    if [ $? -ne 0 ]; then
        AA_STATUS_TEXT=$(aa-status 2>/dev/null)
        echo "$AA_STATUS_TEXT" | head -n 5
        if echo "$AA_STATUS_TEXT" | grep -q "apparmor module is loaded"; then
             echo -e "${GREEN}[OK] Módulo AppArmor carregado.${NC}"
        else
             echo -e "${RED}[!] Módulo AppArmor NÃO carregado.${NC}"
        fi
    else
        echo -e "${GREEN}[OK] AppArmor parece estar funcional.${NC}"
    fi
fi

# 3. Verificação genérica via sysfs se nenhum comando específico achado
if [ $LSM_FOUND -eq 0 ]; then
    if [ -f /sys/kernel/security/lsm ]; then
        ACTIVE_LSM=$(cat /sys/kernel/security/lsm)
        echo -e "${YELLOW}[info] LSMs ativos no kernel: $ACTIVE_LSM${NC}"
        if [[ "$ACTIVE_LSM" == *"selinux"* || "$ACTIVE_LSM" == *"apparmor"* ]]; then
            echo -e "${YELLOW}[*] LSM parece estar carregado no kernel, mas ferramentas de user-space não foram encontradas.${NC}"
        else
            echo -e "${RED}[!] Nenhum LSM maior (SELinux/AppArmor) parece estar ativo.${NC}"
        fi
    else
        echo -e "${RED}[!] Não foi possível determinar o estado do LSM via /sys.${NC}"
    fi
fi

echo -e "${YELLOW}=== Auditoria Concluída ===${NC}"
