#!/bin/bash

protection_mode=0

function show_menu() {
    clear
    echo "============ Menu de Proteção DDoS ============"
    echo "1. Ativar Modo de Proteção 1 (Regras Básicas contra DDoS)"
    echo "2. Ativar Modo de Proteção 2 (Regras Normais)"
    echo "3. Ativar Modo de Proteção 3 (Regras Complexas com Blacklist)"
    echo "4. Desativar Modo de Proteção"
    echo "5. Sair"
    echo "Lembre-se de testar o script em um ambiente controlado antes de aplicá-lo em um ambiente de produção para evitar bloqueios inesperados."
    echo "==============================================="

    read -p "Digite o número da opção desejada: " menu_option

    case $menu_option in
        1)
            enable_protection 1
            ;;
        2)
            enable_protection 2
            ;;
        3)
            enable_protection 3
            ;;
        4)
            disable_protection
            ;;
        5)
            exit_script
            ;;
        *)
            echo "Opção inválida. Tente novamente."
            read -p "Pressione Enter para continuar..."
            show_menu
            ;;
    esac
}

function enable_protection() {
    protection_mode=$1
    configure_firewall
    echo "Modo de Proteção $protection_mode ativado com sucesso!"
    read -p "Pressione Enter para continuar..."
    show_menu
}

function disable_protection() {
    protection_mode=0
    clear_firewall_rules
    echo "Modo de Proteção desativado."
    read -p "Pressione Enter para continuar..."
    show_menu
}

function exit_script() {
    clear_firewall_rules
    echo "Saindo do script. Adeus!"
    echo "Lembre-se de testar o script em um ambiente controlado antes de aplicá-lo em um ambiente de produção para evitar bloqueios inesperados."
    exit 0
}

function configure_firewall() {
    case $protection_mode in
        1)
            configure_basic_rules
            ;;
        2)
            configure_normal_rules
            ;;
        3)
            configure_complex_rules
            ;;
    esac
}

function configure_basic_rules() {
    # Limpar regras antigas
    iptables -F
    iptables -X

    # Definir política padrão para DROP
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT DROP

    # Permitir loopback
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT

    # Permitir tráfego já estabelecido e relacionado
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

    # Permitir ICMP (ping)
    iptables -A INPUT -p icmp -j ACCEPT
    iptables -A OUTPUT -p icmp -j ACCEPT

    # Permitir tráfego em portas específicas (substitua XX pelas portas necessárias)
    iptables -A INPUT -p tcp --dport XX -j ACCEPT
    iptables -A OUTPUT -p tcp --sport XX -j ACCEPT

    # Logar tráfego bloqueado
    iptables -A INPUT -j LOG --log-prefix "Blocked: " --log-level 7

    echo "Regras básicas configuradas."
}

function configure_normal_rules() {
    # Limpar regras antigas
    iptables -F
    iptables -X

    # Definir política padrão para DROP
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT DROP

    # Permitir loopback
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT

    # Permitir tráfego já estabelecido e relacionado
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

    # Permitir ICMP (ping)
    iptables -A INPUT -p icmp -j ACCEPT
    iptables -A OUTPUT -p icmp -j ACCEPT

    # Permitir tráfego apenas nas portas específicas (substitua XX pelas portas necessárias)
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT  # SSH
    iptables -A OUTPUT -p tcp --sport 22 -j ACCEPT

    iptables -A INPUT -p tcp --dport 80 -j ACCEPT  # HTTP
    iptables -A OUTPUT -p tcp --sport 80 -j ACCEPT

    iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
    iptables -A OUTPUT -p tcp --sport 443 -j ACCEPT

    # Bloquear acesso ao serviço de echo (evita ataques de reflexão)
    iptables -A INPUT -p udp --dport 7 -j DROP

    # Bloquear tráfego de broadcast
    iptables -A INPUT -m pkttype --pkt-type broadcast -j DROP

    # Limitar conexões ICMP para evitar ataques de ping flood
    iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

    # Logar tráfego bloqueado
    iptables -A INPUT -j LOG --log-prefix "Blocked: " --log-level 7

    echo "Regras normais configuradas."
}

