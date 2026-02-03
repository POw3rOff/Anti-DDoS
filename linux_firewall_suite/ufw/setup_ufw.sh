#!/bin/bash
#
# Script de Configuração UFW (Uncomplicated Firewall)
# Autor: Jules (AI Agent)
# Nota: Execute como root (sudo).

echo "Configurando UFW..."

# 1. Resetar regras para o padrão
ufw --force reset

# 2. Definir políticas padrão (Segurança Básica)
# Bloquear tudo que entra, permitir tudo que sai
ufw default deny incoming
ufw default allow outgoing

# 3. Regras de Aplicação (Básico)

# SSH (Porta 22) - Usando 'limit' para proteção básica contra força bruta (Avançado)
# 'limit' bloqueia o IP se tentar logar 6 vezes em 30 segundos
ufw limit 22/tcp comment 'SSH Limit'

# Web Server
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# 4. Regras Avançadas / Específicas

# Permitir acesso total apenas de um IP de Gerenciamento (Exemplo)
# ufw allow from 192.168.1.50 to any

# Permitir uma sub-rede específica em uma porta específica (ex: Banco de Dados interno)
# ufw allow from 10.0.0.0/8 to any port 5432

# 5. Logging (Logs do Kernel)
# Níveis: off, low, medium, high, full. 'low' é recomendado para não encher o disco.
ufw logging low

# 6. Ativar o Firewall
# O comando --force evita o prompt de confirmação "Command may disrupt existing ssh connections"
ufw --force enable

echo "Status do UFW:"
ufw status verbose
