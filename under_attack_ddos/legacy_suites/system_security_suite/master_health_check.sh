#!/bin/bash
#
# 10. Health Check Geral (Master Script)
# Autor: Jules (AI Agent)
# Descrição: Executa todos os scripts de auditoria e gera relatório consolidado.

REPORT_DIR="/var/log/security_reports"
REPORT_FILE="$REPORT_DIR/master_report_$(date +%F_%H%M).log"
SCORE=100

mkdir -p "$REPORT_DIR"

echo "=== INICIANDO HEALTH CHECK GERAL ===" | tee "$REPORT_FILE"
echo "Data: $(date)" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Scripts para rodar (Auditoria/Scan)
# Nome do Script | Argumentos | Peso (dedução de score)
SCRIPTS=(
    "hardening_auto.sh| |0" # Apenas executa, não check
    "audit_users_perms.sh| |10"
    "integrity_monitor.sh|check|20"
    "local_port_scanner.sh| |5"
    "detect_suspicious_processes.sh| |15"
    "persistence_checker.sh| |10"
    "scan_suspicious_files.sh| |20"
)

for item in "${SCRIPTS[@]}"; do
    IFS='|' read -r script args weight <<< "$item"

    script_path="./$script"
    if [ ! -f "$script_path" ]; then
        script_path="./system_security_suite/$script"
    fi

    if [ -f "$script_path" ]; then
        echo ">>> Executando: $script $args" | tee -a "$REPORT_FILE"
        echo "---------------------------------------------------" >> "$REPORT_FILE"

        # Executa e anexa output
        OUTPUT=$(bash "$script_path" $args 2>&1)
        echo "$OUTPUT" >> "$REPORT_FILE"

        # Análise simples de falha (busca por palavras chave de erro/alerta)
        if echo "$OUTPUT" | grep -qE "ALERTA|SUSPEITO|ALTERAÇÕES DETECTADAS|MUDANÇAS DETECTADAS|FAILED"; then
            echo "[!] PROBLEMAS ENCONTRADOS EM: $script" | tee -a "$REPORT_FILE"
            SCORE=$((SCORE - weight))
        else
            echo "[OK] $script passou sem alertas críticos." | tee -a "$REPORT_FILE"
        fi
        echo "---------------------------------------------------" >> "$REPORT_FILE"
        echo "" | tee -a "$REPORT_FILE"
    else
        echo "[Erro] Script $script não encontrado." | tee -a "$REPORT_FILE"
    fi
done

echo "=== RELATÓRIO FINAL ===" | tee -a "$REPORT_FILE"
echo "Score de Segurança Estimado: $SCORE/100" | tee -a "$REPORT_FILE"
if [ "$SCORE" -lt 80 ]; then
    echo "STATUS: RISCO ELEVADO - Verifique o relatório imediatamente." | tee -a "$REPORT_FILE"
else
    echo "STATUS: OK - Sistema parece saudável." | tee -a "$REPORT_FILE"
fi

echo ""
echo "Relatório completo salvo em: $REPORT_FILE"
