#!/bin/bash
# detecao_log_tampering.sh
# Detecta possível truncamento ou alteração suspeita em arquivos de log
# Autor: Jules (Assistant)

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

STATE_DIR="/var/lib/log_security"
STATE_FILE="$STATE_DIR/log_state.db"
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR" # Secure the directory

LOGS=("/var/log/auth.log" "/var/log/syslog" "/var/log/messages" "/var/log/kern.log" "/var/log/audit/audit.log")

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Erro: Execute como root.${NC}"
        exit 1
    fi
}

init_db() {
    echo -e "${YELLOW}[*] Inicializando base de dados de integridade...${NC}"
    > "$STATE_FILE"
    chmod 600 "$STATE_FILE"
    for log in "${LOGS[@]}"; do
        if [ -f "$log" ]; then
            stat -c "%n %i %s" "$log" >> "$STATE_FILE"
        fi
    done
    echo -e "${GREEN}Base de dados atualizada.${NC}"
}

check_integrity() {
    echo -e "${YELLOW}[*] Verificando integridade dos logs...${NC}"

    if [ ! -f "$STATE_FILE" ]; then
        echo "Base de dados não encontrada. Inicializando..."
        init_db
        return
    fi

    # Use mktemp for secure temporary file
    current_state_tmp=$(mktemp)

    ALERTS=0

    while read -r name inode size; do
        if [ -f "$name" ]; then
            curr_inode=$(stat -c "%i" "$name")
            curr_size=$(stat -c "%s" "$name")

            if [ "$curr_inode" != "$inode" ]; then
                # Inode mudou. Logrotate?
                echo -e "${YELLOW}[INFO] $name: Inode mudou (provável rotação). $inode -> $curr_inode${NC}"
            else
                # Inode igual. Tamanho diminuiu?
                if [ "$curr_size" -lt "$size" ]; then
                    echo -e "${RED}[ALERTA CRÍTICO] $name: Tamanho DIMINUIU sem mudança de Inode! (Truncamento suspeito)${NC}"
                    echo "  Anterior: $size bytes | Atual: $curr_size bytes"
                    ALERTS=1
                fi
            fi

            # Atualiza estado para proxima execucao
            echo "$name $curr_inode $curr_size" >> "$current_state_tmp"
        else
            echo -e "${YELLOW}[INFO] $name: Arquivo monitorado desapareceu.${NC}"
        fi
    done < "$STATE_FILE"

    mv "$current_state_tmp" "$STATE_FILE"
    chmod 600 "$STATE_FILE"

    if [ "$ALERTS" -eq 1 ]; then
        echo -e "${RED}Verificação concluída com ALERTAS.${NC}"
        exit 1
    else
        echo -e "${GREEN}Verificação concluída. Base de dados atualizada.${NC}"
        exit 0
    fi
}

main() {
    check_root
    if [ "$1" == "--init" ]; then
        init_db
    else
        check_integrity
    fi
}

main "$@"
