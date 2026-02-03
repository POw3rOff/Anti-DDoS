#!/bin/bash
#
# Suite de Testes de Confiança Zero (Zero Trust)
#
# Este script executa verificações focadas em:
# 1. Acesso Lateral (Lateral Movement)
# 2. Isolamento entre Serviços (Service Isolation)
# 3. Acesso Mínimo Necessário (Least Privilege)
#
# Baseado em princípios Zero Trust onde nenhuma entidade é confiável por padrão.
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Iniciando Testes de Confiança Zero (Zero Trust) ==="
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

# ==============================================================================
# 1. Testes de Acesso Lateral (Lateral Access)
# ==============================================================================
echo "--- ZT-01: Verificações de Acesso Lateral ---"

# 1.1 SSH Agent Forwarding
# Se habilitado, um administrador comprometido em um servidor destino pode ter suas chaves usadas pelo atacante.
echo "[Verificação] SSH Agent Forwarding"
if grep -Ei "^AllowAgentForwarding yes" /etc/ssh/sshd_config > /dev/null 2>&1; then
    check_fail "AllowAgentForwarding está habilitado no SSH. Risco de sequestro de sessão SSH."
else
    # Pode estar comentado (default é yes em algumas distros, mas no é safe check)
    # Vamos verificar se está explicitamente 'no'
    if grep -Ei "^AllowAgentForwarding no" /etc/ssh/sshd_config > /dev/null 2>&1; then
        check_pass "AllowAgentForwarding está desabilitado."
    else
        check_warn "AllowAgentForwarding não está explicitamente desabilitado (Padrão pode ser 'yes')."
    fi
fi

# 1.2 ICMP Redirects
# Aceitar redirects permite que roteadores maliciosos redirecionem tráfego (Man-in-the-Middle).
echo -e "\n[Verificação] ICMP Redirects"
REDIRECTS_ENABLED=$(sysctl -n net.ipv4.conf.all.accept_redirects 2>/dev/null)
if [ "$REDIRECTS_ENABLED" -eq 1 ]; then
    check_fail "ICMP Redirects habilitado (net.ipv4.conf.all.accept_redirects = 1)."
else
    check_pass "ICMP Redirects desabilitado globalmente."
fi

# 1.3 Modo Promíscuo
# Interfaces em modo promíscuo podem estar sniffando tráfego lateral.
echo -e "\n[Verificação] Interfaces em Modo Promíscuo"
if ip link | grep -q "PROMISC"; then
    check_fail "Interface de rede detectada em modo PROMISCUO (Risco de Sniffing)."
    ip link | grep "PROMISC"
else
    check_pass "Nenhuma interface em modo promíscuo detectada."
fi

# 1.4 Vizinhança de Rede (ARP)
# Muitos vizinhos na mesma L2 indicam rede plana (falta de micro-segmentação).
echo -e "\n[Verificação] Densidade de Vizinhos (ARP)"
NEIGHBORS=$(ip neigh show | grep -v FAILED | wc -l)
if [ "$NEIGHBORS" -gt 20 ]; then
    check_warn "Muitos vizinhos ARP detectados ($NEIGHBORS). Considere micro-segmentação (VLANs/PVLANs)."
else
    check_pass "Tabela ARP com tamanho razoável ($NEIGHBORS vizinhos)."
fi

# ==============================================================================
# 2. Testes de Isolamento entre Serviços (Service Isolation)
# ==============================================================================
echo -e "\n--- ZT-02: Isolamento entre Serviços ---"

# 2.1 Visibilidade de Processos (/proc)
# Usuários não devem ver processos de outros usuários.
echo "[Verificação] Isolamento de Processos (mount /proc)"
if grep -E "proc.*hidepid=[12]" /proc/mounts > /dev/null 2>&1; then
    check_pass "/proc montado com hidepid (Isolamento de processos ativo)."
else
    check_warn "/proc acessível a todos (hidepid não detectado). Usuários podem listar processos uns dos outros."
