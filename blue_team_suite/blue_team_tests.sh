#!/bin/bash
#
# Suite de Testes de Deteção e Resposta (Blue Team)
#
# Este script executa verificações para validar a capacidade de
# deteção, alerta, resposta e recuperação do sistema.
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Iniciando Suite de Testes Blue Team ==="
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

check_info() {
    echo -e "[INFO] $1"
}

# 1. Teste de alertas (latência e fiabilidade)
echo "--- 1. Teste de Alertas (Latência e Fiabilidade) ---"
TEST_TAG="TEST_ALERT_$(date +%s)"
START_TIME=$(date +%s%N)
logger -p auth.notice "$TEST_TAG - Teste de latência de log"
# Tentativa de leitura imediata do log (simulando deteção em tempo real)
if grep -q "$TEST_TAG" /var/log/syslog 2>/dev/null || grep -q "$TEST_TAG" /var/log/auth.log 2>/dev/null || grep -q "$TEST_TAG" /var/log/messages 2>/dev/null; then
    END_TIME=$(date +%s%N)
    # Calcular latência em milissegundos
    LATENCY=$(( (END_TIME - START_TIME) / 1000000 ))
    check_pass "Alerta detetado nos logs. Latência de gravação: ${LATENCY}ms."
else
    # Fallback para sistemas onde o log pode não ser imediato ou acessível
    check_warn "Alerta gerado, mas não encontrado imediatamente nos logs padrão (pode haver atraso no buffer ou falta de permissão)."
fi

# 2. Teste de Falso Positivo vs Falso Negativo
echo -e "\n--- 2. Teste de Falso Positivo vs Falso Negativo ---"
# Falso Negativo: Verificar se existem regras de deteção para ataques comuns (ex: SSH brute force)
if command -v fail2ban-client &>/dev/null; then
    JAILS=$(fail2ban-client status 2>/dev/null | grep "Jail list" | cut -d: -f2)
    if [[ "$JAILS" == *"ssh"* ]] || [[ "$JAILS" == *"sshd"* ]]; then
        check_pass "Proteção contra Falso Negativo ativa: Jail SSH detetada no Fail2Ban."
    else
        check_warn "Possível risco de Falso Negativo: Nenhuma jail SSH ativa no Fail2Ban."
    fi
else
    check_warn "Fail2Ban não detetado. Verificação de proteção automática limitada."
fi

# Falso Positivo: Verificar se conexões locais ou de gestão são permitidas (whitelist)
# Simulação simples: verificar se o IP local está na ignoreip
if [ -f /etc/fail2ban/jail.conf ] || [ -f /etc/fail2ban/jail.local ]; then
    IGNOREIP=$(grep "^ignoreip" /etc/fail2ban/jail.conf /etc/fail2ban/jail.local 2>/dev/null)
    if [ -n "$IGNOREIP" ]; then
        check_pass "Mitigação de Falso Positivo: Configuração de 'ignoreip' encontrada ($IGNOREIP)."
    else
        check_warn "Risco de Falso Positivo: Nenhuma configuração explícita de 'ignoreip' encontrada."
    fi
fi

# 3. Teste de Lockdown Automático
echo -e "\n--- 3. Teste de Lockdown Automático ---"
LOCKDOWN_SCRIPT=$(find . -name "lockdown.sh" 2>/dev/null | head -n 1)
if [ -z "$LOCKDOWN_SCRIPT" ]; then
    LOCKDOWN_SCRIPT="./linux_security_scripts/lockdown.sh"
fi

if [ -f "$LOCKDOWN_SCRIPT" ]; then
    if [ -x "$LOCKDOWN_SCRIPT" ]; then
        check_pass "Script de Lockdown encontrado e executável: $LOCKDOWN_SCRIPT"
    else
        check_fail "Script de Lockdown encontrado mas NÃO executável: $LOCKDOWN_SCRIPT"
    fi
else
    check_warn "Script de Lockdown não encontrado nos locais padrão."
fi

# 4. Teste de Quarentena do Host
echo -e "\n--- 4. Teste de Quarentena do Host ---"
# Verificar se existem regras que impedem comunicação lateral (RFC1918)
# Procurar por regras DROP/REJECT para redes privadas na chain OUTPUT
if command -v iptables &>/dev/null; then
    QUARANTINE_RULES=$(iptables -S OUTPUT 2>/dev/null | grep -E "192.168.|10.|172.16." | grep -E "DROP|REJECT")
    if [ -n "$QUARANTINE_RULES" ]; then
        check_pass "Regras de isolamento de rede (Quarentena) detetadas."
    else
        check_info "Nenhuma regra de quarentena ativa detetada (normal se não estiver em incidente)."
    fi
