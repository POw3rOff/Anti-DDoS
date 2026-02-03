#!/bin/bash

# Novo Script Anti-DDoS Consolidado
# Baseado nos scripts originais: "blocklist e kernel Anti-DDoS" e "Menu-2.sh"
# @versão 2.0.0
# @autor AI Assistant (Baseado no código original de poweroff)

#----------------------------------------------------------#
# Configurações Iniciais e Variáveis
#----------------------------------------------------------#

# Diretórios e Arquivos
BLOCKLIST_DIR="/tmp/blocklists"
TEMP_FILE_ALLOW="/tmp/allow_list_temp.txt"
TEMP_FILE_BLOCK="/tmp/block_list_temp.txt"

# Lista de URLs dos serviços de blocklist
declare -A BLOCKLIST_URLS=(
    ["all"]="https://lists.blocklist.de/lists/all.txt"
    ["bruteforcelogin"]="https://lists.blocklist.de/lists/bruteforcelogin.txt"
    ["mail"]="https://lists.blocklist.de/lists/mail.txt"
    ["firehol1"]="https://iplists.firehol.org/files/firehol_level1.netset"
    ["spamhaus"]="https://www.spamhaus.org/drop/drop.txt"
    ["blocklist_de"]="https://lists.blocklist.de/lists/zbdl.txt"
    ["emergingthreats"]="https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt"
    ["binarydefense"]="https://www.binarydefense.com/banlist.txt"
    ["feodo"]="https://feodotracker.abuse.ch/blocklist/?download=ipblocklist"
    ["ransomwaretracker"]="https://ransomwaretracker.abuse.ch/downloads/RW_IPBL.txt"
    ["dshield"]="https://www.dshield.org/ipsascii.html"
    ["zeustracker"]="https://zeustracker.abuse.ch/blocklist.php?download=ipblocklist"
    ["malc0de"]="http://malc0de.com/bl/IP_Blacklist.txt"
    ["malwaredomainlist"]="https://www.malwaredomainlist.com/hostslist/ip.txt"
    ["openbl"]="https://www.openbl.org/lists/base.txt"
    ["ciarmy"]="http://cinsscore.com/list/ci-badguys.txt"
)

# Lista de países a permitir (Whitelist)
COUNTRIES_TO_ALLOW=("PT" "BR" "US")

# Função para mensagens
msg() {
    echo -e "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
}

# Função para verificar se é root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        msg "Erro: Este script precisa ser executado como root."
        return 1
    fi
    return 0
}

#----------------------------------------------------------#
# Funções do Kernel (Sysctl)
#----------------------------------------------------------#

configure_kernel_settings() {
    msg "Configurando parâmetros do kernel (sysctl)..."

    # Backup do sysctl.conf atual
    cp /etc/sysctl.conf /etc/sysctl.conf.bak

    # Configurações de segurança e performance
    sysctl -w kernel.printk="4 4 1 7"
    sysctl -w kernel.panic=10
    sysctl -w kernel.sysrq=0
    sysctl -w net.ipv4.conf.all.rp_filter=1
    sysctl -w net.ipv4.conf.default.rp_filter=1

    # Proteção contra SYN Flood e outros ataques
    sysctl -w net.ipv4.tcp_syncookies=1
    sysctl -w net.ipv4.tcp_max_syn_backlog=2048
    sysctl -w net.ipv4.tcp_synack_retries=2
    sysctl -w net.ipv4.tcp_syn_retries=5

    # Ignorar ICMP Broadcasts (Smurf attack)
    sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1
    sysctl -w net.ipv4.icmp_ignore_bogus_error_responses=1

    # Não aceitar redirecionamentos
    sysctl -w net.ipv4.conf.all.accept_redirects=0
    sysctl -w net.ipv4.conf.default.accept_redirects=0
    sysctl -w net.ipv4.conf.all.secure_redirects=0
    sysctl -w net.ipv4.conf.default.secure_redirects=0
    sysctl -w net.ipv4.conf.all.send_redirects=0
    sysctl -w net.ipv4.conf.default.send_redirects=0

    # Não aceitar source routing
    sysctl -w net.ipv4.conf.all.accept_source_route=0
    sysctl -w net.ipv4.conf.default.accept_source_route=0

    # Otimizações TCP
    sysctl -w net.ipv4.tcp_fin_timeout=15
    sysctl -w net.ipv4.tcp_keepalive_time=300
    sysctl -w net.ipv4.tcp_window_scaling=1
    sysctl -w net.ipv4.tcp_sack=1
    sysctl -w net.ipv4.tcp_timestamps=1

    # Persistir configurações
    sysctl -p
    msg "Configurações do kernel aplicadas."
}

#----------------------------------------------------------#
# Funções de Iptables (Tracking e Rate Limit)
#----------------------------------------------------------#

iptables_track_rule() {
    local chain_name=$1
    iptables -N $chain_name 2>/dev/null
    iptables -F $chain_name
    iptables -A $chain_name -j LOG --log-prefix "IPTABLES_TRACK: " --log-level 4
    iptables -A $chain_name -j DROP
}

