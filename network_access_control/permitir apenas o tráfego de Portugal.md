Este script é semelhante ao script anterior, mas ele permite tráfego apenas de endereços IP de Portugal e bloqueia tráfego de endereços IP maliciosos.

Aqui está uma explicação mais detalhada de cada função:

# URL para a lista de IPs de Portugal no formato CIDR
PORTUGAL_IPS_URL="http://www.ipdeny.com/ipblocks/data/countries/pt.zone"

# URL para a lista de IPs maliciosos (substitua pelo URL apropriado)
BLOCKLIST_URL="https://example.com/malicious-ips.txt"
Estas linhas definem as URLs para as listas de IPs de Portugal e de IPs maliciosos.

# Crie conjuntos IPSET para Portugal e para a lista de bloqueio
ipset create portugal hash:net
ipset create blocklist hash:ip
Estas linhas criam dois conjuntos IPSET, um para Portugal e outro para a lista de bloqueio.

# Adicione faixas de IPs associadas a Portugal
wget -O - $PORTUGAL_IPS_URL | xargs -I {} ipset add portugal {}
Esta linha usa o comando wget para baixar uma lista de faixas de IPs associadas a Portugal. Em seguida, usa o comando xargs para adicionar cada faixa de IP ao conjunto portugal.

# Adicione IPs maliciosos à lista de bloqueio
wget -O - $BLOCKLIST_URL | xargs -I {} ipset add blocklist {}
Esta linha é semelhante à anterior, mas adiciona IPs maliciosos à lista de bloqueio.

# Crie uma regra iptables para permitir tráfego de Portugal
iptables -A INPUT -m set --match-set portugal src -j ACCEPT
Esta linha cria uma regra iptables que permite tráfego de qualquer endereço IP que esteja no conjunto portugal.

# Crie uma regra iptables para bloquear tráfego de IPs maliciosos
iptables -A INPUT -m set --match-set blocklist src -j DROP
Esta linha cria uma regra iptables que bloqueia tráfego de qualquer endereço IP que esteja no conjunto blocklist.

# Bloqueie todo o tráfego não especificado
iptables -A INPUT -j DROP
Esta linha adiciona uma regra iptables que bloqueia todo o tráfego que não seja especificado por uma regra anterior.

# Salve as configurações
service iptables save
service iptables restart
Estas linhas salvam as configurações do iptables e as reinicializam.

Para usar este script, você precisará ter os pacotes ipset e iptables instalados em seu sistema. Em seguida, você pode executá-lo como root com o seguinte comando:

sudo bash /path/to/script.sh
Depois de executar o script, todo o tráfego de endereços IP de Portugal será permitido. Todo o tráfego de endereços IP maliciosos e de outros endereços IP será bloqueado.

Aqui estão algumas dicas para usar este script:

Você pode usar o comando ipset list para visualizar os conjuntos IPSET.
Você pode usar o comando iptables -L para visualizar as regras iptables.
Você pode usar o comando iptables -D para remover uma regra iptables.
Você pode usar o comando iptables -F para limpar todas as regras iptables.
Espero que isso ajude!
