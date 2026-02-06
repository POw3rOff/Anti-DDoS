#!/bin/bash
# Validação de backups (restore test)
# Verifica a integridade dos arquivos de backup e simula uma restauração parcial.

BACKUP_DIR="/var/backups" # Configure este caminho conforme necessário
TEMP_RESTORE_DIR="/tmp/restore_test_$(date +%s)"
LOG_FILE="/var/log/backup_validation.log"

echo "Iniciando validação de backup..."
echo "Data: $(date)" > "$LOG_FILE"

# Verifica se o diretório existe
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Erro: Diretório de backup $BACKUP_DIR não encontrado." | tee -a "$LOG_FILE"
    echo "Por favor, edite o script e configure a variável BACKUP_DIR."
else
    # Encontra o backup mais recente (supondo tar.gz ou tgz)
    LATEST_BACKUP=$(find "$BACKUP_DIR" -type f \( -name "*.tar.gz" -o -name "*.tgz" \) | sort -r | head -n 1)

    if [ -z "$LATEST_BACKUP" ]; then
        echo "Erro: Nenhum arquivo de backup (.tar.gz/.tgz) encontrado em $BACKUP_DIR." | tee -a "$LOG_FILE"
    else
        echo "Backup mais recente encontrado: $LATEST_BACKUP" | tee -a "$LOG_FILE"

        # Teste de integridade do arquivo (gzip)
        echo "Testando integridade do arquivo compactado..." | tee -a "$LOG_FILE"
        if gzip -t "$LATEST_BACKUP" 2>> "$LOG_FILE"; then
            echo "Integridade (gzip) OK." | tee -a "$LOG_FILE"

            # Teste de restauração (extração parcial)
            echo "Simulando restauração (teste de extração) em $TEMP_RESTORE_DIR..." | tee -a "$LOG_FILE"
            mkdir -p "$TEMP_RESTORE_DIR"

            # Obtém nome de um arquivo para extrair (evita extrair gigabytes)
            FIRST_FILE=$(tar -tf "$LATEST_BACKUP" 2>/dev/null | head -n 1)

            if [ -n "$FIRST_FILE" ]; then
                if tar -xzf "$LATEST_BACKUP" "$FIRST_FILE" -C "$TEMP_RESTORE_DIR" 2>> "$LOG_FILE"; then
                     echo "Sucesso: Extração de teste () realizada." | tee -a "$LOG_FILE"
                     echo "RESULTADO: Validação de backup APROVADA." | tee -a "$LOG_FILE"
                else
                     echo "FALHA: Erro ao extrair arquivo de teste." | tee -a "$LOG_FILE"
                fi
            else
                echo "Aviso: O arquivo de backup parece vazio (tar list retornou nada)." | tee -a "$LOG_FILE"
            fi

            # Limpeza
            rm -rf "$TEMP_RESTORE_DIR"

        else
            echo "FALHA: Arquivo de backup corrompido (gzip test failed)." | tee -a "$LOG_FILE"
        fi
    fi
fi
