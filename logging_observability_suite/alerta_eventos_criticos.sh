#!/bin/bash
# alerta_eventos_criticos.sh
# Monitora logs por eventos críticos (Panic, Segfault, OOM, Falhas de Auth) nos últimos 10 minutos
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

KEYWORDS="(kernel panic|segfault|oom-killer|Failed password|refused connect|Possible SYN flooding|buffer overflow|suspect)"
MINUTES=10

echo "=== Verificação de Eventos Críticos (Últimos $MINUTES min) ==="

check_journal() {
    if command -v journalctl >/dev/null 2>&1; then
        echo -e "${YELLOW}[*] Consultando Journald...${NC}"
        # -S "10 minutes ago"
        count=$(journalctl -S "$MINUTES minutes ago" --no-pager | grep -E -i "$KEYWORDS" | wc -l)

        if [ "$count" -gt 0 ]; then
            echo -e "${RED}[ALERTA] $count eventos críticos encontrados no Journald:${NC}"
            journalctl -S "$MINUTES minutes ago" --no-pager | grep -E -i "$KEYWORDS" --color=always
        else
            echo -e "${GREEN}[OK] Nenhum evento crítico no Journald recentemente.${NC}"
        fi
    else
        echo -e "${YELLOW}[INFO] Journald não disponível.${NC}"
    fi
}

check_files() {
    # Fallback para arquivos se journald não cobrir tudo ou não existir
    echo -e "${YELLOW}[*] Consultando Arquivos de Log (tail)...${NC}"
    FILES=("/var/log/syslog" "/var/log/messages" "/var/log/kern.log" "/var/log/auth.log")

    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            # Pega as últimas 500 linhas para verificar
            found=$(tail -n 500 "$file" | grep -E -i "$KEYWORDS")
            if [ -n "$found" ]; then
                echo -e "${RED}[ALERTA] Eventos encontrados em $file (últimas 500 linhas):${NC}"
                echo "$found" | tail -n 5
                echo "..."
            fi
        fi
    done
}

check_journal
check_files

# Integração simples com webhook/mail (comentada)
# if [ alerts_found ]; then
#    mail -s "ALERTA DE SEGURANÇA" admin@exemplo.com < /tmp/alert_body
# fi
