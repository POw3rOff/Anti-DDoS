#!/bin/bash
#
# destino_readonly.sh
#
# Descrição: Aplica o atributo de imutabilidade (chattr +i) em arquivos de backup.
# Protege contra exclusão acidental ou modificação maliciosa (ransomware).
# Pode bloquear (lock) ou desbloquear (unlock) arquivos.
#
# Uso: ./destino_readonly.sh <lock|unlock> <arquivo_ou_diretorio>
#
# Exemplo: ./destino_readonly.sh lock /backup/diario
#

ACTION="$1"
TARGET="$2"

if [[ -z "$ACTION" || -z "$TARGET" ]]; then
    echo "Uso: $0 <lock|unlock> <arquivo_ou_diretorio>"
    exit 1
fi

if [[ ! -e "$TARGET" ]]; then
    echo "Erro: Alvo $TARGET não encontrado."
    exit 1
fi

# Verifica se é root
if [[ $EUID -ne 0 ]]; then
   echo "Erro: Este script precisa ser executado como root para alterar atributos de arquivo."
   exit 1
fi

echo "[*] Processando: $ACTION em $TARGET"

if [[ "$ACTION" == "lock" ]]; then
    echo "    -> Aplicando atributo +i (imutável)..."
    chattr -R +i "$TARGET"
    if [[ $? -eq 0 ]]; then
        echo "[+] Arquivos bloqueados com sucesso."
    else
        echo "[-] Falha ao bloquear arquivos. Verifique suporte do sistema de arquivos (ext4/xfs)."
    fi

elif [[ "$ACTION" == "unlock" ]]; then
    echo "    -> Removendo atributo +i (permitir escrita)..."
    chattr -R -i "$TARGET"
    if [[ $? -eq 0 ]]; then
        echo "[+] Arquivos desbloqueados com sucesso."
    else
        echo "[-] Falha ao desbloquear arquivos."
    fi

else
    echo "Erro: Ação desconhecida. Use lock ou unlock."
    exit 1
fi

# Mostra status
echo "[*] Verificando atributos atuais (lsattr):"
if [[ -d "$TARGET" ]]; then
    lsattr -d "$TARGET"
else
    lsattr "$TARGET"
fi
