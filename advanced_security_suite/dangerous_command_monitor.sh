#!/bin/bash
#
# 7. Monitor de Comandos Perigosos
# Autor: Jules (AI Agent)
# Descrição: Varre históricos de shell e logs por comandos arriscados.

DANGEROUS_PATTERNS="(rm -rf /|curl.*bash|wget.*sh|nc -e|mkfifo|dd if=/dev/zero|:(){ :|:& };:)"
SEARCH_DIRS="/home /root"

echo "[*] Procurando comandos perigosos em históricos (.bash_history, .zsh_history)..."

for dir in $SEARCH_DIRS; do
    # Procura arquivos de historico
    find "$dir" -maxdepth 2 -name ".*history" 2>/dev/null | while read histfile; do
        if grep -Eq "$DANGEROUS_PATTERNS" "$histfile"; then
             echo "[!] ALERTA: Comando perigoso encontrado em $histfile:"
             grep -E --color=always "$DANGEROUS_PATTERNS" "$histfile" | tail -n 5
        fi
    done
done

# Checar processos atuais tambem (cmdline)
echo "[*] Verificando processos atuais..."
ps -eo pid,user,cmd | grep -E "$DANGEROUS_PATTERNS" | grep -v grep | while read line; do
     echo "[!] ALERTA: Processo perigoso em execução: $line"
done

echo "[OK] Varredura de comandos concluída."
