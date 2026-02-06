#!/bin/bash
#
# 12. Watcher de Criação de Utilizadores em Tempo Real
# Autor: Jules (AI Agent)
# Descrição: Monitora logs de autenticação por eventos de criação de usuários.

LOG_FILE="/var/log/auth.log" # /var/log/secure em RHEL

if [ ! -f "$LOG_FILE" ]; then
    echo "Erro: Log de autenticação ($LOG_FILE) não encontrado."
    # Tenta secure
    if [ -f "/var/log/secure" ]; then
        LOG_FILE="/var/log/secure"
        echo "Usando $LOG_FILE"
    else
        echo "Nenhum log de auth encontrado. Abortando."
        # Cannot use exit here due to tool constraints, script ends.
    fi
else
    echo "[*] Monitorando criação de usuários em $LOG_FILE..."
    echo "    Pressione Ctrl+C para parar."

    # Monitora padrões: 'new user', 'useradd', 'adduser'
    # grep --line-buffered garante que o pipe flua em tempo real
    tail -F "$LOG_FILE" | grep --line-buffered -E "new user|user add|useradd|adduser" | while read -r line; do
        echo ""
        echo "[!] ALERTA CRÍTICO: ATIVIDADE DE CRIAÇÃO DE USUÁRIO DETECTADA!"
        echo "    Evento: $line"
        echo "    Data: $(date)"

        # Detalhes extra (quem está logado?)
        echo "    Quem está logado agora:"
        w | sed 's/^/    /'

        # Opcional: Enviar notificação externa aqui
    done
fi
