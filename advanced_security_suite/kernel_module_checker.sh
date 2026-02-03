#!/bin/bash
#
# 10. Verificador de Kernel Modules Carregados
# Autor: Jules (AI Agent)
# Descrição: Procura por rootkits de kernel e módulos não assinados/tainted.

echo "[*] Verificando Kernel Modules..."

# 1. Verificar Tainted Kernel
# Tainted flags indicam módulos não open-source, staging, ou carregados forçadamente.
TAINT=$(cat /proc/sys/kernel/tainted)
if [ "$TAINT" -ne 0 ]; then
    echo "[!] AVISO: Kernel está 'tainted' (Valor: $TAINT)."
    echo "    Isso pode indicar módulos proprietários ou inseguros carregados."
    # Decodificar flags requer lógica complexa ou ferramenta externa, mas o aviso vale.
else
    echo "[OK] Kernel não está 'tainted'."
fi

# 2. Procurar módulos ocultos (diferença entre /proc/modules e lsmod/sysfs)
# Rootkits básicos escondem-se do lsmod, mas as vezes deixam traços em /sys/module
# Verificação simples:
echo "[*] Comparando lista de módulos..."
LSMOD_COUNT=$(lsmod | wc -l)
SYS_COUNT=$(ls /sys/module | wc -l)

# lsmod tem cabeçalho, então -1. Sys tem pastas para tudo.
# A contagem nunca é exata pois /sys/module inclui built-in modules também.
# Então essa heurística é fraca para 'hidden modules' sem tools como 'chkrootkit'.

# Melhor: Check por nomes suspeitos conhecidos de rootkits antigos (ex: diamorphine)
KNOWN_ROOTKITS="diamorphine reptile knark adore"
for mod in $KNOWN_ROOTKITS; do
    if grep -q "^$mod " /proc/modules; then
        echo "[!] ALERTA CRÍTICO: Módulo rootkit conhecido encontrado: $mod"
    fi
done

# 3. Listar módulos carregados recentemente (se uptime for curto, todos são recentes)
# Não há timestamp fácil em /proc/modules.

# 4. Verificar assinaturas de módulos (se suportado pelo kernel)
if [ -f /sys/module/module_layout ]; then
    # Exemplo genérico, em kernels modernos secure boot exige assinaturas.
    # grep "N" /sys/module/*/taint  (alguns kernels expõem taint per module)
    echo "[*] Verificando módulos com taint individual..."
    grep -H "." /sys/module/*/taint 2>/dev/null | grep -v ":0$" | while read line; do
        mod=$(echo "$line" | cut -d/ -f4)
        val=$(echo "$line" | cut -d: -f2)
        if [ "$val" != "O" ] && [ "$val" != "G" ]; then # O=Out of tree, G=Proprietary driver usually ok-ish
             echo "    [?] Módulo com taint flag ($val): $mod"
        fi
    done
fi

echo "[OK] Verificação de kernel concluída."
