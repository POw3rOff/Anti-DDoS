
Este script cria conjuntos IPSET para Europa e Brasil, adiciona faixas de IPs associadas a cada conjunto e, em seguida, cria uma regra iptables para permitir tráfego de ambos os conjuntos. O tráfego de todos os outros endereços IP é bloqueado.

Aqui está uma explicação mais detalhada de cada função:

# Crie conjuntos IPSET para Europa e Brasil
ipset create europe hash:net
ipset create brazil hash:net

Estas linhas criam dois conjuntos IPSET, um para Europa e outro para Brasil. Os conjuntos IPSET são um tipo de tabela de roteamento baseada em conteúdo que pode ser usada para permitir ou negar tráfego de endereços IP específicos.

# Adicione faixas de IPs associadas à Europa
wget -O - https://iptodns.com/api/ip/country/EU | xargs -I {} ipset add europe {}

Esta linha usa o comando wget para baixar uma lista de faixas de IPs associadas à Europa. Em seguida, usa o comando xargs para adicionar cada faixa de IP ao conjunto europe.

# Adicione faixas de IPs associadas ao Brasil
wget -O - https://iptodns.com/api/ip/country/BR | xargs -I {} ipset add brazil {}

Esta linha é semelhante à anterior, mas adiciona faixas de IPs associadas ao Brasil ao conjunto brazil.

# Crie uma regra iptables para permitir tráfego de Europa e Brasil
iptables -A INPUT -m set --match-set europe src -j ACCEPT
iptables -A INPUT -m set --match-set brazil src -j ACCEPT

Estas linhas criam duas regras iptables. A primeira regra permite tráfego de qualquer endereço IP que esteja no conjunto europe. A segunda regra permite tráfego de qualquer endereço IP que esteja no conjunto brazil.

# Bloqueie todo o tráfego não especificado
iptables -A INPUT -j DROP

Esta linha adiciona uma regra iptables que bloqueia todo o tráfego que não seja especificado por uma regra anterior.

# Salve as configurações
service iptables save
service iptables restart

Estas linhas salvam as configurações do iptables e as reinicializam.

Para usar este script, você precisará ter os pacotes ipset e iptables instalados em seu sistema. Em seguida, você pode executá-lo como root com o seguinte comando:

sudo bash /path/to/script.sh
Depois de executar o script, todo o tráfego de endereços IP na Europa e no Brasil será permitido. Todo o tráfego de outros endereços IP será bloqueado.

Aqui estão algumas dicas para usar este script:

Você pode usar o comando ipset list para visualizar os conjuntos IPSET.
Você pode usar o comando iptables -L para visualizar as regras iptables.
Você pode usar o comando iptables -D para remover uma regra iptables.
Você pode usar o comando iptables -F para limpar todas as regras iptables.
Espero que isso ajude!
