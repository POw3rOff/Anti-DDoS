#!/bin/bash
# Script: bloqueio_geografico_automatico.sh
# Descrição: Bloqueia tráfego de países específicos usando IPSet.
# Autor: Jules (AI Agent)

COUNTRIES="cn ru kp ir"

if [ "$(id -u)" -ne 0 ]; then
    echo "[ERRO] Precisa ser root."
    exit 1
fi

if ! command -v ipset >/dev/null; then
    echo "[ERRO] 'ipset' não encontrado."
    exit 1
fi

echo "=== Bloqueio Geográfico Automático ==="

# Cria set
if ! ipset list geo_block >/dev/null 2>&1; then
    echo "[*] Criando ipset 'geo_block'..."
    ipset create geo_block hash:net
    iptables -C INPUT -m set --match-set geo_block src -j DROP 2>/dev/null
    if [ $? -ne 0 ]; then
        iptables -I INPUT -m set --match-set geo_block src -j DROP
    fi
fi

# Temp Set (swap)
ipset create geo_block_tmp hash:net 2>/dev/null
ipset flush geo_block_tmp

for COUNTRY in $COUNTRIES; do
    URL="http://www.ipdeny.com/ipblocks/data/countries/$COUNTRY.zone"
    echo "[*] Baixando lista para: $COUNTRY..."

    if command -v curl >/dev/null; then
        LIST=$(curl -s $URL)
    elif command -v wget >/dev/null; then
        LIST=$(wget -qO- $URL)
    else
        echo "[ERRO] curl ou wget necessários."
        exit 1
    fi

    if [ -n "$LIST" ]; then
        echo "    -> Adicionando IPs de $COUNTRY ao set..."
        for IP in $LIST; do
            ipset add geo_block_tmp $IP -exist
        done
    else
        echo "[ERRO] Falha ao baixar lista para $COUNTRY."
    fi
done

echo "[*] Aplicando novas listas (Swap)..."
ipset swap geo_block_tmp geo_block
ipset destroy geo_block_tmp

echo "[OK] Bloqueio Geográfico Atualizado."
COUNT=$(ipset list geo_block | wc -l)
echo "Total de redes bloqueadas: $COUNT"
