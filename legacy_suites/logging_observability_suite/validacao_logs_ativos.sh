#!/bin/bash
# validacao_logs_ativos.sh
# Verifica se os serviços de log estão ativos e se os arquivos estão sendo escritos
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

check_service() {
    service=$1
    echo -n "Verificando serviço $service... "
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}[ATIVO]${NC}"
    else
        echo -e "${RED}[INATIVO]${NC}"
    fi
}

check_file_update() {
    file=$1
    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}Arquivo $file não encontrado.${NC}"
        return
    fi

    last_mod=$(stat -c %Y "$file")
    current_time=$(date +%s)
    diff=$((current_time - last_mod))

    # Considera ativo se modificado nos últimos 30 minutos (1800 segundos)
    echo -n "Verificando atualização de $file... "
    if [ $diff -lt 1800 ]; then
        echo -e "${GREEN}[ATUALIZADO RECENTEMENTE] ($diff segundos atrás)${NC}"
    else
        echo -e "${RED}[DESATUALIZADO] (Modificado há $diff segundos)${NC}"
    fi
}

echo "=== Validação de Logs Ativos ==="
check_service rsyslog
check_service auditd
check_service systemd-journald

echo ""
echo "=== Verificação de Arquivos de Log ==="
# Tenta verificar syslog ou messages dependendo da distro
if [ -f /var/log/syslog ]; then
    check_file_update /var/log/syslog
elif [ -f /var/log/messages ]; then
    check_file_update /var/log/messages
fi

check_file_update /var/log/auth.log
check_file_update /var/log/kern.log

echo ""
echo "=== Verificação do Journald ==="
if journalctl -n 1 >/dev/null 2>&1; then
    echo -e "${GREEN}Journald está acessível e respondendo.${NC}"
else
    echo -e "${RED}Erro ao acessar logs do Journald.${NC}"
fi
