#!/bin/bash
#
# timeline_restauro.sh
#
# Analisa metadados de arquivos para criar uma linha do tempo de modificações.
# Ajuda a identificar quando a invasão ocorreu e qual o backup seguro ("Last Known Good").
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -u

SEARCH_DIR="${1:-/}" # Diretório base, padrão raiz (pode demorar)
DAYS="${2:-7}"       # Quantos dias para trás analisar
OUTPUT_FILE="timeline_$(date +%Y%m%d_%H%M%S).csv"

echo "Gerando timeline para $SEARCH_DIR (últimos $DAYS dias)..."
echo "Saída em: $OUTPUT_FILE"

# Cabeçalho CSV
echo "Timestamp,Type,File,User,Permissions" > "$OUTPUT_FILE"

# Find command
# -mtime -$DAYS : modificados nos últimos N dias
# -printf : formatação customizada para CSV
# %Ty-%Tm-%Td %TH:%TM:%TS : Data YYYY-MM-DD HH:MM:SS
# %y : Tipo (f=file, d=dir)
# %p : Caminho
# %u : Usuário
# %M : Permissões

# Exclui /proc, /sys, /dev, /run para evitar erros e loop
find "$SEARCH_DIR" -mount \
    \( -path /proc -o -path /sys -o -path /dev -o -path /run -o -path /tmp \) -prune \
    -o -mtime -"$DAYS" \
    -printf "%Ty-%Tm-%Td %TH:%TM:%TS,%y,%p,%u,%M\n" >> "$OUTPUT_FILE"

echo "Ordenando resultados por data..."
# Sort pelo primeiro campo (Timestamp)
sort -r "$OUTPUT_FILE" -o "$OUTPUT_FILE.sorted"
mv "$OUTPUT_FILE.sorted" "$OUTPUT_FILE"

echo "Análise concluída."
echo "---------------------------------------------------"
echo "Top 10 arquivos modificados recentemente:"
head -n 10 "$OUTPUT_FILE"
echo "---------------------------------------------------"
echo "DICA: Busque por arquivos com extensões executáveis em diretórios web:"
grep -E "\.(php|sh|pl|py|jsp|asp|exe)$" "$OUTPUT_FILE" | grep -v "/usr/lib" | head -n 20