fi

# 2.2 Serviços Web/DB rodando como Root
# Verifica se os processos filhos de serviços comuns estão rodando como root.
echo -e "\n[Verificação] Execução de Serviços (Non-Root)"
SERVICES="apache2 nginx mysqld postgres"
for service in $SERVICES; do
    if pgrep -x "$service" > /dev/null; then
        # Conta processos desse serviço rodando como root
        ROOT_PROCS=$(ps -C "$service" -o user= | grep "root" | wc -l)
        TOTAL_PROCS=$(ps -C "$service" -o user= | wc -l)

        # Geralmente 1 master process é root, os workers devem ser user limitado
        if [ "$ROOT_PROCS" -eq "$TOTAL_PROCS" ] && [ "$TOTAL_PROCS" -gt 0 ]; then
             check_fail "Todos os processos do serviço '$service' estão rodando como ROOT!"
        elif [ "$TOTAL_PROCS" -gt 0 ]; then
             check_pass "Serviço '$service' detectado com workers não-root."
        fi
    fi
done

# 2.3 Permissões do Diretório Home
# Usuários não devem conseguir entrar no diretório home de outros.
echo -e "\n[Verificação] Permissões de /home"
INSECURE_HOMES=$(find /home -maxdepth 1 -type d -perm -o+r -o -perm -o+x 2>/dev/null)
if [ -n "$INSECURE_HOMES" ]; then
    check_warn "Diretórios home com permissão de leitura/execução para 'outros':"
    echo "$INSECURE_HOMES"
else
    check_pass "Diretórios em /home parecem isolados (sem acesso world)."
fi

# ==============================================================================
# 3. Testes de Acesso Mínimo Necessário (Least Privilege)
# ==============================================================================
echo -e "\n--- ZT-03: Acesso Mínimo Necessário ---"

# 3.1 Sudoers NOPASSWD
# Permitir sudo sem senha quebra o princípio de verificação contínua.
echo "[Verificação] Regras Sudo 'NOPASSWD'"
if grep -r "NOPASSWD" /etc/sudoers /etc/sudoers.d/ 2>/dev/null | grep -v "^#"; then
    check_fail "Regras NOPASSWD encontradas no sudoers (Risco Alto)."
else
    check_pass "Nenhuma regra NOPASSWD ativa encontrada."
fi

# 3.2 Arquivos World-Writable em locais críticos
# Ninguém deve poder escrever em /etc, /bin, /sbin, /boot.
echo -e "\n[Verificação] Arquivos World-Writable em /etc"
WW_FILES=$(find /etc -type f -perm -0002 2>/dev/null)
if [ -n "$WW_FILES" ]; then
    check_fail "Arquivos com permissão de escrita para todos (World-Writable) em /etc:"
    echo "$WW_FILES"
else
    check_pass "Nenhum arquivo world-writable encontrado em /etc."
fi

# 3.3 Contas sem Senha
echo -e "\n[Verificação] Contas sem senha (/etc/shadow)"
# Verifica campos de senha vazios ou incorretos (considerando que shadow não é legível por user comum, precisa de root pra rodar esse script)
if [ -r /etc/shadow ]; then
    EMPTY_PASS=$(awk -F: '($2 == "" || $2 == "!") { print $1 }' /etc/shadow)
    # ! geralmente significa bloqueado, mas vazio é perigoso. Vamos focar no vazio.
    REAL_EMPTY=$(awk -F: '$2 == "" { print $1 }' /etc/shadow)
    if [ -n "$REAL_EMPTY" ]; then
        check_fail "Usuários com senha vazia detectados: $REAL_EMPTY"
    else
        check_pass "Nenhum usuário com senha vazia encontrado."
    fi
else
    check_info "Não foi possível ler /etc/shadow (Permissão negada ou não existe). Execute como root."
fi

echo -e "\n=== Testes Zero Trust Concluídos ==="
