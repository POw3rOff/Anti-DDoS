#!/bin/bash

# Script: hardening_sysctl.sh
# Descrição: Verifica e aplica configurações de hardening via sysctl.
# Autor: Jules (Agente de IA)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APPLY_FIXES=0

if [ "$1" == "--apply" ]; then
    APPLY_FIXES=1
    echo -e "${YELLOW}[*] Modo de aplicação ativado. Alterações serão feitas.${NC}"
else
    echo -e "${YELLOW}[*] Modo auditoria (use --apply para aplicar correções).${NC}"
fi

check_sysctl() {
    local param="$1"
    local expected="$2"
    local description="$3"

    current=$(sysctl -n "$param" 2>/dev/null)

    if [ -z "$current" ]; then
        echo -e "${YELLOW}[?] Parâmetro $param não encontrado.${NC}"
        return
    fi

    if [ "$current" -eq "$expected" ]; then
        echo -e "${GREEN}[OK] $param = $current ($description)${NC}"
    else
        echo -e "${RED}[!] FALHA: $param = $current (Esperado: $expected) - $description${NC}"
        if [ "$APPLY_FIXES" -eq 1 ]; then
            echo -e "${YELLOW}    Aplicando correção...${NC}"
            sysctl -w "$param=$expected"
            # Opcional: Persistir em /etc/sysctl.d/99-security.conf
            # echo "$param = $expected" >> /etc/sysctl.d/99-security.conf
        fi
    fi
}

echo -e "${YELLOW}=== Verificação de Hardening Sysctl ===${NC}"

# Kernel pointers (ASLR leak protection)
check_sysctl "kernel.kptr_restrict" 2 "Ocultar ponteiros do kernel (previne leaks de endereço)"

# Dmesg restrictions
check_sysctl "kernel.dmesg_restrict" 1 "Restringir acesso ao buffer dmesg (apenas root)"

# Ptrace scope (YAMA)
check_sysctl "kernel.yama.ptrace_scope" 1 "Restringir ptrace (apenas processos pai)"

# BPF JIT Hardening
check_sysctl "net.core.bpf_jit_harden" 2 "Hardening do JIT BPF"

# File system protection
check_sysctl "fs.protected_hardlinks" 1 "Proteger hardlinks"
check_sysctl "fs.protected_symlinks" 1 "Proteger symlinks"

# Network
check_sysctl "net.ipv4.conf.all.accept_redirects" 0 "Ignorar redirecionamentos ICMP"
check_sysctl "net.ipv4.conf.all.send_redirects" 0 "Não enviar redirecionamentos ICMP"
check_sysctl "net.ipv4.conf.all.log_martians" 1 "Logar pacotes com origem impossível (martians)"
check_sysctl "net.ipv4.icmp_echo_ignore_broadcasts" 1 "Ignorar ICMP echo broadcast"

echo -e "${YELLOW}=== Verificação Concluída ===${NC}"
