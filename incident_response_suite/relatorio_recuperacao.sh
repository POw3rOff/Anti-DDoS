#!/bin/bash
#
# relatorio_recuperacao.sh
#
# Gera um relatório consolidado das ações tomadas durante a resposta ao incidente.
# Coleta logs dos outros scripts desta suite.
#
# Autor: Jules (Assistente de IA)
# Data: $(date +%Y-%m-%d)

set -u

REPORT_FILE="Relatorio_Incidente_$(date +%Y%m%d_%H%M%S).md"
LOG_SEARCH_PATH="/var/log" # Onde os scripts gravaram logs

echo "Gerando relatório em: $REPORT_FILE"

cat <<EOF > "$REPORT_FILE"
# Relatório de Recuperação de Incidente
**Data:** $(date)
**Servidor:** $(hostname)
**Usuário:** $(whoami)

## 1. Cronograma de Ações Automatizadas

Abaixo estão os registros encontrados dos scripts de resposta a incidentes.

EOF

# Função para adicionar logs ao relatório
add_log_section() {
    TITLE="$1"
    FILE_PATTERN="$2"

    echo "### $TITLE" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"

    # Busca logs recentes (últimas 24h)
    FOUND_LOGS=$(find "$LOG_SEARCH_PATH" -name "$FILE_PATTERN" -mtime -1 2>/dev/null)

    if [ -n "$FOUND_LOGS" ]; then
        for log in $FOUND_LOGS; do
            echo "--- Conteúdo de $(basename "$log") ---" >> "$REPORT_FILE"
            cat "$log" >> "$REPORT_FILE"
            echo "" >> "$REPORT_FILE"
        done
    else
        echo "Nenhum log encontrado para esta etapa nas últimas 24h." >> "$REPORT_FILE"
    fi

    echo "\`\`\`" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Adiciona seções
add_log_section "Snapshot de Incidente" "incident_snapshot.log"
add_log_section "Congelamento de Backup" "incident_freeze_backup.log"
add_log_section "Killswitch de Backup" "incident_killswitch.log"
add_log_section "Divergências de Integridade" "diff_report_*.txt"
add_log_section "Logs Forenses (Localização)" "forensic_log.txt"

# Adiciona info do sistema atual
cat <<EOF >> "$REPORT_FILE"
## 2. Estado Atual do Sistema

**Uptime:**
$(uptime)

**Espaço em Disco:**
\`\`\`
$(df -h / /var /home)
\`\`\`

**Conexões Ativas (Top 10):**
\`\`\`
$(ss -tun | head -n 15)
\`\`\`

## 3. Conclusão

Este relatório foi gerado automaticamente. Verifique a integridade dos serviços restaurados.
EOF

echo "Relatório gerado com sucesso."
echo "Para visualizar: cat $REPORT_FILE"
