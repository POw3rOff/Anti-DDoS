#!/bin/bash
#
# assinatura_backup.sh
#
# Descrição: Gera e verifica assinaturas digitais para arquivos de backup.
# Garante a autenticidade e integridade dos dados, confirmando que não foram alterados
# e foram gerados por uma fonte confiável.
#
# Uso:
#   Assinar: ./assinatura_backup.sh sign <arquivo_backup> [email_chave_gpg]
#   Verificar: ./assinatura_backup.sh verify <arquivo_backup> [arquivo_assinatura]
#

MODE="$1"
FILE="$2"
PARAM3="$3"

if [[ -z "$MODE" || -z "$FILE" ]]; then
    echo "Uso: $0 <sign|verify> <arquivo> [parametro_extra]"
    exit 1
fi

if [[ ! -f "$FILE" ]]; then
    echo "Erro: Arquivo $FILE não encontrado."
    exit 1
fi

if [[ "$MODE" == "sign" ]]; then
    GPG_USER="${PARAM3}"
    SIG_FILE="${FILE}.sig"

    echo "[*] Gerando assinatura digital para: $FILE"

    CMD="gpg --output \"$SIG_FILE\" --detach-sig \"$FILE\""

    if [[ -n "$GPG_USER" ]]; then
        echo "    -> Usando chave de: $GPG_USER"
        CMD="$CMD --local-user \"$GPG_USER\""
    else
        echo "    -> Usando chave padrão do usuário atual."
    fi

    eval "$CMD"

    if [[ $? -eq 0 ]]; then
        echo "[+] Assinatura criada: $SIG_FILE"
        echo "[*] Gerando hash SHA256 para verificação rápida..."
        sha256sum "$FILE" > "${FILE}.sha256"
        echo "[+] Hash salvo em: ${FILE}.sha256"
    else
        echo "[-] Erro ao assinar arquivo."
        exit 1
    fi

elif [[ "$MODE" == "verify" ]]; then
    SIG_FILE="${PARAM3:-${FILE}.sig}"

    if [[ ! -f "$SIG_FILE" ]]; then
        echo "Erro: Arquivo de assinatura $SIG_FILE não encontrado."
        exit 1
    fi

    echo "[*] Verificando assinatura de $FILE usando $SIG_FILE..."
    gpg --verify "$SIG_FILE" "$FILE"

    if [[ $? -eq 0 ]]; then
        echo "[+] VERIFICAÇÃO BEM-SUCEDIDA: A assinatura é válida e o arquivo está íntegro."
    else
        echo "[-] FALHA NA VERIFICAÇÃO: A assinatura é inválida ou o arquivo foi modificado."
        exit 1
    fi

else
    echo "Modo desconhecido. Use sign ou verify."
    exit 1
fi
