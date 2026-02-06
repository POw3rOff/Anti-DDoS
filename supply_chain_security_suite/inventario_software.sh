#!/bin/bash
# inventario_software.sh
# Descrição: Gera um inventário detalhado de software instalado (CSV).
# Autor: Jules (System Security Suite)

OUTPUT_FILE="/var/log/supply_chain_inventario.csv"
mkdir -p "$(dirname "$OUTPUT_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script deve ser executado como root."
    exit 1
fi

log "Gerando inventário em $OUTPUT_FILE..."

# Cabeçalho CSV
echo "Pacote,Versao,Arquitetura,Fornecedor/Mantenedor,DataInstalacao" > "$OUTPUT_FILE"

collect_deb() {
    log "Coletando dados do DPKG..."
    # Formato: Package, Version, Architecture, Maintainer
    # Data de instalação não é trivial no dpkg-query, pegar de logs é complexo. Deixamos vazio ou N/A.
    dpkg-query -W -f='${Package},${Version},${Architecture},${Maintainer},N/A\n' >> "$OUTPUT_FILE"
}

collect_rpm() {
    log "Coletando dados do RPM..."
    # Formato: Name, Version-Release, Arch, Vendor, InstallTime
    rpm -qa --qf '%{NAME},%{VERSION}-%{RELEASE},%{ARCH},%{VENDOR},%{INSTALLTIME:date}\n' >> "$OUTPUT_FILE"
}

if [ -f /etc/debian_version ]; then
    collect_deb
elif [ -f /etc/redhat-release ]; then
    collect_rpm
else
    if command -v rpm >/dev/null; then
        collect_rpm
    elif command -v dpkg >/dev/null; then
        collect_deb
    else
        log "Gerenciador não suportado."
        exit 1
    fi
fi

log "Inventário gerado com sucesso. Total de itens: $(wc -l < "$OUTPUT_FILE")"
log "Arquivo: $OUTPUT_FILE"
