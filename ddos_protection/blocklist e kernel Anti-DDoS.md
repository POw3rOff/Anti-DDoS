um script de proteção anti-DDoS que pode ser usado para fortalecer o primeiro layer de um servidor. Ele funciona baixando e combinando listas de IPs de blocklists conhecidas, e então adicionando essas regras ao iptables. O script também configura algumas variáveis de sysctl para aumentar a segurança do servidor.

Aqui está uma explicação mais detalhada de cada seção do script:


#Proteção Anti-DDoS: Reforçando o Primeiro Layer

Esta seção do script baixa e combina listas de IPs de blocklists conhecidas. As blocklists são listas de IPs que são conhecidos por serem usados para ataques DDoS. O script também permite que você especifique uma lista de países que deseja permitir o tráfego, para que você possa evitar bloquear tráfego legítimo.


#Firewall kernel Anti-DDoS: Reforçando /sysctl.conf

Esta seção do script configura algumas variáveis de sysctl para aumentar a segurança do servidor. As variáveis de sysctl são usadas para controlar o comportamento do kernel do Linux. As variáveis que o script configura são:

net.ipv4.conf.*.rp_filter=1: Esta variável impede que o servidor responda a pacotes com endereços IP de origem falsificados.

net.ipv4.conf.*.accept_redirects=0: Esta variável impede que o servidor aceite pacotes ICMP Redirect. Os pacotes ICMP Redirect são usados pelos atacantes para redirecionar o tráfego de rede para seus próprios servidores.
net.ipv4.conf.*.accept_source_route=0: Esta variável impede que o servidor aceite pacotes com roteamento de origem. Os pacotes com roteamento de origem são usados pelos atacantes para rotear o tráfego de rede por meio de seus próprios servidores.

net.ipv4.icmp_echo_ignore_broadcasts=1: Esta variável impede que o servidor responda a pings direcionados ao endereço de broadcast. Os pings direcionados ao endereço de broadcast são usados pelos atacantes para amplificar ataques de Smurf.

net.ipv4.tcp_syncookies=1: Esta variável ativa os SYN Cookies. Os SYN Cookies são usados para mitigar ataques de TCP SYN Flood.

net.ipv4.tcp_timestamps=1: Esta variável desativa a notificação do tempo contínuo de operação do sistema. Isso pode dificultar para que os atacantes identifiquem a versão do kernel do servidor.

Para usar este script, você precisaria salvá-lo como um arquivo com a extensão .sh e executá-lo como root. Por exemplo, você poderia salvar o script como anti-ddos.sh e executá-lo com o seguinte comando:

sudo bash anti-ddos.sh

O script irá baixar e combinar as listas de blocklists, e então adicionar as regras ao iptables. Ele também irá configurar as variáveis de sysctl especificadas.

É importante observar que este script é apenas um ponto de partida. Você pode precisar ajustá-lo para atender às suas necessidades específicas. Por exemplo, você pode precisar adicionar ou remover blocklists, ou pode precisar alterar as configurações de sysctl.
