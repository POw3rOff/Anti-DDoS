#!/bin/bash
#
# Suite de Testes de Resistência do Sistema (41-50)
#
# Este script executa verificações de segurança para garantir a resiliência do sistema
# contra falhas comuns, configurações incorretas e vetores de ataque persistentes.
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Iniciando Testes de Resistência do Sistema (41-50) ==="
echo "Data: $(date)"
echo ""

check_fail() {
    echo -e "${RED}[FALHA]${NC} $1"
}

check_pass() {
    echo -e "${GREEN}[OK]${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}[ALERTA]${NC} $1"
}

# 41. Teste de falha de firewall (reboot / crash)
echo "--- Teste 41: Falha de Firewall (Persistência) ---"
FIREWALL_ACTIVE=0
if systemctl is-enabled iptables &>/dev/null || systemctl is-enabled ufw &>/dev/null || systemctl is-enabled firewalld &>/dev/null || systemctl is-enabled nftables &>/dev/null; then
    check_pass "Serviço de firewall habilitado para iniciar no boot."
    FIREWALL_ACTIVE=1
else
    # Check manual script in rc.local
    if grep -q "iptables" /etc/rc.local 2>/dev/null; then
        check_pass "Regras de firewall detectadas no /etc/rc.local."
        FIREWALL_ACTIVE=1
    else
        check_fail "Nenhum serviço de firewall habilitado ou script de inicialização detectado."
    fi
fi

# 42. Teste de bypass de firewall por IPv6
echo -e "\n--- Teste 42: Bypass de Firewall por IPv6 ---"
IPV6_ENABLED=$(cat /proc/net/if_inet6 2>/dev/null | wc -l)
if [ "$IPV6_ENABLED" -eq 0 ]; then
    check_pass "IPv6 está desabilitado no sistema."
else
    # IPv6 enabled, check rules
    IPV6_RULES=0
    if command -v ip6tables &>/dev/null; then
        RULES_COUNT=$(ip6tables -L -n | grep -vE "^Chain|target" | wc -l)
        if [ "$RULES_COUNT" -gt 0 ]; then
            IPV6_RULES=1
        fi
    fi

    if command -v ufw &>/dev/null; then
        if ufw status | grep -q "v6"; then
            IPV6_RULES=1
        fi
    fi

    if [ "$IPV6_RULES" -eq 1 ]; then
        check_pass "IPv6 habilitado e regras de firewall detectadas."
    else
        check_fail "IPv6 habilitado MAS nenhuma regra de firewall detectada (Risco de Bypass)."
    fi
fi

# 43. Teste de exposição após update do sistema
echo -e "\n--- Teste 43: Exposição após Update (Arquivos de Configuração) ---"
# Check for .dpkg-dist, .dpkg-new, .rpmnew files which indicate conflicts
CONFLICT_FILES=$(find /etc -name "*.dpkg-dist" -o -name "*.dpkg-new" -o -name "*.rpmnew" -o -name "*.pacnew" 2>/dev/null)
if [ -n "$CONFLICT_FILES" ]; then
    check_warn "Arquivos de conflito de atualização encontrados (verificar configurações):"
    echo "$CONFLICT_FILES"
else
    check_pass "Nenhum arquivo de conflito de configuração crítico encontrado em /etc."
fi

# 44. Teste de portas abertas após reboot (Snapshot atual)
echo -e "\n--- Teste 44: Portas Abertas (Snapshot Atual) ---"
# This is an audit of current state
PORTS=$(ss -tulpn | grep LISTEN)
echo "Portas ouvindo atualmente:"
echo "$PORTS" | awk '{print $5}' | cut -d':' -f2 | sort -u | tr '\n' ' '
echo ""
# Heuristic check: warn if telnet (23) or ftp (21) is open
if echo "$PORTS" | grep -qE ":23 |:21 "; then
    check_warn "Portas inseguras detectadas (Telnet/FTP)."
else
    check_pass "Nenhuma porta obviamente insegura (Telnet/FTP) detectada."
fi

# 45. Teste de rollback malicioso (downgrade attack)
echo -e "\n--- Teste 45: Verificação de Rollback/Downgrade ---"
if [ -f /var/log/dpkg.log ]; then
    DOWNGRADES=$(grep "downgrade" /var/log/dpkg.log | tail -n 5)
    if [ -n "$DOWNGRADES" ]; then
        check_warn "Downgrades recentes de pacotes detectados:"
        echo "$DOWNGRADES"
    else
        check_pass "Nenhum downgrade recente encontrado nos logs do dpkg."
    fi
