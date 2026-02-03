#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Forense de Memória Live
=======================
Realiza análise de memória em tempo real sem desligar o sistema (Live Forensics).
Foca na identificação de processos maliciosos e artefatos em RAM.

Funcionalidades:
- Identificação de processos rodando binários deletados (Fileless/Updates).
- Detecção de regiões de memória RWX (Leitura+Escrita+Execução), comum em shellcodes/unpackers.
- Mapeamento de portas abertas por processo.
- Busca por strings suspeitas (ex: /bin/sh, URLs) em processos marcados.

Uso:
    python3 forense_memoria_live.py --scan-level full
"""

import os
import sys
import re
import argparse
import subprocess
from datetime import datetime

# Padrões de strings suspeitas para buscar na memória
SUSPICIOUS_STRINGS = [
    b"/bin/sh",
    b"/bin/bash",
    b"nc -e",
    b"wget http",
    b"curl http",
    b"eval(",
    b"base64_decode"
]

def get_pids():
    """Retorna lista de PIDs numéricos em /proc."""
    return [int(pid) for pid in os.listdir('/proc') if pid.isdigit()]

def get_process_info(pid):
    """Coleta informações básicas do processo."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline = f.read().replace(b'\0', b' ').decode('utf-8', errors='ignore').strip()

        exe_link = "unknown"
        try:
            exe_link = os.readlink(f"/proc/{pid}/exe")
        except OSError:
            pass

        return {"pid": pid, "cmdline": cmdline, "exe": exe_link}
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None

def check_deleted_binary(info):
    """Verifica se o binário executável foi deletado do disco."""
    if "(deleted)" in info['exe']:
        return True
    return False

def check_rwx_segments(pid):
    """Verifica se o processo possui segmentos de memória RWX (Read-Write-Execute)."""
    rwx_found = False
    try:
        with open(f"/proc/{pid}/maps", "r") as f:
            for line in f:
                # Exemplo: 7f... rwxp ...
                parts = line.split()
                if len(parts) >= 2:
                    perms = parts[1]
                    if "rwx" in perms:
                        rwx_found = True
                        break
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
    return rwx_found

def get_sockets(pid):
    """Retorna sockets associados ao PID usando ls -l /proc/pid/fd."""
    sockets = []
    try:
        fd_dir = f"/proc/{pid}/fd"
        if not os.path.exists(fd_dir): return []

        for fd in os.listdir(fd_dir):
            try:
                link = os.readlink(f"{fd_dir}/{fd}")
                if "socket:[" in link:
                    sockets.append(link)
            except OSError:
                continue
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
    return sockets

def scan_memory_strings(pid):
    """
    Tenta ler /proc/pid/mem (Requer Root e kernel permissivo ou ptrace_scope=0).
    Procura por strings definidas em SUSPICIOUS_STRINGS.
    Nota: Isso pode ser lento e instável. Fazemos apenas leitura segura.
    """
    # Em muitos kernels modernos, ler /proc/pid/mem requer PTRACE_ATTACH.
    # Vamos tentar usar o comando 'grep' externamente se possível ou apenas ler o maps.
    # Para ser seguro e "Live", vamos ler apenas o HEAP e STACK se encontrarmos no maps.

    hits = []
    try:
        maps_file = f"/proc/{pid}/maps"
        mem_file = f"/proc/{pid}/mem"

        regions_to_scan = []
        with open(maps_file, 'r') as f:
            for line in f:
                if "[heap]" in line or "[stack]" in line:
                    parts = line.split()
                    range_str = parts[0]
                    start, end = range_str.split('-')
                    regions_to_scan.append((int(start, 16), int(end, 16)))

        if not regions_to_scan: return []

        fd = os.open(mem_file, os.O_RDONLY)
        try:
            for start, end in regions_to_scan:
                size = end - start
                # Limite de leitura para não travar (ex: 10MB por segmento)
                if size > 10 * 1024 * 1024:
                    size = 10 * 1024 * 1024

                os.lseek(fd, start, os.SEEK_SET)
                chunk = os.read(fd, size)

                for pattern in SUSPICIOUS_STRINGS:
                    if pattern in chunk:
                        hits.append(pattern.decode('utf-8'))
                        if len(hits) >= 5: break # Limite de hits
                if len(hits) >= 5: break
        finally:
            os.close(fd)

    except Exception as e:
        # Permissão negada ou processo morreu
        pass

    return list(set(hits))

def analyze_system():
    print(f"[*] Iniciando Análise Forense de Memória Live em {datetime.now()}")
    print("[*] Verificando processos...")

    suspicious_procs = []

    for pid in get_pids():
        info = get_process_info(pid)
        if not info: continue

        score = 0
        reasons = []

        # 1. Binário Deletado
        if check_deleted_binary(info):
            score += 3
            reasons.append("Binário Deletado")

        # 2. Segmentos RWX
        if check_rwx_segments(pid):
            score += 2
            reasons.append("Memória RWX (Exec+Write)")

        # 3. Nome suspeito ou oculto (básico)
        if len(info['cmdline']) == 0:
            # As vezes kernel threads, mas user process sem cmdline é estranho
            pass

        # Se score alto, analise sockets e strings
        if score > 0:
            sockets = get_sockets(pid)
            if sockets:
                reasons.append(f"Sockets Abertos: {len(sockets)}")

            # Tentar scan de strings (apenas se root)
            if os.geteuid() == 0:
                strings = scan_memory_strings(pid)
                if strings:
                    score += 2
                    reasons.append(f"Strings Suspeitas: {strings}")

            suspicious_procs.append({
                "pid": pid,
                "name": info['cmdline'][:50],
                "exe": info['exe'],
                "score": score,
                "reasons": reasons
            })

    # Relatório
    if not suspicious_procs:
        print("[OK] Nenhum processo altamente suspeito detectado nas heurísticas básicas.")
    else:
        print(f"\n[!] Detectados {len(suspicious_procs)} processos suspeitos:\n")
        suspicious_procs.sort(key=lambda x: x['score'], reverse=True)

        for p in suspicious_procs:
            print(f"PID: {p['pid']}")
            print(f"Exe: {p['exe']}")
            print(f"Cmd: {p['name']}...")
            print(f"Score: {p['score']}")
            print(f"Indicadores: {', '.join(p['reasons'])}")
            print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Forense de Memória Live")
    parser.add_argument('--scan-level', choices=['quick', 'full'], default='quick', help="Nível de scan (full tenta ler memória)")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("[!] AVISO: Execute como root para visibilidade total (/proc/pid/exe, fd, mem).")

    analyze_system()

if __name__ == "__main__":
    main()
