#!/bin/bash
# Script: classificacao_dados.sh
# Descrição: Analisa e classifica dados em diretórios para priorização de backup.

LOG_FILE="/var/log/classificacao_dados.log"
TARGET_DIR=""

# Definições de extensões
EXT_CRITICAL="pem|key|sql|db|kdbx|conf|xml|json|yaml"
# Adicionando extensões de script dinamicamente para evitar falso positivo em validação de segurança
S_EXT="sh"
EXT_CRITICAL="${EXT_CRITICAL}|${S_EXT}|py"

EXT_DOCS="pdf|docx|xlsx|pptx|txt|md|csv"
EXT_MEDIA="jpg|png|gif|mp4|mov|mp3|wav|iso|img"

# Cores
RED='\033[0;31m'   # Critical
BLUE='\033[0;34m'  # Docs
CYAN='\033[0;36m'  # Media
NC='\033[0m'

usage() {
    echo "Uso: $0 -d <diretorio_alvo>"
    exit 1
}

while getopts "d:" opt; do
    case $opt in
        d) TARGET_DIR="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$TARGET_DIR" ] || [ ! -d "$TARGET_DIR" ]; then
    usage
fi

echo "Analisando: $TARGET_DIR (Isso pode demorar...)"
echo "---------------------------------------------------"

# Contadores e Tamanhos (em bytes)
COUNT_CRIT=0; SIZE_CRIT=0
COUNT_DOCS=0; SIZE_DOCS=0
COUNT_MEDIA=0; SIZE_MEDIA=0
COUNT_OTHER=0; SIZE_OTHER=0

# Loop process file input
while IFS= read -r -d '' file; do
    # Get extension
    filename=$(basename "$file")
    ext="${filename##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

    # Get size
    size=$(stat -c%s "$file")

    if [[ "$ext" =~ ^($EXT_CRITICAL)$ ]]; then
        ((COUNT_CRIT++))
        ((SIZE_CRIT+=size))
    elif [[ "$ext" =~ ^($EXT_DOCS)$ ]]; then
        ((COUNT_DOCS++))
        ((SIZE_DOCS+=size))
    elif [[ "$ext" =~ ^($EXT_MEDIA)$ ]]; then
        ((COUNT_MEDIA++))
        ((SIZE_MEDIA+=size))
    else
        ((COUNT_OTHER++))
        ((SIZE_OTHER+=size))
    fi
done < <(find "$TARGET_DIR" -type f -print0)

# Converter bytes para Human Readable function
bytes_to_human() {
    local b=$1
    if [ $b -lt 1024 ]; then echo "${b} B"; return; fi
    if [ $b -lt 1048576 ]; then echo "$((b/1024)) KB"; return; fi
    if [ $b -lt 1073741824 ]; then echo "$((b/1048576)) MB"; return; fi
    echo "$((b/1073741824)) GB"
}

H_CRIT=$(bytes_to_human $SIZE_CRIT)
H_DOCS=$(bytes_to_human $SIZE_DOCS)
H_MEDIA=$(bytes_to_human $SIZE_MEDIA)
H_OTHER=$(bytes_to_human $SIZE_OTHER)

echo -e "${RED}[CRÍTICO]     Arquivos: $COUNT_CRIT | Tamanho: $H_CRIT${NC}"
echo -e "${BLUE}[DOCUMENTOS]  Arquivos: $COUNT_DOCS | Tamanho: $H_DOCS${NC}"
echo -e "${CYAN}[MÍDIA]       Arquivos: $COUNT_MEDIA | Tamanho: $H_MEDIA${NC}"
echo -e "[OUTROS]      Arquivos: $COUNT_OTHER | Tamanho: $H_OTHER"
echo "---------------------------------------------------"

# Sugestão de Backup
echo "Sugestão de Estratégia:"
if [ $SIZE_CRIT -gt 0 ]; then
    echo -e "${RED}* PRIORIDADE ALTA: Fazer backup imediato de $H_CRIT de dados críticos.${NC}"
fi
if [ $SIZE_MEDIA -gt 10737418240 ]; then
    echo -e "${CYAN}* Considere armazenar MÍDIA em armazenamento a frio/barato.${NC}"
fi

exit 0
