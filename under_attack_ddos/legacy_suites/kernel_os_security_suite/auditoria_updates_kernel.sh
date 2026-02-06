#!/bin/bash

# Script: auditoria_updates_kernel.sh
# Descrição: Verifica se o kernel em execução é a versão mais recente instalada.
# Autor: Jules (Agente de IA)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Auditoria de Atualização do Kernel ===${NC}"

RUNNING_KERNEL=$(uname -r)
echo -e "Kernel em execução: ${GREEN}$RUNNING_KERNEL${NC}"

# Tenta encontrar a versão mais recente instalada em /boot
# Procura por vmlinuz-* ou vmlinuz-* (dependendo da distro)
# Ordena por versão (sort -V) e pega a última
LATEST_INSTALLED=$(ls /boot/vmlinuz-* 2>/dev/null | sed 's/.*vmlinuz-//' | sort -V | tail -n 1)

if [ -z "$LATEST_INSTALLED" ]; then
    # Tenta padrão alternativo (ex: Fedora/RHEL pode usar vmlinuz sem versão explicita no nome as vezes, ou links)
    LATEST_INSTALLED=$(ls /boot/kernel-* 2>/dev/null | sed 's/.*kernel-//' | sort -V | tail -n 1)
fi

if [ -n "$LATEST_INSTALLED" ]; then
    echo -e "Kernel instalado mais recente: ${GREEN}$LATEST_INSTALLED${NC}"

    if [ "$RUNNING_KERNEL" != "$LATEST_INSTALLED" ]; then
        echo -e "${RED}[!] AVISO: O kernel em execução NÃO é o mais recente instalado!${NC}"
        echo -e "${YELLOW}    Recomendação: Reinicie o servidor para aplicar a atualização de segurança.${NC}"

        # Comparação básica de versão
        # Se a string for idêntica mas ordem diferente, pode ser só sufixo.
        # Aqui assumimos que se strings são diferentes, versões são diferentes.
    else
        echo -e "${GREEN}[OK] O sistema está rodando a versão mais recente do kernel instalada.${NC}"
    fi
else
    echo -e "${YELLOW}[?] Não foi possível determinar a versão mais recente instalada em /boot.${NC}"
    echo -e "    Verifique manualmente os pacotes do kernel."
fi

# Verifica se precisa de reboot (Debian/Ubuntu specific)
if [ -f /var/run/reboot-required ]; then
    echo -e "${RED}[!] O sistema sinaliza que um REINÍCIO É NECESSÁRIO (/var/run/reboot-required presente).${NC}"
fi

echo -e "${YELLOW}=== Auditoria Concluída ===${NC}"
