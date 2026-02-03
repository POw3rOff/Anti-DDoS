
Este script permite tráfego apenas de endereços IP da Cloudflare e bloqueia tráfego de endereços IP de países específicos.

Aqui está uma explicação mais detalhada de cada função:

# URL para a lista de IPs de Portugal no formato CIDR
CLOUDFLARE_IPS_URL="https://www.cloudflare.com/ips-v4"

# URLs para as listas de IPs associados a países desejados
# Substitua "XX" pelos códigos de dois caracteres dos países que deseja bloquear
BLOCKED_COUNTRIES=("XX")
BLOCKED_COUNTRIES_URL="http://www.ipdeny.com/ipblocks/data/countries"

# Crie conjuntos IPSET para Cloudflare e para os países bloqueados
ipset create cloudflare hash:net
for country in "${BLOCKED_COUNTRIES[@]}"; do
    ipset create $country hash:net
done
Estas linhas definem as URLs para as listas de IPs da Cloudflare e dos países bloqueados.

# Adicione IPs da Cloudflare ao conjunto
wget -O - $CLOUDFLARE_IPS_URL | xargs -I {} ipset add cloudflare {}
Esta linha usa o comando wget para baixar uma lista de IPs da Cloudflare. Em seguida, usa o comando xargs para adicionar cada IP à conjunto cloudflare.

# Adicione IPs dos países bloqueados aos conjuntos correspondentes
for country in "${BLOCKED_COUNTRIES[@]}"; do
    wget -O - "$BLOCKED_COUNTRIES_URL/$country.zone" | xargs -I {} ipset add $country {}
done
Esta linha é semelhante à anterior, mas adiciona IPs dos países bloqueados aos conjuntos correspondentes.

# Crie regras iptables para permitir tráfego da Cloudflare
iptables -A INPUT -m set --match-set cloudflare src -j ACCEPT
Esta linha cria uma regra iptables que permite tráfego de qualquer endereço IP que esteja no conjunto cloudflare.

# Crie regras iptables para bloquear tráfego dos países específicos
for country in "${BLOCKED_COUNTRIES[@]}"; do
    iptables -A INPUT -m set --match-set $country src -j DROP
done
Esta linha cria uma regra iptables que bloqueia tráfego de qualquer endereço IP que esteja em um dos conjuntos de países bloqueados.

# Bloqueie todo o tráfego não especificado
iptables -A INPUT -j DROP
Esta linha adiciona uma regra iptables que bloqueia todo o tráfego que não seja especificado por uma regra anterior.

A diferença é que as regras iptables para bloquear tráfego dos países bloqueados são criadas apenas depois que as listas de IPs dos países bloqueados são atualizadas.

# Agende uma tarefa cron para atualizar as listas de IPs dos países bloqueados a cada 24 horas
(crontab -l 2>/dev/null; echo "0 0 * * * /bin/bash $0 update") | crontab -
Estas linhas agendam uma tarefa cron para atualizar as listas de IPs dos países bloqueados a cada 24 horas. A tarefa cron executa o script com a opção update.


# Salve as configurações
service iptables save
service iptables restart

Estas linhas salvam as configurações do iptables e as reinicializam.

Para usar este script, você precisará ter os pacotes ipset e iptables instalados em seu sistema. Em seguida, você pode executá-lo 

Para usar este script, você precisará ter os pacotes ipset e iptables instalados em seu sistema. Em seguida, você pode executá-lo como root com o seguinte comando:

sudo bash /path/to/script.sh
Depois de executar o script, todo o tráfego de endereços IP da Cloudflare será permitido. Todo o tráfego de endereços IP dos países bloqueados e de outros endereços IP será bloqueado.

Aqui estão algumas dicas para usar este script:

Você pode usar o comando ipset list para visualizar os conjuntos IPSET.
Você pode usar o comando iptables -L para visualizar as regras iptables.
Você pode usar o comando iptables -D para remover uma regra iptables.
Você pode usar o comando iptables -F para limpar todas as regras iptables.
Espero que isso ajude!

Aqui estão algumas observações sobre o script:

O script usa um conjunto IPSET para cada país bloqueado. Isso permite que você bloqueie vários países com um único conjunto iptables.
O script usa um loop para adicionar IPs a cada conjunto IPSET. Isso permite que você adicione facilmente IPs adicionais a um conjunto.
O script usa uma regra iptables para bloquear todo o tráfego não especificado. Isso ajuda a garantir que nenhum tráfego indesejado passe pelo firewall.
Você pode personalizar o script para atender às suas necessidades específicas. Por exemplo, você pode:

Alterar as URLs para as listas de IPs da Cloudflare e dos países bloqueados.
Alterar os códigos de dois caracteres dos países que deseja bloquear.
Adicionar ou remover regras iptables.
