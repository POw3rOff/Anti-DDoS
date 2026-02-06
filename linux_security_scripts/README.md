# Linux Security Scripts

Este diretório contém scripts de segurança para monitoramento, detecção e resposta a incidentes em servidores Linux.

## Scripts Disponíveis

### 1. Simple Honeypot (`simple_honeypot.sh`)
Um honeypot leve que simula um serviço SSH falso na porta 2222.
- **Função:** Detecta e registra tentativas de conexão e varreduras de porta.
- **Uso:** `./simple_honeypot.sh` (Execute em background com `nohup` ou `screen` se necessário).
- **Logs:** Salvos em `honeypot.log` no mesmo diretório.
- **Configuração:** Edite `simple_honeypot.py` para alterar a porta ou banner.

### 2. Monitor de Tráfego de Saída (`outbound_monitor.sh`)
Monitora conexões de rede estabelecidas que saem para portas não padrão.
- **Função:** Ajuda a detectar reverse shells, malwares comunicando com C2, ou exfiltração de dados.
- **Uso:** `./outbound_monitor.sh` (Requer root).
- **Configuração:** Edite a variável `WHITELIST_PORTS` no script para adicionar portas confiáveis.
- **Sugestão:** Adicione ao cron para rodar periodicamente (ex: a cada 5 minutos).

### 3. Lockdown de Emergência (`lockdown.sh`)
Script para resposta rápida a incidentes.
- **Função:** Bloqueia todo o tráfego de entrada (exceto SSH e Loopback) instantaneamente.
- **Uso:**
  - Ativar: `./lockdown.sh on`
  - Desativar (Restaurar regras anteriores): `./lockdown.sh off`
- **Nota:** O script faz um backup das regras iptables atuais em `/tmp/iptables.lockdown.backup` antes de aplicar o bloqueio.

## Requisitos
- Python 3 (para o Honeypot)
- `netstat` ou `ss` (para o Monitor de Tráfego)
- `iptables` (para o Lockdown)
- Privilégios de root para a maioria das operações.

## Instalação
Certifique-se de dar permissão de execução aos scripts:
```bash
chmod +x *.sh
```
