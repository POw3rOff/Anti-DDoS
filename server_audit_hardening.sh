#!/bin/bash

# Script de Auditoria e Hardening de Servidor Linux
# Focado em Segurança Interna, Permissões e Configurações de Serviços
# @versão 1.0.0
# @autor AI Assistant

# Cores para output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Arquivo de Log
LOG_FILE="/var/log/security_audit.log"

# Função para mensagens
msg() {
    local type=$1
    local text=$2
    local color=$NC

    case $type in
        INFO) color=$BLUE ;;
        OK) color=$GREEN ;;
        WARN) color=$YELLOW ;;
        ERROR) color=$RED ;;
    esac

    echo -e "${color}[$type]${NC} $text"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$type] $text" >> "$LOG_FILE"
}

# Banner
banner() {
    echo -e "${BLUE}"
    echo "#########################################################"
    echo "#    Script de Auditoria e Hardening de Segurança       #"
    echo "#             Cyber Gamers Security                     #"
    echo "#########################################################"
    echo -e "${NC}"
}

# Verificar Root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        msg "ERROR" "Este script precisa ser executado como root."
        return 1
    fi
    return 0
}

# ----------------------------------------------------------------------
# 1. Auditoria de Contas e Usuários
# ----------------------------------------------------------------------
audit_users() {
    msg "INFO" "Iniciando auditoria de usuários..."

    # Verificar usuários com UID 0 (além do root)
    msg "INFO" "Verificando usuários com UID 0..."
    uid0_users=$(awk -F: '($3 == 0) {print $1}' /etc/passwd)
    for user in $uid0_users; do
        if [ "$user" != "root" ]; then
            msg "WARN" "Usuário não-root com UID 0 encontrado: $user"
        else
            msg "OK" "Usuário root verificado corretamente."
        fi
    done

    # Verificar contas com senha vazia
    msg "INFO" "Verificando contas com senha vazia..."
    empty_pass=$(awk -F: '($2 == "") {print $1}' /etc/shadow)
    if [ -n "$empty_pass" ]; then
        msg "WARN" "Contas com senha vazia encontradas: $empty_pass"
        msg "INFO" "Recomendação: Bloquear estas contas ou definir senhas."
    else
        msg "OK" "Nenhuma conta com senha vazia encontrada."
    fi
}

# ----------------------------------------------------------------------
# 2. Permissões de Arquivos Críticos
# ----------------------------------------------------------------------
audit_permissions() {
    msg "INFO" "Auditando permissões de arquivos críticos..."

    local critical_files=(
        "/etc/passwd:644:0:0"
        "/etc/shadow:640:0:0"
        "/etc/group:644:0:0"
        "/etc/gshadow:640:0:0"
        "/etc/ssh/sshd_config:600:0:0"
    )

    for item in "${critical_files[@]}"; do
        IFS=":" read -r file perm uid gid <<< "$item"
        if [ -f "$file" ]; then
            current_perm=$(stat -c "%a" "$file")
            current_uid=$(stat -c "%u" "$file")
            current_gid=$(stat -c "%g" "$file")

            if [ "$current_perm" -le "$perm" ] && [ "$current_uid" -eq "$uid" ] && [ "$current_gid" -eq "$gid" ]; then
                msg "OK" "$file: Permissões OK ($current_perm <= $perm)"
            else
                msg "WARN" "$file: Permissões inseguras ou incorretas. Atual: $current_perm Owner: $current_uid:$current_gid. Esperado: $perm $uid:$gid"
            fi
        else
            msg "INFO" "Arquivo $file não encontrado."
        fi
    done
}

# ----------------------------------------------------------------------
# 3. Auditoria SSH
# ----------------------------------------------------------------------
audit_ssh() {
    msg "INFO" "Auditando configurações do SSH (/etc/ssh/sshd_config)..."

    if [ ! -f /etc/ssh/sshd_config ]; then
        msg "WARN" "Arquivo de configuração SSH não encontrado."
        return
    fi

    # Verificar Root Login
    if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then
        msg "OK" "Login de root via SSH desabilitado."
    else
        msg "WARN" "Login de root via SSH pode estar habilitado (Recomendado: 'PermitRootLogin no')."
    fi

    # Verificar Autenticação por Senha
    if grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config; then
        msg "OK" "Autenticação por senha desabilitada."
    else
        msg "WARN" "Autenticação por senha habilitada (Recomendado usar chaves SSH e 'PasswordAuthentication no')."
    fi

    # Verificar Protocolo
    if grep -q "^Protocol 2" /etc/ssh/sshd_config; then
        msg "OK" "Protocolo SSH 2 forçado."
    fi
}

