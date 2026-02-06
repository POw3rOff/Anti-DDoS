#!/bin/bash
#
# 7. Verificação de Persistência
# Autor: Jules (AI Agent)
# Descrição: Busca por mecanismos de persistência recém-criados ou modificados.

echo "=== Verificação de Persistência ==="

DAYS=7 # Verificar modificações nos últimos X dias

# 1. Cron Jobs (Usuário e Sistema)
echo "[*] Cron Jobs modificados nos últimos $DAYS dias:"
find /etc/cron* /var/spool/cron -mtime -$DAYS -ls 2>/dev/null
echo ""

# 2. Systemd Services
echo "[*] Serviços Systemd criados/modificados nos últimos $DAYS dias:"
find /etc/systemd/system -name "*.service" -mtime -$DAYS -ls 2>/dev/null
echo ""

# 3. Scripts de Inicialização (rc.local, init.d)
echo "[*] Scripts de init modificados nos últimos $DAYS dias:"
find /etc/rc.local /etc/init.d -mtime -$DAYS -ls 2>/dev/null
echo ""

# 4. Shell Profile/RC (Bashrc, profile)
echo "[*] Arquivos de perfil de shell modificados (Global e Users):"
find /etc/profile /etc/bash.bashrc /etc/profile.d /home/*/.bashrc /home/*/.profile /home/*/.bash_profile -mtime -$DAYS -ls 2>/dev/null
echo ""

# 5. Listar timers do systemd (alternativa ao cron)
echo "[*] Systemd Timers ativos:"
systemctl list-timers --all --no-pager
echo ""

echo "=== Fim da Verificação ==="
