#!/bin/bash
# detecao_logs_desativados.sh
# Detecta se serviços de log foram desativados ou se regras de auditoria foram removidas
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

ALERTS_FOUND=0

check_service_status() {
    service=$1
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}[OK] Serviço $service está ativo.${NC}"
    else
        echo -e "${RED}[ALERTA] Serviço $service está PARADO ou INEXISTENTE.${NC}"
        ALERTS_FOUND=1
    fi
}

check_auditd_rules() {
    echo -e "${YELLOW}[*] Verificando regras do auditd...${NC}"
    if command -v auditctl >/dev/null 2>&1; then
        rules_count=$(auditctl -l | wc -l)
        status=$(auditctl -s | grep "enabled")

        if [[ "$status" == *"enabled 0"* ]]; then
            echo -e "${RED}[ALERTA] Sistema de auditoria (auditd) está DESABILITADO no kernel.${NC}"
            ALERTS_FOUND=1
        elif [ "$rules_count" -eq 0 ] || [ "$rules_count" -eq 1 ] && [[ $(auditctl -l) == "No rules"* ]]; then
             echo -e "${RED}[ALERTA] Nenhuma regra de auditoria carregada no auditd.${NC}"
             ALERTS_FOUND=1
        else
             echo -e "${GREEN}[OK] $rules_count regras de auditoria ativas.${NC}"
        fi
    else
        echo -e "${YELLOW}[INFO] auditctl não encontrado.${NC}"
    fi
}

check_log_files_empty() {
    echo -e "${YELLOW}[*] Verificando arquivos de log vazios...${NC}"
    FILES=("/var/log/auth.log" "/var/log/syslog" "/var/log/messages" "/var/log/kern.log")

    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            if [ ! -s "$file" ]; then
                echo -e "${RED}[ALERTA] Arquivo $file existe mas está VAZIO.${NC}"
                ALERTS_FOUND=1
            fi
        fi
    done
}

main() {
    echo "=== Detecção de Logs Desativados ==="

    check_service_status rsyslog
    check_service_status systemd-journald
    check_service_status auditd

    check_auditd_rules
    check_log_files_empty

    echo ""
    if [ $ALERTS_FOUND -eq 1 ]; then
        echo -e "${RED}RESULTADO: Problemas detectados na configuração de logs.${NC}"
        exit 1
    else
        echo -e "${GREEN}RESULTADO: Nenhuma anomalia óbvia detectada.${NC}"
        exit 0
    fi
}

main
