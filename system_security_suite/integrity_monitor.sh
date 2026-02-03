#!/bin/bash
#
# 4. Monitor de Integridade de Arquivos (FIM)
# Autor: Jules (AI Agent)
# Descrição: Gera e verifica hashes SHA256 de arquivos críticos.

DB_FILE="/var/lib/security_fim.db"
DIRS_TO_MONITOR=("/bin" "/sbin" "/usr/bin" "/usr/sbin" "/etc")
CRITICAL_FILES=("/etc/passwd" "/etc/shadow" "/etc/ssh/sshd_config")

usage() {
    echo "Uso: $0 {init|check}"
    echo "  init  : Cria/Atualiza a base de dados de hashes (baseline)."
    echo "  check : Verifica alterações contra a base de dados."
}

generate_hashes() {
    echo "[*] Gerando baseline de integridade..."
    rm -f "$DB_FILE"
    touch "$DB_FILE"

    # Arquivos individuais
    for file in "${CRITICAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            sha256sum "$file" >> "$DB_FILE"
        fi
    done

    # Diretórios (apenas executáveis para economizar tempo/espaço)
    # Limitado a arquivos regulares
    for dir in "${DIRS_TO_MONITOR[@]}"; do
        if [ -d "$dir" ]; then
            echo "    - Processando $dir..."
            find "$dir" -type f -maxdepth 1 -exec sha256sum {} + >> "$DB_FILE" 2>/dev/null
        fi
    done

    echo "[*] Baseline criada em $DB_FILE com $(wc -l < "$DB_FILE") entradas."
}

check_integrity() {
    if [ ! -f "$DB_FILE" ]; then
        echo "Erro: Base de dados não encontrada. Execute '$0 init' primeiro."
    else
        echo "[*] Verificando integridade..."
        # O comando sha256sum -c retorna erro se houver falha, e imprime no stdout/stderr
        if sha256sum -c "$DB_FILE" --quiet > /tmp/fim_diff.txt 2>&1; then
             echo "[OK] Nenhuma alteração detectada nos arquivos monitorados."
        else
             echo "[!] ALTERAÇÕES DETECTADAS!"
             cat /tmp/fim_diff.txt
             echo ""
             echo "[!] ALERTA: Arquivos críticos foram modificados!"
        fi
        rm -f /tmp/fim_diff.txt
    fi
}

case "$1" in
    init)
        generate_hashes
        ;;
    check)
        check_integrity
        ;;
    *)
        usage
        ;;
esac
