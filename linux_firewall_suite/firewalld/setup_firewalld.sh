#!/bin/bash
#
# Script de Configuração Firewalld
# Autor: Jules (AI Agent)

# Verifica se o firewalld está rodando
if ! systemctl is-active --quiet firewalld; then
    echo "Firewalld não está rodando. Iniciando..."
    systemctl start firewalld
fi

echo "Configurando Firewalld..."

# Define a zona padrão como 'public' (padrão comum)
firewall-cmd --set-default-zone=public

# --- Configurações Básicas ---

# Permitir serviços essenciais na zona pública
firewall-cmd --zone=public --add-service=ssh --permanent
firewall-cmd --zone=public --add-service=http --permanent
firewall-cmd --zone=public --add-service=https --permanent

# Remover serviços inseguros ou não utilizados (ex: cockpit, dhcpv6-client) se não necessários
firewall-cmd --zone=public --remove-service=cockpit --permanent
firewall-cmd --zone=public --remove-service=dhcpv6-client --permanent

# --- Configurações Avançadas (Rich Rules) ---

# 1. Rate Limiting para SSH (Alternativa ao fail2ban para camada de rede)
# Rejeita conexões SSH se excederem 3 por minuto
firewall-cmd --permanent --zone=public --add-rich-rule='rule service name="ssh" family="ipv4" source address="0.0.0.0/0" limit value="3/m" accept'

# 2. Bloquear um IP ou Subrede específica (Blacklist)
# firewall-cmd --permanent --zone=public --add-rich-rule='rule family="ipv4" source address="192.168.50.0/24" reject'

# 3. Logar pacotes dropados (Kernel logging)
firewall-cmd --set-log-denied=all

# 4. Modo Pânico (Apenas informativo - Comentado)
# Se estiver sob ataque massivo e quiser cortar tudo:
# firewall-cmd --panic-on

# Recarregar para aplicar as mudanças
firewall-cmd --reload

echo "Configuração concluída. Regras atuais:"
firewall-cmd --list-all