function configure_complex_rules() {
    # Limpar regras antigas
    iptables -F
    iptables -X

    # Definir política padrão para DROP
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT DROP

    # Loopback permitido
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT

    # Proteção contra SYN flood
    iptables -A INPUT -p tcp --syn -m limit --limit 1/s -j ACCEPT

    # Proteção contra ping of death
    iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

    # Proteção contra port scanners
    iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
    iptables -A INPUT -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
    iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
    iptables -A INPUT -p tcp --tcp-flags FIN,RST FIN,RST -j DROP
    iptables -A INPUT -p tcp --tcp-flags ACK,FIN FIN -j DROP
    iptables -A INPUT -p tcp --tcp-flags ACK,PSH PSH -j DROP
    iptables -A INPUT -p tcp --tcp-flags ACK,URG URG -j DROP

    # Bloquear tráfego malicioso conhecido
    iptables -A INPUT -m string --string "cmd.exe" -j DROP
    iptables -A INPUT -m string --string "root" -j DROP
    iptables -A INPUT -m string --string "sh" -j DROP
    iptables -A INPUT -m string --string "wget" -j DROP

    # Bloquear conexões de países específicos (substitua XX pelos códigos dos países desejados)
    iptables -A INPUT -m geoip --src-cc XX -j DROP

    # Permitir tráfego nas portas necessárias para seus serviços
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT  # SSH
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT  # HTTP
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS

    # Adiciona regras iptables de rastreamento
    iptables_track_rule "TRACK_PROWLER"
    iptables_track_rule "TRACK_ATTACKER"

    # Chamando a função iptables_register_suspects para configurar o registro de acessos suspeitos.
    # Os parâmetros são semelhantes aos explicados acima.

    msg "Configurando sistema de registo de acessos suspeitos..."
    iptables_register_suspects "TRACK_PROWLER" "prowler" 6 10 60 3600

    # Chamando a função iptables_register_suspects para configurar o registro de ataques.
    # Os parâmetros são semelhantes aos explicados acima.

    msg "Configurando sistema de registo de ataques..."
    iptables_register_suspects "TRACK_ATTACKER" "attacker" 6 10 60 3600

    # Mensagem indicando que as regras complexas, incluindo o sistema de registro, foram configuradas com sucesso.
    echo "Regras complexas com blacklist configuradas."
}

# Função para registrar IPs suspeitos
function iptables_register_suspects() {
    track_name=$1
    prefix=$2
    rapid_limit=$3
    rapid_seconds=$4
    fast_limit=$5
    medium_seconds=$6

    # Critérios de Tempo para a Função iptables_register_suspects:
    # - Tempo de análise rápido: 10 segundos (rápido_limit=6)"
    # - Tempo de análise médio: 60 segundos (fast_limit=10, medium_seconds=60)"
    # - Limite de acessos nos primeiros 10 segundos: 6"
    # - Limite de acessos nos primeiros 60 segundos: 10"
    # - Limite de acessos nos primeiros 300 segundos: 60"

    # Variáveis de configuração
    LOG_LIMIT="10/min"
    LOG_LIMIT_BURST="20"

    # Criar cadeias personalizadas
    iptables -N TRACK_DDOS 2>/dev/null
    iptables -N ANTI_DDOS
    iptables -N ANTI_DDOS_
    iptables -A TRACK_DDOS -j ANTI_DDOS
    iptables -A ANTI_DDOS -i e+ -j ANTI_DDOS_
    iptables -A ANTI_DDOS -i p+ -j ANTI_DDOS_
    iptables -A ANTI_DDOS -i w+ -j ANTI_DDOS_

    # Adicione regras para banir IPs automaticamente
    iptables -A ANTI_DDOS_ -m recent --name ddos-rapid --update --rttl --seconds 10 -j RETURN
    iptables -A ANTI_DDOS_ -m recent --name ddos-rapid --set
    iptables -A ANTI_DDOS_ -m hashlimit --hashlimit-name ddos-rapid --hashlimit-above 100/m --hashlimit-mode srcip --hashlimit-htable-expire 10000 -j RETURN
    iptables -A ANTI_DDOS_ -m recent --name ddos-fast --update --rttl --seconds 60 -j RETURN
    iptables -A ANTI_DDOS_ -m recent --name ddos-fast --set
    iptables -A ANTI_DDOS_ -m hashlimit --hashlimit-name ddos-fast --hashlimit-above 1/m --hashlimit-mode srcip --hashlimit-htable-expire 60000 -j RETURN
    iptables -A ANTI_DDOS_ -m recent --name ddos-medium --update --rttl --seconds 300 -j RETURN
    iptables -A ANTI_DDOS_ -m recent --name ddos-medium --set

    # Banir automaticamente IPs suspeitos
    iptables -A ANTI_DDOS_ -j DROP
    msg "Sistema de registo de ddos e banir IPs automaticamente configurado com sucesso!"
}

