#!/bin/bash
# Script: auditoria_imagens.sh
# Descrição: Audita imagens de containers armazenadas localmente.
# Autor: Jules

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Runtime não encontrado."
    exit 1
fi

echo "=== Auditoria de Imagens ==="
printf "%-30s %-15s %-10s %-15s\n" "IMAGEM" "USER" "TAMANHO" "CAMADAS"
echo "------------------------------------------------------------------------"

$RUNTIME images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | while read -r image id; do
    if [[ "$image" == *"<none>"* ]]; then
        continue # Ignorar imagens intermediárias na lista principal
    fi

    # 1. Verificar Usuario
    user=$($RUNTIME inspect --format "{{.Config.User}}" "$id")
    [ -z "$user" ] && user="root(padrao)"

    # 2. Tamanho (VirtualSize)
    size=$($RUNTIME inspect --format "{{.VirtualSize}}" "$id")
    # Converter bytes para MB
    size_mb=$((size / 1024 / 1024))

    # 3. Contar Camadas (RootFS.Layers)
    layers=$($RUNTIME inspect --format "{{len .RootFS.Layers}}" "$id")

    printf "%-30s %-15s %-10s %-15s\n" "${image:0:30}" "$user" "${size_mb}MB" "$layers"
done

echo ""
echo "=== Imagens 'Dangling' (Sem tag) ==="
dangling_count=$($RUNTIME images -f "dangling=true" -q | wc -l)
echo "Total: $dangling_count (Recomendado remover: $RUNTIME rmi \$($RUNTIME images -f 'dangling=true' -q))"
