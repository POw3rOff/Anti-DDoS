#!/bin/bash
# auditoria_retencao_logs.sh
# Audita configurações do logrotate para verificar políticas de retenção
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo "=== Auditoria de Retenção de Logs (Logrotate) ==="

check_file() {
    file=$1
    if [ ! -f "$file" ]; then return; fi

    echo -e "${YELLOW}Analisando $file...${NC}"

    # Extrair rotação (pode haver multiplos blocos)
    rotates=$(grep -E "^\s*rotate\s+[0-9]+" "$file" | awk "{print \$2}")

    # Processar cada valor encontrado
    if [ -n "$rotates" ]; then
        echo "$rotates" | while read -r rotate; do
            if [ -n "$rotate" ]; then
                 echo "  - Retenção encontrada: $rotate"
                 if [ "$rotate" -lt 4 ]; then
                    echo -e "    ${RED}[ALERTA] Retenção baixa ($rotate ciclos). Recomendado: > 4.${NC}"
                 else
                    echo -e "    ${GREEN}[OK] Retenção aceitável ($rotate).${NC}"
                 fi
            fi
        done
    else
        echo "  - Nenhuma diretiva 'rotate' encontrada neste arquivo."
    fi

    # Verificar frequencia
    interval=$(grep -E "^\s*(daily|weekly|monthly)" "$file" | head -n 1)
    if [ -n "$interval" ]; then
        echo "  - Frequência (primeira encontrada): $interval"
    fi
}

# Conf global
check_file /etc/logrotate.conf

# Confs específicas
echo ""
echo "=== Configurações Específicas ==="
for f in /etc/logrotate.d/*; do
    check_file "$f"
done

echo ""
echo "=== Verificação de Logs Antigos em Disco ==="
# Fix: Added parentheses for grouping OR conditions in find
oldest_log=$(find /var/log -type f \( -name "*.gz" -o -name "*.1" \) -printf "%T+ %p\n" 2>/dev/null | sort | head -n 1)

if [ -n "$oldest_log" ]; then
    echo -e "Log mais antigo encontrado: ${GREEN}$oldest_log${NC}"
else
    echo -e "${YELLOW}Nenhum log rotacionado (arquivados/gz) encontrado em /var/log.${NC}"
fi
