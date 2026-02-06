#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scanner de Segredos Cloud
=========================
Varre diretórios e variáveis de ambiente em busca de credenciais expostas.
Detecta chaves AWS, Google, Azure, Private Keys e palavras-chave suspeitas.

Uso:
    python3 scanner_segredos_cloud.py --path /var/www/html --scan-env
"""

import os
import re
import argparse
import sys

# Padrões de Regex para Segredos
PATTERNS = {
    "AWS Access Key": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
    "AWS Secret Key": r"(?i)aws(.{0,20})?(?-i)['\"][0-9a-zA-Z\/+]{40}['\"]",
    "Google API Key": r"AIza[0-9A-Za-z\\-_]{35}",
    "Slack Token": r"xox[pbora]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32}",
    "Private Key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
    "Generic Secret": r"(?i)(?:password|secret|token|api_key|access_key)(?:.{0,5})?=(?:.{0,5})?['\"][a-zA-Z0-9@#$%^&+=]{8,}['\"]",
    "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,255}"
}

IGNORE_DIRS = [".git", "node_modules", "__pycache__", "venv", ".idea", ".vscode"]
IGNORE_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".exe", ".dll", ".so", ".o", ".pyc"]

def scan_content(content, source_name):
    findings = []
    for name, pattern in PATTERNS.items():
        # Usar finditer para garantir que pegamos o match completo (group 0)
        # independente de grupos de captura internos.
        matches = re.finditer(pattern, content)
        for match in matches:
            match_str = match.group(0)

            # Ofuscar segredo no log
            if len(match_str) > 8:
                masked = match_str[:4] + "*" * (len(match_str) - 8) + match_str[-4:]
            else:
                masked = "****"

            findings.append((name, masked))
    return findings

def scan_file(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            findings = scan_content(content, filepath)
    except Exception as e:
        pass

    if findings:
        print(f"\n[!] Segredos encontrados em ARQUIVO: {filepath}")
        for name, secret in findings:
            print(f"    - {name}: {secret}")

def scan_env():
    print("[*] Iniciando varredura de Variáveis de Ambiente...")
    found = False
    for key, value in os.environ.items():
        findings = scan_content(value, f"ENV:{key}")

        # Check suspicious key names
        if re.search(r"(?i)(key|secret|token|password|auth)", key):
            if len(value) > 8:
                findings.append(("Suspicious Env Var Name", f"{key}=****"))

        if findings:
            found = True
            print(f"[!] Segredos encontrados em VAR AMBIENTE: {key}")
            for name, secret in findings:
                print(f"    - {name}: {secret}")

    if not found:
        print("[OK] Nenhuma credencial óbvia encontrada no ambiente.")

def scan_directory(path):
    print(f"[*] Iniciando varredura em diretório: {path}")
    count = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if any(file.endswith(ext) for ext in IGNORE_EXTS):
                continue

            filepath = os.path.join(root, file)
            scan_file(filepath)
            count += 1
            if count % 1000 == 0:
                print(f"   ...Analisados {count} arquivos")

def main():
    parser = argparse.ArgumentParser(description="Scanner de Segredos Cloud")
    parser.add_argument('--path', help="Caminho do diretório para verificar")
    parser.add_argument('--scan-env', action='store_true', help="Verificar variáveis de ambiente")

    args = parser.parse_args()

    if not args.path and not args.scan_env:
        parser.print_help()
        sys.exit(1)

    if args.scan_env:
        scan_env()

    if args.path:
        if os.path.exists(args.path):
            scan_directory(args.path)
        else:
            print(f"[!] Caminho não encontrado: {args.path}")

if __name__ == "__main__":
    main()
