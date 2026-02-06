#!/bin/bash
#
# 3. Auditoria de Utilizadores e Permissões
# Autor: Jules (AI Agent)
# Descrição: Lista users com shell, procura permissões inseguras e SUIDs.

REPORT_FILE="/var/log/security_audit_$(date +%F).log"
echo "Relatório salvo em: $REPORT_FILE"

{
echo "=== Auditoria Iniciada: $(date) ==="
echo ""

# 1. Utilizadores com Shell Válida
echo "[*] Utilizadores com shell válida (/bin/bash, /bin/sh, etc):"
awk -F: '($7 !~ /nologin|false/) {print $1, $7}' /etc/passwd
echo ""

# 2. Contas sem senha (perigoso!)
echo "[*] Contas sem senha definida (shadow file):"
if [ -r /etc/shadow ]; then
    awk -F: '($2 == "") {print $1}' /etc/shadow
else
    echo "Erro: Não é possível ler /etc/shadow (execute como root)."
fi
echo ""

# 3. Permissões 777 (World Writable)
echo "[*] Procurando arquivos com permissão 777 (pode demorar)..."
# Exclui /proc, /sys, /dev, /tmp, /var/tmp para reduzir ruído
find / -type f -perm 0777 -not -path "/proc/*" -not -path "/sys/*" -not -path "/dev/*" -not -path "/tmp/*" -not -path "/var/tmp/*" 2>/dev/null | head -n 20
echo "... (Limitado aos primeiros 20 resultados)"
echo ""

# 4. Binários SUID/SGID (Privilege Escalation)
echo "[*] Procurando binários SUID (executa como owner):"
find /usr/bin /usr/sbin -type f -perm -4000 2>/dev/null
echo ""

# 5. Alterações recentes em /etc (últimos 7 dias)
echo "[*] Arquivos modificados em /etc nos últimos 7 dias:"
find /etc -type f -mtime -7 -ls 2>/dev/null
echo ""

echo "=== Auditoria Finalizada ==="
} | tee "$REPORT_FILE"
