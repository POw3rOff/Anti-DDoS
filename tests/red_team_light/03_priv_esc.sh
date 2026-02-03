#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Simulação de PrivEsc"
# 1. Cria binário com bit SUID (Fake)
TEST_SUID="/tmp/bash_suid_test"
touch "$TEST_SUID"
chmod 4755 "$TEST_SUID"
log_event "Artefato criado: SUID bit em $TEST_SUID"

# 2. Acesso a arquivos sensíveis
cat /etc/shadow 2>/dev/null
log_event "Tentativa de leitura de /etc/shadow registrada."

sleep 2
rm "$TEST_SUID"
log_event "CONCLUÍDO: Artefatos limpos."