function download_blacklist() {
    # Baixar listas de bloqueio
    curl -o /tmp/blacklist1.txt https://lists.blocklist.de/lists/all.txt
    curl -o /tmp/blacklist2.txt https://www.badips.com/get/list/any/2
    curl -o /tmp/blacklist3.txt https://www.openbl.org/lists/base_all.txt
    curl -o /tmp/blacklist4.txt https://rules.emergingthreats.net/blockrules/compromised-ips.txt
    curl -o /tmp/blacklist5.txt https://www.spamhaus.org/drop/drop.txt
    # Adicionar mais comandos curl conforme necessário
    # Download, combinação e aplicação da blacklist
}

####################################################
# Abra o crontab para edição
# crontab -e

# Adicione a seguinte linha para atualizar a lista a cada 48 horas
# 0 */48 * * * /caminho/para/o/seu/script.sh

# Guarde e saia do editor
####################################################


# Combinação de listas de bloqueio
function combine_blacklists() {
    cat /tmp/blacklist1.txt /tmp/blacklist2.txt /tmp/blacklist3.txt /tmp/blacklist4.txt /tmp/blacklist5.txt > /tmp/combined_blacklist.txt
    # Adicionar mais listas conforme necessário
}

# Aplicar a lista de bloqueio ao iptables com contagem
function apply_blacklist_count() {
    echo "Aplicando a lista de bloqueio ao iptables com contagem..."

    # Criar a tabela recente se não existir
    iptables -N RECENT_BLACKLIST 2>/dev/null

    blocked_ips=0  # Contador de IPs bloqueados

    if [ -f /tmp/combined_blacklist.txt ]; then
        while read -r ip; do
            # Verificar se o IP já atingiu a contagem máxima nos últimos 60 segundos
            iptables -A RECENT_BLACKLIST -m recent --rcheck --seconds 60 --hitcount 5 --name blacklist --rsource -j RETURN

            # Adicionar o IP à lista recente e aplicar a regra de bloqueio
            iptables -A RECENT_BLACKLIST -m recent --set --name blacklist --rsource
            iptables -A INPUT -s "$ip" -j DROP

            blocked_ips=$((blocked_ips + 1))
        done < /tmp/combined_blacklist.txt
    else
        echo "Arquivo /tmp/combined_blacklist.txt não encontrado."
    fi

    # Limpar a tabela recente no final
    iptables -D RECENT_BLACKLIST -j RETURN
    iptables -F RECENT_BLACKLIST
    iptables -X RECENT_BLACKLIST

    echo "Lista de bloqueio aplicada ao iptables com contagem."
    echo "Total de IPs bloqueados: $blocked_ips"
}

# Função para adicionar regras de rastreamento do iptables
function iptables_track_rule() {
    local chain_name=$1

    iptables -N $chain_name
    iptables -A $chain_name -j LOG --log-prefix "IPTABLES_TRACK: "
    iptables -A $chain_name -j DROP
}

