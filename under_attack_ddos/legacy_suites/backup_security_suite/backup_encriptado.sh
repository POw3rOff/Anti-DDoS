#!/bin/bash
#
# backup_encriptado.sh
#
# Descrição: Realiza a encriptação de arquivos de backup utilizando GPG.
# Este script assegura que os dados de backup permaneçam confidenciais em repouso.
#
# Uso: ./backup_encriptado.sh <arquivo_ou_diretorio_origem> <arquivo_destino> [destinatario_gpg]
#
# Exemplo: ./backup_encriptado.sh /var/www/html /backup/site_backup.tar.gz.gpg admin@example.com
#

SOURCE="$1"
DEST="$2"
RECIPIENT="$3"

if [[ -z "$SOURCE" || -z "$DEST" ]]; then
    echo "Uso: $0 <arquivo_ou_diretorio_origem> <arquivo_destino> [destinatario_gpg]"
    echo "Se [destinatario_gpg] não for fornecido, será usada encriptação simétrica (senha)."
    exit 1
fi

if [[ ! -e "$SOURCE" ]]; then
    echo "Erro: Origem \"$SOURCE\" não encontrada."
    exit 1
fi

# Cria o diretório de destino se não existir
mkdir -p "$(dirname "$DEST")"

echo "[*] Iniciando processo de backup encriptado..."
echo "[*] Origem: $SOURCE"
echo "[*] Destino: $DEST"

if [[ -n "$RECIPIENT" ]]; then
    echo "[*] Modo: Encriptação Assimétrica (Chave Pública para $RECIPIENT)"
    # Comprime e encripta em um pipe
    tar -cf - "$SOURCE" | gpg --encrypt --recipient "$RECIPIENT" --output "$DEST"
else
    echo "[*] Modo: Encriptação Simétrica (Senha)"
    echo "[!] Você será solicitado a digitar uma senha para a encriptação."
    # Comprime e encripta em um pipe
    tar -cf - "$SOURCE" | gpg --symmetric --cipher-algo AES256 --output "$DEST"
fi

if [[ $? -eq 0 ]]; then
    echo "[+] Backup encriptado criado com sucesso: $DEST"
else
    echo "[-] Falha ao criar backup encriptado."
    exit 1
fi
