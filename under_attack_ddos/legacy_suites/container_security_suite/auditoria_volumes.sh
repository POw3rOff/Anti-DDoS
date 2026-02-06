#!/bin/bash
# Script: auditoria_volumes.sh
# Descrição: Audita volumes e mounts de containers, detectando mapeamentos perigosos.
# Autor: Jules

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Runtime não encontrado."
    exit 1
fi

echo "=== Auditoria de Volumes e Mounts ==="
echo "Sensitive Paths: /etc, /boot, /proc, /sys, /usr, /var/run, /"

for id in $($RUNTIME ps -q); do
    name=$($RUNTIME inspect --format "{{.Name}}" "$id" | sed "s/\///")

    # Obter mounts do tipo bind usando newline separator para suportar espacos
    # Usando printf no template para garantir nova linha
    binds=$($RUNTIME inspect --format '{{range .Mounts}}{{if eq .Type "bind"}}{{.Source}}|{{.Destination}}|{{.RW}}
{{end}}{{end}}' "$id")

    if [ -n "$binds" ]; then
        echo "Container: $name"
        # Ler linha a linha para lidar com espacos
        echo "$binds" | while read -r bind; do
            [ -z "$bind" ] && continue

            # Formato: Source|Dest|RW (RW=true/false)
            src=$(echo "$bind" | cut -d'|' -f1)
            dst=$(echo "$bind" | cut -d'|' -f2)
            rw=$(echo "$bind" | cut -d'|' -f3)

            perm="RO"
            if [ "$rw" == "true" ]; then perm="RW"; fi

            RISK=""
            if [[ "$src" == "/" ]] || [[ "$src" == "/boot"* ]] || [[ "$src" == "/etc"* ]] || [[ "$src" == "/proc"* ]] || [[ "$src" == "/sys"* ]]; then
                 RISK="[CRÍTICO]"
            elif [[ "$src" == "/var/run/docker.sock" ]]; then
                 RISK="[CRÍTICO-DOCKER-SOCK]"
            fi

            echo "  - $RISK Mount: $src -> $dst ($perm)"
        done
        echo "-----------------------------------"
    fi
done

echo "Auditoria concluída."