# Função para configurar configurações do kernel
function configure_kernel_settings() {
    # Define o nível de mensagens do kernel a serem impressas.
    sysctl -w kernel.printk="4 4 1 7"

    # Define o tempo em segundos que o kernel espera antes de reiniciar automaticamente após um pânico.
    sysctl -w kernel.panic=10

    # Habilita ou desabilita as teclas SysRq. Se definido como 1, as teclas SysRq estão habilitadas.
    sysctl -w kernel.sysrq=0

    # Define se o sistema filtra pacotes com endereços de origem falsificados.
    sysctl -w net.ipv4.conf.all.rp_filter=1

    # Configurações do firewall no kernel
    sysctl -w kernel.shmmax=4294967296
    sysctl -w kernel.shmall=4194304
    sysctl -w kernel.core_uses_pid=1
    sysctl -w kernel.msgmnb=65536
    sysctl -w kernel.msgmax=65536
    sysctl -w vm.swappiness=20
    sysctl -w vm.dirty_ratio=80
    sysctl -w vm.dirty_background_ratio=5
    sysctl -w fs.file-max=2097152
    sysctl -w net.core.netdev_max_backlog=262144
    sysctl -w net.core.rmem_default=31457280
    sysctl -w net.core.rmem_max=67108864
    sysctl -w net.core.wmem_default=31457280
    sysctl -w net.core.wmem_max=67108864
    sysctl -w net.core.somaxconn=65535
    sysctl -w net.core.optmem_max=25165824
    sysctl -w net.ipv4.neigh.default.gc_thresh1=4096
    sysctl -w net.ipv4.neigh.default.gc_thresh2=8192
    sysctl -w net.ipv4.neigh.default.gc_thresh3=16384
    sysctl -w net.ipv4.neigh.default.gc_interval=5
    sysctl -w net.ipv4.neigh.default.gc_stale_time=120
    sysctl -w net.netfilter.nf_conntrack_max=10000000
    sysctl -w net.netfilter.nf_conntrack_tcp_loose=0
    sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=1800
    sysctl -w net.netfilter.nf_conntrack_tcp_timeout_close=10
    sysctl -w net.netfilter.nf_conntrack_tcp_timeout_close_wait=10
    sysctl -w net.netfilter.nf_conntrack_tcp_timeout_fin_wait=20
    sysctl -w net.netfilter.nf_conntrack_tcp_timeout_last_ack=20
    sysctl -w net.netfilter.nf_conntrack_tcp_timeout_syn_recv=20
    sysctl -w net.netfilter.nf_conntrack_tcp_timeout_syn_sent=20
    sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=10
    sysctl -w net.ipv4.tcp_slow_start_after_idle=0
    sysctl -w net.ipv4.ip_local_port_range="1024 65000"
    sysctl -w net.ipv4.ip_no_pmtu_disc=1
    sysctl -w net.ipv4.route.flush=1
    sysctl -w net.ipv4.route.max_size=8048576
    sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1
    sysctl -w net.ipv4.icmp_ignore_bogus_error_responses=1
    sysctl -w net.ipv4.tcp_congestion_control=htcp
    sysctl -w net.ipv4.tcp_mem="65536 131072 262144"
    sysctl -w net.ipv4.udp_mem="65536 131072 262144"
    sysctl -w net.ipv4.tcp_rmem="4096 87380 33554432"
    sysctl -w net.ipv4.udp_rmem_min=16384
    sysctl -w net.ipv4.tcp_wmem="4096 87380 33554432"
    sysctl -w net.ipv4.udp_wmem_min=16384
    sysctl -w net.ipv4.tcp_max_tw_buckets=1440000
    sysctl -w net.ipv4.tcp_tw_recycle=0
    sysctl -w net.ipv4.tcp_tw_reuse=1
    sysctl -w net.ipv4.tcp_max_orphans=400000
    sysctl -w net.ipv4.tcp_window_scaling=1
    sysctl -w net.ipv4.tcp_rfc1337=1
    sysctl -w net.ipv4.tcp_syncookies=1
    sysctl -w net.ipv4.tcp_synack_retries=1
    sysctl -w net.ipv4.tcp_syn_retries=2
    sysctl -w net.ipv4.tcp_max_syn_backlog=16384
    sysctl -w net.ipv4.tcp_timestamps=1
    sysctl -w net.ipv4.tcp_sack=1
    sysctl -w net.ipv4.tcp_fack=1
    sysctl -w net.ipv4.tcp_ecn=2
    sysctl -w net.ipv4.tcp_fin_timeout=10
    sysctl -w net.ipv4.tcp_keepalive_time=600
    sysctl -w net.ipv4.tcp_keepalive_intvl=60
    sysctl -w net.ipv4.tcp_keepalive_probes=10
    sysctl -w net.ipv4.tcp_no_metrics_save=1
    sysctl -w net.ipv4.ip_forward=0
    sysctl -w net.ipv4.conf.all.accept_redirects=0
    sysctl -w net.ipv4.conf.all.send_redirects=0
    sysctl -w net.ipv4.conf.all.accept_source_route=0
    sysctl -w net.ipv4.conf.all.rp_filter=1
}

function clear_firewall_rules() {
    # Limpar regras de firewall aqui
    iptables -F
    echo "Regras de firewall limpas."
}

# Iniciar o menu
while true; do
    show_menu
done