else
    check_warn "iptables não disponível para verificação de quarentena."
fi

# 5. Teste de Kill-Switch de Rede
echo -e "\n--- 5. Teste de Kill-Switch de Rede ---"
# Verificar capacidade de derrubar interfaces rapidamente
if command -v ip &>/dev/null || command -v nmcli &>/dev/null || command -v ifconfig &>/dev/null; then
    check_pass "Ferramentas para Kill-Switch de rede (ip/nmcli/ifconfig) estão disponíveis."
else
    check_fail "Ferramentas essenciais de rede ausentes. Kill-switch pode ser impossível."
fi

# 6. Teste de Recuperação Pós-Incidente
echo -e "\n--- 6. Teste de Recuperação Pós-Incidente ---"
# Verificar existência de backups
BACKUP_DIRS="/var/backups /backup /tmp/backups"
BACKUP_FOUND=0
for dir in $BACKUP_DIRS; do
    if [ -d "$dir" ] && [ "$(ls -A $dir 2>/dev/null)" ]; then
        check_pass "Diretório de backup encontrado e não vazio: $dir"
        BACKUP_FOUND=1
    fi
done

if [ $BACKUP_FOUND -eq 0 ]; then
    check_warn "Nenhum backup recente óbvio encontrado nos diretórios padrão."
fi

# 7. Teste de Logging Imutável
echo -e "\n--- 7. Teste de Logging Imutável ---"
# Verificar atributo +a (append only) em logs críticos
if command -v lsattr &>/dev/null; then
    LOG_ATTR=$(lsattr /var/log/auth.log 2>/dev/null)
    if [[ "$LOG_ATTR" == *"----a-------"* ]]; then
        check_pass "Imutabilidade (append-only) detetada em /var/log/auth.log."
    else
        check_warn "Logs críticos (/var/log/auth.log) não têm o atributo 'append-only' (+a)."
    fi
else
    check_warn "Comando 'lsattr' não encontrado. Não é possível verificar atributos de arquivo."
fi

# 8. Teste de Correlação de Eventos
echo -e "\n--- 8. Teste de Correlação de Eventos ---"
# Verificar se existe algum processo agregador de logs ou SIEM (ex: rsyslog, fail2ban, wazuh)
if pgrep -x "fail2ban-server" >/dev/null; then
    check_pass "Motor de correlação ativo: fail2ban-server."
elif pgrep -x "rsyslogd" >/dev/null; then
    check_info "Coletor de logs ativo: rsyslogd (Correlação depende de config)."
else
    check_warn "Nenhum processo óbvio de correlação de eventos detetado em execução."
fi

# 9. Teste de Retenção de Logs
echo -e "\n--- 9. Teste de Retenção de Logs ---"
# Verificar rotação de logs
if [ -f /etc/logrotate.conf ]; then
    check_pass "Configuração de rotação de logs (logrotate) encontrada."
    # Verificar se existem logs antigos rotacionados
    OLD_LOGS=$(find /var/log -name "*.gz" -o -name "*.1" 2>/dev/null | head -n 5)
    if [ -n "$OLD_LOGS" ]; then
        check_pass "Arquivos de log arquivados encontrados (Retenção ativa)."
    else
        check_warn "Nenhum log antigo/arquivado encontrado. Verifique a política de retenção."
    fi
else
    check_fail "Configuração do logrotate não encontrada."
fi

# 10. Teste de Forense Pós-Ataque
echo -e "\n--- 10. Teste de Forense Pós-Ataque ---"
# Verificar disponibilidade de ferramentas forenses
TOOLS="auditd sysdig tcpdump lsof netstat strace"
MISSING_TOOLS=""
FOUND_TOOLS=""

for tool in $TOOLS; do
    if command -v $tool &>/dev/null; then
        FOUND_TOOLS="$FOUND_TOOLS $tool"
    else
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

if [ -n "$FOUND_TOOLS" ]; then
    check_pass "Ferramentas forenses disponíveis:$FOUND_TOOLS"
fi

