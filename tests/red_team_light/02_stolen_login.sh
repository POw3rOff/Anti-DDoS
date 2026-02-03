#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Simulação de Login Roubado"
# Simula um login bem sucedido de um IP suspeito em horário atípico
SUSPECT_IP="45.10.20.99" # IP Fictício de 'atacante'
logger -t sshd -p authpriv.info "Accepted password for root from $SUSPECT_IP port 54321 ssh2"
logger -t sshd -p authpriv.info "pam_unix(sshd:session): session opened for user root by (uid=0)"
log_event "CONCLUÍDO: Log de acesso suspeito injetado."
