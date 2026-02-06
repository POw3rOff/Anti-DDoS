#!/bin/bash
# Monitorização de Ficheiros Críticos
# Verifica integridade de ficheiros do sistema via hash SHA256

FILES="/etc/passwd /etc/shadow /etc/group /etc/sudoers /etc/ssh/sshd_config /bin/bash /usr/bin/sudo"
BASELINE_FILE="/tmp/critical_files_baseline.sha256" # Using /tmp for sandbox safety, in prod should be protected

# Ensure we are root for reading some files (checked typically, but in sandbox we might not be root, adjusting for portability)
# If running as non-root, some files like /etc/shadow might be unreadable.

echo "Iniciando monitorização de ficheiros críticos..."

if [ ! -f "$BASELINE_FILE" ]; then
    echo "Criando baseline de ficheiros críticos..."
    for f in $FILES; do
        if [ -f "$f" ] && [ -r "$f" ]; then
            sha256sum "$f" >> "$BASELINE_FILE"
        else
            echo "Aviso: $f não encontrado ou sem permissão de leitura."
        fi
    done
    echo "Baseline criada em $BASELINE_FILE"
else
    echo "Verificando integridade..."
    # Check current sums against baseline
    TEMP_CHECK=$(mktemp)

    # Generate current sums
    for f in $FILES; do
        if [ -f "$f" ] && [ -r "$f" ]; then
             sha256sum "$f" >> "$TEMP_CHECK"
        fi
    done

    # Compare
    # Note: sha256sum -c expects the file to match exactly.
    # If the baseline has files we can't read now, -c might fail on open.
    # We will use diff for simplicity in this script context or just sha256sum -c ignoring missing files

    sha256sum -c "$BASELINE_FILE" 2>/dev/null > "$TEMP_CHECK.result"

    if grep -q "FAILED" "$TEMP_CHECK.result"; then
        echo "ALERTA CRÍTICO: Alterações detetadas!"
        grep "FAILED" "$TEMP_CHECK.result"
    else
        echo "Integridade OK."
    fi

    rm -f "$TEMP_CHECK" "$TEMP_CHECK.result"
fi
