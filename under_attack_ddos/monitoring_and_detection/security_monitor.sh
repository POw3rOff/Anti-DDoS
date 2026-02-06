#!/bin/bash

# Script de Monitoramento de Segurança e Integridade (FIM & Log Check)
# @versão 1.0.0
# @autor AI Assistant

# Configurações
DB_FILE="/var/lib/security_monitor.db"
LOG_FILE="/var/log/security_monitor.log"
EMAIL_ALERT="" # Deixe vazio para não enviar email, ou coloque seu email ex: admin@exemplo.com

# Arquivos Críticos para Monitorar Integridade (FIM)
CRITICAL_FILES=(
    "/etc/passwd"
    "/etc/shadow"
    "/etc/group"
    "/etc/ssh/sshd_config"
    "/etc/sudoers"
    "/etc/crontab"
)

# Cores
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
NC="\033[0m"

msg() {
    local type=$1
    local text=$2
    local color=$NC

    if [ "$type" == "RED" ]; then color=$RED;
    elif [ "$type" == "GREEN" ]; then color=$GREEN;
    elif [ "$type" == "YELLOW" ]; then color=$YELLOW;
    fi

    echo -e "${color}[$type]${NC} $text"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$type] $text" >> "$LOG_FILE"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        msg "RED" "Execute como root."
        return 1
    fi
    return 0
}

# ----------------------------------------------------------------------
# 1. Monitoramento de Integridade de Arquivos (FIM)
# ----------------------------------------------------------------------
check_file_integrity() {
    msg "GREEN" "Iniciando verificação de integridade de arquivos..."

    local changes_found=0
    local db_exists=0

    # Verifica se o banco de dados de hashes existe
    if [ -f "$DB_FILE" ]; then
        db_exists=1
    else
        msg "YELLOW" "Base de dados de integridade não encontrada. Criando nova base..."
        touch "$DB_FILE"
    fi

    for file in "${CRITICAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            # Calcula hash atual
            current_hash=$(sha256sum "$file" | awk '{print $1}')

            if [ $db_exists -eq 1 ]; then
                # Busca hash salvo
                saved_entry=$(grep "$file" "$DB_FILE")
                saved_hash=$(echo "$saved_entry" | awk '{print $2}')

                if [ -z "$saved_hash" ]; then
                    msg "YELLOW" "Novo arquivo monitorado: $file"
                    echo "$file $current_hash" >> "$DB_FILE"
                elif [ "$current_hash" != "$saved_hash" ]; then
                    msg "RED" "ALERTA: Arquivo modificado! $file"
                    msg "RED" "Hash Anterior: $saved_hash"
                    msg "RED" "Hash Atual:    $current_hash"
                    changes_found=1
                else
                    msg "GREEN" "OK: $file intacto."
                fi
            else
                # Apenas popula o DB inicial
                echo "$file $current_hash" >> "$DB_FILE"
            fi
        fi
    done

    if [ $changes_found -eq 1 ]; then
        alert "Alterações críticas detectadas em arquivos do sistema!"
    fi
}

# ----------------------------------------------------------------------
# 2. Verificação de Logs (Brute Force Check)
# ----------------------------------------------------------------------
check_auth_logs() {
    msg "GREEN" "Verificando logs de autenticação..."

    local log_path="/var/log/auth.log"
    if [ ! -f "$log_path" ]; then
        log_path="/var/log/secure" # RedHat/CentOS
    fi

    if [ -f "$log_path" ]; then
        # Conta falhas nas últimas 1000 linhas para ser rápido
        local failures=$(tail -n 1000 "$log_path" | grep -c -E "Failed password|authentication failure")

        msg "GREEN" "Tentativas de falha recentes (amostra): $failures"

        if [ "$failures" -gt 50 ]; then
            msg "RED" "ALERTA: Alto número de falhas de login detectadas ($failures)!"
            alert "Possível ataque de Brute Force em andamento. Verifique $log_path"
        fi
    else
        msg "YELLOW" "Log de autenticação não encontrado."
    fi
}

# ----------------------------------------------------------------------
# 3. Verificação de Processos Suspeitos (Básico)
# ----------------------------------------------------------------------
check_processes() {
    msg "GREEN" "Verificando processos..."

    # Processos consumindo muito CPU (>80%)
    high_cpu=$(ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 2 | tail -n 1)
    cpu_usage=$(echo "$high_cpu" | awk '{print $5}' | cut -d. -f1)

    # Verifica se cpu_usage é um número antes de comparar
    if [[ "$cpu_usage" =~ ^[0-9]+$ ]] && [ "$cpu_usage" -gt 80 ]; then
        msg "YELLOW" "Processo com alto uso de CPU detectado:"
        msg "YELLOW" "$high_cpu"
    fi
}

# ----------------------------------------------------------------------
# Função de Alerta
# ----------------------------------------------------------------------
alert() {
    local message=$1
    if [ -n "$EMAIL_ALERT" ]; then
        # Verifica se o comando mail existe
        if command -v mail &> /dev/null; then
            echo "$message" | mail -s "[SECURITY ALERT] Servidor $(hostname)" "$EMAIL_ALERT"
        else
             msg "RED" "Alerta não enviado por e-mail (comando 'mail' não encontrado): $message"
        fi
    else
         msg "RED" "Alerta (Email não configurado): $message"
    fi
}

# ----------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------
main() {
    check_root || return 1

    echo "=================================================="
    echo " Security Monitor - $(date)"
    echo "=================================================="

    check_file_integrity
    echo "--------------------------------------------------"
    check_auth_logs
    echo "--------------------------------------------------"
    check_processes

    echo "=================================================="
    echo "Monitoramento concluído."
}

main
