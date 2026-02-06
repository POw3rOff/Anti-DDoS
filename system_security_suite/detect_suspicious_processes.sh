#!/bin/bash
#
# 6. Detetor de Processos Suspeitos
# Autor: Jules (AI Agent)
# Descrição: Identifica processos com alto consumo ou comportamento anômalo.

echo "=== Análise de Processos em Execução ==="

# 1. Processos consumindo muita CPU/Memória
echo "[*] Top 5 Processos por CPU:"
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 6
echo ""

echo "[*] Top 5 Processos por Memória:"
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -n 6
echo ""

# 2. Processos rodando de diretórios temporários (/tmp, /dev/shm, /var/tmp)
# Malware frequentemente roda daqui
echo "[*] Procurando processos executando de /tmp, /dev/shm ou /var/tmp..."
# Lista links simbólicos em /proc/*/exe que apontam para essas pastas
# Requer root para ver todos os processos
found_suspicious=0
for pid in $(ps -ef | awk 'NR>1 {print $2}'); do
    if [ -d "/proc/$pid" ]; then
        exe=$(readlink -f /proc/$pid/exe 2>/dev/null)
        if [[ "$exe" == /tmp/* ]] || [[ "$exe" == /dev/shm/* ]] || [[ "$exe" == /var/tmp/* ]]; then
             echo "[!] ALERTA: Processo suspeito (PID $pid) rodando de $exe"
             found_suspicious=1
        fi

        # 3. Binários deletados (mas ainda rodando)
        if [[ "$exe" == *" (deleted)"* ]]; then
             # Ignora alguns comuns que fazem update on-the-fly, mas avisa
             echo "[?] AVISO: Processo rodando binário deletado (PID $pid): $exe"
        fi
    fi
done

if [ "$found_suspicious" -eq 0 ]; then
    echo "[OK] Nenhum processo rodando de diretórios temporários detectado."
fi

# 4. Processos com nomes estranhos ou disfarçados (ex: espaços em branco)
# (Difícil detectar deterministicamente, mas podemos checar cmdline vazia ou estranha)

echo "=== Análise Concluída ==="
