#!/bin/bash
#
# comparacao_pre_pos_ataque.sh
#
# Compara o estado atual dos arquivos com um "manifesto" de integridade prévio.
# Útil para detectar web shells, backdoors ou binários modificados.
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -u

# Cores
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

MANIFEST_DIR="/var/backups/manifests"
LATEST_MANIFEST=$(ls -t "$MANIFEST_DIR"/*.sha256 2>/dev/null | head -n 1)

if [ -z "$LATEST_MANIFEST" ]; then
    echo -e "${YELLOW}[AVISO] Nenhum manifesto de integridade encontrado em $MANIFEST_DIR.${NC}"
    echo "Não é possível realizar comparação automática."
    echo ""
    echo "Deseja gerar um manifesto BASE agora para uso futuro? (s/n)"
    read -r RESP
    if [[ "$RESP" =~ ^[Ss]$ ]]; then
        mkdir -p "$MANIFEST_DIR"
        NEW_MANIFEST="$MANIFEST_DIR/manifest_$(date +%Y%m%d_%H%M%S).sha256"
        echo "Gerando manifesto de /bin, /sbin, /usr/bin, /usr/sbin, /etc..."
        find /bin /sbin /usr/bin /usr/sbin /etc -type f -exec sha256sum {} + > "$NEW_MANIFEST"
        echo -e "${GREEN}Manifesto criado: $NEW_MANIFEST${NC}"
    fi
    exit 0
fi

echo -e "${BLUE}Usando manifesto base: $LATEST_MANIFEST${NC}"
echo "Verificando integridade..."

# sha256sum -c verifica os hashes.
# -quiet suprime OKs
OUTPUT_DIFF="diff_report_$(date +%Y%m%d_%H%M%S).txt"

# Verifica arquivos listados no manifesto
sha256sum -c "$LATEST_MANIFEST" 2>/dev/null | grep -v ": OK$" > "$OUTPUT_DIFF"

if [ -s "$OUTPUT_DIFF" ]; then
    echo -e "${RED}[ALERTA] Divergências encontradas!${NC}"
    echo "Arquivos modificados ou com falha de verificação:"
    cat "$OUTPUT_DIFF"
    echo ""
    echo "Relatório salvo em: $OUTPUT_DIFF"
else
    echo -e "${GREEN}[SUCESSO] Todos os arquivos verificados correspondem ao manifesto.${NC}"
    rm -f "$OUTPUT_DIFF"
fi

# Verificação de arquivos NOVOS (que não estão no manifesto)
# Isso requer comparar a lista de arquivos atual com a lista do manifesto.
echo ""
echo "Verificando arquivos NOVOS em diretórios críticos (ex: /usr/bin)..."
# Extrai caminhos do manifesto
awk "{print \$2}" "$LATEST_MANIFEST" | sort > /tmp/manifest_files.txt
# Lista arquivos atuais
find /bin /sbin /usr/bin /usr/sbin /etc -type f | sort > /tmp/current_files.txt

# Compara
comm -13 /tmp/manifest_files.txt /tmp/current_files.txt > "$OUTPUT_DIFF.added"

if [ -s "$OUTPUT_DIFF.added" ]; then
    echo -e "${YELLOW}[AVISO] Arquivos NOVOS detectados (não presentes no manifesto):${NC}"
    head -n 20 "$OUTPUT_DIFF.added"
    if [ $(wc -l < "$OUTPUT_DIFF.added") -gt 20 ]; then
        echo "... (total: $(wc -l < "$OUTPUT_DIFF.added"))"
    fi
    echo "Lista completa em: $OUTPUT_DIFF.added"
else
    echo "Nenhum arquivo novo detectado nos caminhos monitorados."
    rm -f "$OUTPUT_DIFF.added"
fi

rm -f /tmp/manifest_files.txt /tmp/current_files.txt
