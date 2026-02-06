#!/bin/bash
# Deteção de Comunicação C2

echo '--- Deteção de Potencial Tráfego C2 ---'

echo '[*] Conexões externas suspeitas (>1024):'
netstat -antup 2>/dev/null | grep ESTABLISHED | grep -v '127.0.0.1' | awk '{print $5, $7}'

echo '[*] Shells com conexões (Reverse Shell):'
lsof -i -n -P | grep -E 'bash|sh|nc|netcat|python|perl|php' | grep ESTABLISHED
echo 'Análise C2 concluída.'
