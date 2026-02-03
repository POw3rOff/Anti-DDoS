#!/bin/bash
# Nome: alerta_app_comprometida.sh
# Descricao: Agrega alertas dos scripts de seguranca e verifica integridade critica
# Autor: Jules

LOG_FILES="/var/log/rce_alerts.log /var/log/lfi_rfi_alerts.log /var/log/webshell_scan.log /var/log/uploads_monitor.log /var/log/secrets_scan.log"
CRITICAL_KEYWORD="ALERTA|PERIGO|SUSPEITA"
BASELINE_FILE="/var/log/index_checksum.sha256"
INDEX_FILE="/var/www/html/index.php"

echo "[*] Verificando estado de seguranca da aplicacao..."

# 1. Verificar logs de alertas gerados pelos outros scripts
ALERT_COUNT=0
for log in $LOG_FILES; do
    if [ -f "$log" ]; then
        # Conta linhas com palavras chave nas ultimas 24h (simulado aqui pegando tudo)
        COUNT=$(grep -E "$CRITICAL_KEYWORD" "$log" | wc -l)
        if [ "$COUNT" -gt 0 ]; then
            echo "[!] $COUNT alertas encontrados em $log"
            # Mostra os ultimos 3
            grep -E "$CRITICAL_KEYWORD" "$log" | tail -n 3 | sed 's/^/    /'
            ALERT_COUNT=$((ALERT_COUNT + COUNT))
        fi
    fi
done

# 2. Verificar Defacement (Checksum do index)
if [ -f "$INDEX_FILE" ]; then
    CURRENT_SUM=$(sha256sum "$INDEX_FILE" | awk '{print $1}')
    if [ -f "$BASELINE_FILE" ]; then
        OLD_SUM=$(cat "$BASELINE_FILE")
        if [ "$CURRENT_SUM" != "$OLD_SUM" ]; then
            echo "[!!!] CRITICO: O hash do arquivo principal (index.php) mudou! Possivel Defacement."
            echo "    Anterior: $OLD_SUM"
            echo "    Atual:    $CURRENT_SUM"
            ALERT_COUNT=$((ALERT_COUNT + 1))
        fi
    else
        echo "$CURRENT_SUM" > "$BASELINE_FILE"
        echo "[*] Baseline de integridade criada para index.php (Hash salvo)."
    fi
fi

if [ "$ALERT_COUNT" -gt 0 ]; then
    echo "--------------------------------------------------"
    echo "RESUMO: Total de $ALERT_COUNT indicativos de compromisso."
    echo "Acao recomendada: Isolar servidor e iniciar resposta a incidentes."
else
    echo "[OK] Nenhum alerta critico detectado nos logs monitorados."
fi
