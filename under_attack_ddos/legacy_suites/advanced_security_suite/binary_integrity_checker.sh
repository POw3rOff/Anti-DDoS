#!/bin/bash
#
# 9. Scanner de Binários Trocados (Integridade de Pacotes)
# Autor: Jules (AI Agent)
# Descrição: Verifica a integridade de binários do sistema usando o gerenciador de pacotes.

echo "[*] Verificando integridade de binários do sistema..."

# Binários críticos para verificar
BINARIES="coreutils net-tools iproute2 procps openssh-server bash"
# Nota: Nomes de pacotes variam por distro (ex: coreutils vs coreutils-bin)

if command -v dpkg >/dev/null; then
    # Debian/Ubuntu
    echo "    Modo: Debian/Ubuntu (dpkg --verify)"
    # dpkg --verify não aceita lista de pacotes facilmente, mas podemos iterar
    # Ou verificar tudo (lento). Vamos focar nos críticos.

    PACKAGES="coreutils net-tools iproute2 procps openssh-server bash"
    for pkg in $PACKAGES; do
        if dpkg -l "$pkg" >/dev/null 2>&1; then
            echo "    Verificando $pkg..."
            # dpkg -V retorna output se houver mudança (checksum 5, size S, permission M...)
            # Filtrar apenas checksum (5)
            RESULT=$(dpkg -V "$pkg" | grep "5")
            if [ -n "$RESULT" ]; then
                echo "[!] ALERTA: Binários alterados em $pkg!"
                echo "$RESULT"
            fi
        fi
    done

elif command -v rpm >/dev/null; then
    # RHEL/CentOS
    echo "    Modo: RHEL/CentOS (rpm -Va)"
    # rpm -V verifica
    PACKAGES="coreutils net-tools iproute procps-ng openssh-server bash"
    for pkg in $PACKAGES; do
        if rpm -q "$pkg" >/dev/null 2>&1; then
            echo "    Verificando $pkg..."
            # Filtrar checksum (5) na saída do rpm -V (ex: S.5....T.)
            rpm -V "$pkg" | grep "5" | while read line; do
                 echo "[!] ALERTA: Alteração detectada: $line"
            done
        fi
    done

else
    echo "Erro: Gerenciador de pacotes não suportado (apenas dpkg/rpm)."
    # Alternativa: Hash manual contra baseline (se não tiver package manager)
fi

echo "[OK] Verificação concluída."
