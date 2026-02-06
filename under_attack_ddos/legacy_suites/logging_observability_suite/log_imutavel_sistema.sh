#!/bin/bash
# log_imutavel_sistema.sh
# Aplica atributo append-only (+a) em logs críticos
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

LOG_FILES=(
    "/var/log/auth.log"
    "/var/log/syslog"
    "/var/log/messages"
    "/var/log/kern.log"
    "/var/log/audit/audit.log"
)

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Erro: Este script deve ser executado como root.${NC}"
        exit 1
    fi
}

set_immutable() {
    echo -e "${YELLOW}[*] Aplicando atributo append-only (+a)...${NC}"
    echo -e "${RED}[AVISO] O atributo +a impede a rotação normal de logs (logrotate).${NC}"
    echo -e "${RED}Certifique-se de usar scripts 'prerotate' (chattr -a) e 'postrotate' (chattr +a) no logrotate.${NC}"
    echo -e "${RED}Ou execute a opção 2 (Remover proteção) antes de manutenções.${NC}"
    read -p "Continuar? (s/n): " confirm
    if [[ "$confirm" != "s" ]]; then return; fi

    for file in "${LOG_FILES[@]}"; do
        if [ -f "$file" ]; then
            chattr +a "$file" 2>/dev/null
            if lsattr "$file" | grep -q "a"; then
                echo -e "${GREEN}[OK] $file protegido (append-only).${NC}"
            else
                echo -e "${RED}[ERRO] Falha ao proteger $file.${NC}"
            fi
        else
            echo -e "${YELLOW}[SKIP] $file não encontrado.${NC}"
        fi
    done
}

unset_immutable() {
    echo -e "${YELLOW}[*] Removendo atributo append-only (-a)...${NC}"
    for file in "${LOG_FILES[@]}"; do
        if [ -f "$file" ]; then
            chattr -a "$file" 2>/dev/null
            if ! lsattr "$file" | grep -q "a"; then
                echo -e "${GREEN}[OK] $file desprotegido.${NC}"
            else
                echo -e "${RED}[ERRO] Falha ao desproteger $file.${NC}"
            fi
        fi
    done
}

main() {
    check_root
    echo "=== Proteção de Logs Imutáveis ==="
    echo "1. Aplicar proteção (+a)"
    echo "2. Remover proteção (-a)"
    read -p "Escolha uma opção (1/2): " option

    case $option in
        1) set_immutable ;;
        2) unset_immutable ;;
        *) echo "Opção inválida." ;;
    esac
}

main
