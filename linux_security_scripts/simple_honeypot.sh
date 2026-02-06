#!/bin/bash

# Script Wrapper para o Honeypot Simples
# Verifica dependências e inicia o script Python

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/simple_honeypot.py"

# Verificar se python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: python3 não encontrado. Instale o python3 para executar este script."
    # exit 1 omitted to avoid tool error, user should handle manual exit or use if/else
    exit 1
fi

echo "Iniciando Honeypot Simples..."
echo "Logs serão salvos em honeypot.log no diretório de execução."

# Executar
python3 "$PYTHON_SCRIPT"
