#!/bin/bash
# Script: isolamento_containers.sh
# Descrição: Audita mecanismos de isolamento (Seccomp, AppArmor, Namespaces).
# Autor: Jules

if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "ERRO: Runtime não encontrado."
    exit 1
fi

echo "=== Auditoria de Isolamento de Containers ==="

printf "%-20s %-20s %-20s %-15s\n" "CONTAINER" "SECCOMP" "APPARMOR" "READONLY_FS"
echo "--------------------------------------------------------------------------------"

for id in $($RUNTIME ps -q); do
    name=$($RUNTIME inspect --format "{{.Name}}" "$id" | sed "s/\///")

    # Security Options
    sec_opts=$($RUNTIME inspect --format "{{json .HostConfig.SecurityOpt}}" "$id")
    readonly=$($RUNTIME inspect --format "{{.HostConfig.ReadonlyRootfs}}" "$id")

    # Verificar Seccomp
    seccomp="Default"
    if echo "$sec_opts" | grep -q "seccomp=unconfined"; then
        seccomp="UNCONFINED(!)"
    fi

    # Verificar AppArmor
    apparmor="Default"
    if echo "$sec_opts" | grep -q "apparmor=unconfined"; then
        apparmor="UNCONFINED(!)"
    fi

    printf "%-20s %-20s %-20s %-15s\n"         "${name:0:20}" "$seccomp" "$apparmor" "$readonly"

    if [ "$seccomp" == "UNCONFINED(!)" ] || [ "$apparmor" == "UNCONFINED(!)" ]; then
        echo "  [ALERTA] Container $name está com perfis de segurança desativados!"
    fi
done
