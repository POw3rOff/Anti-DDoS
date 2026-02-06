#!/bin/bash

# Wrapper para o Detector de Anomalias em Python
# Garante que as dependências estejam presentes e executa o script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/log_anomaly_detector.py"

# Cores
RED='[0;31m'
GREEN='[0;32m'
NC='[0m' # No Color

# Verificar root se necessário (opcional, dependendo do log)
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Aviso: Você não é root. Pode não conseguir ler logs como /var/log/auth.log${NC}"
fi

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erro: Python 3 não encontrado. Instale-o para continuar.${NC}"
    echo "sudo apt update && sudo apt install python3"
    exit 1
fi

# Exibir ajuda se nenhum argumento for passado
if [ $# -eq 0 ]; then
    python3 "$PYTHON_SCRIPT" --help
    exit 0
fi

# Executar o script Python passando todos os argumentos
python3 "$PYTHON_SCRIPT" "$@"
