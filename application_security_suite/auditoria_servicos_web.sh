#!/bin/bash
# Nome: auditoria_servicos_web.sh
# Descricao: Auditoria de seguranca para servicos web (Apache/Nginx)
# Autor: Jules (Assistant)

DATA=$(date +%Y-%m-%d_%H-%M-%S)
LOG_FILE="/var/log/web_audit_${DATA}.log"

echo "[*] Iniciando auditoria de servicos web em $DATA" | tee -a "$LOG_FILE"

# Funcao para verificar servico
check_service() {
    SERVICE=$1
    if systemctl is-active --quiet "$SERVICE"; then
        echo "[+] Servico $SERVICE esta a correr." | tee -a "$LOG_FILE"
        # Tenta obter a versao de forma simples
        if [ "$SERVICE" == "nginx" ]; then
             nginx -v 2>&1 | tee -a "$LOG_FILE"
        elif [ "$SERVICE" == "apache2" ]; then
             apache2 -v 2>&1 | head -n 1 | tee -a "$LOG_FILE"
        elif [ "$SERVICE" == "httpd" ]; then
             httpd -v 2>&1 | head -n 1 | tee -a "$LOG_FILE"
        fi
    else
        echo "[-] Servico $SERVICE nao esta a correr." | tee -a "$LOG_FILE"
    fi
}

# Verificar Nginx
check_service "nginx"

# Verificar Apache
if systemctl list-units --full -all | grep -Fq "apache2.service"; then
    check_service "apache2"
elif systemctl list-units --full -all | grep -Fq "httpd.service"; then
    check_service "httpd"
fi

# Verificar Portas (80, 443)
echo "[*] Verificando portas padrao..." | tee -a "$LOG_FILE"
ss -tulpn | grep -E ":(80|443)" | tee -a "$LOG_FILE"

# Verificar permissoes de ficheiros de configuracao (amostra)
echo "[*] Verificando permissoes de configuracao..." | tee -a "$LOG_FILE"
for conf_dir in /etc/nginx /etc/apache2 /etc/httpd; do
    if [ -d "$conf_dir" ]; then
        echo "Checking $conf_dir" | tee -a "$LOG_FILE"
        find "$conf_dir" -type f -name "*.conf" -exec ls -l {} \; 2>/dev/null | head -n 5 | tee -a "$LOG_FILE"
    fi
done

echo "[*] Auditoria concluida." | tee -a "$LOG_FILE"
