#!/bin/bash
#
# hardening_agente_backup.sh
#
# Descrição: Aplica configurações de hardening para o usuário de backup.
# Reduz a superfície de ataque caso as credenciais de backup sejam comprometidas.
#
# Uso: ./hardening_agente_backup.sh <usuario_backup>
#
# Exemplo: ./hardening_agente_backup.sh backupuser
#

USER="$1"

if [[ -z "$USER" ]]; then
    echo "Uso: $0 <usuario_backup>"
    exit 1
fi

if ! id "$USER" &>/dev/null; then
    echo "Erro: Usuário $USER não existe."
    exit 1
fi

echo "[*] Iniciando Hardening para usuário: $USER"

# 1. Definir Shell Restrito (rbash) se disponível
RBASH=$(command -v rbash)
if [[ -n "$RBASH" ]]; then
    echo "[*] Alterando shell para rbash (Restricted Bash)..."
    usermod -s "$RBASH" "$USER"
else
    echo "[-] rbash não encontrado. Recomendado instalar para restringir comandos."
fi

# 2. Bloquear login direto por senha (apenas chaves SSH)
echo "[*] Bloqueando senha (apenas chave SSH permitida)..."
passwd -l "$USER"

# 3. Configurar expiração de senha (inativação de conta nunca usada)
echo "[*] Configurando inativação de conta após 30 dias inativa..."
chage -I 30 "$USER"

# 4. Verificar diretório home seguro
HOMEDIR=$(eval echo "~$USER")
echo "[*] Ajustando permissões do Home ($HOMEDIR) para 700..."
chmod 700 "$HOMEDIR"

# 5. SSH: Sugestão de configuração (não altera sshd_config automaticamente por risco)
echo "[*] RECOMENDAÇÃO SSH: Adicione o seguinte ao seu /etc/ssh/sshd_config:"
echo ""
echo "Match User $USER"
echo "    AllowAgentForwarding no"
echo "    AllowTcpForwarding no"
echo "    X11Forwarding no"
echo "    PermitTTY no"
# echo "    ForceCommand /usr/local/bin/backup-only-script.sh"
echo ""

echo "[+] Hardening básico aplicado para $USER."
