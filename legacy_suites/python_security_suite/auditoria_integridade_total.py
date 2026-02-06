#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Auditoria de Integridade Total (FIM)
====================================
Verifica a integridade de arquivos críticos do sistema calculando hashes SHA256
e comparando com um estado conhecido (baseline).

Funcionalidades:
- Monitora diretórios críticos (/bin, /sbin, /etc, etc).
- Detecta arquivos criados, removidos e modificados.
- Detecta alterações de permissões/dono.
- Base de dados local em JSON.

Uso:
    Inicializar base:
    python3 auditoria_integridade_total.py --action init

    Verificar integridade:
    python3 auditoria_integridade_total.py --action check

    Atualizar base (após mudanças legítimas):
    python3 auditoria_integridade_total.py --action update
"""

import os
import sys
import hashlib
import json
import argparse
import stat
from datetime import datetime

# Diretórios para monitorar
MONITOR_DIRS = [
    "/bin",
    "/sbin",
    "/usr/bin",
    "/usr/sbin",
    "/etc",
    "/boot"
]

# Extensões ou arquivos para ignorar
IGNORE_EXT = ['.swp', '.tmp', '.cache']
IGNORE_FILES = ['mtab', 'adjtime']

DB_FILE = "integrity_db.json"

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError):
        return None

def get_file_metadata(filepath):
    try:
        st = os.stat(filepath)
        mode = stat.S_IMODE(st.st_mode)
        return {
            "uid": st.st_uid,
            "gid": st.st_gid,
            "mode": oct(mode),
            "size": st.st_size,
            "mtime": st.st_mtime
        }
    except OSError:
        return None

def scan_system():
    print(f"[*] Iniciando scan do sistema em {datetime.now()}...")
    current_state = {}
    count = 0

    for directory in MONITOR_DIRS:
        if not os.path.exists(directory):
            continue

        print(f"   Scan: {directory}")
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in IGNORE_EXT): continue
                if file in IGNORE_FILES: continue

                filepath = os.path.join(root, file)
                if os.path.islink(filepath): continue

                meta = get_file_metadata(filepath)
                if not meta: continue

                file_hash = calculate_sha256(filepath)
                if not file_hash: continue

                current_state[filepath] = {
                    "hash": file_hash,
                    "meta": meta
                }
                count += 1
                if count % 1000 == 0:
                    print(f"      Processados {count} arquivos...")

    print(f"[*] Scan concluído. Total de arquivos monitorados: {count}")
    return current_state

def save_db(state):
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "files": state
        }
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"[*] Base de integridade salva em {DB_FILE}")
    except IOError as e:
        print(f"[!] Erro ao salvar DB: {e}")

def load_db():
    if not os.path.exists(DB_FILE):
        return None
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Erro ao carregar DB: {e}")
        return None

def compare_states(old_state, new_state):
    print("\n[*] Comparando estados...")
    changes = {
        "added": [],
        "removed": [],
        "modified_content": [],
        "modified_perms": []
    }

    old_files = old_state.get('files', {})
    new_files = new_state

    for fpath, data in old_files.items():
        if fpath not in new_files:
            changes['removed'].append(fpath)
        else:
            new_data = new_files[fpath]
            if data['hash'] != new_data['hash']:
                changes['modified_content'].append(fpath)
            elif data['meta']['mode'] != new_data['meta']['mode'] or \
                 data['meta']['uid'] != new_data['meta']['uid']:
                changes['modified_perms'].append(fpath)

    for fpath in new_files:
        if fpath not in old_files:
            changes['added'].append(fpath)

    return changes

def print_report(changes):
    total_changes = sum(len(v) for v in changes.values())
    if total_changes == 0:
        print("\n[OK] Integridade Verificada: Nenhuma alteração detectada.")
        return

    print(f"\n[!] ALERTAS DE INTEGRIDADE: {total_changes} alterações detectadas!\n")

    if changes['modified_content']:
        print("[MODIFICADOS - CONTEÚDO]")
        for f in changes['modified_content']:
            print(f"   ! {f}")

    if changes['modified_perms']:
        print("\n[MODIFICADOS - PERMISSÕES/DONO]")
        for f in changes['modified_perms']:
            print(f"   * {f}")

    if changes['added']:
        print("\n[NOVOS ARQUIVOS]")
        for f in changes['added']:
            print(f"   + {f}")

    if changes['removed']:
        print("\n[ARQUIVOS REMOVIDOS]")
        for f in changes['removed']:
            print(f"   - {f}")

def main():
    parser = argparse.ArgumentParser(description="Auditoria de Integridade de Arquivos (FIM)")
    parser.add_argument('--action', choices=['init', 'check', 'update'], required=True, help="Ação a executar")
    args = parser.parse_args()

    if args.action == 'init':
        if os.path.exists(DB_FILE):
            print("[!] DB já existe. Use 'update' para sobrescrever ou remova o arquivo.")
            return
        state = scan_system()
        save_db(state)

    elif args.action == 'check':
        db = load_db()
        if not db:
            print("[!] Base de dados não encontrada. Execute com --action init primeiro.")
            return

        current_state = scan_system()
        changes = compare_states(db, current_state)
        print_report(changes)

    elif args.action == 'update':
        print("[*] Atualizando base de integridade (aceitando estado atual como válido)...")
        state = scan_system()
        save_db(state)

if __name__ == "__main__":
    main()
