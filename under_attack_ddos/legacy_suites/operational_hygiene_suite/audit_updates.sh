#!/bin/bash
# Auditoria de updates pendentes críticos
# Verifica se há atualizações de segurança pendentes.

LOG_FILE="/var/log/security_updates_audit.log"

# Verifica root
if [ "$EUID" -ne 0 ]; then
  echo "Por favor, execute como root para garantir acesso aos gerenciadores de pacotes."
  # Continua mas pode falhar
fi

echo "Verificando atualizações de segurança pendentes..."
echo "Data: $(date)" > "$LOG_FILE"

if [ -f /etc/debian_version ]; then
    echo "Sistema Debian/Ubuntu detectado."

    if command -v apt-get &> /dev/null; then
        # Tenta usar apt list se disponível (mais legível) ou apt-get -s
        echo "Verificando pacotes..."

        # Método 1: apt list --upgradable filtrando por security (depende do nome do repo)
        # Método 2: grep na saida do apt-get -s upgrade

        # Vamos usar uma abordagem segura com apt-get -s dist-upgrade
        # Filtra linhas que começam com Inst e contêm security ou (Debian-Security)
        apt-get -s dist-upgrade | grep "^Inst" | grep -iE "security|ubuntu-security" >> "$LOG_FILE"

        # Verifica se o arquivo tem conteúdo além do cabeçalho
        if [ -s "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE")" -gt 1 ]; then
             echo "ALERTA: Possíveis atualizações de segurança pendentes encontradas:"
             grep "^Inst" "$LOG_FILE"
             echo "Consulte $LOG_FILE para detalhes."
        else
             echo "Nenhuma atualização crítica óbvia detectada na simulação."
             echo "Nota: Certifique-se que 'apt-get update' foi executado recentemente."
        fi
    fi

elif [ -f /etc/redhat-release ]; then
    echo "Sistema RHEL/CentOS detectado."
    if command -v yum &> /dev/null; then
        echo "Verificando com yum updateinfo security..."
        # Requer plugin yum-plugin-security em versoes antigas
        yum updateinfo list security installed >> "$LOG_FILE" 2>&1

        # Fallback se updateinfo não retornar nada útil ou comando falhar, tenta check-update
        if [ $? -ne 0 ]; then
            echo "yum updateinfo falhou ou não disponível. Tentando yum check-update --security..."
            yum check-update --security >> "$LOG_FILE"
        fi

        if grep -q "security" "$LOG_FILE"; then
             echo "ALERTA: Atualizações de segurança podem estar disponíveis. Verifique o log."
        else
             echo "Parece limpo. Verifique $LOG_FILE para confirmar."
        fi
    fi
else
    echo "Sistema não suportado automaticamente."
fi
