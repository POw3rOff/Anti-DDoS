#!/bin/bash
# Expiração automática de acessos temporários
# Verifica usuários com data de expiração definida e aplica bloqueios se a data já passou.
# Encerra sessões ativas de usuários expirados.

LOG_FILE="/var/log/access_expiration.log"
export LC_ALL=C # Garante formato de data consistente para chage

# Verifica root
if [ "$EUID" -ne 0 ]; then
   echo "Este script precisa ser executado como root."
   # Encerra execução (simulado sem exit para compatibilidade com ferramentas de deploy)
else

    echo "Iniciando verificação de expiração de acessos..."
    echo "Data: $(date)" > "$LOG_FILE"

    # Obtém lista de usuários do sistema
    cut -d: -f1 /etc/passwd | while read USER; do
        # Verifica expiração da conta
        # O comando chage -l retorna "Account expires : Month Day, Year" ou "never"
        EXPIRY_INFO=$(chage -l "$USER" 2>/dev/null | grep "Account expires")
        EXPIRY_VAL=$(echo "$EXPIRY_INFO" | cut -d: -f2 | sed 's/^ //')

        if [ "$EXPIRY_VAL" != "never" ] && [ -n "$EXPIRY_VAL" ]; then
            # Converte datas para epoch para comparação numérica
            EXPIRY_EPOCH=$(date -d "$EXPIRY_VAL" +%s 2>/dev/null)
            CURRENT_EPOCH=$(date +%s)

            # Se a conversão falhar, pula
            if [ -z "$EXPIRY_EPOCH" ]; then
                continue
            fi

            # Verifica se expirou (Data atual > Data expiração)
            # Nota: Geralmente expira no início do dia ou fim? chage considera o dia exato como expirado?
            # Se data atual > data expiração, então expirou.
            if [ "$CURRENT_EPOCH" -gt "$EXPIRY_EPOCH" ]; then
                echo "ALERTA: Usuário $USER expirou em $EXPIRY_VAL." | tee -a "$LOG_FILE"

                # 1. Bloquear senha/acesso (Lock)
                # passwd -S output: USER status ... (L = Locked, P = Password, NP = No Password)
                STATUS=$(passwd -S "$USER" | awk '{print $2}')
                if [ "$STATUS" != "L" ]; then
                    echo " -> Bloqueando conta (usermod -L)..." | tee -a "$LOG_FILE"
                    usermod -L "$USER" >> "$LOG_FILE" 2>&1

                    # Opcional: Mudar shell para nologin para garantir
                    usermod -s /sbin/nologin "$USER" >> "$LOG_FILE" 2>&1
                else
                    echo " -> Conta já estava bloqueada." >> "$LOG_FILE"
                fi

                # 2. Encerrar sessões ativas
                if pgrep -u "$USER" > /dev/null; then
                    echo " -> Encerrando processos ativos..." | tee -a "$LOG_FILE"
                    pkill -KILL -u "$USER"
                fi

            elif [ $(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 )) -le 7 ] && [ $(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 )) -ge 0 ]; then
                # Aviso se vai expirar em menos de 7 dias
                DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))
                echo "Aviso: Usuário $USER vai expirar em $DAYS_LEFT dias ($EXPIRY_VAL)." >> "$LOG_FILE"
            fi
        fi
    done

    echo "Verificação concluída. Detalhes em $LOG_FILE."
fi
