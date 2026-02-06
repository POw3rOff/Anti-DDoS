#!/bin/bash
# Script: score_maturidade_backup.sh
# Descrição: Calcula um "Score de Maturidade" para o sistema de backups.
# Autor: Jules (Assistant)

SCORE=0
MAX_SCORE=100

echo "=== Avaliação de Maturidade de Backup ==="

# 1. Existência de Scripts de Backup (+10)
if [ -d "smart_backup_suite" ] || [ -d "/etc/backup.d" ]; then
    echo "[+10] Scripts de backup detetados."
    SCORE=$((SCORE+10))
else
    echo "[0] Scripts de backup não encontrados."
fi

# 2. Governança e Controle (+10)
if [ -d "governance_and_control_suite" ]; then
    echo "[+10] Suite de Governança instalada."
    SCORE=$((SCORE+10))
else
    echo "[0] Governança ausente."
fi

# 3. Encriptação (+10)
# Procura indícios de GPG ou chaves
if command -v gpg >/dev/null || [ -f "/root/.gnupg/pubring.kbx" ]; then
    echo "[+10] Capacidade de encriptação detetada."
    SCORE=$((SCORE+10))
else
    echo "[0] Encriptação não verificada."
fi

# 4. Redundância (+10)
if [ -d "redundancy_and_survival_suite" ]; then
    echo "[+10] Suite de Redundância detetada."
    SCORE=$((SCORE+10))
else
    echo "[0] Redundância não verificada."
fi

# 5. Monitoramento / Logs (+10)
if [ -d "/var/log/backups" ] || grep -q "backup" /var/log/syslog 2>/dev/null; then
    echo "[+10] Logs de backup detetados."
    SCORE=$((SCORE+10))
else
    echo "[0] Logs centralizados não encontrados."
fi

# 6. Testes de Restauro (+20) - Peso maior
if [ -d "restore_validation_suite" ]; then
    echo "[+20] Suite de Validação de Restauro encontrada."
    SCORE=$((SCORE+20))
else
    echo "[0] Validação de restauro não automatizada."
fi

# 7. Segurança de Acesso (+10)
if [ -f "/etc/hosts.allow" ] || [ -f "linux_firewall_suite/iptables_rules.sh" ]; then
    echo "[+10] Controles de acesso de rede detetados."
    SCORE=$((SCORE+10))
else
    echo "[0] Controle de acesso específico não detetado."
fi

# 8. Documentação (+10)
if [ -d "documentation" ]; then
    echo "[+10] Documentação encontrada."
    SCORE=$((SCORE+10))
else
    echo "[0] Documentação ausente."
fi

# 9. Backups Recentes (+10)
# Verifica se existe algum arquivo modificado nas últimas 24h em /var/backups (se existir)
if [ -d "/var/backups" ] && find "/var/backups" -type f -mtime -1 -print -quit | grep -q .; then
    echo "[+10] Backups recentes (24h) encontrados."
    SCORE=$((SCORE+10))
else
    echo "[0] Nenhum backup recente encontrado ou diretório inacessível."
fi

echo "------------------------------------------------"
echo "SCORE FINAL: $SCORE / $MAX_SCORE"

if [ $SCORE -ge 80 ]; then
    echo "Nível: ALTO (Excelente)"
elif [ $SCORE -ge 50 ]; then
    echo "Nível: MÉDIO (Bom, mas pode melhorar)"
else
    echo "Nível: BAIXO (Crítico - Ação Requerida)"
fi

echo "=== Fim da Avaliação ==="
