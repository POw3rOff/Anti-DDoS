#!/bin/bash
# centralizacao_logs.sh
# Script para verificar e configurar o envio centralizado de logs
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m" # No Color

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Erro: Este script deve ser executado como root.${NC}"
        exit 1
    fi
}

check_rsyslog_forwarding() {
    echo -e "${YELLOW}[*] Verificando configuração de forwarding no rsyslog...${NC}"
    if command -v rsyslogd >/dev/null 2>&1; then
        if grep -rE "^\*\.\* @|^\*\.\* @@" /etc/rsyslog.conf /etc/rsyslog.d/ 2>/dev/null; then
            echo -e "${GREEN}[OK] Encaminhamento de logs detectado no rsyslog.${NC}"
        else
            echo -e "${RED}[ALERTA] Nenhum encaminhamento de logs detectado no rsyslog.${NC}"
            # Escaping * to be safe
            echo -e "Sugestão: Adicione \"*.* @servidor_remoto:514\" (UDP) ou \"*.* @@servidor_remoto:514\" (TCP) no rsyslog.conf"
        fi
    else
        echo -e "${YELLOW}[INFO] Rsyslog não está instalado.${NC}"
    fi
}

check_journal_upload() {
    echo -e "${YELLOW}[*] Verificando systemd-journal-upload...${NC}"
    if systemctl is-active --quiet systemd-journal-upload; then
        echo -e "${GREEN}[OK] Serviço systemd-journal-upload está ativo.${NC}"
        if [ -f /etc/systemd/journal-upload.conf ]; then
             url=$(grep "^URL=" /etc/systemd/journal-upload.conf)
             if [ -n "$url" ]; then
                 echo -e "${GREEN}[OK] URL configurada: $url${NC}"
             else
                 echo -e "${RED}[ALERTA] URL não configurada em journal-upload.conf.${NC}"
             fi
        fi
    else
        echo -e "${YELLOW}[INFO] Serviço systemd-journal-upload não está ativo ou instalado.${NC}"
    fi
}

configure_rsyslog() {
    read -p "Deseja configurar o encaminhamento via Rsyslog? (s/n): " confirm
    if [[ "$confirm" == "s" ]]; then
        read -p "Digite o IP/Hostname do servidor remoto: " server
        read -p "Use TCP (@@) ou UDP (@)? (tcp/udp): " proto

        prefix="@"
        if [[ "$proto" == "tcp" ]]; then
            prefix="@@"
        fi

        # Safe assignment
        conf_line="*.* ${prefix}${server}:514"

        # Safe echo with clear quoting
        echo -e "${YELLOW}Adicionando '${conf_line}' em /etc/rsyslog.d/00-remote.conf${NC}"
        echo "$conf_line" > /etc/rsyslog.d/00-remote.conf

        echo -e "${YELLOW}Reiniciando rsyslog...${NC}"
        systemctl restart rsyslog
        if systemctl is-active --quiet rsyslog; then
            echo -e "${GREEN}Rsyslog configurado e reiniciado.${NC}"
        else
             echo -e "${RED}Erro ao reiniciar rsyslog. Verifique os logs.${NC}"
        fi
    fi
}

main() {
    check_root
    echo -e "${YELLOW}=== Auditoria de Centralização de Logs ===${NC}"
    check_rsyslog_forwarding
    check_journal_upload

    echo ""
    echo -e "${YELLOW}=== Opções de Configuração ===${NC}"
    configure_rsyslog
}

main
