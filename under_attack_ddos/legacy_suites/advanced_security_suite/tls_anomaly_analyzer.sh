#!/bin/bash
#
# 4. Análise de Ligações TLS Estranhas (JA3 / Fingerprints)
# Autor: Jules (AI Agent)
# Descrição: Analisa conexões HTTPS/TLS para destinos incomuns ou portas não-padrão.

echo "[*] Analisando conexões TLS..."

# 1. Conexões na porta 443 para IPs não resolvidos ou suspeitos
# ss -nt state established '( dport = :443 or dport = :8443 )'
echo "    Conexões ativas HTTPS (443/8443):"
ss -nt state established '( dport = :443 or dport = :8443 )' | awk 'NR>1 {print $4, $5}' | while read src dst; do
    dst_ip=$(echo $dst | cut -d: -f1)
    dst_port=$(echo $dst | cut -d: -f2)

    # Tenta resolver reverso (pode ser lento)
    # host $dst_ip
    echo "    -> $dst_ip:$dst_port"
done

# 2. Conexões TLS em portas não padrão (Heurística: tráfego criptografado em porta alta)
# Difícil sem inspeção de pacote (DPI).
# Alternativa: Verificar processos conhecidos (browsers, curl) usando portas estranhas.

# 3. JA3 (Requer tcpdump + ferramenta externa, difícil em bash puro)
# Simulação: Verificar Cipher Suites com nmap/sslscan se disponível
if command -v sslscan >/dev/null; then
    echo "[*] Ferramenta sslscan encontrada. Exemplo de uso:"
    echo "    sslscan <target>"
else
    echo "[*] Sugestão: Instale 'sslscan' ou use 'tshark' para análise JA3 real."
fi

# 4. Checar certificados de conexões ativas (Openssl s_client)
# Pega IPs conectados na 443 e verifica validade do cert
echo "[*] Verificando validade de certificados de hosts conectados (Amostragem)..."
ss -nt state established dport = :443 | awk 'NR>1 {print $5}' | cut -d: -f1 | sort | uniq | head -n 3 | while read ip; do
    echo "    Checando $ip:443..."
    timeout 5 openssl s_client -connect $ip:443 -servername $ip < /dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep "notAfter"
done

echo "[OK] Análise TLS concluída."
