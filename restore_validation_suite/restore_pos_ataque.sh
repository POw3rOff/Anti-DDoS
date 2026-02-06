#!/bin/bash
# restore_pos_ataque.sh
#
# Descrição: Procedimento de restore seguro após um incidente de segurança.
# Verifica assinaturas, restaura em quarentena e escaneia antes de mover para produção.
#
# Uso: ./restore_pos_ataque.sh <arquivo_backup>

BACKUP_FILE="$1"
QUARANTINE_DIR="/tmp/quarentena_restore_$(date +%s)"

if [[ -z "$BACKUP_FILE" ]]; then
    echo "[ERRO] Uso: $0 <arquivo_backup>"
    exit 1
fi

echo "[SEGURANÇA] Iniciando protocolo de restore pós-ataque."

# 1. Verificar integridade (Hash/Assinatura)
echo "[PASSO 1] Verificando integridade do backup..."
if [[ -f "${BACKUP_FILE}.sha256" ]]; then
    echo "[INFO] Arquivo de hash encontrado. Verificando..."
    sha256sum -c "${BACKUP_FILE}.sha256"
    if [[ $? -ne 0 ]]; then
        echo "[ERRO CRÍTICO] Falha na verificação de integridade! O backup pode estar adulterado."
        exit 1
    fi
    echo "[OK] Integridade confirmada."
else
    echo "[AVISO] Arquivo de hash/assinatura não encontrado (${BACKUP_FILE}.sha256)."
    echo "[ALERTA] Prosseguindo sem verificação criptográfica de integridade."
fi

# 2. Restore em Quarentena
echo "[PASSO 2] Restaurando em ambiente de quarentena: $QUARANTINE_DIR"
mkdir -p "$QUARANTINE_DIR"
tar -xzf "$BACKUP_FILE" -C "$QUARANTINE_DIR"

if [[ $? -ne 0 ]]; then
    echo "[ERRO] Falha ao extrair backup."
    rm -rf "$QUARANTINE_DIR"
    exit 1
fi

# 3. Escaneamento (Ex: ClamAV)
echo "[PASSO 3] Escaneando arquivos restaurados por ameaças..."
if command -v clamscan &> /dev/null; then
    clamscan -r "$QUARANTINE_DIR"
    SCAN_RESULT=$?
    if [[ $SCAN_RESULT -eq 0 ]]; then
        echo "[OK] Nenhum malware detectado."
    else
        echo "[PERIGO] Ameaças detectadas! Restore abortado."
        # rm -rf "$QUARANTINE_DIR" # Manter para análise forense?
        exit 1
    fi
else
    echo "[AVISO] ClamAV não encontrado. Certifique-se de escanear os arquivos manualmente antes de usar."
fi

echo "[SUCESSO] O backup está limpo (ou verificado na medida do possível) e pronto."
echo "Arquivos disponíveis em: $QUARANTINE_DIR"
