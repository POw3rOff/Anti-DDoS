#!/bin/bash
# Verificação de pacotes alterados
# Este script verifica a integridade dos pacotes instalados no sistema.
# Detecta automaticamente se é um sistema baseado em Debian ou RHEL.

LOG_FILE="/var/log/package_integrity_check.log"

# Verifica se é root
if [ "$EUID" -ne 0 ]; then
  echo "Por favor, execute como root."
  # Terminamos se não for root
else

    echo "Iniciando verificação de integridade de pacotes..."
    echo "Data: $(date)" > "$LOG_FILE"

    if [ -f /etc/debian_version ]; then
        echo "Sistema Debian/Ubuntu detectado."
        if command -v dpkg &> /dev/null; then
            echo "Executando dpkg --verify..."
            dpkg --verify >> "$LOG_FILE" 2>&1

            echo "Verificação concluída. Detalhes salvos em $LOG_FILE."

            COUNT=$(wc -l < "$LOG_FILE")
            if [ "$COUNT" -gt 1 ]; then
                echo "ALERTA: Foram encontradas inconsistências em pacotes."
                grep -v "Data:" "$LOG_FILE" | head -n 5
                if [ "$COUNT" -gt 6 ]; then echo "... (mais entradas no log)"; fi
            else
                echo "Nenhuma alteração detectada."
            fi

        else
            echo "Erro: dpkg não encontrado."
        fi
    elif [ -f /etc/redhat-release ]; then
        echo "Sistema RHEL/CentOS detectado."
        if command -v rpm &> /dev/null; then
            echo "Executando rpm -Va..."
            rpm -Va >> "$LOG_FILE" 2>&1

            echo "Verificação concluída. Detalhes salvos em $LOG_FILE."

            COUNT=$(wc -l < "$LOG_FILE")
            if [ "$COUNT" -gt 1 ]; then
                echo "ALERTA: Foram encontradas inconsistências em pacotes."
                grep -v "Data:" "$LOG_FILE" | head -n 5
                if [ "$COUNT" -gt 6 ]; then echo "... (mais entradas no log)"; fi
            else
                echo "Nenhuma alteração detectada."
            fi
        else
            echo "Erro: rpm não encontrado."
        fi
    else
        echo "Sistema operacional não suportado para esta verificação automática."
    fi

    echo "Relatório completo em: $LOG_FILE"
fi
