#!/bin/bash

# Script: verificacao_binarios_sistema.sh
# Descrição: Verifica a integridade dos binários do sistema usando o gerenciador de pacotes.
# Autor: Jules (Agente de IA)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Verificação de Integridade de Binários ===${NC}"

# Detecta gerenciador de pacotes
if command -v rpm >/dev/null 2>&1; then
    echo -e "${YELLOW}[*] Sistema baseado em RPM detectado.${NC}"
    echo -e "${YELLOW}[*] Executando verificação (rpm -Va). Isso pode demorar...${NC}"

    # Filtra apenas binários em /bin, /sbin, /usr/bin, /usr/sbin para ser mais rápido e focado
    # Ignora arquivos de configuração (c), documentação (d)
    FAILED_FILES=$(rpm -Va --nofiles --nodeps --noscripts | grep -E '^..5' | grep -E ' /bin/|/sbin/|/usr/bin/|/usr/sbin/|/lib/|/lib64/')

    if [ -n "$FAILED_FILES" ]; then
        echo -e "${RED}[!] Arquivos com checksum alterado detectados:${NC}"
        echo "$FAILED_FILES"
    else
        echo -e "${GREEN}[OK] Nenhuma alteração de checksum detectada nos binários monitorados pelo RPM.${NC}"
    fi

elif command -v dpkg >/dev/null 2>&1; then
    echo -e "${YELLOW}[*] Sistema baseado em DPKG/Debian detectado.${NC}"

    if command -v debsums >/dev/null 2>&1; then
        echo -e "${YELLOW}[*] Executando 'debsums' em binários essenciais...${NC}"
        debsums -s -c 2>/dev/null
        if [ $? -eq 0 ]; then
             echo -e "${GREEN}[OK] debsums não reportou erros.${NC}"
        else
             echo -e "${RED}[!] debsums encontrou discrepâncias (veja acima).${NC}"
        fi
    else
        echo -e "${YELLOW}[*] 'debsums' não instalado. Usando 'dpkg --verify'...${NC}"
        # dpkg --verify output format: ??5?????? filename
        FAILED_FILES=$(dpkg --verify | grep '..5' | grep -E '/bin/|/sbin/')

        if [ -n "$FAILED_FILES" ]; then
             echo -e "${RED}[!] Arquivos com checksum alterado detectados:${NC}"
             echo "$FAILED_FILES"
        else
             echo -e "${GREEN}[OK] dpkg --verify não reportou alterações em binários.${NC}"
        fi
    fi

else
    echo -e "${YELLOW}[!] Gerenciador de pacotes não suportado ou não encontrado.${NC}"
    echo -e "${YELLOW}[*] Executando verificação de timestamp (fallback)...${NC}"

    # Verifica se binaries principais foram modificados nos últimos 2 dias (exemplo simples)
    RECENT_MOD=$(find /bin /sbin /usr/bin /usr/sbin -type f -mtime -2 2>/dev/null)
    if [ -n "$RECENT_MOD" ]; then
         echo -e "${RED}[!] Binários modificados nos últimos 2 dias:${NC}"
         echo "$RECENT_MOD"
    else
         echo -e "${GREEN}[OK] Nenhum binário principal modificado recentemente (2 dias).${NC}"
    fi
fi

echo -e "${YELLOW}=== Verificação Concluída ===${NC}"
