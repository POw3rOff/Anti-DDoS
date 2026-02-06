#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Simulação de Persistência"
CRON_JOB="/etc/cron.d/evil_persistence"
# Verifica se tem permissão (root)
if [ -w "/etc/cron.d" ]; then
    echo "* * * * * root /tmp/.hidden_script.sh" > "$CRON_JOB"
    log_event "Cron job malicioso criado em $CRON_JOB"
    sleep 2
    rm "$CRON_JOB"
    log_event "Artefato removido."
else
    log_event "ERRO: Sem permissão de escrita em /etc/cron.d (Execute como root)."
fi
# Simula alteração de timestamp (Timestomping)
touch -d "2020-01-01" /tmp/old_file_sim
log_event "CONCLUÍDO: Teste de persistência."