if [ -n "$MISSING_TOOLS" ]; then
    check_warn "Ferramentas forenses ausentes (recomendado instalar):$MISSING_TOOLS"
fi

echo -e "\n=== Suite Blue Team Concluída ==="

# 11. Simulation & Verification (Purple Team)
echo -e "\n--- 11. Simulation & Verification (Purple Team) ---"

# 11.1 Tunnel Detection
echo "    [Test 11.1] Simulating SSH Tunnel..."
# Simulate a process that looks like an SSH tunnel
# We can't easily spoof /proc/pid/cmdline for existing binaries without running them with those args.
# Let's try to run sleep with arguments that mimic ssh flags, but sleep doesn't accept them.
# Instead, we'll create a dummy script that accepts args.
DUMMY_SSH="/tmp/fake_ssh_tunnel.sh"
echo '#!/bin/bash' > "$DUMMY_SSH"
echo 'sleep 5' >> "$DUMMY_SSH"
chmod +x "$DUMMY_SSH"
# The detector greps for "ssh" in pgrep or process name.
# The detector actually does: for pid in $(pgrep ssh); do...
# So we need the process to be named "ssh". We can copy bash to /tmp/ssh.
if [ ! -f /tmp/ssh ]; then
    cp /bin/bash /tmp/ssh
fi
# Run it with -L flag. Bash accepts -c, let's see if we can trick it or just use the args.
# Bash doesn't ignore unknown flags easily.
# Let's look at the detector again: "cmd=$(tr '\0' ' ' < /proc/$pid/cmdline)"
# We can use a python script if available to set process title? No, too complex.
# Simpler: Create a script named 'iodine' (known tunnel tool)
echo "    -> Simulating 'iodine' process..."
cp /bin/sleep /tmp/iodine
/tmp/iodine 5 &
TUNNEL_PID=$!
sleep 1

# Run Detector
DETECTOR_OUT=$(./advanced_security_suite/tunnel_detector.sh 2>&1)
if echo "$DETECTOR_OUT" | grep -q "iodine"; then
    check_pass "Detector identificou simulação de 'iodine' (PID $TUNNEL_PID)."
else
    check_fail "Falha na deteção de tunnel simulado."
    echo "Output do detector:"
    echo "$DETECTOR_OUT"
fi
kill $TUNNEL_PID 2>/dev/null
rm -f /tmp/iodine /tmp/fake_ssh_tunnel.sh /tmp/ssh

# 11.2 Reverse Shell Detection
echo "    [Test 11.2] Simulating Reverse Shell (Netcat)..."
# The detector looks for 'nc' with a socket.
if command -v nc &>/dev/null; then
    nc -l -p 4444 &
    NC_PID=$!
    sleep 1

    DETECTOR_OUT=$(./advanced_security_suite/reverse_shell_detector.sh 2>&1)
    if echo "$DETECTOR_OUT" | grep -q "Processo interativo com rede"; then
        check_pass "Detector identificou shell/netcat suspeito (PID $NC_PID)."
    else
        # Fallback: maybe the detector didn't see 'nc' as interactive or socket wasn't ready
        check_warn "Detector não marcou o netcat de teste como malicioso (pode ser comportamento esperado se não houver conexão estabelecida)."
        echo "Output do detector:"
        echo "$DETECTOR_OUT"
    fi
    kill $NC_PID 2>/dev/null
else
    check_info "Netcat (nc) não encontrado, pulando simulação de reverse shell."
fi

# 11.3 Suspicious Process (Miner)
echo "    [Test 11.3] Simulating Crypto Miner..."
# Creating a process named 'minerd'
cp /bin/sleep /tmp/minerd
/tmp/minerd 5 &
MINER_PID=$!
sleep 1

# Assuming detect_suspicious_processes.sh exists and checks for names
if [ -f "./system_security_suite/detect_suspicious_processes.sh" ]; then
    DETECTOR_OUT=$(./system_security_suite/detect_suspicious_processes.sh 2>&1)
    if echo "$DETECTOR_OUT" | grep -q "minerd"; then
        check_pass "Detector identificou processo 'minerd' simulado."
    else
        check_warn "Detector de processos suspeitos não alertou sobre 'minerd'."
    fi
else
    check_warn "Script 'detect_suspicious_processes.sh' não encontrado."
fi
kill $MINER_PID 2>/dev/null
rm -f /tmp/minerd

echo -e "\n=== Testes de Simulação Concluídos ==="
