#!/bin/bash
# Nome: auditoria_configs_app.sh
# Descricao: Audita arquivos de configuracao da aplicacao por permissoes e settings inseguros
# Autor: Jules

SEARCH_DIR="/var/www/html"
CONFIG_FILES="wp-config.php .env config.php settings.py database.php"
OUTPUT_LOG="/var/log/app_config_audit.log"

echo "[*] Iniciando auditoria de configs em $(date)" | tee -a "$OUTPUT_LOG"

# Encontra arquivos de configuracao
for file in $CONFIG_FILES; do
    find "$SEARCH_DIR" -name "$file" 2>/dev/null | while read -r filepath; do
        echo "[*] Analisando $filepath" | tee -a "$OUTPUT_LOG"

        # Verificar permissoes (Ideal: 640 ou 600, Max: 644)
        PERMS=$(stat -c "%a" "$filepath")
        if [ "$PERMS" -gt 644 ]; then
            echo "[!] ALERTA: Permissoes inseguras ($PERMS) em $filepath. Recomendado: 640 ou 600." | tee -a "$OUTPUT_LOG"
        fi

        # Verificar Debug Mode
        # Patterns: WP_DEBUG true, APP_DEBUG=true, 'debug' => true
        if grep -qiE "debug['\"]?\s*=>\s*true|DEBUG\s*=\s*True|WP_DEBUG',\s*true|APP_DEBUG=true" "$filepath"; then
            echo "[!] ALERTA: Modo DEBUG habilitado em $filepath" | tee -a "$OUTPUT_LOG"
        fi
    done
done

echo "[*] Auditoria concluida." | tee -a "$OUTPUT_LOG"