iptables_register_suspects() {
    # Argumentos: nome_chain prefixo
    local track_name=$1
    local prefix=$2

    msg "Configurando regras de rastreamento para: $track_name"

    # Criar chains se não existirem
    iptables -N TRACK_DDOS 2>/dev/null
    iptables -N ANTI_DDOS 2>/dev/null
    iptables -N ANTI_DDOS_ 2>/dev/null

    # Limpar chains para evitar duplicatas ao reexecutar
    iptables -F TRACK_DDOS
    iptables -F ANTI_DDOS
    iptables -F ANTI_DDOS_

    # Estrutura de redirecionamento
    iptables -A TRACK_DDOS -j ANTI_DDOS
    # Redirecionar interfaces comuns (wildcard +)
    iptables -A ANTI_DDOS -i eth+ -j ANTI_DDOS_
    iptables -A ANTI_DDOS -i ens+ -j ANTI_DDOS_

    # Regras de Rate Limit (Recent module)
    # Banir IPs que excedem limites

    # 1. Bloqueio Rápido: Muitos pacotes em poucos segundos
    iptables -A ANTI_DDOS_ -m recent --name ddos-rapid --update --seconds 10 --hitcount 10 -j DROP
    iptables -A ANTI_DDOS_ -m recent --name ddos-rapid --set

    # 2. Bloqueio Médio: Persistência
    iptables -A ANTI_DDOS_ -m recent --name ddos-medium --update --seconds 60 --hitcount 30 -j DROP
    iptables -A ANTI_DDOS_ -m recent --name ddos-medium --set

    # Hashlimit como segurança adicional
    iptables -A ANTI_DDOS_ -m hashlimit --hashlimit-name ddos-limit --hashlimit-above 200/sec --hashlimit-burst 500 --hashlimit-mode srcip -j DROP

    msg "Regras de rastreamento e rate limit aplicadas."
}

#----------------------------------------------------------#
# Funções de Blocklist e GeoIP
#----------------------------------------------------------#

check_and_create_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
    fi
}

allow_countries() {
    msg "Configurando permissão de países (Whitelist)..."
    > "$TEMP_FILE_ALLOW"

    for country_code in "${COUNTRIES_TO_ALLOW[@]}"; do
        cc_lower=$(echo "$country_code" | tr "[:upper:]" "[:lower:]")
        # URL do ipdeny
        ipdeny_url="http://www.ipdeny.com/ipblocks/data/countries/$cc_lower.zone"

        msg "Baixando lista para $country_code..."
        curl -sS --max-time 10 "$ipdeny_url" | grep -vE "^(#|$)" >> "$TEMP_FILE_ALLOW" || msg "Falha ao baixar $country_code"
    done

    if [ -f "$TEMP_FILE_ALLOW" ] && [ -s "$TEMP_FILE_ALLOW" ]; then
        msg "Aplicando regras de Whitelist..."
        # Criar chain específica para whitelist
        iptables -N WHITELIST_COUNTRIES 2>/dev/null
        iptables -F WHITELIST_COUNTRIES

        # Inserir no topo do INPUT
        iptables -D INPUT -j WHITELIST_COUNTRIES 2>/dev/null
        iptables -I INPUT 1 -j WHITELIST_COUNTRIES

        while read -r ip; do
            if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+ ]]; then
                iptables -A WHITELIST_COUNTRIES -s "$ip" -j ACCEPT
            fi
        done < "$TEMP_FILE_ALLOW"
        rm "$TEMP_FILE_ALLOW"
    else
        msg "Nenhum IP de país baixado ou erro no download."
    fi
}

block_malicious_lists() {
    msg "Baixando e processando Blocklists..."
    > "$TEMP_FILE_BLOCK"

    for service in "${!BLOCKLIST_URLS[@]}"; do
        msg "Baixando $service..."
        curl -sS --max-time 15 "${BLOCKLIST_URLS[$service]}" >> "$TEMP_FILE_BLOCK" || msg "Falha ao baixar $service"
    done

    # Filtrar apenas IPs válidos
    grep -oE "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" "$TEMP_FILE_BLOCK" | sort -u > "$BLOCKLIST_DIR/blocklist_combined.txt"
    rm "$TEMP_FILE_BLOCK"

    local total_ips=$(wc -l < "$BLOCKLIST_DIR/blocklist_combined.txt")
    msg "Total de IPs maliciosos encontrados: $total_ips"

    if [ "$total_ips" -gt 0 ]; then
        msg "Aplicando regras de Blocklist (DROP)..."

        # Criar chain para blacklist
        iptables -N BLACKLIST_SETS 2>/dev/null
        iptables -F BLACKLIST_SETS

        # Adicionar após whitelist
        iptables -D INPUT -j BLACKLIST_SETS 2>/dev/null
        iptables -I INPUT 2 -j BLACKLIST_SETS

        # Limitar a 5000 IPs para evitar travamento se não usar ipset
        local count=0
        local limit=5000

        while read -r ip; do
            if [ "$count" -lt "$limit" ]; then
                iptables -A BLACKLIST_SETS -s "$ip" -j DROP
                count=$((count + 1))
            else
                msg "Aviso: Limite de $limit regras atingido. Use IPSET para mais."
                break
            fi
        done < "$BLOCKLIST_DIR/blocklist_combined.txt"
    fi
}

#----------------------------------------------------------#
# Execução Principal
#----------------------------------------------------------#

main() {
    check_root || return 1
    check_and_create_directory "$BLOCKLIST_DIR"

    # 1. Kernel Hardening
    configure_kernel_settings

    # 2. Configurar Iptables Tracking
    iptables_register_suspects "TRACK_ATTACKER" "attacker"

    # 3. Whitelist de Países
    allow_countries

    # 4. Blacklists
    block_malicious_lists

    msg "Script Anti-DDoS finalizado com sucesso."
    msg "Verifique as regras com: iptables -L -n -v"
}

# Iniciar
main
