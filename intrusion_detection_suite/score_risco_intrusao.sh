#!/bin/bash
# Cálculo de Score de Risco de Intrusão
# Agrega resultados de verificações para gerar uma pontuação de risco (0-100)

SCORE=0
DETAILS=""

echo "--- Calculando Score de Risco de Intrusão ---"

# 1. Verificar Ficheiros Críticos (+50)
if ./monitorizacao_ficheiros_criticos.sh 2>/dev/null | grep -q "FAILED"; then
    SCORE=$((SCORE + 50))
    DETAILS+="- Alteração em ficheiros críticos detetada (+50)\n"
fi

# 2. Verificar Logins Falhados (+20)
FAIL_COUNT=$(grep "Failed password" /var/log/auth.log 2>/dev/null | wc -l)
if [ "$FAIL_COUNT" -gt 10 ]; then
    SCORE=$((SCORE + 20))
    DETAILS+="- Múltiplos logins falhados ($FAIL_COUNT) (+20)\n"
fi

# 3. Processos Suspeitos (+30)
if ./detecao_execucoes_suspeitas.sh 2>/dev/null | grep -q "SUSPEITO"; then
    SCORE=$((SCORE + 30))
    DETAILS+="- Execução suspeita detetada (+30)\n"
fi

# 4. Portas/Conexões (+10)
# Simplificado
if ss -tun | grep -q "ESTAB"; then
    # Apenas ter conexões não é risco, mas vamos assumir que se houver muitas...
    # Melhor: verificar se c2 deteta algo
    if ./detecao_comunicacao_c2.sh 2>/dev/null | grep -q "Suspeito"; then
        SCORE=$((SCORE + 20))
         DETAILS+="- Potencial comunicação C2 detetada (+20)\n"
    fi
fi

echo "----------------------------------------"
echo "SCORE DE RISCO: $SCORE / 100"
echo "----------------------------------------"
if [ -n "$DETAILS" ]; then
    echo -e "Detalhes do Risco:\n$DETAILS"
fi

if [ "$SCORE" -ge 50 ]; then
    echo "AÇÃO RECOMENDADA: Investigação Imediata!"
    ./alerta_intrusao.sh "Score de risco elevado: $SCORE" "CRITICAL"
elif [ "$SCORE" -ge 20 ]; then
    echo "AÇÃO RECOMENDADA: Revisar logs."
else
    echo "Sistema parece saudável."
fi
