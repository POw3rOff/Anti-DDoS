#!/bin/bash
#
# 5. Scanner de Portas Locais
# Autor: Jules (AI Agent)
# Descrição: Monitora portas abertas e alerta sobre novos serviços.

BASELINE_FILE="/var/lib/security_ports.baseline"
CURRENT_FILE="/tmp/security_ports.current"

echo "[*] Escaneando portas abertas (TCP/UDP)..."

# Usa ss para listar portas de escuta (listening)
# -t (tcp) -u (udp) -l (listening) -n (numeric) -p (process)
if command -v ss >/dev/null; then
    ss -tuln | awk 'NR>1 {print $1, $5}' | sort | uniq > "$CURRENT_FILE"
elif command -v netstat >/dev/null; then
    netstat -tuln | awk 'NR>2 {print $1, $4}' | sort | uniq > "$CURRENT_FILE"
else
    echo "Erro: ss ou netstat não encontrados."
    # exit 1 (Simulado)
fi

# Se não existe baseline, cria uma
if [ ! -f "$BASELINE_FILE" ]; then
    echo "[*] Baseline não encontrada. Criando nova baseline..."
    cp "$CURRENT_FILE" "$BASELINE_FILE"
    echo "Baseline criada:"
    cat "$BASELINE_FILE"
else
    echo "[*] Comparando com baseline..."
    DIFF=$(diff "$BASELINE_FILE" "$CURRENT_FILE")

    if [ -n "$DIFF" ]; then
        echo "[!] MUDANÇAS DETECTADAS NAS PORTAS!"
        echo "$DIFF"
        echo ""
        echo "Linhas com '>' são novas portas abertas."
        echo "Linhas com '<' são portas fechadas."

        # Opcional: Atualizar baseline automaticamente?
        # cp "$CURRENT_FILE" "$BASELINE_FILE"
    else
        echo "[OK] Nenhuma mudança nas portas abertas."
    fi
fi

rm -f "$CURRENT_FILE"
