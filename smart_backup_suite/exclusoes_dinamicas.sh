#!/bin/bash
# exclusoes_dinamicas.sh
# Gera uma lista de arquivos e diretórios a serem excluídos do backup.
#
# Uso: ./exclusoes_dinamicas.sh > exclude.list

# Padrões estáticos
echo "*.tmp"
echo "*.temp"
echo "*.log"
echo "*.swp"
echo "*.iso"
echo ".cache"
echo "node_modules"
echo "Trash"

# Exclusões baseadas em diretórios comuns de cache/temp
echo "/tmp/*"
echo "/var/tmp/*"
echo "/var/cache/*"
echo "/proc/*"
echo "/sys/*"
echo "/dev/*"
echo "/run/*"
echo "/mnt/*"
echo "/media/*"

# (Opcional) Encontrar arquivos muito grandes (> 5GB) que não sejam backups antigos
# find /home -type f -size +5G ... (Comentado para evitar lentidão)
# echo "caminho/para/arquivo_grande.iso"
