#!/bin/bash

# Script: detecao_rootkits.sh
# Descrição: Detecção básica de sinais de rootkits (Preload, Processos ocultos, Arquivos anômalos).
# Autor: Jules (Agente de IA)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Inspecção de Sinais de Rootkit ===${NC}"

# 1. Verificação de LD_PRELOAD
echo -e "${YELLOW}[*] Verificando LD_PRELOAD...${NC}"
if [ -s /etc/ld.so.preload ]; then
    echo -e "${RED}[!] ALERTA: /etc/ld.so.preload não está vazio! Conteúdo:${NC}"
    cat /etc/ld.so.preload
else
    echo -e "${GREEN}[OK] /etc/ld.so.preload está vazio ou inexistente.${NC}"
fi

if [ -n "$LD_PRELOAD" ]; then
    echo -e "${RED}[!] ALERTA: Variável de ambiente LD_PRELOAD está definida: $LD_PRELOAD${NC}"
fi

# 2. Processos Ocultos (Comparação básica PS vs PROC)
echo -e "${YELLOW}[*] Buscando processos ocultos (PID existe em /proc mas não no ps)...${NC}"
# Obtém lista de PIDs numéricos de /proc
PROC_PIDS=$(ls -d /proc/[0-9]* | grep -o "[0-9]*" | sort -n)
# Obtém lista de PIDs do ps
PS_PIDS=$(ps -e -o pid= | sort -n)

# Encontra PIDs que estão em PROC mas não em PS
HIDDEN_PIDS=$(comm -23 <(echo "$PROC_PIDS") <(echo "$PS_PIDS"))

if [ -n "$HIDDEN_PIDS" ]; then
    # Filtra falsos positivos comuns (processos que morreram durante a execução)
    REAL_HIDDEN=0
    for pid in $HIDDEN_PIDS; do
        if [ -d "/proc/$pid" ]; then
            echo -e "${RED}[!] Processo possivelmente oculto detectado: PID $pid${NC}"
            ls -ld "/proc/$pid"
            cat "/proc/$pid/comm" 2>/dev/null
            REAL_HIDDEN=1
        fi
    done
    if [ $REAL_HIDDEN -eq 0 ]; then
         echo -e "${GREEN}[OK] Nenhum processo oculto persistente encontrado.${NC}"
    fi
else
    echo -e "${GREEN}[OK] Consistência entre /proc e ps verificada.${NC}"
fi

# 3. Arquivos suspeitos em /dev
echo -e "${YELLOW}[*] Verificando arquivos suspeitos em /dev...${NC}"
# Procura arquivos regulares em /dev (normalmente /dev só tem arquivos de dispositivo)
SUSPICIOUS_DEV=$(find /dev -type f -not -path "/dev/shm/*" -not -path "/dev/mqueue/*" 2>/dev/null)
if [ -n "$SUSPICIOUS_DEV" ]; then
    echo -e "${RED}[!] Arquivos regulares encontrados em /dev (comum em rootkits):${NC}"
    echo "$SUSPICIOUS_DEV"
else
    echo -e "${GREEN}[OK] Apenas arquivos de dispositivo encontrados em /dev.${NC}"
fi

echo -e "${YELLOW}=== Verificação Concluída ===${NC}"
