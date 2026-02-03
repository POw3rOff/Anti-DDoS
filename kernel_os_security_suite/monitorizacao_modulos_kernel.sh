#!/bin/bash

# Script: monitorizacao_modulos_kernel.sh
# Descrição: Monitora módulos do kernel carregados e deteta alterações.
# Autor: Jules (Agente de IA)

SNAPSHOT_DIR="/var/log/kernel_monitor"
SNAPSHOT_FILE="$SNAPSHOT_DIR/modules_snapshot.txt"
CURRENT_FILE="$SNAPSHOT_DIR/modules_current.txt"
SUSPICIOUS_MODULES="diamorphine|lkm|rootkit|adore|knark"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p "$SNAPSHOT_DIR"

echo -e "${YELLOW}[*] Verificando módulos do kernel...${NC}"

# Captura estado atual (apenas nomes para facilitar diff)
lsmod | awk '{print $1}' | sort > "$CURRENT_FILE"

# Verifica módulos suspeitos conhecidos (por nome)
echo -e "${YELLOW}[*] Buscando módulos com nomes suspeitos...${NC}"
if grep -Eiq "$SUSPICIOUS_MODULES" "$CURRENT_FILE"; then
    echo -e "${RED}[!] ALERTA CRÍTICO: Módulo com nome suspeito encontrado!${NC}"
    grep -Eiq "$SUSPICIOUS_MODULES" "$CURRENT_FILE"
else
    echo -e "${GREEN}[OK] Nenhum módulo com nome obviamente malicioso encontrado.${NC}"
fi

# Comparação com snapshot anterior
if [ -f "$SNAPSHOT_FILE" ]; then
    echo -e "${YELLOW}[*] Comparando com snapshot anterior...${NC}"
    CHANGES=$(diff "$SNAPSHOT_FILE" "$CURRENT_FILE")

    if [ -z "$CHANGES" ]; then
        echo -e "${GREEN}[OK] Nenhuma alteração na lista de módulos carregados.${NC}"
    else
        echo -e "${YELLOW}[!] Alterações detectadas nos módulos carregados:${NC}"
        echo "$CHANGES" | grep ">" | sed 's/>/  [+] Adicionado:/'
        echo "$CHANGES" | grep "<" | sed 's/</  [-] Removido:/'
    fi
else
    echo -e "${YELLOW}[INFO] Nenhum snapshot anterior encontrado. Criando base inicial.${NC}"
fi

# Atualiza snapshot
cp "$CURRENT_FILE" "$SNAPSHOT_FILE"
echo -e "${GREEN}[*] Snapshot atualizado em $SNAPSHOT_FILE${NC}"
