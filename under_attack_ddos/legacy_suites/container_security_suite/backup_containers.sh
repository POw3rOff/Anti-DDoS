#!/bin/bash
# Script: backup_containers.sh
# Descrição: Backup completo (imagem + volumes) de containers.
# Autor: Jules

BACKUP_DIR="/var/backups/containers"
DATE=$(date +%Y%m%d_%H%M%S)

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Runtime não encontrado."
    exit 1
fi

perform_backup() {
    local container=$1
    echo ">>> Iniciando backup de: $container"

    local safe_name=$(echo "$container" | sed 's/[^a-zA-Z0-9_-]//g')
    local dest_dir="$BACKUP_DIR/$safe_name/$DATE"
    mkdir -p "$dest_dir"

    # 1. Commit e Save da Imagem (Estado atual)
    echo "  [1/3] Salvando estado (commit)..."
    local img_name="${safe_name}_backup:$DATE"
    $RUNTIME commit "$container" "$img_name" > /dev/null
    $RUNTIME save -o "$dest_dir/image.tar" "$img_name"
    $RUNTIME rmi "$img_name" > /dev/null 2>&1

    # 2. Backup de Volumes
    echo "  [2/3] Copiando volumes..."
    # Método genérico: usar container temporário para montar volumes e tar
    # Nota: requer busybox ou similar. Se não tiver, tentar cp (menos confiável para volumes nomeados)

    # Lista volumes/mounts
    local mounts=$($RUNTIME inspect --format '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}} {{end}}{{end}}' "$container")

    if [ -n "$mounts" ]; then
        for vol in $mounts; do
             echo "    - Volume: $vol"
             $RUNTIME run --rm -v "$vol":/data -v "$dest_dir":/backup alpine tar czf "/backup/vol_${vol}.tar.gz" -C /data .
        done
    else
        echo "    (Nenhum volume nomeado detectado)"
    fi

    # 3. Gerar Checksums
    echo "  [3/3] Gerando checksums..."
    cd "$dest_dir" && sha256sum * > SHA256SUMS

    echo "  [OK] Backup concluído em: $dest_dir"
}

if [ "$1" == "--all" ] || [ "$1" == "-a" ]; then
    for cid in $($RUNTIME ps -q); do
        name=$($RUNTIME inspect --format "{{.Name}}" "$cid" | sed "s/\///")
        perform_backup "$name"
    done
elif [ -n "$1" ]; then
    perform_backup "$1"
else
    echo "Uso: $0 <container_name> | --all"
    exit 1
fi