else
    check_warn "Log do dpkg não encontrado (sistema não Debian/Ubuntu?)."
fi

# 46. Teste de permissões após restore de backup (Simulação)
echo -e "\n--- Teste 46: Permissões de Arquivos Críticos ---"
CRITICAL_FILES=("/etc/shadow:000:640" "/etc/passwd:644:644" "/etc/ssh/sshd_config:600:644")
FAIL_PERM=0
for entry in "${CRITICAL_FILES[@]}"; do
    IFS=':' read -r file secure_perm1 secure_perm2 <<< "$entry"
    if [ -f "$file" ]; then
        CURRENT_PERM=$(stat -c %a "$file")
        # Check if perm is strictly secure (allow limited variation)
        if [ "$CURRENT_PERM" -le "$secure_perm2" ]; then
             check_pass "$file tem permissões seguras ($CURRENT_PERM)."
        else
             check_fail "$file tem permissões permissivas ($CURRENT_PERM). Esperado <= $secure_perm2."
             FAIL_PERM=1
        fi
    fi
done

# 47. Teste de persistência pós-reboot
echo -e "\n--- Teste 47: Verificação de Persistência (Cron/Systemd) ---"
# Check for suspicious cron jobs (common malware paths)
SUSPICIOUS_CRON=$(grep -rE "/tmp/|/dev/shm/|wget|curl|nc " /etc/cron* /var/spool/cron/crontabs 2>/dev/null)
if [ -n "$SUSPICIOUS_CRON" ]; then
    check_warn "Jobs cron suspeitos encontrados:"
    echo "$SUSPICIOUS_CRON"
else
    check_pass "Nenhum job cron com padrões suspeitos óbvios encontrado."
fi

# 48. Teste de execução de binários em /tmp
echo -e "\n--- Teste 48: Execução em /tmp ---"
TEST_SCRIPT_TMP="/tmp/test_exec_$(date +%s).sh"
echo -e "#!/bin/bash\necho 'EXECUTED'" > "$TEST_SCRIPT_TMP"
chmod +x "$TEST_SCRIPT_TMP"
OUTPUT_TMP=$("$TEST_SCRIPT_TMP" 2>/dev/null)
RET_TMP=$?
rm -f "$TEST_SCRIPT_TMP"

if [ "$OUTPUT_TMP" == "EXECUTED" ]; then
    check_fail "Execução em /tmp permitida! (Vulnerável)"
else
    if [ $RET_TMP -eq 126 ] || [ $RET_TMP -eq 127 ]; then
        check_pass "Execução em /tmp bloqueada."
    else
        check_warn "Resultado inconclusivo em /tmp (RetCode: $RET_TMP)."
    fi
fi

# 49. Teste de execução em /dev/shm
echo -e "\n--- Teste 49: Execução em /dev/shm ---"
TEST_SCRIPT_SHM="/dev/shm/test_exec_$(date +%s).sh"
echo -e "#!/bin/bash\necho 'EXECUTED'" > "$TEST_SCRIPT_SHM"
chmod +x "$TEST_SCRIPT_SHM"
OUTPUT_SHM=$("$TEST_SCRIPT_SHM" 2>/dev/null)
RET_SHM=$?
rm -f "$TEST_SCRIPT_SHM"

if [ "$OUTPUT_SHM" == "EXECUTED" ]; then
    check_fail "Execução em /dev/shm permitida! (Vulnerável)"
else
    if [ $RET_SHM -eq 126 ] || [ $RET_SHM -eq 127 ]; then
        check_pass "Execução em /dev/shm bloqueada."
    else
        check_warn "Resultado inconclusivo em /dev/shm (RetCode: $RET_SHM)."
    fi
fi

# 50. Teste de noexec realmente aplicado
echo -e "\n--- Teste 50: Verificação de Montagem noexec ---"
check_mount_option() {
    MOUNT_POINT=$1
    if mount | grep "on $MOUNT_POINT " | grep -q "noexec"; then
        check_pass "$MOUNT_POINT montado com noexec."
    else
        check_fail "$MOUNT_POINT NÃO está montado com noexec."
    fi
}

check_mount_option "/tmp"
check_mount_option "/dev/shm"

echo -e "\n=== Testes Concluídos ==="
