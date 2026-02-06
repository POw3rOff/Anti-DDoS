#!/bin/bash
#
# 6. Detetor de Escalada de Privilégios
# Autor: Jules (AI Agent)
# Descrição: Analisa logs em busca de escaladas suspeitas.

LOG_AUTH="/var/log/auth.log" # /var/log/secure em RHEL
BASELINE_SUID="/var/lib/suid_baseline.db"

echo "[*] Verificando logs de autenticação..."

# 1. Uso excessivo de sudo ou falhas de root
if [ -f "$LOG_AUTH" ]; then
    echo "    Falhas de Sudo/Root recentes:"
    grep -E "sudo:.*COMMAND|FAILED su" "$LOG_AUTH" | tail -n 10

    # Detectar 'sudo bash' ou 'sudo su' (Pattern matching seguro para bash session)
    # Procurando por shells comuns executados via sudo
    if grep -qE "sudo:.*COMMAND=.*(ash|zsh|su)" "$LOG_AUTH"; then
        echo "[!] AVISO: Uso de Shell via Sudo detectado!"
        grep -E "sudo:.*COMMAND=.*(ash|zsh|su)" "$LOG_AUTH" | tail -n 5
    fi
else
    echo "    Log de autenticação não encontrado."
fi

# 2. Monitoramento de novos binários SUID (Diferencial)
echo "[*] Checando novos arquivos SUID..."
CURRENT_SUID="/tmp/suid_current.list"
find / -perm -4000 -type f 2>/dev/null | sort > "$CURRENT_SUID"

if [ ! -f "$BASELINE_SUID" ]; then
    echo "    Criando baseline SUID..."
    cp "$CURRENT_SUID" "$BASELINE_SUID"
else
    DIFF=$(diff "$BASELINE_SUID" "$CURRENT_SUID" | grep ">")
    if [ -n "$DIFF" ]; then
        echo "[!] ALERTA: Novos arquivos SUID encontrados!"
        echo "$DIFF"
    else
        echo "[OK] Nenhum novo SUID detectado."
    fi
fi
rm -f "$CURRENT_SUID"

echo "[OK] Verificação PrivEsc concluída."
