#!/bin/bash

# Script: auditoria_kernel.sh
# Descrição: Audita a versão do kernel, parâmetros de boot e estado "tainted".
# Autor: Jules (Agente de IA)

# Cores para saída
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[*] Iniciando Auditoria do Kernel...${NC}"

# 1. Versão do Kernel
KERNEL_VERSION=$(uname -r)
echo -e "Versão do Kernel: ${GREEN}$KERNEL_VERSION${NC}"

# 2. Verificação de Taint (Contaminação)
TAINTED_FILE="/proc/sys/kernel/tainted"
if [ -f "$TAINTED_FILE" ]; then
    TAINT_VAL=$(cat "$TAINTED_FILE")
    if [ "$TAINT_VAL" -ne 0 ]; then
        echo -e "${RED}[!] AVISO: O kernel está marcado como TAINTED (Valor: $TAINT_VAL).${NC}"
        echo -e "    Isso pode indicar módulos proprietários, hardware instável ou carregamento forçado de módulos."
    else
        echo -e "${GREEN}[OK] O kernel não está tainted.${NC}"
    fi
else
    echo -e "${YELLOW}[?] Arquivo de taint não encontrado.${NC}"
fi

# 3. Parâmetros de Boot (Cmdline)
CMDLINE_FILE="/proc/cmdline"
if [ -f "$CMDLINE_FILE" ]; then
    CMDLINE=$(cat "$CMDLINE_FILE")
    echo -e "Parâmetros de Boot: $CMDLINE"

    # Verificações simples de segurança no boot
    if [[ "$CMDLINE" != *"mitigations=off"* ]]; then
        echo -e "${GREEN}[OK] Mitigações de CPU não parecem estar desativadas globalmente.${NC}"
    else
        echo -e "${RED}[!] PERIGO: 'mitigations=off' encontrado. Proteções de CPU desativadas!${NC}"
    fi

    if [[ "$CMDLINE" == *"nosmap"* || "$CMDLINE" == *"nosmep"* ]]; then
        echo -e "${RED}[!] PERIGO: Proteções SMAP/SMEP desativadas via boot!${NC}"
    fi
else
    echo -e "${YELLOW}[?] Não foi possível ler /proc/cmdline.${NC}"
fi

# 4. KASLR (Verificação simples se o endereço base muda ou se está ativo na config - difícil sem config, assumindo padrão)
# Esta é uma verificação básica.
if grep -q "kaslr" "$CMDLINE_FILE"; then
    echo -e "${GREEN}[OK] KASLR explicitamente ativado nos parâmetros de boot.${NC}"
elif grep -q "nokaslr" "$CMDLINE_FILE"; then
    echo -e "${RED}[!] PERIGO: KASLR explicitamente desativado ('nokaslr').${NC}"
else
    echo -e "${YELLOW}[info] KASLR não especificado explicitamente no boot (pode estar ativo por padrão).${NC}"
fi

echo -e "${YELLOW}[*] Auditoria do Kernel concluída.${NC}"
