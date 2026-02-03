#!/usr/bin/env python3
import sys
import argparse
import threading
import time
import random
import urllib.request
import urllib.error
import string
import json

# Configuração de cores
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

stats = {
    "requests": 0,
    "2xx": 0,
    "401": 0,
    "403": 0,
    "429": 0,
    "errors": 0
}
running = True

def generate_fake_token():
    return 'eyJ' + ''.join(random.choices(string.ascii_letters + string.digits, k=120))

def attack_thread(url, tokens, rate_delay):
    global stats, running

    while running:
        try:
            req = urllib.request.Request(url)

            # Escolher token ou gerar um falso
            if tokens:
                token = random.choice(tokens)
            else:
                token = generate_fake_token()

            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "API-Stress-Tester/1.0")

            # Simular payload JSON se for POST (assumindo GET para load básico, mas adicionando flexibilidade futura)
            # Para este script, vamos focar em GET para validar auth/rate-limit

            start_req = time.time()
            with urllib.request.urlopen(req, timeout=5) as response:
                stats["requests"] += 1
                if 200 <= response.status < 300:
                    stats["2xx"] += 1

        except urllib.error.HTTPError as e:
            stats["requests"] += 1
            if e.code == 401:
                stats["401"] += 1
            elif e.code == 403:
                stats["403"] += 1
            elif e.code == 429:
                stats["429"] += 1
            else:
                stats["errors"] += 1
        except Exception:
            stats["errors"] += 1

        if rate_delay > 0:
            time.sleep(rate_delay)

def monitor_thread():
    global stats, running
    start_time = time.time()
    while running:
        elapsed = time.time() - start_time
        if elapsed > 0:
            rps = stats["requests"] / elapsed
            print(f"\r{Colors.OKBLUE}[*] Reqs: {stats['requests']} | 200 OK: {stats['2xx']} | 401 Auth: {stats['401']} | 429 RateLimit: {stats['429']} | Errors: {stats['errors']}{Colors.ENDC}", end="")
        time.sleep(1)

def main():
    global running
    parser = argparse.ArgumentParser(description="Simulador de Abuso de API (Token Rotation & Rate Limit Test)")
    parser.add_argument("url", help="Endpoint da API (ex: http://api.example.com/v1/users)")
    parser.add_argument("--tokens", help="Arquivo com lista de tokens válidos (opcional, se não fornecido gera aleatórios)")
    parser.add_argument("--threads", type=int, default=5, help="Número de threads (default: 5)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay entre requisições por thread em segundos (default: 0)")
    parser.add_argument("--duration", type=int, default=60, help="Duração do teste (default: 60s)")

    args = parser.parse_args()

    loaded_tokens = []
    if args.tokens:
        try:
            with open(args.tokens, 'r') as f:
                loaded_tokens = [line.strip() for line in f if line.strip()]
            print(f"{Colors.OKGREEN}Carregados {len(loaded_tokens)} tokens do arquivo.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Erro ao ler arquivo de tokens: {e}{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"{Colors.WARNING}Nenhum arquivo de token fornecido. Usando tokens aleatórios (Fuzzing de Auth).{Colors.ENDC}")

    print(f"{Colors.HEADER}=== Iniciando API Abuse Simulator ==={Colors.ENDC}")
    print(f"Alvo: {args.url}")

    monitor = threading.Thread(target=monitor_thread)
    monitor.daemon = True
    monitor.start()

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=attack_thread, args=(args.url, loaded_tokens, args.delay))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrompido!{Colors.ENDC}")

    running = False
    print(f"\n{Colors.OKGREEN}Teste finalizado.{Colors.ENDC}")
    print(f"Stats finais: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    main()