# ----------------------------------------------------------------------
# 4. Auditoria de Rede
# ----------------------------------------------------------------------
audit_network() {
    msg "INFO" "Verificando portas ouvindo (Listening Ports)..."

    # Requer netstat ou ss
    if command -v ss &> /dev/null; then
        ports=$(ss -tuln | grep LISTEN)
        msg "INFO" "Portas abertas:\n$ports"
    elif command -v netstat &> /dev/null; then
        ports=$(netstat -tuln | grep LISTEN)
        msg "INFO" "Portas abertas:\n$ports"
    else
        msg "WARN" "Comandos 'ss' ou 'netstat' não encontrados para auditar rede."
    fi
}

# ----------------------------------------------------------------------
# 5. Hardening (Aplicação de Correções)
# ----------------------------------------------------------------------
apply_hardening() {
    echo -e "${YELLOW}!!! ATENÇÃO !!!${NC}"
    echo "Você está prestes a aplicar correções de segurança."
    echo "Isso pode alterar arquivos de configuração e permissões."
    read -p "Deseja continuar? (s/N): " confirm
    if [[ "$confirm" != "s" && "$confirm" != "S" ]]; then
        msg "INFO" "Operação de hardening cancelada pelo usuário."
        return
    fi

    msg "INFO" "Aplicando correções de permissões em arquivos críticos..."
    chmod 644 /etc/passwd
    chown root:root /etc/passwd
    chmod 600 /etc/shadow
    chown root:root /etc/shadow
    chmod 644 /etc/group
    chown root:root /etc/group
    chmod 600 /etc/gshadow 2>/dev/null

    if [ -f /etc/ssh/sshd_config ]; then
        chmod 600 /etc/ssh/sshd_config
        chown root:root /etc/ssh/sshd_config
        msg "OK" "Permissões de arquivos SSH e sistema corrigidas."
    fi

    # Bloquear contas sem senha (definindo shell nologin)
    empty_pass=$(awk -F: '($2 == "") {print $1}' /etc/shadow)
    if [ -n "$empty_pass" ]; then
        msg "INFO" "Bloqueando contas sem senha: $empty_pass"
        for user in $empty_pass; do
            passwd -l "$user"
            msg "OK" "Conta $user bloqueada."
        done
    fi

    # Configuração de sysctl básica (redundante com script anti-ddos, mas bom ter aqui também focado em sistema)
    msg "INFO" "Aplicando proteção contra IP Spoofing (sysctl)..."
    sysctl -w net.ipv4.conf.all.rp_filter=1 > /dev/null
    sysctl -w net.ipv4.conf.default.rp_filter=1 > /dev/null
    msg "OK" "Configurações de sysctl aplicadas."

    msg "INFO" "Hardening concluído. Verifique o log em $LOG_FILE."
}

# ----------------------------------------------------------------------
# Menu Principal
# ----------------------------------------------------------------------
main_menu() {
    check_root || return 1
    banner

    echo "1. Executar Auditoria Completa (Apenas Relatório)"
    echo "2. Executar Hardening (Aplicar Correções Básicas)"
    echo "3. Sair"
    echo
    read -p "Escolha uma opção: " option

    case $option in
        1)
            > "$LOG_FILE"
            audit_users
            audit_permissions
            audit_ssh
            audit_network
            echo
            msg "INFO" "Auditoria finalizada. Relatório salvo em $LOG_FILE"
            ;;
        2)
            > "$LOG_FILE"
            apply_hardening
            ;;
        3)
            return 0
            ;;
        *)
            echo "Opção inválida."
            ;;
    esac
}

# Executar
main_menu
