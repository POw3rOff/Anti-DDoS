#!/bin/bash
#
# deteccao_ransomware_backup.sh
#
# Descrição: Verifica diretórios em busca de sinais de ransomware antes do backup.
# Procura por extensões de arquivos conhecidas por ransomware e notas de resgate.
#
# Uso: ./deteccao_ransomware_backup.sh <diretorio_para_verificar>
#
# Exemplo: ./deteccao_ransomware_backup.sh /var/www/html
#

DIR="$1"

if [[ -z "$DIR" ]]; then
    echo "Uso: $0 <diretorio_para_verificar>"
    exit 1
fi

echo "[*] Iniciando varredura anti-ransomware em: $DIR"

# Lista de extensões suspeitas (Exemplos comuns, lista deve ser atualizada)
SUSPICIOUS_EXT=("wannacry" "encrypted" "wnry" "locky" "crypt" "crypto" "darkness" "enc" "ransom" "locked")
# Lista de padrões de notas de resgate
RANSOM_NOTES=("*DECRYPT*" "*HOW_TO_RECOVER*" "*RESTORE_FILES*" "*README_FOR_DECRYPT*")

FOUND_THREATS=0

# 1. Verificar extensões
echo "[*] Verificando extensões de arquivos suspeitas..."
for ext in "${SUSPICIOUS_EXT[@]}"; do
    COUNT=$(find "$DIR" -type f -name "*.$ext" | wc -l)
    if [[ "$COUNT" -gt 0 ]]; then
        echo "[!] ALERTA: Encontrados $COUNT arquivos com extensão suspeita .$ext"
        find "$DIR" -type f -name "*.$ext" | head -n 5
        FOUND_THREATS=$((FOUND_THREATS + 1))
    fi
done

# 2. Verificar notas de resgate
echo "[*] Verificando notas de resgate..."
for note in "${RANSOM_NOTES[@]}"; do
    COUNT=$(find "$DIR" -type f -name "$note" | wc -l)
    if [[ "$COUNT" -gt 0 ]]; then
        echo "[!] ALERTA: Encontrados $COUNT arquivos parecidos com notas de resgate ($note)"
        find "$DIR" -type f -name "$note" | head -n 5
        FOUND_THREATS=$((FOUND_THREATS + 1))
    fi
done

# 3. Verificação de Canário (opcional, se houver arquivo canário configurado)
CANARY_FILE="$DIR/canary_file.docx"
if [[ -f "$CANARY_FILE" ]]; then
    # Verifica integridade simples (se foi modificado recentemente ou tipo de arquivo mudou)
    # Aqui apenas checamos se ainda é um arquivo legível ou se mudou drasticamente
    echo "[*] Verificando arquivo canário..."
    # Lógica simplificada: se canário foi modificado nos últimos 60 minutos e não fomos nós
    # (Isso requer mais contexto, deixaremos como placeholder)
fi

if [[ "$FOUND_THREATS" -gt 0 ]]; then
    echo "[-]"
    echo "[-] AMEAÇA DETECTADA! O backup deve ser abortado para evitar contaminação."
    echo "[-] Verifique os alertas acima."
    exit 1
else
    echo "[+] Nenhum indicador óbvio de ransomware detectado."
    exit 0
fi
