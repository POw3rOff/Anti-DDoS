#!/bin/bash
#
# 5. Watcher de Alterações em Firewall (Anti-Tampering)
# Autor: Jules (AI Agent)
# Descrição: Monitora integridade das regras de firewall (iptables/nftables).

SUM_FILE="/var/lib/firewall_checksum.db"

# Detecta qual firewall usar
CMD=""
if command -v iptables-save >/dev/null; then
    CMD="iptables-save"
elif command -v nft >/dev/null; then
    CMD="nft list ruleset"
fi

if [ -z "$CMD" ]; then
    echo "Erro: Nem iptables nem nftables encontrados."
else
    get_checksum() {
        $CMD | sha256sum | awk '{print $1}'
    }

    if [ ! -f "$SUM_FILE" ]; then
        echo "[*] Criando baseline de firewall..."
        get_checksum > "$SUM_FILE"
        echo "Baseline salva: $(cat $SUM_FILE)"
    else
        OLD_SUM=$(cat "$SUM_FILE")
        NEW_SUM=$(get_checksum)

        if [ "$OLD_SUM" != "$NEW_SUM" ]; then
            echo "[!] ALERTA CRÍTICO: As regras de firewall foram alteradas!"
            echo "    Hash Antigo: $OLD_SUM"
            echo "    Hash Novo:   $NEW_SUM"
            echo ""
            echo "    Verifique manualmente as alterações."

            # Atualiza baseline? (Opcional, manual)
            # echo "$NEW_SUM" > "$SUM_FILE"
        else
            echo "[OK] Firewall íntegro (Hash: $NEW_SUM)."
        fi
    fi
fi
