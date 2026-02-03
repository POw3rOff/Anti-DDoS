#!/bin/bash

# Script de Segurança para Servidores Web (Apache & Nginx)
# Focado em Hardening de Configuração e Headers de Segurança
# @versão 1.0.0
# @autor AI Assistant

# Cores
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m"

LOG_FILE="/var/log/webserver_security.log"

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

check_root() {
    if [ "$EUID" -ne 0 ]; then
        msg "ERROR" "Execute como root."
        return 1
    fi
    return 0
}

# ----------------------------------------------------------------------
# Detecção de Servidor Web
# ----------------------------------------------------------------------
detect_server() {
    msg "INFO" "Detectando servidor web..."
    if command -v nginx &> /dev/null; then
        SERVER_TYPE="nginx"
        msg "OK" "Nginx detectado."
    elif command -v apache2 &> /dev/null; then
        SERVER_TYPE="apache"
        msg "OK" "Apache detectado."
    elif command -v httpd &> /dev/null; then
        SERVER_TYPE="apache"
        msg "OK" "Apache (httpd) detectado."
    else
        msg "ERROR" "Nenhum servidor web comum (Nginx/Apache) detectado no PATH."
        return 1
    fi
    return 0
}

# ----------------------------------------------------------------------
# Segurança Nginx
# ----------------------------------------------------------------------
secure_nginx() {
    local conf_file="/etc/nginx/nginx.conf"

    msg "INFO" "Auditando Nginx em $conf_file..."

    if [ ! -f "$conf_file" ]; then
        msg "ERROR" "Arquivo de configuração principal do Nginx não encontrado."
        return
    fi

    # 1. Ocultar Versão do Nginx
    if grep -q "server_tokens off;" "$conf_file"; then
        msg "OK" "server_tokens off (Versão oculta)."
    else
        msg "WARN" "server_tokens pode estar ativo (Padrão: on). Adicione 'server_tokens off;' no bloco http."
    fi

    # 2. Tamanho do Buffer e Body (Mitigação DDoS/Overflow)
    if grep -q "client_max_body_size" "$conf_file"; then
        msg "OK" "client_max_body_size configurado."
    else
        msg "WARN" "client_max_body_size não encontrado explicitamente. Verifique se o padrão é seguro para você."
    fi

    # 3. Security Headers (Geralmente em conf.d ou sites-available)
    # Procurar em todos os arquivos de configuração
    msg "INFO" "Verificando Headers de Segurança (HSTS, XSS, Frame-Options)..."
    local headers_found=0

    grep -r "add_header X-Frame-Options" /etc/nginx/ &> /dev/null && headers_found=$((headers_found+1))
    grep -r "add_header X-XSS-Protection" /etc/nginx/ &> /dev/null && headers_found=$((headers_found+1))
    grep -r "add_header X-Content-Type-Options" /etc/nginx/ &> /dev/null && headers_found=$((headers_found+1))

    if [ $headers_found -ge 3 ]; then
        msg "OK" "Headers de segurança básicos encontrados nas configurações."
    else
        msg "WARN" "Alguns headers de segurança parecem faltar. Recomendado adicionar:"
        echo "      add_header X-Frame-Options \"SAMEORIGIN\";"
        echo "      add_header X-XSS-Protection \"1; mode=block\";"
        echo "      add_header X-Content-Type-Options \"nosniff\";"
    fi
}

# ----------------------------------------------------------------------
# Segurança Apache
# ----------------------------------------------------------------------
secure_apache() {
    # Tenta localizar config do Apache (Debian/Ubuntu vs RHEL/CentOS)
    local conf_dir="/etc/apache2"
    if [ ! -d "$conf_dir" ]; then
        conf_dir="/etc/httpd"
    fi

    msg "INFO" "Auditando Apache em $conf_dir..."

    # 1. Ocultar Assinatura e Versão
    local tokens_found=$(grep -r "ServerTokens" "$conf_dir")
    local signature_found=$(grep -r "ServerSignature" "$conf_dir")

    if [[ "$tokens_found" == *"Prod"* ]]; then
        msg "OK" "ServerTokens configurado para Prod (Versão mínima)."
    else
        msg "WARN" "ServerTokens pode não estar como Prod. Recomendado: 'ServerTokens Prod'."
    fi

    if [[ "$signature_found" == *"Off"* ]]; then
        msg "OK" "ServerSignature configurado para Off."
    else
        msg "WARN" "ServerSignature pode estar On. Recomendado: 'ServerSignature Off'."
    fi

    # 2. ModSecurity e ModEvasive
    if apache2ctl -M 2>/dev/null | grep -q "security2_module"; then
        msg "OK" "ModSecurity (security2_module) está carregado."
    else
        msg "WARN" "ModSecurity não parece estar carregado. Considere instalar libapache2-mod-security2."
    fi

    if apache2ctl -M 2>/dev/null | grep -q "evasive_module"; then
        msg "OK" "ModEvasive (evasive_module) está carregado."
    else
        msg "WARN" "ModEvasive não parece estar carregado. Útil contra DDoS (HTTP Floods)."
    fi

    # 3. Proteção contra Clickjacking
    local frame_options=$(grep -r "Header always set X-Frame-Options" "$conf_dir")
    if [ -n "$frame_options" ]; then
        msg "OK" "Header X-Frame-Options encontrado."
    else
        msg "WARN" "Header X-Frame-Options não encontrado. Recomendado configurar para evitar Clickjacking."
    fi
}

# ----------------------------------------------------------------------
# Verifica Certificados SSL (Básico)
# ----------------------------------------------------------------------
check_ssl() {
    msg "INFO" "Procurando certificados SSL comuns..."
    # Apenas verifica existência de arquivos comuns de certbot/letsencrypt
    if [ -d "/etc/letsencrypt/live" ]; then
        msg "OK" "Diretório do Let's Encrypt encontrado."
        # Listar domínios
        domains=$(ls /etc/letsencrypt/live 2>/dev/null)
        msg "INFO" "Domínios configurados: $domains"
    else
        msg "INFO" "Nenhum diretório padrão Let's Encrypt encontrado."
    fi
}

# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
main() {
    check_root || return 1

    detect_server
    if [ "$SERVER_TYPE" == "nginx" ]; then
        secure_nginx
    elif [ "$SERVER_TYPE" == "apache" ]; then
        secure_apache
    fi

    check_ssl

    echo
    msg "INFO" "Auditoria concluída. Verifique os avisos (WARN) acima."
}

main
