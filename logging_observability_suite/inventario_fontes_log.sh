#!/bin/bash
# inventario_fontes_log.sh
# Inventário de arquivos de log, tamanhos e atividades recentes
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo "=== Inventário de Fontes de Log ==="

echo -e "\n${YELLOW}[*] Top 10 Maiores Arquivos de Log:${NC}"
find /var/log -type f -exec du -h {} + 2>/dev/null | sort -rh | head -n 10

echo -e "\n${YELLOW}[*] Logs Ativos (Modificados nos últimos 60 min):${NC}"
find /var/log -type f -mmin -60 -exec ls -lh {} + 2>/dev/null | awk "{print \$9, \"(\" \$5 \")\"}"

echo -e "\n${YELLOW}[*] Logs \"Mortos\" (Não modificados há > 30 dias):${NC}"
find /var/log -type f -mtime +30 -exec ls -lh {} + 2>/dev/null | head -n 10
echo "(... e mais, se houver)"

echo -e "\n${YELLOW}[*] Processos mantendo logs abertos (lsof):${NC}"
if command -v lsof >/dev/null 2>&1; then
    lsof +D /var/log | awk "{print \$1, \$2, \$9}" | sort | uniq | head -n 20
else
    echo "lsof não instalado."
fi

echo -e "\n${YELLOW}[*] Uso de Disco do Journald:${NC}"
if command -v journalctl >/dev/null 2>&1; then
    journalctl --disk-usage
else
    echo "Journald não disponível."
fi
